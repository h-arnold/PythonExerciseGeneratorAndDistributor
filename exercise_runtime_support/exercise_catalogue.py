"""Shared exercise catalogue for runtime support modules.

The source repository loads this from ``exercise_metadata.registry``. Packaged
Classroom exports remain metadata-free, so this module falls back to a checked-in
snapshot of the same catalogue data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class ExerciseCatalogueEntry:
    """Runtime-friendly view of an exercise catalogue entry."""

    exercise_key: str
    exercise_id: int
    slug: str
    title: str
    display_label: str
    construct: str
    exercise_type: str
    parts: int
    layout: str


_FALLBACK_CATALOGUE: tuple[ExerciseCatalogueEntry, ...] = (
    ExerciseCatalogueEntry(
        exercise_key="ex002_sequence_modify_basics",
        exercise_id=2,
        slug="ex002_sequence_modify_basics",
        title="Sequence Modify Basics",
        display_label="ex002 Sequence Modify Basics",
        construct="sequence",
        exercise_type="modify",
        parts=10,
        layout="legacy",
    ),
    ExerciseCatalogueEntry(
        exercise_key="ex003_sequence_modify_variables",
        exercise_id=3,
        slug="ex003_sequence_modify_variables",
        title="Sequence Modify Variables",
        display_label="ex003 Sequence Modify Variables",
        construct="sequence",
        exercise_type="modify",
        parts=10,
        layout="legacy",
    ),
    ExerciseCatalogueEntry(
        exercise_key="ex004_sequence_debug_syntax",
        exercise_id=4,
        slug="ex004_sequence_debug_syntax",
        title="Debug Syntax Errors",
        display_label="ex004 Debug Syntax Errors",
        construct="sequence",
        exercise_type="debug",
        parts=10,
        layout="canonical",
    ),
    ExerciseCatalogueEntry(
        exercise_key="ex005_sequence_debug_logic",
        exercise_id=5,
        slug="ex005_sequence_debug_logic",
        title="Debug Logical Errors",
        display_label="ex005 Debug Logical Errors",
        construct="sequence",
        exercise_type="debug",
        parts=10,
        layout="legacy",
    ),
    ExerciseCatalogueEntry(
        exercise_key="ex006_sequence_modify_casting",
        exercise_id=6,
        slug="ex006_sequence_modify_casting",
        title="Casting and Type Conversion",
        display_label="ex006 Casting and Type Conversion",
        construct="sequence",
        exercise_type="modify",
        parts=10,
        layout="legacy",
    ),
    ExerciseCatalogueEntry(
        exercise_key="ex007_sequence_debug_casting",
        exercise_id=7,
        slug="ex007_sequence_debug_casting",
        title="Sequence Debug Casting",
        display_label="ex007 Sequence Debug Casting",
        construct="sequence",
        exercise_type="debug",
        parts=10,
        layout="legacy",
    ),
)


def _to_runtime_entry(entry: Any) -> ExerciseCatalogueEntry:
    """Normalise metadata catalogue output into the runtime dataclass."""
    return ExerciseCatalogueEntry(
        exercise_key=entry["exercise_key"],
        exercise_id=entry["exercise_id"],
        slug=entry["slug"],
        title=entry["title"],
        display_label=entry["display_label"],
        construct=entry["construct"],
        exercise_type=entry["exercise_type"],
        parts=entry["parts"],
        layout=entry["layout"],
    )


@lru_cache(maxsize=1)
def get_exercise_catalogue() -> tuple[ExerciseCatalogueEntry, ...]:
    """Return the shared exercise catalogue."""
    try:
        registry = import_module("exercise_metadata.registry")
        build_catalogue = registry.build_exercise_catalogue
        return tuple(_to_runtime_entry(entry) for entry in build_catalogue())
    except (ImportError, AttributeError, RuntimeError, FileNotFoundError, LookupError, ValueError):
        return _FALLBACK_CATALOGUE


def get_catalogue_entry(exercise_key: str) -> ExerciseCatalogueEntry:
    """Return a single catalogue entry by exercise key."""
    for entry in get_exercise_catalogue():
        if entry.exercise_key == exercise_key:
            return entry
    available = ", ".join(
        item.exercise_key for item in get_exercise_catalogue())
    raise ValueError(
        f"Unknown notebook '{exercise_key}'. Available: {available}")


def get_catalogue_key_for_exercise_id(exercise_id: int) -> str:
    """Return the exercise key for a numeric exercise identifier."""
    for entry in get_exercise_catalogue():
        if entry.exercise_id == exercise_id:
            return entry.exercise_key
    raise ValueError(f"Unknown exercise_id {exercise_id!r}")
