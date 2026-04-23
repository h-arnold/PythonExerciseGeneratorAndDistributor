"""Shared exercise catalogue for runtime support modules.

The catalogue is always built from ``exercise_metadata.registry`` so source and
packaged runtimes share the same metadata-backed resolution path.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import exercise_metadata.registry as metadata_registry


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


def _build_metadata_catalogue() -> tuple[ExerciseCatalogueEntry, ...]:
    """Load the runtime catalogue from the metadata registry."""
    return tuple(
        _to_runtime_entry(entry)
        for entry in metadata_registry.build_exercise_catalogue()
    )


@lru_cache(maxsize=1)
def get_exercise_catalogue() -> tuple[ExerciseCatalogueEntry, ...]:
    """Return the shared exercise catalogue."""
    return _build_metadata_catalogue()


def get_catalogue_entry(exercise_key: str) -> ExerciseCatalogueEntry:
    """Return a single catalogue entry by exercise key."""
    for entry in get_exercise_catalogue():
        if entry.exercise_key == exercise_key:
            return entry
    available = ", ".join(
        item.exercise_key for item in get_exercise_catalogue())
    raise ValueError(
        f"Unknown exercise key '{exercise_key}'. Available: {available}")


def get_catalogue_key_for_exercise_id(exercise_id: int) -> str:
    """Return the exercise key for a numeric exercise identifier."""
    for entry in get_exercise_catalogue():
        if entry.exercise_id == exercise_id:
            return entry.exercise_key
    raise ValueError(f"Unknown exercise_id {exercise_id!r}")
