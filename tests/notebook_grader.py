from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class NotebookGradingError(RuntimeError):
    pass


def _read_notebook(notebook_path: str | Path) -> dict[str, Any]:
    path = Path(notebook_path)
    if not path.exists():
        raise NotebookGradingError(f"Notebook not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(f"Invalid JSON in notebook: {path}") from exc


def _cell_tags(cell: dict[str, Any]) -> set[str]:
    metadata = cell.get("metadata") or {}
    tags = metadata.get("tags") or []
    if isinstance(tags, str):
        return {tags}
    if isinstance(tags, list):
        return {t for t in tags if isinstance(t, str)}
    return set()


def _cell_source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "\n".join(source)
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

    tagged_sources: list[str] = []

    for cell in cells:
        if not isinstance(cell, dict):
            continue
        if cell.get("cell_type") != "code":
            continue
        if tag not in _cell_tags(cell):
            continue

        tagged_sources.append(_cell_source_text(cell))

    if not tagged_sources:
        raise NotebookGradingError(
            f"No code cells tagged '{tag}' found in notebook: {Path(notebook_path)}"
        )

    return "\n\n".join(tagged_sources).strip() + "\n"


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

    compiled = compile(code, filename, "exec")
    exec(compiled, ns, ns)
    return ns
