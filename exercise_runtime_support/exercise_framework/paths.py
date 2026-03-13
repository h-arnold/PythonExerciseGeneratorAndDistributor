"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

from pathlib import Path

from exercise_runtime_support.execution_variant import (
    Variant,
    get_active_variant,
    resolve_variant_notebook_path,
)
from exercise_runtime_support.exercise_catalogue import get_catalogue_entry

__all__ = ["resolve_exercise_notebook_path", "resolve_notebook_path"]


def _framework_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _has_local_metadata_package(repo_root: Path) -> bool:
    return (repo_root / "exercise_metadata" / "__init__.py").exists()


def _resolve_source_canonical_notebook_path(
    exercise_key: str,
    *,
    variant: Variant | None = None,
) -> Path:
    from exercise_metadata.resolver import resolve_notebook_path as resolve_metadata_notebook_path

    selected_variant = get_active_variant() if variant is None else variant
    return resolve_metadata_notebook_path(exercise_key, selected_variant)


def resolve_exercise_notebook_path(
    exercise_key: str,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve a notebook path from an exercise key.

    Source repositories use canonical metadata-backed paths for canonical
    exercises. Metadata-free packaged exports fall back to the flattened
    ``notebooks/<exercise_key>.ipynb`` surface generated for Classroom repos.
    Legacy source exercises continue to use the existing flattened notebooks/
    layout so variant selection still works.
    """
    if not isinstance(exercise_key, str):
        raise TypeError(
            f"exercise_key must be a str, not {type(exercise_key).__name__!r}"
        )

    selected_variant = get_active_variant() if variant is None else variant
    repo_root = _framework_repo_root()
    catalogue_entry = get_catalogue_entry(exercise_key)
    has_local_metadata = _has_local_metadata_package(repo_root)
    if has_local_metadata and catalogue_entry.layout == "canonical":
        return _resolve_source_canonical_notebook_path(
            exercise_key,
            variant=selected_variant,
        )

    relative_notebook_path = Path("notebooks") / f"{exercise_key}.ipynb"
    if not has_local_metadata and selected_variant == "student":
        exported_notebook = repo_root / relative_notebook_path
        if exported_notebook.exists():
            return exported_notebook

    return resolve_notebook_path(relative_notebook_path, variant=selected_variant)


def resolve_notebook_path(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve notebook paths using the repository's grading semantics."""
    repo_root = _framework_repo_root()
    return resolve_variant_notebook_path(
        notebook_path,
        variant=variant,
        repo_root=repo_root,
        anchor_to_repo_root=True,
    )
