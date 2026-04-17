"""Execution helpers for exercise notebook cells.

This module wraps notebook grader helpers and adds optional execution artefact caching
for repeated checks within a single run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from exercise_runtime_support import notebook_grader
from exercise_runtime_support.execution_variant import Variant

__all__ = [
    "RuntimeCache",
    "exec_tagged_code",
    "extract_tagged_code",
    "get_explanation_cell",
    "resolve_notebook_path",
    "run_cell_and_capture_output",
    "run_cell_with_input",
]


class RuntimeCache:
    """In-memory cache for extracted code and captured outputs."""

    def __init__(self) -> None:
        self.code_by_tag: dict[tuple[str, str], str] = {}
        self.output_by_tag: dict[tuple[str, str], str] = {}
        self.input_output_by_tag: dict[tuple[str, str, tuple[str, ...]], str] = {}


def _path_key(notebook_path: str | Path) -> str:
    return str(Path(notebook_path))


def resolve_notebook_path(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve a notebook path using the shared path semantics."""
    return notebook_grader.resolve_notebook_path(notebook_path, variant=variant)


def extract_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    cache: RuntimeCache | None = None,
    variant: Variant | None = None,
) -> str:
    """Extract tagged code, using cache when provided."""
    key = (_path_key(resolve_notebook_path(notebook_path, variant=variant)), tag)
    if cache is not None and key in cache.code_by_tag:
        return cache.code_by_tag[key]

    code = notebook_grader.extract_tagged_code(notebook_path, tag=tag, variant=variant)
    if cache is not None:
        cache.code_by_tag[key] = code
    return code


def exec_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    filename_hint: str | None = None,
    variant: Variant | None = None,
) -> dict[str, Any]:
    """Execute tagged code and return namespace."""
    return notebook_grader.exec_tagged_code(
        notebook_path,
        tag=tag,
        filename_hint=filename_hint,
        variant=variant,
    )


def run_cell_and_capture_output(
    notebook_path: str | Path,
    *,
    tag: str,
    cache: RuntimeCache | None = None,
    variant: Variant | None = None,
) -> str:
    """Run a tagged cell and capture stdout, with optional caching."""
    key = (_path_key(resolve_notebook_path(notebook_path, variant=variant)), tag)
    if cache is not None and key in cache.output_by_tag:
        return cache.output_by_tag[key]

    output = notebook_grader.run_cell_and_capture_output(
        notebook_path,
        tag=tag,
        variant=variant,
    )
    if cache is not None:
        cache.output_by_tag[key] = output
    return output


def run_cell_with_input(
    notebook_path: str | Path,
    *,
    tag: str,
    inputs: list[str],
    cache: RuntimeCache | None = None,
    variant: Variant | None = None,
) -> str:
    """Run a tagged cell with mocked input, with optional caching."""
    key = (_path_key(resolve_notebook_path(notebook_path, variant=variant)), tag, tuple(inputs))
    if cache is not None and key in cache.input_output_by_tag:
        return cache.input_output_by_tag[key]

    output = notebook_grader.run_cell_with_input(
        notebook_path,
        tag=tag,
        inputs=inputs,
        variant=variant,
    )
    if cache is not None:
        cache.input_output_by_tag[key] = output
    return output


def get_explanation_cell(
    notebook_path: str | Path,
    *,
    tag: str,
    variant: Variant | None = None,
) -> str:
    """Return explanation markdown content for a tagged cell."""
    return notebook_grader.get_explanation_cell(notebook_path, tag=tag, variant=variant)
