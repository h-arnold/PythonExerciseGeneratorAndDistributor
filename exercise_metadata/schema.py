"""Minimal exercise.json schema definition.

Canonical fields (all required):
    schema_version  int   always 1 for this schema
    exercise_key    str   unique slug, e.g. "ex004_sequence_debug_syntax"
    exercise_id     int   numeric exercise number (4)
    slug            str   same as exercise_key for canonical exercises
    title           str   human-readable exercise title
    construct       str   programming construct, e.g. "sequence"
    exercise_type   str   exercise type, e.g. "debug", "modify"
    parts           int   number of exercise parts/tasks

Convention-based fields (deliberately excluded from metadata):
    tags            - derived from parts and exercise_type at runtime
    notebook paths  - convention: exercises/<construct>/<key>/notebooks/
    ordering        - derived from exercise_id
    mandatory cells - fixed by repository convention, not per-exercise config
"""

from __future__ import annotations

from typing import Final, TypedDict

SCHEMA_VERSION: Final[int] = 1
REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "schema_version",
    "exercise_key",
    "exercise_id",
    "slug",
    "title",
    "construct",
    "exercise_type",
    "parts",
)


class ExerciseMetadata(TypedDict):
    """Typed representation of exercise.json contents."""

    schema_version: int
    exercise_key: str
    exercise_id: int
    slug: str
    title: str
    construct: str
    exercise_type: str
    parts: int
