"""Central exercise.json loader.

Loads exercise metadata from the canonical exercises/ tree.
Accepts an exercise directory ``Path`` as input; the exercise_key-to-path
resolution is handled upstream by ``resolver.resolve_exercise_dir()``.
"""

from __future__ import annotations

import json
from pathlib import Path

from exercise_metadata.schema import REQUIRED_FIELDS, SCHEMA_VERSION, ExerciseMetadata


def load_exercise_metadata(exercise_dir: Path) -> ExerciseMetadata:
    """Load and validate exercise.json from an exercise directory.

    Args:
        exercise_dir: Path to the exercise directory containing exercise.json.

    Returns:
        Validated ExerciseMetadata dict.

    Raises:
        FileNotFoundError: If exercise.json is missing.
        ValueError: If required fields are missing or schema_version is wrong.
    """
    json_path = exercise_dir / "exercise.json"
    if not json_path.exists():
        raise FileNotFoundError(f"exercise.json not found at {json_path}")

    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"exercise.json at {json_path} is missing required fields: {missing}")

    if data["schema_version"] != SCHEMA_VERSION:
        raise ValueError(
            f"exercise.json at {json_path} has unsupported schema_version "
            f"{data['schema_version']!r}; expected {SCHEMA_VERSION}"
        )

    return ExerciseMetadata(**{k: data[k] for k in REQUIRED_FIELDS})  # type: ignore[misc]
