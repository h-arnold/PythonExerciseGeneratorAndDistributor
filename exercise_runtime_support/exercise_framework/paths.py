"""Notebook path resolution helpers for the exercise framework."""

from __future__ import annotations

from pathlib import Path

import exercise_metadata.resolver as metadata_resolver
from exercise_runtime_support.execution_variant import (
    Variant,
    get_active_variant,
    resolve_variant_notebook_path,
)

__all__ = ["resolve_exercise_notebook_path", "resolve_notebook_path"]


def _framework_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def resolve_exercise_notebook_path(
    exercise_key: str,
    *,
    variant: Variant | None = None,
) -> Path:
    """Resolve a notebook path from an exercise key.

    The runtime catalogue resolution is metadata-backed for both source and
    packaged modes. Raw ``notebooks/...`` path inputs are rejected by
    :func:`resolve_notebook_path`.
    """
    selected_variant = get_active_variant() if variant is None else variant
    return metadata_resolver.resolve_notebook_path(
        exercise_key,
        variant=selected_variant,
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

    if _is_source_legacy_notebook_path(
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
