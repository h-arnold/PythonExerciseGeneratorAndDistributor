"""Exercise path resolver.

This module provides the canonical resolver API for the new metadata-driven
layout.  It accepts ONLY exercise_key as input; path-based inputs are
rejected immediately with a TypeError.

PYTUTOR_NOTEBOOKS_DIR is deliberately ignored; this resolver targets the
canonical exercise home convention, `exercises/<construct>/<exercise_key>/`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from exercise_metadata.manifest import ExerciseLayout, get_exercise_layout

_EXERCISES_ROOT = Path(__file__).resolve().parents[1] / "exercises"
_KNOWN_CONSTRUCTS = (
    "file_handling",
    "data_types",
    "dictionaries",
    "exceptions",
    "functions",
    "iteration",
    "libraries",
    "selection",
    "sequence",
    "lists",
    "oop",
)

Variant = Literal["student", "solution"]


def _derive_construct_from_exercise_key(exercise_key: str) -> str:
    """Return the construct encoded in an exercise key."""
    _, separator, remainder = exercise_key.partition("_")
    if not separator:
        raise LookupError(
            f"exercise_key {exercise_key!r} does not match the canonical "
            "exNNN_<construct>_<slug> format."
        )

    for construct in _KNOWN_CONSTRUCTS:
        if remainder == construct or remainder.startswith(f"{construct}_"):
            return construct

    raise LookupError(
        f"exercise_key {exercise_key!r} does not contain a known construct. "
        "Cannot derive the canonical exercise directory."
    )


def resolve_exercise_dir(exercise_key: object, exercises_root: Path | None = None) -> Path:
    """Return the canonical directory for the given exercise_key.

    The canonical exercise home is `exercises/<construct>/<exercise_key>/`.
    This function derives the canonical path directly from the exercise_key
    and rejects legacy `exercises/<construct>/<type>/<exercise_key>/` matches.

    Args:
        exercise_key: The unique exercise identifier, e.g.
            ``"ex004_sequence_debug_syntax"``.
        exercises_root: Override the exercises root directory (for testing).

    Returns:
        Path to the exercise directory.

    Raises:
        TypeError: If exercise_key is not a str (e.g. a Path was passed).
        LookupError: If the canonical directory does not exist.
    """
    if not isinstance(exercise_key, str):
        raise TypeError(
            f"exercise_key must be a str, not {type(exercise_key).__name__!r}. "
            "Path-based resolution is not supported; use exercise_key only."
        )
    root = exercises_root or _EXERCISES_ROOT
    construct = _derive_construct_from_exercise_key(exercise_key)
    candidate = root / construct / exercise_key
    if candidate.is_dir():
        return candidate

    legacy_matches = [
        path for path in root.rglob(exercise_key) if path.is_dir() and path != candidate
    ]
    legacy_hint = ""
    if legacy_matches:
        matches = ", ".join(str(path) for path in legacy_matches)
        legacy_hint = (
            " Found non-canonical matches instead: "
            f"{matches}. The canonical path must not include an exercise_type segment."
        )
    raise LookupError(
        f"Canonical exercise directory not found for exercise_key={exercise_key!r}. "
        f"Expected {candidate} under {root}.{legacy_hint}"
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

    try:
        layout = get_exercise_layout(exercise_key, manifest_path)
    except KeyError as exc:
        raise LookupError(
            f"exercise {exercise_key!r} is not in the migration manifest. "
            "Add it to the migration manifest before resolving notebooks."
        ) from exc
    if layout != ExerciseLayout.CANONICAL:
        raise LookupError(
            f"exercise {exercise_key!r} has layout={layout.value!r} in the migration manifest. "
            "resolve_notebook_path() only supports canonical exercises. "
            "Legacy layouts are not valid input to this resolver. "
            "Migrate this exercise to the canonical layout first."
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
