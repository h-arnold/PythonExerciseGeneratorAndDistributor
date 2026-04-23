"""Tests for ``exercise_runtime_support.exercise_catalogue``."""

from __future__ import annotations

from dataclasses import asdict

import pytest

import exercise_metadata.registry as metadata_registry
from exercise_runtime_support import exercise_catalogue


def test_get_exercise_catalogue_matches_metadata_catalogue() -> None:
    """The runtime catalogue mirrors the metadata catalogue in the source repo."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    runtime_catalogue = exercise_catalogue.get_exercise_catalogue()
    metadata_catalogue = metadata_registry.build_exercise_catalogue()

    assert [asdict(entry) for entry in runtime_catalogue] == metadata_catalogue

    exercise_catalogue.get_exercise_catalogue.cache_clear()


def test_get_exercise_catalogue_unknown_key_and_id_fail_fast() -> None:
    """Unknown catalogue lookups keep the documented ValueError contract."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    unknown_key_message = "Unknown exercise key"
    unknown_id_message = "Unknown exercise_id"

    with pytest.raises(ValueError, match=unknown_key_message):
        exercise_catalogue.get_catalogue_entry("ex999_missing")

    with pytest.raises(ValueError, match=unknown_id_message):
        exercise_catalogue.get_catalogue_key_for_exercise_id(999_999)

    exercise_catalogue.get_exercise_catalogue.cache_clear()


def test_get_exercise_catalogue_uses_metadata_registry_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runtime catalogue is always built directly from metadata registry data."""
    exercise_catalogue.get_exercise_catalogue.cache_clear()

    expected_catalogue = [
        {
            "exercise_key": "ex321_sequence_demo",
            "exercise_id": 321,
            "slug": "sequence_demo",
            "title": "Demo",
            "display_label": "ex321 Demo",
            "construct": "sequence",
            "exercise_type": "modify",
            "parts": 1,
            "layout": "canonical",
        },
    ]
    monkeypatch.setattr(
        metadata_registry,
        "build_exercise_catalogue",
        lambda: expected_catalogue,
    )

    runtime_catalogue = exercise_catalogue.get_exercise_catalogue()
    assert [asdict(entry) for entry in runtime_catalogue] == expected_catalogue

    exercise_catalogue.get_exercise_catalogue.cache_clear()
