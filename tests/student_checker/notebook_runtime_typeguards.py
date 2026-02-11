"""Type guards for the student notebook runtime helpers."""

from __future__ import annotations

from typing import Any, TypeGuard, cast

NotebookCell = dict[str, Any]
NotebookMetadata = dict[str, Any]
NotebookJson = dict[str, object]


def is_notebook_json(value: object) -> TypeGuard[NotebookJson]:
    """Return True when the value looks like the top-level notebook JSON."""
    if not isinstance(value, dict):
        return False
    typed_mapping = cast(dict[object, object], value)
    return all(isinstance(key, str) for key in typed_mapping)


def is_notebook_cell(value: object) -> TypeGuard[NotebookCell]:
    """Return True when the value matches a notebook cell shape."""
    return isinstance(value, dict)


def is_notebook_metadata(value: object) -> TypeGuard[NotebookMetadata]:
    """Return True when the value can be treated as notebook metadata."""
    return isinstance(value, dict)


def is_notebook_cells_list(value: object) -> TypeGuard[list[NotebookCell]]:
    """Return True when the value is a list of notebook cells."""
    if not isinstance(value, list):
        return False
    typed_list = cast(list[NotebookCell], value)
    return all(is_notebook_cell(item) for item in typed_list)
