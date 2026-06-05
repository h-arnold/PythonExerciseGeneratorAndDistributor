"""Shared test helpers for exercise_metadata tests.

Provides utilities for writing exercise.json files in isolated tmp_path fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def make_exercise_json(directory: Path, data: dict[str, Any]) -> Path:
    """Write exercise.json into directory and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "exercise.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
