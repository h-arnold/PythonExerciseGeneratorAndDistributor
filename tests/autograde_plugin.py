"""Pytest plugin scaffolding for autograding exercise notebooks.

The plugin will aggregate detailed test results for consumption by the
GitHub Classroom autograder. It centralises result collection, normalises
metadata (task numbers, friendly names), and records captured output for the
final report. Error handling will prioritise resilience: the hooks will guard
against unexpected pytest objects and fall back to safe defaults so that a
malformed test cannot abort the entire grading run.
"""

from __future__ import annotations

import inspect
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AutogradeTestResult:
    """Container for per-test outcome data destined for the autograder."""

    nodeid: str
    display_name: str
    task_number: int | None
    status: str
    score: float
    message: str | None
    line_number: int | None
    duration: float | None
    captured_stdout: str | None = None
    captured_stderr: str | None = None
    captured_log: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AutogradeState:
    """Mutable state shared across pytest hooks during autograde collection."""

    results: list[AutogradeTestResult] = field(default_factory=list)
    total_score: float = 0.0
    max_score: float = 0.0
    encountered_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    start_timestamp: float | None = None
    end_timestamp: float | None = None
    results_path: Path | None = None
    metadata: dict[str, AutogradeTestMetadata] = field(default_factory=dict)
    reported_nodeids: set[str] = field(default_factory=set)


@dataclass(slots=True)
class AutogradeTestMetadata:
    """Static metadata describing a collected pytest item."""

    display_name: str
    task_number: int | None
    marker_name: str | None = None


_AUTOGRADE_STATE: AutogradeState | None = None


def _normalise_name(raw_name: str) -> str:
    """Normalise a raw test name by fixing whitespace and prefixes."""

    cleaned = " ".join(raw_name.strip().split())
    lowered = cleaned.lower()
    for prefix in ("test ", "test_", "tests ", "tests_"):
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    cleaned = cleaned.lstrip(" _")
    cleaned = cleaned.replace("_", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned or raw_name.strip() or "Unnamed test"


def derive_display_name(nodeid: str, *, doc: str | None, marker_name: str | None = None) -> str:
    """Return a human-friendly display name derived from pytest metadata."""

    candidates: list[str] = []
    if marker_name:
        candidates.append(str(marker_name))
    if doc:
        first_line = doc.strip().splitlines()[0].strip()
        if first_line:
            candidates.append(first_line)
    last_segment = nodeid.split("::")[-1]
    candidates.append(last_segment)
    for candidate in candidates:
        normalised = _normalise_name(candidate)
        if normalised:
            return normalised
    return "Unnamed test"


def trim_failure_message(message: str, *, max_length: int = 1_000) -> str:
    """Shorten failure messages while preserving key diagnostic information."""

    normalised = " ".join(message.strip().split())
    if max_length <= 3:
        return normalised[:max_length]
    if len(normalised) <= max_length:
        return normalised
    return normalised[: max_length - 3].rstrip() + "..."


def pytest_addoption(parser: Any) -> None:
    """Register command-line options for configuring the autograde plugin."""

    group = parser.getgroup("autograde", "Autograde integration")
    group.addoption(
        "--autograde-results-path",
        action="store",
        default=None,
        metavar="PATH",
        help=(
            "Write autograde results JSON to PATH; required in CI workflows but "
            "optional for local runs."
        ),
    )


def pytest_configure(config: Any) -> None:
    """Initialise plugin state and attach it to the pytest config object."""

    global _AUTOGRADE_STATE

    results_option = None
    try:
        results_option = config.getoption("autograde_results_path")
    except Exception:  # pragma: no cover - defensive for unexpected config
        results_option = None

    state = getattr(config, "_autograde_state", None)
    if state is None:
        state = AutogradeState()
        config._autograde_state = state  # type: ignore[attr-defined]

    state.results_path = Path(results_option) if results_option else None
    if state.start_timestamp is None:
        state.start_timestamp = time.time()
    if state.results_path is None:
        warning = (
            "Autograde plugin active but --autograde-results-path was not provided; "
            "results will not be written."
        )
        if warning not in state.notes:
            state.notes.append(warning)

    _AUTOGRADE_STATE = state


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Augment collected tests with autograde metadata before execution."""

    state = getattr(config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    for item in items:
        marker = item.get_closest_marker("task") if hasattr(
            item, "get_closest_marker") else None
        marker_kwargs = marker.kwargs if marker else {}
        task_number_raw = marker_kwargs.get(
            "taskno") if isinstance(marker_kwargs, dict) else None
        task_number: int | None
        if isinstance(task_number_raw, int):
            task_number = task_number_raw
        elif isinstance(task_number_raw, str):
            task_number = int(
                task_number_raw) if task_number_raw.isdigit() else None
        else:
            task_number = None

        marker_name = marker_kwargs.get("name") if isinstance(
            marker_kwargs, dict) else None
        doc = None
        if hasattr(item, "obj"):
            try:
                doc = inspect.getdoc(item.obj)
            except Exception:  # pragma: no cover - defensive guard
                doc = None

        display_name = derive_display_name(
            item.nodeid,
            doc=doc,
            marker_name=str(marker_name) if marker_name is not None else None,
        )
        state.metadata[item.nodeid] = AutogradeTestMetadata(
            display_name=display_name,
            task_number=task_number,
            marker_name=str(marker_name) if marker_name is not None else None,
        )

    state.max_score = float(len(state.metadata))


def pytest_runtest_logreport(report: Any) -> None:
    """Record per-phase test results emitted by pytest's reporting pipeline."""

    state = _AUTOGRADE_STATE
    if not isinstance(state, AutogradeState):
        return

    nodeid = getattr(report, "nodeid", None)
    if not isinstance(nodeid, str):
        return

    when = getattr(report, "when", None)
    outcome = getattr(report, "outcome", None)

    is_call_phase = when == "call"
    already_recorded = nodeid in state.reported_nodeids

    if is_call_phase and already_recorded:
        return
    if not is_call_phase and (outcome != "failed" or already_recorded):
        return

    metadata = state.metadata.get(nodeid)
    doc = None
    if metadata is None and hasattr(report, "head_line"):
        doc = getattr(report, "head_line", None)

    display_name = metadata.display_name if metadata else derive_display_name(
        nodeid, doc=doc, marker_name=None)
    task_number = metadata.task_number if metadata else None

    if is_call_phase:
        if outcome == "passed":
            status = "pass"
            score = 1.0
            message = None
        elif outcome == "skipped":
            status = "fail"
            score = 0.0
            message_source = getattr(
                report, "longreprtext", None) or "Test skipped"
            message = trim_failure_message(message_source)
        else:
            status = "fail"
            score = 0.0
            message_source = getattr(report, "longreprtext", None)
            if not message_source and hasattr(report, "longrepr"):
                message_source = str(report.longrepr)
            message = trim_failure_message(message_source or "Test failed")
    else:
        status = "error"
        score = 0.0
        message_source = getattr(report, "longreprtext", None)
        if not message_source and hasattr(report, "longrepr"):
            message_source = str(report.longrepr)
        message = trim_failure_message(
            message_source or "Test error during setup/teardown")

    location = getattr(report, "location", None)
    if isinstance(location, tuple) and len(location) > 1:
        try:
            line_number = int(location[1]) + 1
        except Exception:
            line_number = 0
    else:
        line_number = 0

    duration = getattr(report, "duration", None)
    captured_stdout = getattr(report, "capstdout", None)
    captured_stderr = getattr(report, "capstderr", None)
    captured_log = getattr(report, "caplogtext", None)

    result = AutogradeTestResult(
        nodeid=nodeid,
        display_name=display_name,
        task_number=task_number,
        status=status,
        score=score,
        message=message,
        line_number=line_number,
        duration=duration,
        captured_stdout=captured_stdout or None,
        captured_stderr=captured_stderr or None,
        captured_log=captured_log or None,
    )

    state.results.append(result)
    state.reported_nodeids.add(nodeid)
    state.total_score += score
    state.max_score = float(max(len(state.metadata), len(state.results)))

    if status == "error" and message:
        detail = f"{display_name}: {message}"
        if detail not in state.encountered_errors:
            state.encountered_errors.append(detail)


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Finalise aggregation and prepare data for consumption post-test run."""

    state = getattr(session.config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    state.end_timestamp = time.time()

    results_path = state.results_path
    results_payload = [_result_to_dict(res) for res in state.results]
    max_score = float(len(state.metadata)) if state.metadata else float(
        len(results_payload))
    earned_score = float(sum(entry["score"] for entry in results_payload))
    overall_status = _derive_overall_status(state, results_payload)

    state.max_score = max_score
    state.total_score = earned_score

    payload: dict[str, Any] = {
        "status": overall_status,
        "score": earned_score,
        "max_score": max_score,
        "tests": results_payload,
        "start_timestamp": state.start_timestamp,
        "end_timestamp": state.end_timestamp,
    }
    if state.encountered_errors:
        payload["errors"] = state.encountered_errors
    if state.notes:
        payload["notes"] = state.notes

    if not results_path:
        return

    try:
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with results_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except Exception as exc:  # pragma: no cover - exercised in error handling tests
        fallback = {"status": "error", "score": 0.0,
                    "max_score": 0.0, "tests": []}
        try:
            with results_path.open("w", encoding="utf-8") as handle:
                json.dump(fallback, handle, ensure_ascii=False, indent=2)
        except Exception:
            pass
        state.encountered_errors.append(
            f"Failed to write autograde results: {exc}")
        print(
            f"Autograde plugin failed to write results: {exc}", file=sys.stderr)


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Emit a concise summary tailored for the GitHub Classroom autograder."""

    config = getattr(terminalreporter, "config", None)
    state = getattr(config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    total_tests = len(state.metadata) if state.metadata else len(state.results)
    passed = sum(1 for result in state.results if result.status == "pass")
    overall_status = _derive_overall_status(
        state, [_result_to_dict(res) for res in state.results])
    if state.results_path:
        terminalreporter.write_line(
            f"Autograde summary: {passed}/{total_tests} passed | "
            f"Score {state.total_score}/{state.max_score} | Status {overall_status}"
        )
        terminalreporter.write_line(
            f"Autograde results written to: {state.results_path}")
    else:
        terminalreporter.write_line(
            "Autograde summary: no results file written (missing --autograde-results-path)"
        )
    for message in state.encountered_errors:
        terminalreporter.write_line(f"Autograde error: {message}")
    for note in state.notes:
        terminalreporter.write_line(f"Autograde note: {note}")


def _result_to_dict(result: AutogradeTestResult) -> dict[str, Any]:
    """Convert a test result dataclass to a serialisable dictionary."""

    entry: dict[str, Any] = {
        "nodeid": result.nodeid,
        "name": result.display_name,
        "taskno": result.task_number,
        "status": result.status,
        "score": result.score,
        "message": result.message,
        "line_no": result.line_number,
        "duration": result.duration,
    }
    if result.captured_stdout:
        entry["stdout"] = result.captured_stdout
    if result.captured_stderr:
        entry["stderr"] = result.captured_stderr
    if result.captured_log:
        entry["log"] = result.captured_log
    if result.extra:
        entry["extra"] = result.extra
    return entry


def _derive_overall_status(state: AutogradeState, tests: list[dict[str, Any]]) -> str:
    """Compute overall status across all collected tests."""

    has_error = any(result.get("status") == "error" for result in tests)
    if has_error or state.encountered_errors:
        return "error"
    has_fail = any(result.get("status") == "fail" for result in tests)
    if has_fail:
        return "fail"
    if tests:
        return "pass"
    return "error"
