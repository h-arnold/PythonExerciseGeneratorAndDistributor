"""Generic notebook execution checks used in student notebooks."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, TypedDict, TypeGuard, cast

from exercise_runtime_support.execution_variant import (
    Variant,
    active_variant_context,
    get_active_variant,
)
from exercise_runtime_support.exercise_framework.paths import resolve_notebook_path
from exercise_runtime_support.exercise_framework.reporting import render_grouped_table_with_errors
from exercise_runtime_support.notebook_grader import (
    NotebookCell,
    NotebookGradingError,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)

from .checks import has_exercise_checks, run_exercise_checks
from .models import ExerciseCheckResult, NotebookTagCheckResult
from .readability import (
    CellAnalysis,
    NotebookAnalysis,
    ReadabilityToolError,
    analyze_notebook,
)

_EXERCISE_TAG_PATTERN = re.compile(r"exercise(\d+)")
_DEFAULT_INPUT_VALUE = "2"
_MISSING_INPUT_ERROR_MESSAGE = "Test expected more input values"
_MAX_AUTOMATED_INPUTS = 10


class NotebookJson(TypedDict):
    """Typed notebook JSON shape used by the student checker."""

    cells: list[NotebookCell]


def _is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    """Return whether parsed JSON is a mapping with string keys."""
    if not isinstance(value, dict):
        return False
    mapping = cast(dict[Any, Any], value)
    return all(isinstance(key, str) for key in mapping)


def _as_json_object(value: object) -> dict[str, object] | None:
    if not _is_json_object(value):
        return None
    return value


def _is_notebook_cell(value: object) -> TypeGuard[NotebookCell]:
    """Return whether a parsed value is a notebook cell mapping."""
    cell = _as_json_object(value)
    if cell is None:
        return False
    cell_type = cell.get("cell_type")
    if not isinstance(cell_type, str):
        return False
    return _has_valid_source(cell) and _has_valid_metadata(cell)


def _has_valid_source(cell: dict[str, object]) -> bool:
    source = cell.get("source")
    if source is None:
        return True
    if isinstance(source, str):
        return True
    if isinstance(source, list):
        items = cast(list[Any], source)
        return all(isinstance(item, str) for item in items)
    return False


def _has_valid_metadata(cell: dict[str, object]) -> bool:
    metadata = cell.get("metadata")
    if metadata is None:
        return True
    metadata_mapping = _as_json_object(metadata)
    if metadata_mapping is None:
        return False
    tags = metadata_mapping.get("tags")
    if tags is None:
        return True
    if isinstance(tags, str):
        return True
    return _is_string_list(tags)


def _is_object_list(value: object) -> TypeGuard[list[Any]]:
    """Return whether a parsed value is a list."""
    return isinstance(value, list)


def _is_notebook_cell_list(value: object) -> TypeGuard[list[NotebookCell]]:
    """Return whether a parsed value is a list of notebook cell mappings."""
    if not _is_object_list(value):
        return False
    return all(_is_notebook_cell(item) for item in value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    """Return whether a parsed value is a list of strings."""
    if not _is_object_list(value):
        return False
    return all(isinstance(item, str) for item in value)


def run_notebook_checks(exercise_key: str) -> None:
    """Print functional and required readability results for an exercise.

    Args:
        exercise_key: Canonical exercise identity used to resolve the active
            student or solution notebook.

    Returns:
        ``None``. Results are printed in a task-grouped table without a footer.

    Raises:
        ReadabilityToolError: Ruff cannot provide readability results. Available
            functional results are printed before the tooling error is re-raised.
        LookupError: The canonical exercise metadata or selected notebook cannot
            be resolved.
        NotebookGradingError: Fallback notebook loading or tag discovery fails.
    """
    with active_variant_context() as variant:
        resolved_path = resolve_notebook_path(exercise_key, variant=variant)
        if has_exercise_checks(exercise_key):
            functional_results = run_exercise_checks(exercise_key)
        else:
            tags = _collect_exercise_tags(resolved_path)
            if not tags:
                print(f"No exercise tags found in {resolved_path}.")
                return
            functional_results = _run_notebook_checks(resolved_path, tags)

        try:
            analysis = analyze_notebook(resolved_path)
        except ReadabilityToolError as exc:
            print(f"Self-check: {exercise_key} ({variant})")
            _print_functional_only_results(functional_results)
            print(f"\nReadability tool ERROR: {exc}")
            raise
        _print_integrated_results(exercise_key, variant, functional_results, analysis)


def _load_notebook_json(path: Path) -> NotebookJson:
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotebookGradingError(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(f"Unable to parse notebook JSON: {path}") from exc
    if not _is_json_object(data):
        raise NotebookGradingError(f"Notebook JSON must be a JSON object: {path}")
    cells = data.get("cells")
    if not _is_notebook_cell_list(cells):
        raise NotebookGradingError(
            f"Notebook JSON must contain a 'cells' list of notebook cell objects: {path}"
        )
    notebook_json: NotebookJson = {"cells": cells}
    return notebook_json


def _extract_tags_from_cell(cell: object) -> list[str]:
    if not _is_notebook_cell(cell):
        return []
    metadata = cell.get("metadata")
    if not _is_json_object(metadata):
        return []
    raw_tags = metadata.get("tags")
    if isinstance(raw_tags, str):
        candidates = [raw_tags]
    elif _is_string_list(raw_tags):
        candidates = raw_tags
    else:
        return []

    return [tag for tag in candidates if _EXERCISE_TAG_PATTERN.fullmatch(tag)]


def _collect_exercise_tags(path: Path) -> list[str]:
    data = _load_notebook_json(path)
    cells = data["cells"]
    tags: list[str] = []
    for cell in cells:
        tags.extend(_extract_tags_from_cell(cell))
    return tags


def _run_notebook_checks(path: Path, tags: list[str]) -> list[NotebookTagCheckResult]:
    results: list[NotebookTagCheckResult] = []
    for tag in tags:
        try:
            _run_tagged_cell(path, tag)
            results.append(NotebookTagCheckResult(tag=tag, passed=True, message=""))
        except NotebookGradingError as exc:
            results.append(NotebookTagCheckResult(tag=tag, passed=False, message=str(exc)))
    return results


def _run_tagged_cell(notebook_path: str | Path, tag: str) -> None:
    input_calls = _count_input_calls(notebook_path, tag=tag)
    if input_calls == 0:
        run_cell_and_capture_output(
            notebook_path, tag=tag, variant=get_active_variant(default="student")
        )
        return
    _run_interactive_cell_with_backfill(notebook_path, tag=tag, input_calls=input_calls)


def _run_interactive_cell_with_backfill(
    notebook_path: str | Path,
    *,
    tag: str,
    input_calls: int,
) -> None:
    required_inputs = max(input_calls, 1)
    while True:
        inputs = [_DEFAULT_INPUT_VALUE for _ in range(required_inputs)]
        try:
            run_cell_with_input(
                notebook_path,
                tag=tag,
                inputs=inputs,
                variant=get_active_variant(default="student"),
            )
            return
        except NotebookGradingError as exc:
            if not _is_missing_input_error(exc):
                raise
            if required_inputs >= _MAX_AUTOMATED_INPUTS:
                raise
            required_inputs = min(_MAX_AUTOMATED_INPUTS, required_inputs + 1)


def _is_missing_input_error(exc: NotebookGradingError) -> bool:
    cause = exc.__cause__
    if isinstance(cause, RuntimeError):
        return str(cause) == _MISSING_INPUT_ERROR_MESSAGE
    return False


def _count_input_calls(notebook_path: str | Path, *, tag: str) -> int:
    """Count direct `input()` calls in a tagged code cell."""
    code = extract_tagged_code(
        notebook_path, tag=tag, variant=get_active_variant(default="student")
    )
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    return sum(1 for node in ast.walk(tree) if _is_input_call(node))


def _is_input_call(node: ast.AST) -> bool:
    """Return True when a node represents an `input()` call."""
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == "input"
    if isinstance(node.func, ast.Attribute):
        return (
            node.func.attr == "input"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "builtins"
        )
    return False


def _format_tag_label(tag: str) -> str:
    match = _EXERCISE_TAG_PATTERN.match(tag)
    return f"Exercise {match.group(1)}" if match else tag


def _print_functional_only_results(
    results: list[ExerciseCheckResult] | list[NotebookTagCheckResult],
) -> None:
    rows = _functional_rows(results)
    print(render_grouped_table_with_errors(rows))


def _print_integrated_results(
    exercise_key: str,
    variant: Variant,
    functional_results: list[ExerciseCheckResult] | list[NotebookTagCheckResult],
    analysis: NotebookAnalysis,
) -> None:
    cells_by_task: dict[str, list[CellAnalysis]] = {}
    for cell in analysis.cells:
        cells_by_task.setdefault(cell.task_tag, []).append(cell)
    rows: list[tuple[str, str, bool | None, str]] = []
    shown_cells: set[int] = set()
    for functional_row, result in zip(
        _functional_rows(functional_results), functional_results, strict=True
    ):
        rows.append(functional_row)
        task_tag = (
            f"exercise{result.exercise_no}"
            if isinstance(result, ExerciseCheckResult)
            else result.tag
        )
        for cell in cells_by_task.get(task_tag, []):
            if cell.cell_index in shown_cells:
                continue
            rows.append(_readability_row(cell))
            shown_cells.add(cell.cell_index)
    for cell in analysis.cells:
        if cell.cell_index not in shown_cells:
            rows.append(_readability_row(cell))

    print(f"Self-check: {exercise_key} ({variant})")
    print(render_grouped_table_with_errors(rows))


def _readability_row(cell: CellAnalysis) -> tuple[str, str, bool | None, str]:
    exercise_label = _format_tag_label(cell.task_tag)
    title = "Readability"
    if cell.syntax_blocked:
        return exercise_label, title, None, "Not checked - make sure your code runs first"
    message = _cell_findings(cell)
    return (
        exercise_label,
        title,
        not cell.findings,
        message or "No selected readability issues found",
    )


def _functional_rows(
    results: list[ExerciseCheckResult] | list[NotebookTagCheckResult],
) -> list[tuple[str, str, bool, str]]:
    rows: list[tuple[str, str, bool, str]] = []
    for result in results:
        if isinstance(result, ExerciseCheckResult):
            label = f"Exercise {result.exercise_no}"
            title = result.title
            message = "; ".join(result.issues)
        else:
            label = _format_tag_label(result.tag)
            title = result.tag
            message = result.message
        rows.append((label, title, result.passed, message))
    return rows


def _cell_findings(cell: CellAnalysis) -> str:
    return "; ".join(
        f"{finding.code} line {finding.line} column {finding.column}: {finding.message}"
        for finding in cell.findings
    )
