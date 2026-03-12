"""Exercise path resolver.

This module provides the canonical resolver API for the new metadata-driven
layout.  It accepts ONLY exercise_key as input; path-based inputs are
rejected immediately with a TypeError.

PYTUTOR_NOTEBOOKS_DIR is deliberately ignored; this resolver addresses the
canonical exercises/ tree only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from exercise_metadata.manifest import ExerciseLayout, get_exercise_layout

_EXERCISES_ROOT = Path(__file__).resolve().parents[1] / "exercises"

Variant = Literal["student", "solution"]


def resolve_exercise_dir(exercise_key: object, exercises_root: Path | None = None) -> Path:
    """Return the canonical directory for the given exercise_key.

    Searches the exercises/ tree for a directory whose name matches
    exercise_key.  Returns the path whether or not the exercise has been
    migrated (the caller can check layout via the manifest).

    Args:
        exercise_key: The unique exercise identifier, e.g.
            ``"ex004_sequence_debug_syntax"``.
        exercises_root: Override the exercises root directory (for testing).

    Returns:
        Path to the exercise directory.

    Raises:
        TypeError: If exercise_key is not a str (e.g. a Path was passed).
        LookupError: If no directory matching exercise_key is found.
    """
    if not isinstance(exercise_key, str):
        raise TypeError(
            f"exercise_key must be a str, not {type(exercise_key).__name__!r}. "
            "Path-based resolution is not supported; use exercise_key only."
        )
    root = exercises_root or _EXERCISES_ROOT
    for candidate in root.rglob(exercise_key):
        if candidate.is_dir():
            return candidate
    raise LookupError(
        f"No exercise directory found for exercise_key={exercise_key!r} "
        f"under {root}. Check that the exercise exists in the exercises/ tree."
    )


def resolve_notebook_path(
    exercise_key: object,
    variant: Variant,
    exercises_root: Path | None = None,
    manifest_path: Path | None = None,
) -> Path:
    """Return the canonical notebook path for the given exercise and variant.

    Only exercises marked as ``"canonical"`` in the migration manifest are
    supported.  Legacy exercises fail hard with a clear error.

    Args:
        exercise_key: The unique exercise identifier.
        variant: ``"student"`` or ``"solution"``.
        exercises_root: Override for testing.
        manifest_path: Override for testing.

    Returns:
        Path to the notebook file (existence guaranteed by this function).

    Raises:
        TypeError: If exercise_key is not a str.
        ValueError: If variant is not "student" or "solution".
        LookupError: If the exercise is not in the manifest or its canonical
            notebook files are missing.
    """
    if not isinstance(exercise_key, str):
        raise TypeError(
            f"exercise_key must be a str, not {type(exercise_key).__name__!r}. "
            "Path-based resolution is not supported."
        )
    if variant not in ("student", "solution"):
        raise ValueError(f"variant must be 'student' or 'solution', not {variant!r}")

    layout = get_exercise_layout(exercise_key, manifest_path)
    if layout != ExerciseLayout.CANONICAL:
        raise LookupError(
            f"exercise {exercise_key!r} has layout={layout.value!r} in the migration manifest. "
            "resolve_notebook_path() only supports canonical exercises. "
            "Migrate this exercise to the canonical layout first, or use the "
            "legacy notebooks/ path directly for now."
        )

    exercise_dir = resolve_exercise_dir(exercise_key, exercises_root)
    notebook_path = exercise_dir / "notebooks" / f"{variant}.ipynb"
    if not notebook_path.exists():
        raise LookupError(
            f"exercise {exercise_key!r} is marked as canonical in the migration manifest "
            f"but the expected notebook is missing: {notebook_path}. "
            "Add the notebook file or correct the manifest."
        )
    return notebook_path
