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
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ELLIPSIS_GUARD_LENGTH = 3
LOCATION_MIN_LENGTH = 2


def _empty_results() -> list[AutogradeTestResult]:
    return []


def _empty_error_messages() -> list[str]:
    return []


def _empty_notes() -> list[str]:
    return []


def _empty_metadata() -> dict[str, AutogradeTestMetadata]:
    return {}


def _empty_reported_nodeids() -> set[str]:
    return set()


def _empty_extra() -> dict[str, Any]:
    return {}


_autograde_state: AutogradeState | None = None


def _set_autograde_state(state: AutogradeState | None) -> None:
    global _autograde_state
    _autograde_state = state


def _get_autograde_state() -> AutogradeState | None:
    return _autograde_state


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
    extra: dict[str, Any] = field(default_factory=_empty_extra)


@dataclass(slots=True)
class AutogradeState:
    """Mutable state shared across pytest hooks during autograde collection."""

    results: list[AutogradeTestResult] = field(default_factory=_empty_results)
    total_score: float = 0.0
    max_score: float = 0.0
    encountered_errors: list[str] = field(default_factory=_empty_error_messages)
    notes: list[str] = field(default_factory=_empty_notes)
    start_timestamp: float | None = None
    end_timestamp: float | None = None
    results_path: Path | None = None
    metadata: dict[str, AutogradeTestMetadata] = field(default_factory=_empty_metadata)
    reported_nodeids: set[str] = field(default_factory=_empty_reported_nodeids)


@dataclass(slots=True)
class AutogradeTestMetadata:
    """Static metadata describing a collected pytest item."""

    display_name: str
    task_number: int | None
    marker_name: str | None = None
    slug: str | None = None


@dataclass(slots=True)
class _ReportContext:
    nodeid: str
    display_name: str
    task_number: int | None
    line_number: int | None
    duration: float | None
    captured_stdout: str | None
    captured_stderr: str | None
    captured_log: str | None


def _normalise_name(raw_name: str) -> str:
    """Normalise a raw test name by fixing whitespace and prefixes."""

    cleaned = " ".join(raw_name.strip().split())
    lowered = cleaned.lower()
    for prefix in ("test ", "test_", "tests ", "tests_"):
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    cleaned = cleaned.lstrip(" _")
    cleaned = cleaned.replace("_", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned or raw_name.strip() or "Unnamed test"


def _extract_slug_from_nodeid(nodeid: str) -> str | None:
    if not nodeid:
        return None
    path_segment = nodeid.split("::", 1)[0]
    if not path_segment:
        return None
    potential = path_segment.split("[", 1)[0].strip()
    if not potential:
        return None
    slug = Path(potential).stem
    return slug or None


def _get_task_marker(item: Any) -> Any | None:
    if not hasattr(item, "get_closest_marker"):
        return None
    try:
        return item.get_closest_marker("task")
    except Exception:  # pragma: no cover - defensive guard
        return None


def _extract_marker_kwargs(marker: Any) -> dict[str, Any]:
    kwargs = getattr(marker, "kwargs", None)
    return kwargs if isinstance(kwargs, dict) else {}


def _extract_marker_args(marker: Any) -> Sequence[Any]:
    args = getattr(marker, "args", ())
    if isinstance(args, Sequence) and not isinstance(args, (str, bytes)):
        return args
    return ()


def _select_task_source(marker_kwargs: dict[str, Any], marker_args: Sequence[Any]) -> Any | None:
    for key in ("taskno", "number"):
        if key in marker_kwargs:
            return marker_kwargs[key]
    if marker_args:
        return marker_args[0]
    return None


def _resolve_task_number(
    task_source: Any | None,
    *,
    item: Any,
    state: AutogradeState,
) -> int | None:
    if task_source is None:
        return None
    try:
        return int(task_source)
    except (TypeError, ValueError):
        note = (
            f"Task marker for {getattr(item, 'nodeid', 'unknown item')} "
            f"ignored invalid task number {task_source!r}."
        )
        if note not in state.notes:
            state.notes.append(note)
        return None


def _parse_task_marker(item: Any, state: AutogradeState) -> tuple[int | None, str | None]:
    marker = _get_task_marker(item)
    marker_kwargs = _extract_marker_kwargs(marker)
    marker_args = _extract_marker_args(marker)

    task_source = _select_task_source(marker_kwargs, marker_args)
    task_number = _resolve_task_number(task_source, item=item, state=state)

    marker_name_raw = marker_kwargs.get("name") if marker_kwargs else None
    marker_name = str(marker_name_raw) if marker_name_raw is not None else None
    return task_number, marker_name


def _get_item_doc(item: Any) -> str | None:
    if hasattr(item, "obj"):
        try:
            return inspect.getdoc(item.obj)
        except Exception:  # pragma: no cover - defensive guard
            return None
    return None


def derive_display_name(
    nodeid: str,
    *,
    doc: str | None,
    marker_name: str | None = None,
    slug: str | None = None,
) -> str:
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
    chosen: str | None = None
    for candidate in candidates:
        normalised = _normalise_name(candidate)
        if normalised:
            chosen = normalised
            break
    if chosen is None:
        chosen = "Unnamed test"
    return f"{slug} - {chosen}" if slug else chosen


def _should_process_report(
    state: AutogradeState,
    nodeid: str,
    is_call_phase: bool,
    outcome: Any,
) -> bool:
    already_recorded = nodeid in state.reported_nodeids
    if is_call_phase:
        return not already_recorded
    return outcome == "failed" and not already_recorded


def _derive_display_context(
    state: AutogradeState,
    report: Any,
    nodeid: str,
) -> tuple[str, int | None]:
    metadata = state.metadata.get(nodeid)
    if metadata is not None:
        return metadata.display_name, metadata.task_number

    doc: str | None = None
    head_line = getattr(report, "head_line", None)
    if isinstance(head_line, str):
        doc = head_line
    slug = _extract_slug_from_nodeid(nodeid)
    display_name = derive_display_name(nodeid, doc=doc, marker_name=None, slug=slug)
    return display_name, None


def _resolve_line_number_from_location(location: Sequence[Any] | None) -> int | None:
    if not isinstance(location, Sequence) or isinstance(location, (str, bytes)):
        return None
    if len(location) < LOCATION_MIN_LENGTH:
        return None

    candidate = location[1]
    if isinstance(candidate, bool):  # bool is subclass of int but semantically different
        candidate = int(candidate)

    result: int | None = None
    if isinstance(candidate, (int, float)):
        result = int(candidate) + 1
    elif isinstance(candidate, str):
        stripped = candidate.strip()
        if stripped:
            try:
                result = int(stripped) + 1
            except ValueError:
                result = None
    return result


def _resolve_line_number(report: Any) -> int | None:
    longrepr = getattr(report, "longrepr", None)
    reprcrash = getattr(longrepr, "reprcrash", None)
    lineno_candidate = getattr(reprcrash, "lineno", None) if reprcrash else None
    if isinstance(lineno_candidate, int):
        return lineno_candidate

    location = getattr(report, "location", None)
    return _resolve_line_number_from_location(location)


def _extract_captured_output(report: Any) -> tuple[str | None, str | None, str | None]:
    stdout = getattr(report, "capstdout", None) or None
    stderr = getattr(report, "capstderr", None) or None
    log = getattr(report, "caplogtext", None) or None
    return stdout, stderr, log


def _build_call_phase_result(
    *,
    report: Any,
    outcome: str | None,
    context: _ReportContext,
) -> AutogradeTestResult:
    if outcome == "passed":
        status = "pass"
        score = 1.0
        message: str | None = None
    elif outcome == "skipped":
        status = "fail"
        score = 0.0
        message_source = getattr(report, "longreprtext", None) or "Test skipped"
        message = trim_failure_message(message_source)
    else:
        status = "fail"
        score = 0.0
        message_source = getattr(report, "longreprtext", None)
        if not message_source and hasattr(report, "longrepr"):
            message_source = str(report.longrepr)
        message = trim_failure_message(message_source or "Test failed")

    return AutogradeTestResult(
        nodeid=context.nodeid,
        display_name=context.display_name,
        task_number=context.task_number,
        status=status,
        score=score,
        message=message,
        line_number=context.line_number,
        duration=context.duration,
        captured_stdout=context.captured_stdout,
        captured_stderr=context.captured_stderr,
        captured_log=context.captured_log,
    )


def _build_non_call_phase_result(
    *,
    report: Any,
    context: _ReportContext,
) -> AutogradeTestResult:
    message_source = getattr(report, "longreprtext", None)
    if not message_source and hasattr(report, "longrepr"):
        message_source = str(report.longrepr)
    message = trim_failure_message(message_source or "Test error during setup/teardown")

    return AutogradeTestResult(
        nodeid=context.nodeid,
        display_name=context.display_name,
        task_number=context.task_number,
        status="error",
        score=0.0,
        message=message,
        line_number=context.line_number,
        duration=context.duration,
        captured_stdout=context.captured_stdout,
        captured_stderr=context.captured_stderr,
        captured_log=context.captured_log,
    )


def trim_failure_message(message: str, *, max_length: int = 1_000) -> str:
    """Shorten failure messages while preserving key diagnostic information."""

    normalised = " ".join(message.strip().split())
    if max_length <= ELLIPSIS_GUARD_LENGTH:
        return normalised[:max_length]
    if len(normalised) <= max_length:
        return normalised
    return normalised[: max_length - ELLIPSIS_GUARD_LENGTH].rstrip() + "..."


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

    results_option = None
    try:
        results_option = config.getoption("autograde_results_path")
    except Exception:  # pragma: no cover - defensive for unexpected config
        results_option = None

    state = getattr(config, "_autograde_state", None)
    if state is None:
        state = AutogradeState()
        config._autograde_state = state  # type: ignore[attr-defined]

    state.results_path = Path(results_option).expanduser().resolve() if results_option else None
    if state.start_timestamp is None:
        state.start_timestamp = time.time()
    if state.results_path is None:
        warning = (
            "Autograde plugin active but --autograde-results-path was not provided; "
            "results will not be written."
        )
        if warning not in state.notes:
            state.notes.append(warning)

    _set_autograde_state(state)


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Augment collected tests with autograde metadata before execution."""

    state = getattr(config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    for item in items:
        task_number, marker_name = _parse_task_marker(item, state)
        doc = _get_item_doc(item)
        slug = _extract_slug_from_nodeid(item.nodeid)
        display_name = derive_display_name(
            item.nodeid,
            doc=doc,
            marker_name=marker_name,
            slug=slug,
        )
        state.metadata[item.nodeid] = AutogradeTestMetadata(
            display_name=display_name,
            task_number=task_number,
            marker_name=marker_name,
            slug=slug,
        )

    state.max_score = float(len(state.metadata))


def pytest_runtest_logreport(report: Any) -> None:
    """Record per-phase test results emitted by pytest's reporting pipeline."""

    state = _get_autograde_state()
    if not isinstance(state, AutogradeState):
        return

    nodeid = getattr(report, "nodeid", None)
    if not isinstance(nodeid, str):
        return

    when = getattr(report, "when", None)
    outcome = getattr(report, "outcome", None)

    is_call_phase = when == "call"

    if not _should_process_report(state, nodeid, is_call_phase, outcome):
        return

    display_name, task_number = _derive_display_context(state, report, nodeid)

    line_number = _resolve_line_number(report)
    duration = getattr(report, "duration", None)
    captured_stdout, captured_stderr, captured_log = _extract_captured_output(report)

    context = _ReportContext(
        nodeid=nodeid,
        display_name=display_name,
        task_number=task_number,
        line_number=line_number,
        duration=duration,
        captured_stdout=captured_stdout,
        captured_stderr=captured_stderr,
        captured_log=captured_log,
    )

    if is_call_phase:
        result = _build_call_phase_result(
            report=report,
            outcome=outcome,
            context=context,
        )
    else:
        result = _build_non_call_phase_result(
            report=report,
            context=context,
        )

    state.results.append(result)
    state.reported_nodeids.add(nodeid)
    state.total_score += result.score
    state.max_score = float(max(len(state.metadata), len(state.results)))

    if result.status == "error" and result.message:
        detail = f"{display_name}: {result.message}"
        if detail not in state.encountered_errors:
            state.encountered_errors.append(detail)


def _compute_final_scores(
    state: AutogradeState,
    results_payload: list[dict[str, Any]],
) -> tuple[float, float]:
    """Compute earned and maximum scores from test results.

    Args:
        state: The AutogradeState containing test results and metadata.
        results_payload: Pre-computed list of result dictionaries.

    Returns:
        A tuple of (earned_score, max_score).
    """
    max_score = float(len(state.metadata)) if state.metadata else float(len(results_payload))
    earned_score = float(sum(entry["score"] for entry in results_payload))
    return earned_score, max_score


def _build_json_payload(
    state: AutogradeState,
    earned: float,
    max_score: float,
    results_payload: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the complete JSON payload for autograder output.

    Args:
        state: The AutogradeState containing test results and metadata.
        earned: The total earned score.
        max_score: The maximum possible score.
        results_payload: Pre-computed list of result dictionaries.

    Returns:
        A dictionary containing all autograder output fields.
    """
    overall_status = _derive_overall_status(state, results_payload)

    payload: dict[str, Any] = {
        "status": overall_status,
        "score": earned,
        "max_score": max_score,
        "tests": results_payload,
        "start_timestamp": state.start_timestamp,
        "end_timestamp": state.end_timestamp,
    }
    if state.encountered_errors:
        payload["errors"] = state.encountered_errors
    if state.notes:
        payload["notes"] = state.notes

    return payload


def _write_json_with_fallback(payload: dict[str, Any], path: Path, state: AutogradeState) -> None:
    """Write JSON payload to file with error handling and fallback.

    Args:
        payload: The JSON payload to write.
        path: The destination file path.
        state: The AutogradeState for error tracking.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except Exception as exc:  # pragma: no cover - exercised in error handling tests
        error_message = f"Failed to write autograde results to {path}: {exc}"
        state.encountered_errors.append(error_message)
        print(f"Autograde plugin failed to write results: {error_message}", file=sys.stderr)

        fallback: dict[str, Any] = {"status": "error", "score": 0.0, "max_score": 0.0, "tests": []}
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(fallback, handle, ensure_ascii=False, indent=2)
        except Exception as fallback_exc:  # pragma: no cover - defensive fallback guard
            fallback_message = (
                f"Fallback write for autograde results failed at {path}: {fallback_exc}"
            )
            state.encountered_errors.append(fallback_message)
            print(
                f"Autograde plugin fallback write failed: {fallback_message}",
                file=sys.stderr,
            )


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Finalise aggregation and prepare data for consumption post-test run."""

    state = getattr(session.config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    state.end_timestamp = time.time()

    results_payload = [_result_to_dict(res) for res in state.results]
    earned_score, max_score = _compute_final_scores(state, results_payload)
    state.max_score = max_score
    state.total_score = earned_score

    payload = _build_json_payload(state, earned_score, max_score, results_payload)

    if state.results_path:
        _write_json_with_fallback(payload, state.results_path, state)


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Emit a concise summary tailored for the GitHub Classroom autograder."""

    config = getattr(terminalreporter, "config", None)
    state = getattr(config, "_autograde_state", None)
    if not isinstance(state, AutogradeState):
        return

    total_tests = len(state.metadata) if state.metadata else len(state.results)
    passed = sum(1 for result in state.results if result.status == "pass")
    overall_status = _derive_overall_status(state, [_result_to_dict(res) for res in state.results])
    if state.results_path:
        terminalreporter.write_line(
            f"Autograde summary: {passed}/{total_tests} passed | "
            f"Score {state.total_score}/{state.max_score} | Status {overall_status}"
        )
        terminalreporter.write_line(f"Autograde results written to: {state.results_path}")
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
    return "pass"
