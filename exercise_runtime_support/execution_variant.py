"""Helpers for the explicit notebook-variant execution contract."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Literal

Variant = Literal["student", "solution"]

ACTIVE_VARIANT_ENV_VAR = "PYTUTOR_ACTIVE_VARIANT"


def validate_variant(variant: str) -> Variant:
    """Return a validated notebook variant."""
    if variant == "student":
        return "student"
    if variant == "solution":
        return "solution"
    raise RuntimeError(
        f"{ACTIVE_VARIANT_ENV_VAR} must be 'student' or 'solution', not {variant!r}")


def get_active_variant(*, default: Variant = "solution") -> Variant:
    """Return the active notebook variant from the environment."""
    raw_variant = os.environ.get(ACTIVE_VARIANT_ENV_VAR)
    if raw_variant is None:
        return default
    stripped_variant = raw_variant.strip()
    if stripped_variant == "":
        return default
    return validate_variant(stripped_variant)


def configure_variant_environment(
    env: MutableMapping[str, str],
    variant: Variant,
) -> None:
    """Store the explicit notebook variant in an environment mapping."""
    env[ACTIVE_VARIANT_ENV_VAR] = variant


def resolve_variant_notebook_path(
    notebook_path: str | Path,
    *,
    variant: Variant | None = None,
    repo_root: Path | None = None,
    anchor_to_repo_root: bool = False,
) -> Path:
    """Return the notebook path selected by the explicit variant contract."""
    selected_variant = variant or get_active_variant()
    original = Path(notebook_path)
    resolved = _anchor_path(
        original, repo_root) if anchor_to_repo_root else original
    return _resolve_canonical_notebook_path(resolved, selected_variant)


def _anchor_path(path: Path, repo_root: Path | None) -> Path:
    if path.is_absolute() or repo_root is None:
        return path
    return (repo_root / path).resolve()


def _resolve_canonical_notebook_path(notebook_path: Path, variant: Variant) -> Path:
    expected_name = f"{variant}.ipynb"
    if notebook_path.name in {"student.ipynb", "solution.ipynb"}:
        return notebook_path.with_name(expected_name)
    return notebook_path
