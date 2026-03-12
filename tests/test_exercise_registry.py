"""Tests for exercise_metadata.registry module."""
from __future__ import annotations

from pathlib import Path

import pytest

from exercise_metadata.manifest import ExerciseLayout, get_exercise_layout
from exercise_metadata.registry import (
    build_exercise_registry,
    get_all_exercise_keys,
    get_canonical_exercise_keys,
)
from tests.exercise_metadata_helpers import make_manifest

# ---------------------------------------------------------------------------
# Happy-path tests using the real manifest
# ---------------------------------------------------------------------------

TOTAL_EXERCISE_COUNT = 7
CANONICAL_KEY = "ex004_sequence_debug_syntax"
CANONICAL_EXERCISE_ID = 4


def test_build_exercise_registry_returns_all_exercises() -> None:
    """build_exercise_registry() returns an entry for every exercise in the manifest."""
    registry = build_exercise_registry()
    assert len(registry) == TOTAL_EXERCISE_COUNT


def test_canonical_entry_has_correct_layout_and_metadata() -> None:
    """The ex004 canonical entry has layout='canonical' and non-None metadata."""
    registry = build_exercise_registry()
    canonical = next(e for e in registry if e["exercise_key"] == CANONICAL_KEY)
    assert canonical["layout"] == ExerciseLayout.CANONICAL.value
    assert canonical["metadata"] is not None
    assert canonical["metadata"]["exercise_key"] == CANONICAL_KEY
    assert canonical["metadata"]["exercise_id"] == CANONICAL_EXERCISE_ID


def test_legacy_entries_have_none_metadata() -> None:
    """All legacy entries have metadata=None."""
    registry = build_exercise_registry()
    legacy = [e for e in registry if e["layout"] == ExerciseLayout.LEGACY.value]
    assert len(legacy) == TOTAL_EXERCISE_COUNT - 1
    for entry in legacy:
        assert entry["metadata"] is None, f"Expected metadata=None for legacy {entry['exercise_key']!r}"


def test_canonical_entries_come_before_legacy_entries() -> None:
    """Canonical entries appear before legacy entries in the registry."""
    registry = build_exercise_registry()
    layouts = [e["layout"] for e in registry]
    # Find last canonical and first legacy
    last_canonical_idx = max(
        i for i, layout in enumerate(layouts) if layout == ExerciseLayout.CANONICAL.value
    )
    first_legacy_idx = min(
        i for i, layout in enumerate(layouts) if layout == ExerciseLayout.LEGACY.value
    )
    assert last_canonical_idx < first_legacy_idx


def test_get_canonical_exercise_keys_returns_only_canonical() -> None:
    """get_canonical_exercise_keys() returns only canonical exercise keys."""
    keys = get_canonical_exercise_keys()
    assert keys == [CANONICAL_KEY]


def test_get_all_exercise_keys_returns_all_seven() -> None:
    """get_all_exercise_keys() returns all 7 exercise keys."""
    keys = get_all_exercise_keys()
    assert len(keys) == TOTAL_EXERCISE_COUNT
    assert CANONICAL_KEY in keys


def test_get_all_exercise_keys_canonical_first() -> None:
    """Canonical keys appear before legacy keys in get_all_exercise_keys()."""
    keys = get_all_exercise_keys()
    canonical_idx = keys.index(CANONICAL_KEY)
    # All other keys are legacy, so canonical key must appear before all of them
    for key in keys:
        if key != CANONICAL_KEY:
            assert canonical_idx < keys.index(key)


def test_registry_entries_are_typed_dicts() -> None:
    """Each registry entry has the expected TypedDict keys."""
    registry = build_exercise_registry()
    for entry in registry:
        assert "exercise_key" in entry
        assert "layout" in entry
        assert "metadata" in entry


# ---------------------------------------------------------------------------
# Error-case tests using tmp_path fixtures
# ---------------------------------------------------------------------------


def test_canonical_exercise_with_missing_exercise_json_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """build_exercise_registry() raises RuntimeError if a canonical exercise has no exercise.json."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
    )
    # Provide an exercises_root with no ex004 directory at all
    empty_root = tmp_path / "exercises"
    empty_root.mkdir()

    with pytest.raises(RuntimeError, match="Failed to load metadata for canonical exercise"):
        build_exercise_registry(manifest_path=manifest_path, exercises_root=empty_root)


def test_unknown_exercise_key_in_manifest_raises_key_error(tmp_path: Path) -> None:
    """get_exercise_layout() raises KeyError for an exercise_key absent from the manifest."""
    manifest_path = make_manifest(tmp_path, {"ex001_sanity": {"layout": "legacy"}})

    with pytest.raises(KeyError, match="ex999_nonexistent"):
        get_exercise_layout("ex999_nonexistent", manifest_path)


def test_build_registry_with_only_legacy_exercises(tmp_path: Path) -> None:
    """build_exercise_registry() works correctly when all exercises are legacy."""
    exercises = {
        "ex001_sanity": {"layout": "legacy"},
        "ex002_sequence_modify_basics": {"layout": "legacy"},
    }
    manifest_path = make_manifest(tmp_path, exercises)
    expected_count = len(exercises)

    registry = build_exercise_registry(manifest_path=manifest_path)
    assert len(registry) == expected_count
    for entry in registry:
        assert entry["layout"] == ExerciseLayout.LEGACY.value
        assert entry["metadata"] is None


def test_registry_entry_keys_are_strings() -> None:
    """All exercise_key values in the registry are strings."""
    registry = build_exercise_registry()
    for entry in registry:
        assert isinstance(entry["exercise_key"], str)
        assert isinstance(entry["layout"], str)

