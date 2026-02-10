"""Generic notebook execution checks used in student notebooks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.exercise_framework.reporting import render_grouped_table_with_errors
from tests.notebook_grader import (
    NotebookGradingError,
    resolve_notebook_path,
    run_cell_and_capture_output,
)

from .models import NotebookTagCheckResult

_EXERCISE_TAG_PATTERN = re.compile(r"exercise\d+")


def run_notebook_checks(notebook_path: str) -> None:
    """Execute each tagged exercise cell and print a friendly status table."""
    resolved_path = resolve_notebook_path(notebook_path)
    tags = _collect_exercise_tags(resolved_path)
    if not tags:
        print(f"No exercise tags found in {resolved_path}.")
        return

    results = _run_notebook_checks(resolved_path, tags)
    _print_notebook_check_results(results)


def _load_notebook_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotebookGradingError(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(f"Unable to parse notebook JSON: {path}") from exc
    if not isinstance(data, dict):
        return {}
    return data


def _extract_tags_from_cell(cell: object) -> list[str]:
    if not isinstance(cell, dict):
        return []
    metadata = cell.get("metadata")
    if not isinstance(metadata, dict):
        return []
    cell_tags = metadata.get("tags")
    if isinstance(cell_tags, str):
        candidates = [cell_tags]
    elif isinstance(cell_tags, list):
        candidates = cell_tags
    else:
        return []

    tags: list[str] = []
    for tag in candidates:
        if isinstance(tag, str) and _EXERCISE_TAG_PATTERN.fullmatch(tag):
            tags.append(tag)
    return tags


def _collect_exercise_tags(path: Path) -> list[str]:
    data = _load_notebook_json(path)
    cells = data.get("cells")
    if not isinstance(cells, list):
        return []

    tags: list[str] = []
    for cell in cells:
        tags.extend(_extract_tags_from_cell(cell))
    return tags


def _run_notebook_checks(path: Path, tags: list[str]) -> list[NotebookTagCheckResult]:
    results: list[NotebookTagCheckResult] = []
    for tag in tags:
        try:
            run_cell_and_capture_output(str(path), tag=tag)
            results.append(NotebookTagCheckResult(tag=tag, passed=True, message=""))
        except NotebookGradingError as exc:
            results.append(NotebookTagCheckResult(tag=tag, passed=False, message=str(exc)))
    return results


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
