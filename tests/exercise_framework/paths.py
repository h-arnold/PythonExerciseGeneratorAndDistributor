"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    repo_root = Path(__file__).resolve().parents[2]
    notebooks_root = repo_root / "notebooks"

    path = Path(notebook_path)
    if not path.is_absolute():
        path = (repo_root / path).resolve()

    override_root = os.environ.get("PYTUTOR_NOTEBOOKS_DIR")
    if not override_root:
        return path

    override_root_path = Path(override_root)

    try:
        rel = path.relative_to(notebooks_root)
    except ValueError:
        rel = Path(path.name)

    candidate = override_root_path / rel
    return candidate if candidate.exists() else path
