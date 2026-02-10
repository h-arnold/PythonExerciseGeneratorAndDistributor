"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    repo_root = Path(__file__).resolve().parents[2]
    original = Path(notebook_path)
    override_root = os.environ.get("PYTUTOR_NOTEBOOKS_DIR")
    if not override_root:
        if original.is_absolute():
            return original
        return (repo_root / original).resolve()

    override_root_path = Path(override_root)
    if not override_root_path.is_absolute():
        override_root_path = (repo_root / override_root_path).resolve()

    try:
        rel = original.relative_to("notebooks")
    except ValueError:
        rel = Path(original.name)

    candidate = override_root_path / rel
    return candidate if candidate.exists() else original
