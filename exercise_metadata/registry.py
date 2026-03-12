"""Exercise registry - metadata-driven aggregate view of all exercises.

This module builds an ordered list of exercise metadata by:
1. Reading exercises/migration_manifest.json for the list of exercise_keys.
2. For canonical exercises: loading their exercise.json via load_exercise_metadata().
3. For legacy exercises: returning a stub entry with only exercise_key populated
   from the manifest (since they have no exercise.json yet).

The registry order is determined by exercise_id for canonical exercises, with
legacy exercises inserted in manifest order for exercises that lack an exercise_id.

Exported Classroom repositories (GitHub Classroom student repos) remain
metadata-free by design - they do not ship exercise.json or migration_manifest.json.
The registry is a source-repository concept only.
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from exercise_metadata.loader import load_exercise_metadata
from exercise_metadata.manifest import ExerciseLayout, load_migration_manifest
from exercise_metadata.resolver import resolve_exercise_dir
from exercise_metadata.schema import ExerciseMetadata


class RegistryEntry(TypedDict):
    """A single entry in the exercise registry.

    For canonical exercises all fields from ExerciseMetadata are populated.
    For legacy exercises only exercise_key and layout are populated.
    """

    exercise_key: str
    layout: str
    metadata: ExerciseMetadata | None


def build_exercise_registry(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[RegistryEntry]:
    """Build the full exercise registry from the migration manifest.

    Returns a list of RegistryEntry dicts. Canonical exercises include their
    loaded ExerciseMetadata. Legacy exercises have metadata=None.

    The list is ordered by exercise_id for canonical exercises; legacy exercises
    are appended in manifest order after all canonical exercises are placed.

    Args:
        manifest_path: Override for testing.
        exercises_root: Override for testing.

    Returns:
        Ordered list of RegistryEntry dicts.

    Raises:
        RuntimeError: If a canonical exercise's metadata cannot be loaded.
    """
    manifest = load_migration_manifest(manifest_path)
    exercises = manifest["exercises"]

    canonical_entries: list[RegistryEntry] = []
    legacy_entries: list[RegistryEntry] = []

    for exercise_key, entry in exercises.items():
        layout = ExerciseLayout(entry["layout"])
        if layout == ExerciseLayout.CANONICAL:
            try:
                exercise_dir = resolve_exercise_dir(exercise_key, exercises_root)
                metadata = load_exercise_metadata(exercise_dir)
            except (LookupError, FileNotFoundError, ValueError) as exc:
                raise RuntimeError(
                    f"Failed to load metadata for canonical exercise {exercise_key!r}: {exc}"
                ) from exc
            canonical_entries.append(
                RegistryEntry(exercise_key=exercise_key, layout=layout.value, metadata=metadata)
            )
        else:
            legacy_entries.append(
                RegistryEntry(exercise_key=exercise_key, layout=layout.value, metadata=None)
            )

    # Sort canonical entries by exercise_id; legacy entries maintain manifest order
    canonical_entries.sort(key=lambda e: e["metadata"]["exercise_id"])  # type: ignore[index]
    return canonical_entries + legacy_entries


def get_canonical_exercise_keys(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[str]:
    """Return exercise_keys for all canonical exercises, ordered by exercise_id.

    Args:
        manifest_path: Override for testing.
        exercises_root: Override for testing.

    Returns:
        List of exercise_key strings for canonical exercises only.
    """
    registry = build_exercise_registry(manifest_path, exercises_root)
    return [e["exercise_key"] for e in registry if e["layout"] == ExerciseLayout.CANONICAL.value]


def get_all_exercise_keys(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise_keys from the manifest in registry order.

    Order: canonical exercises by exercise_id, then legacy exercises in manifest order.

    Args:
        manifest_path: Override for testing.
        exercises_root: Override for testing.

    Returns:
        List of all exercise_key strings.
    """
    registry = build_exercise_registry(manifest_path, exercises_root)
    return [e["exercise_key"] for e in registry]
