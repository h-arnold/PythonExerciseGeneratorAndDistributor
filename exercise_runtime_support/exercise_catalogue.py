"""Shared exercise catalogue for runtime support modules.

The source repository loads this directly from
``exercise_metadata.registry.build_exercise_catalogue()``. Packaged Classroom
exports remain metadata-free, so this module falls back to a generated runtime
snapshot stored alongside the package.
"""

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExerciseCatalogueEntry:
    """Runtime-friendly view of an exercise catalogue entry."""

    exercise_key: str
    exercise_id: int
    slug: str
    title: str
    display_label: str
    construct: str
    exercise_type: str
    parts: int
    layout: str


CATALOGUE_SNAPSHOT_FILENAME = "exercise_catalogue_snapshot.json"


def _to_runtime_entry(entry: Any) -> ExerciseCatalogueEntry:
    """Normalise metadata catalogue output into the runtime dataclass."""
    return ExerciseCatalogueEntry(
        exercise_key=entry["exercise_key"],
        exercise_id=entry["exercise_id"],
        slug=entry["slug"],
        title=entry["title"],
        display_label=entry["display_label"],
        construct=entry["construct"],
        exercise_type=entry["exercise_type"],
        parts=entry["parts"],
        layout=entry["layout"],
    )


def get_catalogue_snapshot_path(runtime_package_dir: Path | None = None) -> Path:
    """Return the path for the generated runtime catalogue snapshot."""
    package_dir = Path(__file__).resolve(
    ).parent if runtime_package_dir is None else runtime_package_dir
    return package_dir / CATALOGUE_SNAPSHOT_FILENAME


def _has_local_metadata_package(runtime_package_dir: Path | None = None) -> bool:
    """Return whether the runtime package lives beside source metadata."""
    package_dir = Path(__file__).resolve(
    ).parent if runtime_package_dir is None else runtime_package_dir
    metadata_init = package_dir.parent / "exercise_metadata" / "__init__.py"
    return metadata_init.exists()


def _build_metadata_catalogue() -> tuple[ExerciseCatalogueEntry, ...]:
    """Load the runtime catalogue from source-repository metadata."""
    registry = import_module("exercise_metadata.registry")
    build_catalogue = registry.build_exercise_catalogue
    return tuple(_to_runtime_entry(entry) for entry in build_catalogue())


def load_catalogue_snapshot(snapshot_path: Path | None = None) -> tuple[ExerciseCatalogueEntry, ...]:
    """Load the runtime catalogue snapshot used in packaged exports."""
    target_path = get_catalogue_snapshot_path(
    ) if snapshot_path is None else snapshot_path
    snapshot_entries = json.loads(target_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot_entries, list):
        raise ValueError(
            f"Runtime catalogue snapshot at {target_path} must contain a list")
    return tuple(_to_runtime_entry(entry) for entry in snapshot_entries)


def write_catalogue_snapshot(
    snapshot_path: Path | None = None,
    *,
    exercise_keys: Collection[str] | None = None,
) -> Path:
    """Write a runtime catalogue snapshot for metadata-free packaged exports."""
    target_path = get_catalogue_snapshot_path(
    ) if snapshot_path is None else snapshot_path
    selected_exercise_keys = None if exercise_keys is None else set(
        exercise_keys)
    snapshot_entries = [
        asdict(entry)
        for entry in _build_metadata_catalogue()
        if selected_exercise_keys is None or entry.exercise_key in selected_exercise_keys
    ]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(snapshot_entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target_path


@lru_cache(maxsize=1)
def get_exercise_catalogue() -> tuple[ExerciseCatalogueEntry, ...]:
    """Return the shared exercise catalogue."""
    snapshot_path = get_catalogue_snapshot_path()
    if _has_local_metadata_package(snapshot_path.parent):
        return _build_metadata_catalogue()

    if snapshot_path.exists():
        return load_catalogue_snapshot(snapshot_path)

    raise FileNotFoundError(
        "Runtime catalogue snapshot is missing and no local exercise metadata "
        f"package was found beside {snapshot_path.parent}"
    )


def get_catalogue_entry(exercise_key: str) -> ExerciseCatalogueEntry:
    """Return a single catalogue entry by exercise key."""
    for entry in get_exercise_catalogue():
        if entry.exercise_key == exercise_key:
            return entry
    available = ", ".join(
        item.exercise_key for item in get_exercise_catalogue())
    raise ValueError(
        f"Unknown notebook '{exercise_key}'. Available: {available}")


def get_catalogue_key_for_exercise_id(exercise_id: int) -> str:
    """Return the exercise key for a numeric exercise identifier."""
    for entry in get_exercise_catalogue():
        if entry.exercise_id == exercise_id:
            return entry.exercise_key
    raise ValueError(f"Unknown exercise_id {exercise_id!r}")
