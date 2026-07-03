"""Exercise registry and catalogue helpers.

This module builds shared metadata-derived views of the exercises discovered
via filesystem scanning for ``exercise.json`` files under the exercises root.

All exercises are canonical (migration is complete); there are no legacy
exercises. The catalogue requires metadata for every discovered exercise so
callers can rely on consistent ordering, titles, construct grouping, and
display labels.

Exported Classroom repositories remain metadata-free by design. This module is
a source-repository concern only.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from exercise_metadata.loader import load_exercise_metadata
from exercise_metadata.resolver import resolve_exercise_dir
from exercise_metadata.schema import ExerciseMetadata

_EXERCISES_ROOT = Path(__file__).resolve().parents[1] / "exercises"


class RegistryEntry(TypedDict):
    """A single entry in the exercise registry."""

    exercise_key: str
    metadata: ExerciseMetadata


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


def build_display_label(exercise_id: int, title: str) -> str:
    """Return the standard notebook label for an exercise."""
    return f"ex{exercise_id:03d} {title}"


def _validate_unique_exercise_ids(catalogue: list[ExerciseCatalogueEntry]) -> None:
    """Fail fast when multiple exercises in the same construct claim the same exercise_id."""
    seen_ids: dict[tuple[str, int], str] = {}
    for entry in catalogue:
        key = (entry["construct"], entry["exercise_id"])
        duplicate_key = seen_ids.get(key)
        if duplicate_key is not None:
            raise RuntimeError(
                "Exercise catalogue requires unique exercise_id values within each "
                f"construct, but exercise_id {entry['exercise_id']} in construct "
                f"{entry['construct']!r} is claimed by both "
                f"{duplicate_key!r} and {entry['exercise_key']!r}."
            )
        seen_ids[key] = entry["exercise_key"]


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
    exercises_root: Path | None,
) -> ExerciseMetadata:
    """Load and validate metadata for a registry entry.

    All exercises are canonical, so metadata is always required. Raises
    ``RuntimeError`` immediately if the exercise directory or ``exercise.json``
    cannot be resolved.

    Returns:
        Validated ``ExerciseMetadata``.
    """
    try:
        exercise_dir = resolve_exercise_dir(exercise_key, exercises_root)
    except LookupError as exc:
        raise RuntimeError(f"Failed to load metadata for exercise {exercise_key!r}: {exc}") from exc

    try:
        metadata = load_exercise_metadata(exercise_dir)
        _validate_metadata_identity(exercise_key, exercise_dir, metadata)
        return metadata
    except (FileNotFoundError, ValueError) as exc:
        raise RuntimeError(f"Failed to load metadata for exercise {exercise_key!r}: {exc}") from exc


def build_exercise_registry(
    exercises_root: Path | None = None,
) -> list[RegistryEntry]:
    """Build the exercise registry by discovering exercises via filesystem glob.

    Scans the exercises root for ``exercise.json`` files using
    ``rglob("exercise.json")``, loads metadata for each, and returns a
    single list sorted by ``(exercise_id, construct)``.

    Args:
        exercises_root: Override the exercises root directory (for testing).

    Returns:
        List of ``RegistryEntry``, sorted by exercise_id then construct.
    """
    root = exercises_root or _EXERCISES_ROOT
    registry: list[RegistryEntry] = []

    for exercise_json_path in sorted(root.rglob("exercise.json")):
        exercise_key = exercise_json_path.parent.name
        metadata = _load_registry_metadata(exercise_key, exercises_root)
        registry.append(RegistryEntry(exercise_key=exercise_key, metadata=metadata))

    registry.sort(
        key=lambda entry: (entry["metadata"]["exercise_id"], entry["metadata"]["construct"])
    )
    return registry


def build_exercise_catalogue(
    exercises_root: Path | None = None,
) -> list[ExerciseCatalogueEntry]:
    """Build the shared metadata-derived exercise catalogue."""
    registry = build_exercise_registry(exercises_root)
    catalogue: list[ExerciseCatalogueEntry] = []
    for entry in registry:
        metadata = entry["metadata"]
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
            )
        )
    _validate_unique_exercise_ids(catalogue)
    return sorted(catalogue, key=lambda entry: (entry["exercise_id"], entry["construct"]))


def get_catalogue_exercise_keys(
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise keys from the metadata-backed catalogue."""
    return [
        entry["exercise_key"] for entry in build_exercise_catalogue(exercises_root=exercises_root)
    ]


def get_canonical_exercise_keys(
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise keys (all exercises are canonical)."""
    return get_all_exercise_keys(exercises_root=exercises_root)


def get_all_exercise_keys(
    exercises_root: Path | None = None,
) -> list[str]:
    """Return all exercise keys in registry order."""
    registry = build_exercise_registry(exercises_root)
    return [entry["exercise_key"] for entry in registry]
