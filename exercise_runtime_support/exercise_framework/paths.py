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


def _is_path_like_string(value: str) -> bool:
    return "/" in value or "\\" in value or Path(value).suffix != ""


def _is_source_legacy_notebook_path(notebook_path: Path, repo_root: Path) -> bool:
    if notebook_path.is_absolute():
        return notebook_path.is_relative_to(repo_root / "notebooks")
    return notebook_path.parts[:1] == ("notebooks",)


def _raise_path_like_string_error(notebook_path: str) -> None:
    raise LookupError(
        "resolver input must be an exercise_key, not a path-like string: "
        f"{notebook_path!r}. Path-like inputs are not supported."
    )


def _raise_legacy_source_path_error(notebook_path: Path) -> None:
    raise LookupError(
        "Source-repository notebook resolution requires an exercise_key, not a "
        f"legacy notebooks/ path: {notebook_path!r}. Pass an exercise_key "
        "string instead."
    )


def _resolve_source_canonical_notebook_path(
    exercise_key: str,
    *,
    variant: Variant | None = None,
) -> Path:
    from exercise_metadata.resolver import resolve_notebook_path as resolve_metadata_notebook_path

    selected_variant = get_active_variant() if variant is None else variant
    return resolve_metadata_notebook_path(exercise_key, selected_variant)


def _relative_packaged_notebooks_dir(exercise_key: str) -> Path:
    catalogue_entry = get_catalogue_entry(exercise_key)
    return Path("exercises") / catalogue_entry.construct / exercise_key / "notebooks"


def _relative_packaged_notebook_path(exercise_key: str) -> Path:
    return (
        _relative_packaged_notebooks_dir(exercise_key)
        / "student.ipynb"
    )


def _relative_packaged_solution_path(exercise_key: str) -> Path:
    return _relative_packaged_notebooks_dir(exercise_key) / "solution.ipynb"


def _resolve_source_legacy_notebook_path(
    exercise_key: str,
    *,
    variant: Variant,
    repo_root: Path,
) -> Path:
    if variant == "student":
        return repo_root / _relative_packaged_notebook_path(exercise_key)
    return repo_root / _relative_packaged_solution_path(exercise_key)


def _resolve_packaged_notebook_path(
    exercise_key: str,
    *,
    variant: Variant,
    repo_root: Path,
) -> Path:
    relative_notebook_path = _relative_packaged_notebook_path(exercise_key)
    if variant == "student":
        return repo_root / relative_notebook_path

    packaged_solution = repo_root / \
        _relative_packaged_solution_path(exercise_key)
    if packaged_solution.exists():
        return packaged_solution

    raise FileNotFoundError(
        "Metadata-free packaged repositories do not include solution notebooks "
        "for exercise-key resolution. Expected an optional solution mirror at "
        f"{packaged_solution} for {exercise_key!r}."
    )


def resolve_exercise_notebook_path(
    exercise_key: str,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve a notebook path from an exercise key.

    Source repositories use canonical metadata-backed paths for canonical
    exercises. Metadata-free packaged exports fall back to the packaged
    exercise-local student surface
    ``exercises/<construct>/<exercise_key>/notebooks/student.ipynb``.
    Packaged solution-mode resolution requires an explicit optional
    ``.../notebooks/solution.ipynb`` mirror and fails fast when
    that surface is absent. Legacy source exercises continue to use the
    existing flattened notebooks/ layout when addressed by exercise_key,
    but raw ``notebooks/...`` path inputs are rejected by
    :func:`resolve_notebook_path`.
    """
    selected_variant = get_active_variant() if variant is None else variant
    repo_root = _framework_repo_root()
    catalogue_entry = get_catalogue_entry(exercise_key)
    has_local_metadata = _has_local_metadata_package(repo_root)
    if has_local_metadata and catalogue_entry.layout == "canonical":
        return _resolve_source_canonical_notebook_path(
            exercise_key,
            variant=selected_variant,
        )

    if not has_local_metadata:
        return _resolve_packaged_notebook_path(
            exercise_key,
            variant=selected_variant,
            repo_root=repo_root,
        )

    return _resolve_source_legacy_notebook_path(
        exercise_key,
        variant=selected_variant,
        repo_root=repo_root,
    )


def resolve_notebook_path(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve an exercise_key string or explicit notebook Path.

    String inputs are treated as exercise keys and must not look like legacy
    notebook paths. Explicit :class:`~pathlib.Path` inputs keep variant
    switching for canonical notebooks and anchor relative paths to the repo
    root, but source-repository ``notebooks/`` paths fail fast so callers
    migrate to exercise_key-based resolution.
    """
    repo_root = _framework_repo_root()
    selected_variant = get_active_variant() if variant is None else variant

    if isinstance(notebook_path, str):
        if _is_path_like_string(notebook_path):
            _raise_path_like_string_error(notebook_path)
        return resolve_exercise_notebook_path(notebook_path, variant=selected_variant)

    if _has_local_metadata_package(repo_root) and _is_source_legacy_notebook_path(
        notebook_path,
        repo_root,
    ):
        _raise_legacy_source_path_error(notebook_path)

    return resolve_variant_notebook_path(
        notebook_path,
        variant=selected_variant,
        repo_root=repo_root,
        anchor_to_repo_root=True,
    )
