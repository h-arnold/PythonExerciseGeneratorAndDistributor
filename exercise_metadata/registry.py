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


def _validate_unique_exercise_ids(catalogue: list[ExerciseCatalogueEntry]) -> None:
    """Fail fast when multiple exercises claim the same exercise_id."""
    seen_ids: dict[int, str] = {}
    for entry in catalogue:
        duplicate_key = seen_ids.get(entry["exercise_id"])
        if duplicate_key is None:
            seen_ids[entry["exercise_id"]] = entry["exercise_key"]
            continue
        raise RuntimeError(
            "Exercise catalogue requires unique exercise_id values, but "
            f"exercise_id {entry['exercise_id']} is claimed by both "
            f"{duplicate_key!r} and {entry['exercise_key']!r}."
        )


def _validate_metadata_identity(
    exercise_key: str,
    exercise_dir: Path,
    metadata: ExerciseMetadata,
) -> None:
    """Fail fast when metadata identity diverges from its canonical home."""
    metadata_path = exercise_dir / "exercise.json"
    if metadata["exercise_key"] != exercise_key:
        raise ValueError(
            f"exercise.json at {metadata_path} has exercise_key "
            f"{metadata['exercise_key']!r}; expected {exercise_key!r}"
        )

    expected_construct = exercise_dir.parent.name
    if metadata["construct"] != expected_construct:
        raise ValueError(
            f"exercise.json at {metadata_path} has construct "
            f"{metadata['construct']!r}; expected {expected_construct!r} "
            "from the canonical directory path"
        )


def _load_registry_metadata(
    exercise_key: str,
    layout: ExerciseLayout,
    exercises_root: Path | None,
) -> ExerciseMetadata | None:
    """Load metadata for a registry entry when an ``exercise.json`` file exists."""
    try:
        exercise_dir = resolve_exercise_dir(exercise_key, exercises_root)
    except LookupError as exc:
        if layout == ExerciseLayout.CANONICAL:
            raise RuntimeError(
                f"Failed to load metadata for canonical exercise {exercise_key!r}: {exc}"
            ) from exc
        return None

    try:
        metadata = load_exercise_metadata(exercise_dir)
        _validate_metadata_identity(exercise_key, exercise_dir, metadata)
        return metadata
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
        metadata = _load_registry_metadata(
            exercise_key, layout, exercises_root)
        target = canonical_entries if layout == ExerciseLayout.CANONICAL else legacy_entries
        target.append(
            RegistryEntry(exercise_key=exercise_key,
                          layout=layout.value, metadata=metadata)
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
                display_label=build_display_label(
                    metadata["exercise_id"], metadata["title"]),
                construct=metadata["construct"],
                exercise_type=metadata["exercise_type"],
                parts=metadata["parts"],
                layout=entry["layout"],
            )
        )
    _validate_unique_exercise_ids(catalogue)
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
