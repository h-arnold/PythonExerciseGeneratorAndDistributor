"""Shared helpers for the template packager package."""

from __future__ import annotations

import json
from pathlib import Path


def load_exercise_metadata(repo_root: Path, exercise_key: str) -> dict[str, object]:
    """Load exercise metadata by globbing for exercise.json.

    Args:
        repo_root: Root directory of the repository.
        exercise_key: The exercise key.

    Returns:
        Parsed exercise.json contents as a dict.

    Raises:
        ValueError: If the exercise metadata cannot be found or parsed.
    """
    try:
        exercise_metadata_path = next(
            (repo_root / "exercises").glob(f"*/{exercise_key}/exercise.json")
        )
        return json.loads(exercise_metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, StopIteration, json.JSONDecodeError) as cause:
        raise ValueError(
            f"Failed to load metadata for exercise '{exercise_key}': {cause}"
        ) from cause
