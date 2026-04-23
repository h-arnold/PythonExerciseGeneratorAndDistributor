from __future__ import annotations

import builtins
import contextlib
import json
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Any, TypedDict, cast

from exercise_runtime_support.execution_variant import Variant
from exercise_runtime_support.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)


class NotebookCell(TypedDict, total=False):
    """TypedDict for a notebook cell as found in an `.ipynb` JSON file.

    Keys are optional since student/solution notebooks may omit some fields.
    """

    cell_type: str
    source: list[str] | str
    metadata: dict[str, Any]


class NotebookGradingError(RuntimeError):
    pass


def _read_notebook(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
) -> dict[str, Any]:
    path = resolve_framework_notebook_path(notebook_path, variant=variant)
    if not path.exists():
        raise NotebookGradingError(f"Notebook not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(f"Invalid JSON in notebook: {path}") from exc


def _cell_tags(cell: NotebookCell | dict[str, Any]) -> set[str]:
    """Return a set of string tags found in a cell's metadata.

    This function is defensive: it validates that `metadata` is a mapping and
    that `tags` is either a string or list of strings before using them.
    """
    metadata = cell.get("metadata")
    if not isinstance(metadata, dict):
        return set()

    md = cast(dict[str, Any], metadata)
    tags = md.get("tags")
    if isinstance(tags, str):
        return {tags}
    if isinstance(tags, list):
        tags_list: list[str] = []
        for t in cast(Sequence[object], tags):
            if isinstance(t, str):
                tags_list.append(t)
        return set(tags_list)
    return set()


def _cell_source_text(cell: NotebookCell | dict[str, Any]) -> str:
    """Return source text for a cell, joining lists into a single string.

    The notebook format allows `source` to be either a `str` or `list[str]`.
    We coerce and filter to strings for safety.
    """
    source = cell.get("source", "")
    if isinstance(source, list):
        source_list: list[str] = []
        for s in cast(Sequence[object], source):
            if isinstance(s, str):
                source_list.append(s)
        return "\n".join(source_list)
    if isinstance(source, str):
        return source
    return ""


def extract_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    variant: Variant | None = None,
) -> str:
    """Return the concatenated source of all code cells tagged with `tag`.

    The notebook is expected to be a standard `.ipynb` JSON file where each cell has:
      - `cell_type`: "code" or "markdown"
      - `source`: list[str] OR str
      - `metadata.tags`: optional list[str]

    We keep this pure-stdlib (no nbformat/nbclient dependency) to reduce classroom friction.
    """

    nb = _read_notebook(notebook_path, variant=variant)
    cells = nb.get("cells")
    if not isinstance(cells, list):
        raise NotebookGradingError("Notebook has no 'cells' list")

    tagged_sources = _collect_tagged_sources(cast(Sequence[object], cells), tag)

    if not tagged_sources:
        raise NotebookGradingError(
            f"No code cells tagged '{tag}' found in notebook: {Path(notebook_path)}"
        )

    return "\n\n".join(tagged_sources).strip() + "\n"


def _collect_tagged_sources(cells: Sequence[object], tag: str) -> list[str]:
    """Collect source text from code cells tagged with the given tag."""
    tagged_sources: list[str] = []

    for cell in cells:
        if not isinstance(cell, dict):
            continue
        cell_dict = cast(dict[str, Any], cell)
        if cell_dict.get("cell_type") != "code":
            continue
        if tag not in _cell_tags(cell_dict):
            continue

        tagged_sources.append(_cell_source_text(cell_dict))

    return tagged_sources


def exec_tagged_code(
    notebook_path: str | Path,
    *,
    tag: str = "student",
    filename_hint: str | None = None,
    variant: Variant | None = None,
) -> dict[str, Any]:
    """Execute tagged code cells and return the resulting namespace."""

    code = extract_tagged_code(notebook_path, tag=tag, variant=variant)

    path = resolve_framework_notebook_path(notebook_path, variant=variant)
    filename = filename_hint or str(path)

    ns: dict[str, Any] = {
        "__name__": "__student__",
        "__file__": filename,
    }

    try:
        compiled = compile(code, filename, "exec")
    except SyntaxError as exc:  # Provide clearer error for notebook authors
        raise NotebookGradingError(
            f"Failed to compile code tagged {tag!r} in {filename}: {exc}"
        ) from exc

    try:
        exec(compiled, ns, ns)
    except Exception as exc:  # Wrap runtime errors to include notebook context
        raise NotebookGradingError(
            f"Execution failed for code tagged {tag!r} in {filename}: {exc}"
        ) from exc

    return ns


def run_cell_and_capture_output(
    notebook_path: str | Path,
    *,
    tag: str,
    variant: Variant | None = None,
) -> str:
    """Execute a tagged cell and capture its print output.

    This is the primary testing pattern for notebook exercises. Students write
    code that prints output, and tests verify the printed results.

    Args:
        notebook_path: Exercise key or explicit notebook file path
        tag: Cell metadata tag to execute (e.g., "exercise1")

    Returns:
        The captured stdout output as a string

    Example:
        >>> output = run_cell_and_capture_output(
        ...     "ex002_sequence_modify_basics",
        ...     tag="exercise1",
        ... )
        >>> assert output.strip() == "Hello Python!"
    """
    with contextlib.redirect_stdout(StringIO()) as buffer:
        exec_tagged_code(notebook_path, tag=tag, variant=variant)
        return buffer.getvalue()


def run_cell_with_input(
    notebook_path: str | Path,
    *,
    tag: str,
    inputs: list[str],
    variant: Variant | None = None,
) -> str:
    """Execute a tagged cell with mocked input() and capture stdout.

    For exercises that require user input, this helper mocks the input()
    function to provide predetermined values while capturing print output.

    Args:
        notebook_path: Exercise key or explicit notebook file path
        tag: Cell metadata tag to execute (e.g., "exercise1")
        inputs: List of strings to provide as input() values

    Returns:
        The captured stdout output as a string

    Raises:
        RuntimeError: If the code calls input() more times than provided

    Example:
        >>> output = run_cell_with_input(
        ...     "ex002_sequence_modify_basics",
        ...     tag="exercise1",
        ...     inputs=["Alice"]
        ... )
        >>> assert "Alice" in output
    """
    original_input = builtins.input
    iterator = iter(inputs)

    def fake_input(prompt: str = "") -> str:
        # Write prompt to stdout to match real input() behavior
        if prompt:
            print(prompt, end="")
        try:
            return next(iterator)
        except StopIteration as exc:
            raise RuntimeError("Test expected more input values") from exc

    builtins.input = fake_input

    try:
        with contextlib.redirect_stdout(StringIO()) as buffer:
            exec_tagged_code(notebook_path, tag=tag, variant=variant)
            return buffer.getvalue()
    finally:
        builtins.input = original_input


def get_explanation_cell(
    notebook_path: str | Path,
    *,
    tag: str,
    variant: Variant | None = None,
) -> str:
    """Extract explanation cell content by tag.

    Used to verify that students have filled in explanation/reflection cells
    in debugging and problem-solving exercises.

    Args:
        notebook_path: Exercise key or explicit notebook file path
        tag: Cell metadata tag to extract (e.g., "explanation1")

    Returns:
        The markdown cell content as a string

    Raises:
        AssertionError: If no cell with the specified tag is found

    Example:
        >>> explanation = get_explanation_cell(
        ...     "ex004_sequence_debug_syntax",
        ...     tag="explanation1",
        ... )
        >>> assert len(explanation.strip()) > 10, "Explanation must have content"
    """
    nb = _read_notebook(notebook_path, variant=variant)
    cells = cast(Sequence[object], nb.get("cells", []))

    for cell in cells:
        if not isinstance(cell, dict):
            continue
        cell_dict = cast(dict[str, Any], cell)
        if tag not in _cell_tags(cell_dict):
            continue
        return _format_cell_source(cell_dict.get("source", []))

    raise AssertionError(f"No cell with tag {tag!r} found in {notebook_path}")


def _format_cell_source(source: object) -> str:
    """Return a single string representation of a cell's source value."""

    if isinstance(source, str):
        return source
    if isinstance(source, Sequence):
        return "".join(str(s) for s in cast(Sequence[object], source) if isinstance(s, str))
    return str(source)
