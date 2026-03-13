"""Tests for ``exercise_runtime_support.exercise_catalogue``."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from exercise_metadata.registry import build_exercise_catalogue
from exercise_runtime_support import exercise_catalogue


def test_get_exercise_catalogue_matches_metadata_catalogue() -> None:
    """The runtime catalogue mirrors the metadata catalogue in the source repo."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    runtime_catalogue = exercise_catalogue.get_exercise_catalogue()
    metadata_catalogue = build_exercise_catalogue()

    assert [asdict(entry) for entry in runtime_catalogue] == metadata_catalogue

    exercise_catalogue.get_exercise_catalogue.cache_clear()


def test_get_exercise_catalogue_prefers_source_metadata_over_snapshot(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Source repos ignore adjacent snapshots and keep live metadata authoritative."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    snapshot_path = tmp_path / exercise_catalogue.CATALOGUE_SNAPSHOT_FILENAME
    snapshot_path.write_text("[]\n", encoding="utf-8")
    expected_catalogue = (
        exercise_catalogue.ExerciseCatalogueEntry(
            exercise_key="ex999_sequence_demo",
            exercise_id=999,
            slug="sequence_demo",
            title="Demo",
            display_label="ex999 Demo",
            construct="sequence",
            exercise_type="modify",
            parts=1,
            layout="flat",
        ),
    )

    def resolve_snapshot_path(_runtime_package_dir: Path | None = None) -> Path:
        return snapshot_path

    def raise_if_snapshot_loaded(_snapshot_path: Path | None = None):
        raise AssertionError(
            "source repositories must not load the runtime snapshot")

    monkeypatch.setattr(
        exercise_catalogue,
        "get_catalogue_snapshot_path",
        resolve_snapshot_path,
    )
    monkeypatch.setattr(
        exercise_catalogue,
        "_has_local_metadata_package",
        lambda _runtime_package_dir=None: True,
    )
    monkeypatch.setattr(
        exercise_catalogue,
        "load_catalogue_snapshot",
        raise_if_snapshot_loaded,
    )
    monkeypatch.setattr(
        exercise_catalogue,
        "_build_metadata_catalogue",
        lambda: expected_catalogue,
    )

    assert exercise_catalogue.get_exercise_catalogue() == expected_catalogue

    exercise_catalogue.get_exercise_catalogue.cache_clear()


def test_get_exercise_catalogue_loads_generated_snapshot_without_metadata_import(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Packaged repositories can load the generated snapshot without metadata."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    snapshot_path = tmp_path / exercise_catalogue.CATALOGUE_SNAPSHOT_FILENAME
    exercise_catalogue.write_catalogue_snapshot(snapshot_path)

    def raise_runtime_error(_module_name: str):
        raise RuntimeError("metadata import should not be attempted")

    def resolve_snapshot_path(_runtime_package_dir: Path | None = None) -> Path:
        return snapshot_path

    monkeypatch.setattr(exercise_catalogue,
                        "import_module", raise_runtime_error)
    monkeypatch.setattr(exercise_catalogue,
                        "get_catalogue_snapshot_path", resolve_snapshot_path)
    monkeypatch.setattr(
        exercise_catalogue,
        "_has_local_metadata_package",
        lambda _runtime_package_dir=None: False,
    )

    catalogue = exercise_catalogue.get_exercise_catalogue()
    metadata_catalogue = build_exercise_catalogue()

    assert [asdict(entry) for entry in catalogue] == metadata_catalogue

    exercise_catalogue.get_exercise_catalogue.cache_clear()
