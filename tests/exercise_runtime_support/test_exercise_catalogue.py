"""Tests for ``exercise_runtime_support.exercise_catalogue``."""

from __future__ import annotations

from exercise_metadata.registry import build_exercise_catalogue
from exercise_runtime_support import exercise_catalogue


def test_get_exercise_catalogue_matches_metadata_catalogue() -> None:
    """The runtime catalogue mirrors the metadata catalogue in the source repo."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    runtime_catalogue = exercise_catalogue.get_exercise_catalogue()
    metadata_catalogue = build_exercise_catalogue()

    assert [entry.exercise_key for entry in runtime_catalogue] == [
        entry["exercise_key"] for entry in metadata_catalogue
    ]
    assert [entry.display_label for entry in runtime_catalogue] == [
        entry["display_label"] for entry in metadata_catalogue
    ]


def test_get_exercise_catalogue_falls_back_without_metadata_import(
    monkeypatch,
) -> None:
    """Packaged repositories can still use the shared catalogue without metadata."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    def raise_import_error(_module_name: str):
        raise ImportError("metadata unavailable")

    monkeypatch.setattr(exercise_catalogue,
                        "import_module", raise_import_error)

    catalogue = exercise_catalogue.get_exercise_catalogue()
    exercise_keys = [entry.exercise_key for entry in catalogue]

    assert catalogue[0].exercise_key == "ex002_sequence_modify_basics"
    assert catalogue[-1].exercise_key == "ex007_sequence_debug_casting"
    assert catalogue[2].display_label == "ex004 Debug Syntax Errors"
    assert "ex001_sanity" not in exercise_keys

    exercise_catalogue.get_exercise_catalogue.cache_clear()
