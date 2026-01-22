from __future__ import annotations

import builtins
import contextlib
import json
import os
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Any, TypedDict, cast


class NotebookCell(TypedDict, total=False):
    """TypedDict for a notebook cell as found in an `.ipynb` JSON file.

    Keys are optional since student/solution notebooks may omit some fields.
    """
    cell_type: str
    source: list[str] | str
    metadata: dict[str, Any]


class NotebookGradingError(RuntimeError):
    pass


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve a notebook path, optionally redirecting to a mirrored notebooks dir.

    Set the environment variable `PYTUTOR_NOTEBOOKS_DIR` to point tests at an
    alternate notebook root (for example: `notebooks/solutions`).

    This allows the same tests to run against either student notebooks
    (default) or solution notebooks (mirrors).
    """

    original = Path(notebook_path)
    override_root = os.environ.get("PYTUTOR_NOTEBOOKS_DIR")
    if not override_root:
        return original

    override_root_path = Path(override_root)

    try:
        rel = original.relative_to("notebooks")
    except ValueError:
        # If a caller passes something that isn't under notebooks/, we still
        # allow overriding by using the filename.
        rel = Path(original.name)

    candidate = override_root_path / rel
    return candidate if candidate.exists() else original


def _read_notebook(notebook_path: str | Path) -> dict[str, Any]:
    path = resolve_notebook_path(notebook_path)
    if not path.exists():
        raise NotebookGradingError(f"Notebook not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(
            f"Invalid JSON in notebook: {path}") from exc


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


def extract_tagged_code(notebook_path: str | Path, *, tag: str = "student") -> str:
    """Return the concatenated source of all code cells tagged with `tag`.

    The notebook is expected to be a standard `.ipynb` JSON file where each cell has:
      - `cell_type`: "code" or "markdown"
      - `source`: list[str] OR str
      - `metadata.tags`: optional list[str]

    We keep this pure-stdlib (no nbformat/nbclient dependency) to reduce classroom friction.
    """

    nb = _read_notebook(notebook_path)
    cells = nb.get("cells")
    if not isinstance(cells, list):
        raise NotebookGradingError("Notebook has no 'cells' list")

    tagged_sources = _collect_tagged_sources(
        cast(Sequence[object], cells), tag)

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
    notebook_path: str | Path, *, tag: str = "student", filename_hint: str | None = None
) -> dict[str, Any]:
    """Execute tagged code cells and return the resulting namespace."""

    code = extract_tagged_code(notebook_path, tag=tag)

    path = Path(notebook_path)
    filename = filename_hint or str(path)

    ns: dict[str, Any] = {
        "__name__": "__student__",
        "__file__": filename,
    }

    try:
        compiled = compile(code, filename, "exec")
    except SyntaxError as exc:  # Provide clearer error for notebook authors
        raise NotebookGradingError(
            f"Failed to compile code tagged {tag!r} in {filename}: {exc}") from exc

    try:
        exec(compiled, ns, ns)
    except Exception as exc:  # Wrap runtime errors to include notebook context
        raise NotebookGradingError(
            f"Execution failed for code tagged {tag!r} in {filename}: {exc}") from exc

    return ns


def run_cell_and_capture_output(notebook_path: str | Path, *, tag: str) -> str:
    """Execute a tagged cell and capture its print output.

    This is the primary testing pattern for notebook exercises. Students write
    code that prints output, and tests verify the printed results.

    Args:
        notebook_path: Path to the notebook file
        tag: Cell metadata tag to execute (e.g., "exercise1")

    Returns:
        The captured stdout output as a string

    Example:
        >>> output = run_cell_and_capture_output("notebooks/ex001.ipynb", tag="exercise1")
        >>> assert output.strip() == "Hello Python!"
    """
    with contextlib.redirect_stdout(StringIO()) as buffer:
        exec_tagged_code(notebook_path, tag=tag)
        return buffer.getvalue()


def run_cell_with_input(notebook_path: str | Path, *, tag: str, inputs: list[str]) -> str:
    """Execute a tagged cell with mocked input() and capture stdout.

    For exercises that require user input, this helper mocks the input()
    function to provide predetermined values while capturing print output.

    Args:
        notebook_path: Path to the notebook file
        tag: Cell metadata tag to execute (e.g., "exercise1")
        inputs: List of strings to provide as input() values

    Returns:
        The captured stdout output as a string

    Raises:
        RuntimeError: If the code calls input() more times than provided

    Example:
        >>> output = run_cell_with_input(
        ...     "notebooks/ex002.ipynb",
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
            exec_tagged_code(notebook_path, tag=tag)
            return buffer.getvalue()
    finally:
        builtins.input = original_input


def get_explanation_cell(notebook_path: str | Path, *, tag: str) -> str:
    """Extract explanation cell content by tag.

    Used to verify that students have filled in explanation/reflection cells
    in debugging and problem-solving exercises.

    Args:
        notebook_path: Path to the notebook file
        tag: Cell metadata tag to extract (e.g., "explanation1")

    Returns:
        The markdown cell content as a string

    Raises:
        AssertionError: If no cell with the specified tag is found

    Example:
        >>> explanation = get_explanation_cell("notebooks/ex001.ipynb", tag="explanation1")
        >>> assert len(explanation.strip()) > 10, "Explanation must have content"
    """
    nb = _read_notebook(notebook_path)
    cells = cast(Sequence[object], nb.get("cells", []))

    for cell in cells:
        if not isinstance(cell, dict):
            continue
        cell_dict = cast(dict[str, Any], cell)
        if tag in _cell_tags(cell_dict):
            source = cell_dict.get("source", [])
            if isinstance(source, list):
                source_list: list[str] = []
                for s in cast(Sequence[object], source):
                    if isinstance(s, str):
                        source_list.append(s)
                return "".join(source_list)
            if isinstance(source, str):
                return source
            return str(source)

    raise AssertionError(f"No cell with tag {tag!r} found in {notebook_path}")
