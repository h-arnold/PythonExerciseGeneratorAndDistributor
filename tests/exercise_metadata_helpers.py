"""Shared test helpers for exercise_metadata tests.

Provides utilities for writing temporary migration manifests and exercise.json
files in isolated tmp_path fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def make_manifest(tmp_path: Path, exercises: dict[str, Any], schema_version: int = 1) -> Path:
    """Write a minimal migration_manifest.json to tmp_path and return its path."""
    manifest: dict[str, Any] = {"schema_version": schema_version, "exercises": exercises}
    path = tmp_path / "migration_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def make_exercise_json(directory: Path, data: dict[str, Any]) -> Path:
    """Write exercise.json into directory and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "exercise.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
