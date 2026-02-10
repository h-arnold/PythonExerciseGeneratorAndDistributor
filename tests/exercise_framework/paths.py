"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

from pathlib import Path

from tests import notebook_grader


def resolve_notebook_path(notebook_path: str | Path) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    return notebook_grader.resolve_notebook_path(notebook_path)
