"""Tests for ``exercise_metadata.registry``."""

from __future__ import annotations

from pathlib import Path

import pytest

from exercise_metadata.registry import (
    build_display_label,
    build_exercise_catalogue,
    build_exercise_registry,
    get_all_exercise_keys,
    get_canonical_exercise_keys,
    get_catalogue_exercise_keys,
)
from tests.exercise_metadata_helpers import make_exercise_json

CANONICAL_KEY = "ex004_sequence_debug_syntax"
CANONICAL_EXERCISE_ID = 4


def _expected_all_keys() -> list[str]:
    """Return all exercise keys from the filesystem."""
    exercises_root = Path(__file__).resolve().parents[1] / "exercises"
    return sorted(p.parent.name for p in exercises_root.rglob("exercise.json"))


def test_build_exercise_registry_returns_all_exercises() -> None:
    """``build_exercise_registry()`` returns an entry for every filesystem-discovered exercise."""
    registry = build_exercise_registry()
    assert {entry["exercise_key"]
            for entry in registry} == set(_expected_all_keys())


def test_canonical_entry_has_correct_metadata() -> None:
    """The canonical ex004 entry exposes its metadata."""
    registry = build_exercise_registry()
    canonical = next(
        entry for entry in registry if entry["exercise_key"] == CANONICAL_KEY)
    assert canonical["metadata"] is not None
    assert canonical["metadata"]["exercise_key"] == CANONICAL_KEY
    assert canonical["metadata"]["exercise_id"] == CANONICAL_EXERCISE_ID


def test_get_canonical_exercise_keys_returns_all_keys() -> None:
    """``get_canonical_exercise_keys()`` returns all exercise keys (no legacy distinction)."""
    assert get_canonical_exercise_keys() == get_all_exercise_keys()


def test_get_all_exercise_keys_returns_all_keys_from_filesystem() -> None:
    """``get_all_exercise_keys()`` returns every exercise key from the filesystem."""
    keys = get_all_exercise_keys()
    assert set(keys) == set(_expected_all_keys())
    assert CANONICAL_KEY in keys


def test_build_exercise_catalogue_orders_by_exercise_id() -> None:
    """The catalogue order follows metadata exercise IDs."""
    catalogue = build_exercise_catalogue()
    expected_keys = _expected_all_keys()
    expected_ids = [
        int(key.split("_")[0].removeprefix("ex"))
        for key in expected_keys
    ]
    assert [entry["exercise_id"]
            for entry in catalogue] == expected_ids
    assert [entry["exercise_key"]
            for entry in catalogue] == expected_keys


def test_build_exercise_catalogue_exposes_metadata_derived_labels() -> None:
    """Display labels come from metadata-derived titles and IDs."""
    catalogue = build_exercise_catalogue()
    ex004 = next(
        entry for entry in catalogue if entry["exercise_key"] == CANONICAL_KEY)
    assert ex004["title"] == "Debug Syntax Errors"
    assert ex004["display_label"] == build_display_label(
        4, "Debug Syntax Errors")


def test_get_catalogue_exercise_keys_returns_metadata_order() -> None:
    """``get_catalogue_exercise_keys()`` returns the full metadata-backed order."""
    assert get_catalogue_exercise_keys() == _expected_all_keys()


def test_registry_entries_are_typed_dicts() -> None:
    """Each registry entry has the expected TypedDict keys."""
    registry = build_exercise_registry()
    for entry in registry:
        assert "exercise_key" in entry
        assert "metadata" in entry


def test_canonical_exercise_with_mismatched_metadata_key_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """Canonical metadata must match the filesystem exercise_key exactly."""
    exercise_dir = tmp_path / "exercises" / \
        "sequence" / "ex004_sequence_debug_syntax"
    make_exercise_json(
        exercise_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex999_sequence_wrong_identity",
            "exercise_id": 4,
            "slug": "ex004_sequence_debug_syntax",
            "title": "Debug Syntax Errors",
            "construct": "sequence",
            "exercise_type": "debug",
            "parts": 10,
        },
    )

    with pytest.raises(RuntimeError) as exc_info:
        build_exercise_registry(exercises_root=tmp_path / "exercises")

    message = str(exc_info.value)
    assert "Failed to load metadata for exercise" in message
    assert "has exercise_key 'ex999_sequence_wrong_identity'" in message
    assert "expected 'ex004_sequence_debug_syntax'" in message


def test_canonical_exercise_with_mismatched_construct_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """Canonical metadata construct must match the canonical directory path."""
    exercise_dir = tmp_path / "exercises" / \
        "sequence" / "ex004_sequence_debug_syntax"
    make_exercise_json(
        exercise_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex004_sequence_debug_syntax",
            "exercise_id": 4,
            "slug": "ex004_sequence_debug_syntax",
            "title": "Debug Syntax Errors",
            "construct": "selection",
            "exercise_type": "debug",
            "parts": 10,
        },
    )

    with pytest.raises(RuntimeError) as exc_info:
        build_exercise_registry(exercises_root=tmp_path / "exercises")

    message = str(exc_info.value)
    assert "Failed to load metadata for exercise" in message
    assert "has construct 'selection'" in message
    assert "expected 'sequence'" in message


def test_build_exercise_catalogue_rejects_duplicate_exercise_ids(tmp_path: Path) -> None:
    """The metadata-backed catalogue fails fast when exercise_id values collide."""
    exercises_root = tmp_path / "exercises"

    for exercise_key in ("ex101_sequence_first", "ex102_sequence_second"):
        make_exercise_json(
            exercises_root / "sequence" / exercise_key,
            {
                "schema_version": 1,
                "exercise_key": exercise_key,
                "exercise_id": 101,
                "slug": exercise_key,
                "title": exercise_key.replace("_", " ").title(),
                "construct": "sequence",
                "exercise_type": "modify",
                "parts": 1,
            },
        )

    with pytest.raises(RuntimeError, match="requires unique exercise_id values"):
        build_exercise_catalogue(exercises_root=exercises_root)


def test_registry_entry_keys_are_strings() -> None:
    """All registry key fields are strings."""
    registry = build_exercise_registry()
    for entry in registry:
        assert isinstance(entry["exercise_key"], str)
        assert isinstance(entry["metadata"], dict)
        assert isinstance(entry["metadata"]["exercise_key"], str)
