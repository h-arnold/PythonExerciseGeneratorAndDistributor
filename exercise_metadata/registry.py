"""Exercise registry and catalogue helpers.

This module builds shared metadata-derived views of the exercises declared in
``exercises/migration_manifest.json``.

The registry preserves layout information and tolerates legacy exercises that do
not yet have metadata. The catalogue is stricter: it requires metadata for every
listed exercise so callers can rely on consistent ordering, titles, construct
grouping, and display labels.

Exported Classroom repositories remain metadata-free by design. This module is a
source-repository concern only.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from exercise_metadata.loader import load_exercise_metadata
from exercise_metadata.manifest import ExerciseLayout, load_migration_manifest
from exercise_metadata.resolver import resolve_exercise_dir
from exercise_metadata.schema import ExerciseMetadata


class RegistryEntry(TypedDict):
    """A single entry in the exercise registry."""

    exercise_key: str
    layout: str
    metadata: ExerciseMetadata | None


class ExerciseCatalogueEntry(TypedDict):
    """Metadata-backed exercise information for shared catalogue consumers."""

    exercise_key: str
    exercise_id: int
    slug: str
    title: str
    display_label: str
    construct: str
    exercise_type: str
    parts: int
    layout: str


def build_display_label(exercise_id: int, title: str) -> str:
    """Return the standard notebook label for an exercise."""
    return f"ex{exercise_id:03d} {title}"


def _find_metadata_directory(exercise_key: str, exercises_root: Path | None) -> Path | None:
    """Return the canonical exercise directory when it exists."""
    try:
        return resolve_exercise_dir(exercise_key, exercises_root)
    except LookupError:
        return None


def _load_registry_metadata(
    exercise_key: str,
    layout: ExerciseLayout,
    exercises_root: Path | None,
) -> ExerciseMetadata | None:
    """Load metadata for a registry entry when an ``exercise.json`` file exists."""
    exercise_dir = _find_metadata_directory(exercise_key, exercises_root)
    if exercise_dir is None:
        if layout == ExerciseLayout.CANONICAL:
            raise RuntimeError(
                f"Failed to load metadata for canonical exercise {exercise_key!r}: "
                "exercise.json was not found"
            )
        return None

    try:
        return load_exercise_metadata(exercise_dir)
    except FileNotFoundError as exc:
        if layout == ExerciseLayout.LEGACY:
            return None
        raise RuntimeError(
            f"Failed to load metadata for {layout.value} exercise {exercise_key!r}: {exc}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            f"Failed to load metadata for {layout.value} exercise {exercise_key!r}: {exc}"
        ) from exc


def build_exercise_registry(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[RegistryEntry]:
    """Build the full exercise registry from the migration manifest."""
    manifest = load_migration_manifest(manifest_path)
    exercises = manifest["exercises"]

    canonical_entries: list[RegistryEntry] = []
    legacy_entries: list[RegistryEntry] = []

    for exercise_key, entry in exercises.items():
        layout = ExerciseLayout(entry["layout"])
        metadata = _load_registry_metadata(exercise_key, layout, exercises_root)
        target = canonical_entries if layout == ExerciseLayout.CANONICAL else legacy_entries
        target.append(
            RegistryEntry(exercise_key=exercise_key, layout=layout.value, metadata=metadata)
        )

    canonical_entries.sort(key=lambda entry: entry["metadata"]["exercise_id"])
    return canonical_entries + legacy_entries


def build_exercise_catalogue(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[ExerciseCatalogueEntry]:
    """Build the shared metadata-derived exercise catalogue."""
    registry = build_exercise_registry(manifest_path, exercises_root)
    catalogue: list[ExerciseCatalogueEntry] = []
    for entry in registry:
        metadata = entry["metadata"]
        if metadata is None:
            raise RuntimeError(
                f"Exercise catalogue requires metadata for {entry['exercise_key']!r}, "
                "but no exercise.json was found."
            )
        catalogue.append(
            ExerciseCatalogueEntry(
                exercise_key=entry["exercise_key"],
                exercise_id=metadata["exercise_id"],
                slug=metadata["slug"],
                title=metadata["title"],
                display_label=build_display_label(metadata["exercise_id"], metadata["title"]),
                construct=metadata["construct"],
                exercise_type=metadata["exercise_type"],
                parts=metadata["parts"],
                layout=entry["layout"],
            )
        )
    return sorted(catalogue, key=lambda entry: entry["exercise_id"])


def get_catalogue_exercise_keys(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise keys from the metadata-backed catalogue."""
    return [
        entry["exercise_key"]
        for entry in build_exercise_catalogue(manifest_path=manifest_path, exercises_root=exercises_root)
    ]


def get_canonical_exercise_keys(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[str]:
    """Return exercise keys for canonical exercises, ordered by exercise_id."""
    registry = build_exercise_registry(manifest_path, exercises_root)
    return [entry["exercise_key"] for entry in registry if entry["layout"] == ExerciseLayout.CANONICAL.value]


def get_all_exercise_keys(
    manifest_path: Path | None = None,
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise keys from the manifest in registry order."""
    registry = build_exercise_registry(manifest_path, exercises_root)
    return [entry["exercise_key"] for entry in registry]
