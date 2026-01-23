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
from typing import Any

DEFAULT_PYTEST_ARGS = ["-q"]
AUTOGRADE_OPTION = "--autograde-results-path"
SUMMARY_HEADER = "=== Autograde Summary ==="


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
    if notebooks_dir and notebooks_dir != "notebooks":
        raise RuntimeError(
            "PYTUTOR_NOTEBOOKS_DIR must be unset or 'notebooks' when building autograde payloads."
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


def load_results(results_path: Path) -> dict[str, Any]:
    """Load the autograde JSON results emitted by the pytest plugin."""

    if not results_path.exists():
        raise RuntimeError(f"Autograde results not found at {results_path}")
    try:
        with results_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Results JSON at {results_path} is invalid: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Autograde results must be a JSON object.")
    for key in ("max_score", "status", "tests"):
        if key not in data:
            raise RuntimeError(f"Autograde results missing required key: {key}")
    if not isinstance(data["tests"], list):
        raise RuntimeError("Autograde results 'tests' entry must be a list.")

    return data


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


def _normalise_test_entry(test: Any) -> dict[str, Any]:
    """Internal helper to map a raw test result into the payload-friendly form."""

    if not isinstance(test, dict):
        raise RuntimeError("Each test entry must be an object.")
    entry = dict(test)
    name = entry.get("name") or entry.get("nodeid") or "Unnamed test"
    entry["name"] = str(name)
    entry["status"] = str(entry.get("status", "error"))
    entry["score"] = _ensure_float(
        entry.get("score", 0.0), f"Test entry for {entry['name']} has non-numeric score."
    )
    entry["line_no"] = _normalise_line_number(entry.get("line_no"))
    entry.setdefault("task", entry.get("taskno"))
    entry.setdefault("nodeid", test.get("nodeid"))
    entry.setdefault("duration", test.get("duration"))
    return entry


def _calculate_earned_score(raw_results: dict[str, Any], tests: Sequence[dict[str, Any]]) -> float:
    """Internal helper to derive the earned score while mirroring legacy checks."""

    if "score" in raw_results and raw_results["score"] is not None:
        candidate = raw_results["score"]
    else:
        candidate = sum(test.get("score", 0.0) for test in tests)
    return _ensure_float(candidate, "score in results must be numeric if provided.")


def build_payload(raw_results: dict[str, Any]) -> dict[str, Any]:
    """Construct the payload dictionary expected by autograding-grading-reporter."""

    max_score = _ensure_float(raw_results["max_score"], "max_score in results must be numeric.")
    status = str(raw_results["status"])
    raw_tests = raw_results.get("tests", [])
    normalised_tests = [_normalise_test_entry(test) for test in raw_tests]
    earned_score_value = _calculate_earned_score(raw_results, normalised_tests)

    payload: dict[str, Any] = {
        "status": status,
        "max_score": max_score,
        "score": earned_score_value,
        "tests": normalised_tests,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    for key in ("errors", "notes", "start_timestamp", "end_timestamp"):
        if key in raw_results:
            payload[key] = raw_results[key]
    return payload


def encode_payload(payload: dict[str, Any]) -> str:
    """Encode the payload as a Base64 JSON string."""

    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    encoded = base64.b64encode(json_bytes)
    return encoded.decode("ascii")


def print_summary(payload: dict[str, Any]) -> None:
    """Emit a human-readable summary of the autograde results."""

    tests = payload.get("tests", [])
    max_score = payload.get("max_score", 0.0)
    earned_score = payload.get("score", 0.0)
    status = payload.get("status", "unknown")
    total_tests = len(tests)
    passed_tests = sum(1 for test in tests if test.get("status") == "pass")
    percentage = (earned_score / max_score * 100.0) if max_score else 0.0

    print(SUMMARY_HEADER)
    print(f"Status: {status}")
    print(f"Points: {earned_score}/{max_score} ({percentage:.1f}%)")
    print(f"Tests Passed: {passed_tests}/{total_tests}")

    grouped: dict[str | int | None, list[dict[str, Any]]] = defaultdict(list)
    for test in tests:
        grouped[test.get("task")].append(test)

    print("Task Breakdown:")
    header = f"{'Task':<10}{'Passed':>8}{'Total':>8}{'Points':>10}"
    print(header)
    for task_id, task_tests in sorted(
        grouped.items(),
        key=lambda item: (item[0] is None, str(item[0])),
    ):
        passed = sum(1 for test in task_tests if test.get("status") == "pass")
        total = len(task_tests)
        points = sum(float(test.get("score", 0.0)) for test in task_tests)
        task_label = "None" if task_id is None else str(task_id)
        print(f"{task_label:<10}{passed:>8}{total:>8}{points:>10.2f}")

    failing_tests = [test for test in tests if test.get("status") != "pass"]
    if failing_tests:
        print("Failing Tests:")
        for test in failing_tests:
            message = test.get("message")
            message_text = "(no message)" if message is None else str(message)
            truncated = textwrap.shorten(message_text, width=200, placeholder="...")
            print(f"- {test['name']}: {truncated}")


def write_outputs(
    encoded_payload: str,
    payload: dict[str, Any],
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


def write_github_outputs(encoded: str, payload: dict[str, Any]) -> None:
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
