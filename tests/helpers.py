from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.notebook_grader import (
    get_explanation_cell as grading_get_explanation_cell,
)
from tests.notebook_grader import (
    resolve_notebook_path as grading_resolve_notebook_path,
)
from tests.notebook_grader import (
    run_cell_and_capture_output,
    run_cell_with_input,
)


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Return the absolute notebook path following the grading helpers."""
    return grading_resolve_notebook_path(notebook_path)


def run_tagged_cell_output(
    notebook_path: str,
    tag: str,
    *,
    inputs: list[str] | None = None,
) -> str:
    """Execute a tagged cell and capture its output (optionally providing inputs)."""
    if inputs is not None:
        return run_cell_with_input(notebook_path, tag=tag, inputs=inputs)

    return run_cell_and_capture_output(notebook_path, tag=tag)


def load_notebook(notebook_path: str | Path, *, use_solution: bool = False) -> dict[str, Any]:
    """Load a notebook JSON document, optionally redirecting to the solution directory."""
    target = resolve_notebook_path(
        notebook_path) if use_solution else Path(notebook_path)
    with open(target, encoding="utf-8") as handle:
        return json.load(handle)


def _find_code_cell(notebook: dict[str, Any], tag: str) -> dict[str, Any] | None:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            return cell
    return None


def assert_code_cell_present(
    notebook_path: str,
    tag: str,
    *,
    use_solution: bool = False,
    ensure_not_empty: bool = True,
    allow_todo: bool = True,
) -> str:
    """Assert that a code cell with the specified tag exists and return its source."""
    notebook = load_notebook(notebook_path, use_solution=use_solution)
    cell = _find_code_cell(notebook, tag)
    assert cell is not None, f"No code cell found with tag {tag}"
    assert cell.get("cell_type") == "code", f"Cell {tag} must be a code cell"

    source = "".join(cell.get("source", []))
    if ensure_not_empty:
        assert source.strip(), f"Cell {tag} must not be empty"
    if not allow_todo and "TODO" in source:
        raise AssertionError(
            f"Solution cell {tag} should not contain TODO placemarkers")

    return source


def get_explanation_cell(notebook_path: str, *, tag: str) -> str:
    """Return the content of a tagged explanation cell from the grading helper."""
    return grading_get_explanation_cell(notebook_path, tag=tag)
