"""Migration manifest loader.

The migration manifest at exercises/migration_manifest.json records whether
each exercise uses the legacy layout (notebooks/ tree) or has been migrated
to the canonical layout (exercises/<construct>/<key>/ tree).
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import TypedDict


class ExerciseLayout(StrEnum):
    """Layout state for a single exercise."""

    LEGACY = "legacy"
    CANONICAL = "canonical"


class ExerciseManifestEntry(TypedDict):
    """A single entry in the migration manifest exercises dict."""

    layout: str


class MigrationManifest(TypedDict):
    """Typed representation of migration_manifest.json."""

    schema_version: int
    exercises: dict[str, ExerciseManifestEntry]


_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "exercises" / "migration_manifest.json"


def load_migration_manifest(manifest_path: Path | None = None) -> MigrationManifest:
    """Load exercises/migration_manifest.json.

    Args:
        manifest_path: Override path for testing. Defaults to the canonical
            exercises/migration_manifest.json in the repository.

    Returns:
        The parsed migration manifest.

    Raises:
        FileNotFoundError: If the manifest file is missing.
        ValueError: If the manifest has an unexpected schema_version.
    """
    path = manifest_path or _MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Migration manifest not found at {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schema_version") != 1:
        raise ValueError(
            f"Unsupported migration manifest schema_version: {data.get('schema_version')!r}"
        )
    if "exercises" not in data:
        raise ValueError(f"Migration manifest at {path} is missing required 'exercises' key")
    return data  # type: ignore[return-value]


def get_exercise_layout(exercise_key: str, manifest_path: Path | None = None) -> ExerciseLayout:
    """Return the layout state for a given exercise_key.

    Args:
        exercise_key: The unique exercise identifier.
        manifest_path: Override path for testing.

    Returns:
        The ExerciseLayout for the given exercise_key.

    Raises:
        KeyError: If the exercise_key is not in the manifest.
    """
    manifest = load_migration_manifest(manifest_path)
    exercises = manifest["exercises"]
    if exercise_key not in exercises:
        raise KeyError(
            f"exercise_key {exercise_key!r} is not in the migration manifest. "
            f"Known keys: {sorted(exercises)}"
        )
    return ExerciseLayout(exercises[exercise_key]["layout"])
