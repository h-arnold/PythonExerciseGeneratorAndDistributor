"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_from_repo_root(repo_root: Path, notebook_path: Path) -> Path:
    if notebook_path.is_absolute():
        return notebook_path
    return (repo_root / notebook_path).resolve()


def _normalise_override_root(override_root: str) -> str:
    normalised = override_root.replace("\\", "/").strip()
    if normalised.startswith("./"):
        normalised = normalised[2:]
    return normalised.rstrip("/")


def _relative_notebook_path(notebook_path: Path) -> Path:
    try:
        return notebook_path.relative_to("notebooks")
    except ValueError:
        return Path(notebook_path.name)


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    repo_root = Path(__file__).resolve().parents[2]
    original = Path(notebook_path)
    override_root = os.environ.get("PYTUTOR_NOTEBOOKS_DIR")
    if not override_root:
        return _resolve_from_repo_root(repo_root, original)

    normalised_override_root = _normalise_override_root(override_root)
    if not normalised_override_root:
        return _resolve_from_repo_root(repo_root, original)
    override_root_path = Path(normalised_override_root)
    if not override_root_path.is_absolute():
        override_root_path = (repo_root / override_root_path).resolve()

    candidate = override_root_path / _relative_notebook_path(original)
    return candidate if candidate.exists() else original
