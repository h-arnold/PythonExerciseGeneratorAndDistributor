"""CLI wrapper for building GitHub Classroom autograde payloads.

This script orchestrates a pytest run using the autograde plugin, loads the
resulting JSON artefact, validates the structure, and emits both a Base64
payload for the `autograding-grading-reporter` action and optional human-readable
summary output. The script is intended to run inside GitHub Actions but remains
usable locally for debugging the grading pipeline:

    uv run python scripts/build_autograde_payload.py --pytest-args=-k test_name

The command will write the raw autograde results, a Base64 payload suitable for
exporting as a GitHub Actions output, and an optional summary JSON file.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shlex
import subprocess
import sys
import textwrap
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict, TypeGuard

DEFAULT_PYTEST_ARGS = ["-q"]
AUTOGRADE_OPTION = "--autograde-results-path"
SUMMARY_HEADER = "=== Autograde Summary ==="


class AutogradeTestEntry(TypedDict):
    """Raw test entry emitted by the autograde pytest plugin."""

    status: str
    score: float | int | str | None
    name: NotRequired[str]
    nodeid: NotRequired[str]
    taskno: NotRequired[int | str | None]
    task: NotRequired[int | str | None]
    message: NotRequired[str | None]
    line_no: NotRequired[int | float | str | None]
    duration: NotRequired[float | int | None]
    stdout: NotRequired[str]
    stderr: NotRequired[str]
    log: NotRequired[str]
    extra: NotRequired[dict[str, Any]]


class AutogradePayloadTest(TypedDict):
    """Normalised test entry persisted in the autograde payload."""

    name: str
    status: str
    score: float
    line_no: int
    task: NotRequired[int | str | None]
    taskno: NotRequired[int | str | None]
    nodeid: NotRequired[str | None]
    duration: NotRequired[float | int | None]
    message: NotRequired[str | None]
    stdout: NotRequired[str]
    stderr: NotRequired[str]
    log: NotRequired[str]
    extra: NotRequired[dict[str, Any]]


class AutogradeResults(TypedDict):
    """JSON payload emitted by the pytest plugin before CLI processing."""

    status: str
    max_score: float | int
    tests: list[AutogradeTestEntry]
    score: NotRequired[float | int | None]
    errors: NotRequired[list[str] | str | None]
    notes: NotRequired[list[str] | str | None]
    start_timestamp: NotRequired[float | str | None]
    end_timestamp: NotRequired[float | str | None]


class AutogradePayload(TypedDict):
    """Payload consumed by the GitHub autograding reporter."""

    status: str
    max_score: float
    score: float
    tests: list[AutogradePayloadTest]
    generated_at: str
    errors: NotRequired[list[str] | str | None]
    notes: NotRequired[list[str] | str | None]
    start_timestamp: NotRequired[float | str | None]
    end_timestamp: NotRequired[float | str | None]


def _is_autograde_results(obj: object) -> TypeGuard[AutogradeResults]:
    """Best-effort structural check for plugin result payloads."""

    if not isinstance(obj, dict):
        return False
    for key in ("max_score", "status", "tests"):
        if key not in obj:
            return False
    tests = obj.get("tests")
    if not isinstance(tests, list):
        return False
    return all(isinstance(test, dict) for test in tests)


def _validate_results_payload(data: object) -> AutogradeResults:
    """Validate the plugin JSON payload and return a typed mapping."""

    if not isinstance(data, dict):
        raise RuntimeError("Autograde results must be a JSON object.")

    missing_key = next((key for key in ("max_score", "status", "tests") if key not in data), None)
    if missing_key is not None:
        raise RuntimeError(f"Autograde results missing required key: {missing_key}")

    tests = data.get("tests")
    if not isinstance(tests, list):
        raise RuntimeError("Autograde results 'tests' entry must be a list.")

    if not all(isinstance(test, dict) for test in tests):
        raise RuntimeError("Autograde results 'tests' entries must be objects.")

    if not _is_autograde_results(data):
        raise RuntimeError("Autograde results failed structural validation.")

    return data


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the CLI wrapper."""

    parser = argparse.ArgumentParser(
        description="Execute pytest with the autograde plugin and emit payload data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--pytest-args",
        action="append",
        default=None,
        help=(
            "Additional arguments forwarded to pytest. Repeat the flag to supply "
            "multiple arguments (e.g. --pytest-args=-k --pytest-args task1)."
        ),
    )
    parser.add_argument(
        "--results-json",
        type=Path,
        default=Path("tmp/autograde/results.json"),
        help="Path where the autograde plugin should write its JSON results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/autograde/payload.txt"),
        help="Destination file for the Base64-encoded autograde payload.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Optional path for writing the decoded payload as formatted JSON.",
    )

    args = parser.parse_args(argv)

    raw_pytest_args = args.pytest_args
    if raw_pytest_args is None:
        args.pytest_args = list(DEFAULT_PYTEST_ARGS)
    else:
        expanded: list[str] = []
        for chunk in raw_pytest_args:
            expanded.extend(shlex.split(chunk))
        args.pytest_args = expanded if expanded else list(DEFAULT_PYTEST_ARGS)

    return args


def validate_environment() -> None:
    """Ensure environment variables are compatible with the autograde flow."""

    notebooks_dir = os.environ.get("PYTUTOR_NOTEBOOKS_DIR")
    reported_value = notebooks_dir if notebooks_dir else "<unset>"
    print(f"Environment: PYTUTOR_NOTEBOOKS_DIR={reported_value}")
    if not notebooks_dir:
        return

    normalised_dir = notebooks_dir.replace("\\", "/")
    allowed_dirs = {"notebooks", "notebooks/solutions"}
    # TODO: offer a CLI flag to override the notebook directory when workflows expand.
    if normalised_dir in allowed_dirs:
        return

    allowed_display = "', '".join(sorted(allowed_dirs))
    raise RuntimeError(
        "PYTUTOR_NOTEBOOKS_DIR must be unset or one of "
        f"'{allowed_display}' when building autograde payloads."
    )


def _ensure_autograde_option(pytest_args: Sequence[str], results_path: Path) -> list[str]:
    """Attach the autograde results path option if not already present."""

    option_present = any(
        arg == AUTOGRADE_OPTION or arg.startswith(f"{AUTOGRADE_OPTION}=") for arg in pytest_args
    )
    if option_present:
        return list(pytest_args)
    updated = list(pytest_args)
    updated.append(f"{AUTOGRADE_OPTION}={results_path}")
    return updated


def run_pytest(pytest_args: Sequence[str], results_path: Path) -> int:
    """Run pytest with the autograde plugin and return the exit code."""

    args_with_option = _ensure_autograde_option(pytest_args, results_path)
    command = [sys.executable, "-m", "pytest", *args_with_option]
    printable = shlex.join(command)
    print(f"Executing: {printable}")
    try:
        completed_process = subprocess.run(command, check=False)
    except OSError as exc:  # pragma: no cover - defensive logging for unexpected failures
        print(f"Failed to execute pytest: {exc}", file=sys.stderr)
        return 1
    return int(completed_process.returncode)


def load_results(results_path: Path) -> AutogradeResults:
    """Load the autograde JSON results emitted by the pytest plugin."""

    if not results_path.exists():
        raise RuntimeError(f"Autograde results not found at {results_path}")
    try:
        with results_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Results JSON at {results_path} is invalid: {exc}") from exc

    return _validate_results_payload(data)


def _ensure_float(value: Any, error_message: str) -> float:
    """Internal helper to coerce numeric fields to float with consistent errors."""

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(error_message) from exc


def _normalise_line_number(value: Any) -> int:
    """Internal helper to provide a safe integer line number for a test entry."""

    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _populate_task_fields(
    payload: AutogradePayloadTest,
    test: AutogradeTestEntry,
) -> None:
    """Populate task-related metadata for a payload entry."""

    has_task_information = "task" in test or "taskno" in test
    if not has_task_information:
        return

    task_value: int | str | None = test.get("task")
    if task_value is None:
        task_value = test.get("taskno")
    payload["task"] = task_value
    if "taskno" in test:
        payload["taskno"] = test.get("taskno")


def _populate_optional_fields(
    payload: AutogradePayloadTest,
    test: AutogradeTestEntry,
) -> None:
    """Populate optional diagnostic fields for a payload entry."""

    node_identifier = test.get("nodeid")
    if node_identifier is not None:
        payload["nodeid"] = str(node_identifier)

    duration_value = test.get("duration")
    if duration_value is not None:
        payload["duration"] = duration_value

    message = test.get("message")
    if message is not None:
        payload["message"] = str(message)

    stdout_value = test.get("stdout")
    if stdout_value is not None:
        payload["stdout"] = str(stdout_value)

    stderr_value = test.get("stderr")
    if stderr_value is not None:
        payload["stderr"] = str(stderr_value)

    log_value = test.get("log")
    if log_value is not None:
        payload["log"] = str(log_value)

    extra_value = test.get("extra")
    if isinstance(extra_value, dict):
        payload["extra"] = extra_value


def _normalise_test_entry(test: AutogradeTestEntry) -> AutogradePayloadTest:
    """Internal helper to map a raw test result into the payload-friendly form."""

    name_source = test.get("name") or test.get("nodeid") or "Unnamed test"
    normalised_name = str(name_source)
    status = str(test.get("status", "error"))
    score_value = _ensure_float(
        test.get("score", 0.0), f"Test entry for {normalised_name} has non-numeric score."
    )
    line_number = _normalise_line_number(test.get("line_no"))

    payload: AutogradePayloadTest = {
        "name": normalised_name,
        "status": status,
        "score": score_value,
        "line_no": line_number,
    }

    _populate_task_fields(payload, test)
    _populate_optional_fields(payload, test)

    return payload


def _calculate_earned_score(
    raw_results: AutogradeResults,
    tests: Sequence[AutogradePayloadTest],
) -> float:
    """Internal helper to derive the earned score while mirroring legacy checks."""

    if "score" in raw_results and raw_results["score"] is not None:
        candidate = raw_results["score"]
    else:
        candidate = sum(test["score"] for test in tests)
    return _ensure_float(candidate, "score in results must be numeric if provided.")


def build_payload(raw_results: AutogradeResults) -> AutogradePayload:
    """Construct the payload dictionary expected by autograding-grading-reporter."""

    max_score = _ensure_float(raw_results["max_score"], "max_score in results must be numeric.")
    status = str(raw_results["status"])
    raw_tests = raw_results["tests"]
    normalised_tests = [_normalise_test_entry(test) for test in raw_tests]
    earned_score_value = _calculate_earned_score(raw_results, normalised_tests)

    payload: AutogradePayload = {
        "status": status,
        "max_score": max_score,
        "score": earned_score_value,
        "tests": normalised_tests,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    # Explicitly assign optional fields to satisfy TypedDict type checking
    if "errors" in raw_results:
        payload["errors"] = raw_results["errors"]
    if "notes" in raw_results:
        payload["notes"] = raw_results["notes"]
    if "start_timestamp" in raw_results:
        payload["start_timestamp"] = raw_results["start_timestamp"]
    if "end_timestamp" in raw_results:
        payload["end_timestamp"] = raw_results["end_timestamp"]

    return payload


def encode_payload(payload: AutogradePayload) -> str:
    """Encode the payload as a Base64 JSON string."""

    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    encoded = base64.b64encode(json_bytes)
    return encoded.decode("ascii")


def _coerce_task_id_to_int(task_id: Any) -> int | None:
    """Best-effort coercion for numeric task identifiers."""

    result: int | None = None
    if isinstance(task_id, bool):
        result = None
    elif isinstance(task_id, int):
        result = task_id
    elif isinstance(task_id, float) and task_id.is_integer():
        result = int(task_id)
    elif isinstance(task_id, str):
        candidate = task_id.strip()
        if candidate:
            try:
                result = int(candidate)
            except ValueError:
                result = None
    return result


def _task_group_sort_key(
    item: tuple[str | int | None, list[AutogradePayloadTest]],
) -> tuple[int, int, str]:
    """Sort key that prefers numeric task identifiers."""

    task_id, _ = item
    if task_id is None:
        return (2, 0, "")
    numeric_task = _coerce_task_id_to_int(task_id)
    if numeric_task is not None:
        return (0, numeric_task, "")
    return (1, 0, str(task_id))


def print_summary(payload: AutogradePayload) -> None:
    """Emit a human-readable summary of the autograde results."""

    tests = payload["tests"]
    max_score = payload["max_score"]
    earned_score = payload["score"]
    status = payload["status"]
    total_tests = len(tests)
    passed_tests = sum(1 for test in tests if test["status"] == "pass")
    percentage = (earned_score / max_score * 100.0) if max_score else 0.0

    print(SUMMARY_HEADER)
    print(f"Status: {status}")
    print(f"Points: {earned_score}/{max_score} ({percentage:.1f}%)")
    print(f"Tests Passed: {passed_tests}/{total_tests}")

    grouped: dict[str | int | None, list[AutogradePayloadTest]] = defaultdict(list)
    for test in tests:
        grouped[test.get("task")].append(test)

    print("Task Breakdown:")
    header = f"{'Task':<10}{'Passed':>8}{'Total':>8}{'Points':>10}"
    print(header)
    for task_id, task_tests in sorted(grouped.items(), key=_task_group_sort_key):
        passed = sum(1 for test in task_tests if test["status"] == "pass")
        total = len(task_tests)
        points = sum(test["score"] for test in task_tests)
        task_label = "None" if task_id is None else str(task_id)
        print(f"{task_label:<10}{passed:>8}{total:>8}{points:>10.2f}")

    failing_tests = [test for test in tests if test["status"] != "pass"]
    if failing_tests:
        print("Failing Tests:")
        for test in failing_tests:
            message = test.get("message")
            message_text = "(no message)" if message is None else str(message)
            truncated = textwrap.shorten(message_text, width=200, placeholder="...")
            print(f"- {test['name']}: {truncated}")


def write_outputs(
    encoded_payload: str,
    payload: AutogradePayload,
    output_path: Path,
    summary_path: Path | None,
) -> None:
    """Persist the encoded payload and optional JSON summary to disk."""

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            handle.write(encoded_payload)
            handle.write("\n")
    except Exception as exc:
        print(f"Warning: failed to write payload to {output_path}: {exc}", file=sys.stderr)

    if summary_path is None:
        return

    try:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except Exception as exc:
        print(f"Warning: failed to write summary to {summary_path}: {exc}", file=sys.stderr)


def write_github_outputs(encoded: str, payload: AutogradePayload) -> None:
    """Append outputs for downstream GitHub Actions steps when possible."""

    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if not github_output_path:
        return

    entries = {
        "encoded_payload": encoded,
        "overall_status": str(payload.get("status", "unknown")),
        "earned_score": str(payload.get("score", "0")),
        "max_score": str(payload.get("max_score", "0")),
    }

    try:
        with Path(github_output_path).open("a", encoding="utf-8") as handle:
            for key, value in entries.items():
                handle.write(f"{key}={value}\n")
    except Exception as exc:
        print(f"Warning: failed to write GitHub outputs: {exc}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the CLI wrapper."""

    try:
        args = parse_args(argv)
        validate_environment()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    results_path: Path = args.results_json
    output_path: Path = args.output
    summary_path: Path | None = args.summary
    results_path.parent.mkdir(parents=True, exist_ok=True)

    exit_code = run_pytest(args.pytest_args, results_path)

    try:
        raw_results = load_results(results_path)
        payload = build_payload(raw_results)
        encoded_payload = encode_payload(payload)
        print_summary(payload)
        write_outputs(encoded_payload, payload, output_path, summary_path)
        write_github_outputs(encoded_payload, payload)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return int(exit_code)


if __name__ == "__main__":  # pragma: no cover - entry point guard
    sys.exit(main())
