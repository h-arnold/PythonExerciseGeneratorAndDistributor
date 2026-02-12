"""Execution helpers for exercise notebook cells.

This module wraps notebook grader helpers and adds optional execution artefact caching
for repeated checks within a single run.
"""

from __future__ import annotations

import ast
import io
import token
import tokenize
from pathlib import Path
from typing import Any

from tests import notebook_grader


class RuntimeCache:
    """In-memory cache for extracted code and captured outputs."""

    def __init__(self) -> None:
        self.code_by_tag: dict[tuple[str, str], str] = {}
        self.output_by_tag: dict[tuple[str, str], str] = {}
        self.input_output_by_tag: dict[tuple[str,
                                             str, tuple[str, ...]], str] = {}


def semantic_code_signature(code: str) -> str:
    """Return a deterministic semantic signature for Python source code.

    This normalises away comments and formatting-only differences. The primary
    representation is the parsed AST dump without location attributes.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _token_signature(code)
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def is_code_semantically_modified(student_code: str, starter_code: str) -> bool:
    """Return True when student code differs semantically from starter code."""
    return semantic_code_signature(student_code) != semantic_code_signature(starter_code)


def is_tagged_cell_semantically_modified(
    notebook_path: str | Path,
    *,
    tag: str,
    starter_code: str,
    cache: RuntimeCache | None = None,
) -> bool:
    """Return whether a tagged notebook cell is semantically modified.

    Whitespace-only and comment-only edits are treated as unchanged.
    """
    student_code = extract_tagged_code(notebook_path, tag=tag, cache=cache)
    return is_code_semantically_modified(student_code, starter_code)


def _token_signature(code: str) -> str:
    token_values: list[str] = []
    ignored_types = {
        token.COMMENT,
        token.NL,
        token.NEWLINE,
        token.INDENT,
        token.DEDENT,
        token.ENDMARKER,
        token.ENCODING,
    }
    stream = io.StringIO(code)
    for token_info in tokenize.generate_tokens(stream.readline):
        if token_info.type in ignored_types:
            continue
        token_values.append(f"{token_info.type}:{token_info.string}")
    return "|".join(token_values)


def _path_key(notebook_path: str | Path) -> str:
    return str(Path(notebook_path))


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve a notebook path using the shared path semantics."""
    return notebook_grader.resolve_notebook_path(notebook_path)


def extract_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    cache: RuntimeCache | None = None,
) -> str:
    """Extract tagged code, using cache when provided."""
    key = (_path_key(notebook_path), tag)
    if cache is not None and key in cache.code_by_tag:
        return cache.code_by_tag[key]

    code = notebook_grader.extract_tagged_code(notebook_path, tag=tag)
    if cache is not None:
        cache.code_by_tag[key] = code
    return code


def exec_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    filename_hint: str | None = None,
) -> dict[str, Any]:
    """Execute tagged code and return namespace."""
    return notebook_grader.exec_tagged_code(
        notebook_path,
        tag=tag,
        filename_hint=filename_hint,
    )


def run_cell_and_capture_output(
    notebook_path: str | Path,
    *,
    tag: str,
    cache: RuntimeCache | None = None,
) -> str:
    """Run a tagged cell and capture stdout, with optional caching."""
    key = (_path_key(notebook_path), tag)
    if cache is not None and key in cache.output_by_tag:
        return cache.output_by_tag[key]

    output = notebook_grader.run_cell_and_capture_output(
        notebook_path, tag=tag)
    if cache is not None:
        cache.output_by_tag[key] = output
    return output


def run_cell_with_input(
    notebook_path: str | Path,
    *,
    tag: str,
    inputs: list[str],
    cache: RuntimeCache | None = None,
) -> str:
    """Run a tagged cell with mocked input, with optional caching."""
    key = (_path_key(notebook_path), tag, tuple(inputs))
    if cache is not None and key in cache.input_output_by_tag:
        return cache.input_output_by_tag[key]

    output = notebook_grader.run_cell_with_input(
        notebook_path, tag=tag, inputs=inputs)
    if cache is not None:
        cache.input_output_by_tag[key] = output
    return output


def get_explanation_cell(notebook_path: str | Path, *, tag: str) -> str:
    """Return explanation markdown content for a tagged cell."""
    return notebook_grader.get_explanation_cell(notebook_path, tag=tag)
