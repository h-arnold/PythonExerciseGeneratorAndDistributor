"""Generic notebook execution checks used in student notebooks."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import cast

from tests.exercise_framework.reporting import render_grouped_table_with_errors
from tests.notebook_grader import (
    NotebookGradingError,
    extract_tagged_code,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from tests.student_checker.notebook_runtime_typeguards import (
    NotebookCell,
    NotebookJson,
    NotebookMetadata,
    is_notebook_cell,
    is_notebook_cells_list,
    is_notebook_json,
    is_notebook_metadata,
)

from .models import NotebookTagCheckResult

_EXERCISE_TAG_PATTERN = re.compile(r"exercise\d+")
_DEFAULT_INPUT_VALUE = "2"
_MISSING_INPUT_ERROR_MESSAGE = "Test expected more input values"
_MAX_AUTOMATED_INPUTS = 10


def run_notebook_checks(notebook_path: str) -> None:
    """Execute each tagged exercise cell and print a friendly status table."""
    resolved_path = resolve_notebook_path(notebook_path)
    tags = _collect_exercise_tags(resolved_path)
    if not tags:
        print(f"No exercise tags found in {resolved_path}.")
        return

    results = _run_notebook_checks(resolved_path, tags)
    _print_notebook_check_results(results)


def _load_notebook_json(path: Path) -> NotebookJson:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotebookGradingError(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(f"Unable to parse notebook JSON: {path}") from exc
    if is_notebook_json(data):
        return data
    return {}


def _extract_tags_from_cell(cell: object) -> list[str]:
    if not is_notebook_cell(cell):
        return []
    cell_dict: NotebookCell = cell
    metadata = cell_dict.get("metadata")
    if not is_notebook_metadata(metadata):
        return []
    metadata_dict: NotebookMetadata = metadata
    return _extract_tags_from_metadata(metadata_dict)


def _extract_tags_from_metadata(metadata: NotebookMetadata) -> list[str]:
    """Return the exercise tags encoded in notebook metadata."""
    raw_tags = metadata.get("tags")
    if isinstance(raw_tags, str):
        candidates = (raw_tags,)
    elif isinstance(raw_tags, list):
        typed_tags = cast(list[object], raw_tags)
        str_items: list[str] = []
        for item in typed_tags:
            if not isinstance(item, str):
                return []
            str_items.append(item)
        candidates = tuple(str_items)
    else:
        return []

    tags: list[str] = []
    for tag in candidates:
        if _EXERCISE_TAG_PATTERN.fullmatch(tag):
            tags.append(tag)
    return tags


def _collect_exercise_tags(path: Path) -> list[str]:
    data = _load_notebook_json(path)
    cells = data.get("cells")
    if not is_notebook_cells_list(cells):
        return []

    tags: list[str] = []
    for cell in cells:
        tags.extend(_extract_tags_from_cell(cell))
    return tags


def _run_notebook_checks(path: Path, tags: list[str]) -> list[NotebookTagCheckResult]:
    results: list[NotebookTagCheckResult] = []
    for tag in tags:
        try:
            _run_tagged_cell(str(path), tag)
            results.append(NotebookTagCheckResult(tag=tag, passed=True, message=""))
        except NotebookGradingError as exc:
            results.append(NotebookTagCheckResult(tag=tag, passed=False, message=str(exc)))
    return results


def _run_tagged_cell(notebook_path: str, tag: str) -> None:
    input_calls = _count_input_calls(notebook_path, tag=tag)
    if input_calls == 0:
        run_cell_and_capture_output(notebook_path, tag=tag)
        return
    _run_interactive_cell_with_backfill(notebook_path, tag=tag, input_calls=input_calls)


def _run_interactive_cell_with_backfill(
    notebook_path: str,
    *,
    tag: str,
    input_calls: int,
) -> None:
    required_inputs = max(input_calls, 1)
    while True:
        inputs = [_DEFAULT_INPUT_VALUE for _ in range(required_inputs)]
        try:
            run_cell_with_input(notebook_path, tag=tag, inputs=inputs)
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


def _count_input_calls(notebook_path: str, *, tag: str) -> int:
    """Count direct `input()` calls in a tagged code cell."""
    code = extract_tagged_code(notebook_path, tag=tag)
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


def _print_notebook_check_results(results: list[NotebookTagCheckResult]) -> None:
    rows = [
        (_format_tag_label(result.tag), result.tag, result.passed, result.message)
        for result in results
    ]
    print(render_grouped_table_with_errors(rows))

    failures = [result for result in results if not result.passed]
    if failures:
        print("\nFix the failing cells above, then re-run this cell.")
    else:
        print("\nGreat work! All exercise cells ran without errors.")


def _format_tag_label(tag: str) -> str:
    match = re.match(r"exercise(\d+)", tag)
    return f"Exercise {match.group(1)}" if match else tag
