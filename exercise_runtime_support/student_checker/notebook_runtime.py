"""Generic notebook execution checks used in student notebooks."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, TypedDict, TypeGuard, cast

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
from .models import NotebookTagCheckResult
from .reporting import print_exercise_results

_EXERCISE_TAG_PATTERN = re.compile(r"exercise\d+")
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
    """Run notebook-facing student checks for the given canonical exercise key."""
    if has_exercise_checks(exercise_key):
        print_exercise_results(run_exercise_checks(exercise_key))
        return

    resolved_path = resolve_notebook_path(exercise_key, variant="student")
    tags = _collect_exercise_tags(resolved_path)
    if not tags:
        print(f"No exercise tags found in {resolved_path}.")
        return

    results = _run_notebook_checks(resolved_path, tags)
    _print_notebook_check_results(results)


def _load_notebook_json(path: Path) -> NotebookJson:
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotebookGradingError(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(
            f"Unable to parse notebook JSON: {path}") from exc
    if not _is_json_object(data):
        raise NotebookGradingError(
            f"Notebook JSON must be a JSON object: {path}")
    cells = data.get("cells")
    if not _is_notebook_cell_list(cells):
        raise NotebookGradingError(
            f"Notebook JSON must contain a 'cells' list of notebook cell "
            f"objects: {path}")
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
            results.append(NotebookTagCheckResult(
                tag=tag, passed=True, message=""))
        except NotebookGradingError as exc:
            results.append(NotebookTagCheckResult(
                tag=tag, passed=False, message=str(exc)))
    return results


def _run_tagged_cell(notebook_path: str | Path, tag: str) -> None:
    input_calls = _count_input_calls(notebook_path, tag=tag)
    if input_calls == 0:
        run_cell_and_capture_output(notebook_path, tag=tag, variant="student")
        return
    _run_interactive_cell_with_backfill(
        notebook_path, tag=tag, input_calls=input_calls)


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
                variant="student",
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
    code = extract_tagged_code(notebook_path, tag=tag, variant="student")
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
