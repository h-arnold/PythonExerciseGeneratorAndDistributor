"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

from pathlib import Path

from exercise_runtime_support.execution_variant import Variant, resolve_variant_notebook_path


def resolve_notebook_path(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    repo_root = Path(__file__).resolve().parents[2]
    return resolve_variant_notebook_path(
        notebook_path,
        variant=variant,
        repo_root=repo_root,
        anchor_to_repo_root=True,
    )
