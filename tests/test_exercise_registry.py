"""Tests for ``exercise_metadata.registry``."""

from __future__ import annotations

from pathlib import Path

import pytest

from exercise_metadata.manifest import ExerciseLayout, get_exercise_layout, load_migration_manifest
from exercise_metadata.registry import (
    build_display_label,
    build_exercise_catalogue,
    build_exercise_registry,
    get_all_exercise_keys,
    get_canonical_exercise_keys,
    get_catalogue_exercise_keys,
)
from tests.exercise_metadata_helpers import make_exercise_json, make_manifest

CANONICAL_KEY = "ex004_sequence_debug_syntax"
CANONICAL_EXERCISE_ID = 4


def _get_manifest_exercises() -> dict[str, dict[str, str]]:
    """Return the live manifest exercises mapping for expectation derivation."""
    return load_migration_manifest()["exercises"]


def _expected_all_keys() -> list[str]:
    """Return all exercise keys from the live manifest."""
    return list(_get_manifest_exercises())


def _expected_canonical_keys() -> list[str]:
    """Return canonical exercise keys from the live manifest."""
    return [
        key
        for key, entry in _get_manifest_exercises().items()
        if entry["layout"] == ExerciseLayout.CANONICAL.value
    ]


def _assert_canonical_before_legacy(
    values: list[str],
    *,
    canonical_values: set[str],
    legacy_values: set[str],
    item_name: str,
) -> None:
    """Assert that no canonical value appears after the first legacy value."""
    seen_legacy = False
    for index, value in enumerate(values):
        if value in legacy_values:
            seen_legacy = True
        elif value in canonical_values and seen_legacy:
            pytest.fail(
                f"Canonical {item_name} {value!r} found at index {index} after a legacy {item_name}"
            )


def test_build_exercise_registry_returns_all_exercises() -> None:
    """``build_exercise_registry()`` returns an entry for every manifest exercise."""
    registry = build_exercise_registry()
    assert {entry["exercise_key"]
            for entry in registry} == set(_expected_all_keys())


def test_canonical_entry_has_correct_layout_and_metadata() -> None:
    """The canonical ex004 entry exposes its metadata."""
    registry = build_exercise_registry()
    canonical = next(
        entry for entry in registry if entry["exercise_key"] == CANONICAL_KEY)
    assert canonical["layout"] == ExerciseLayout.CANONICAL.value
    assert canonical["metadata"] is not None
    assert canonical["metadata"]["exercise_key"] == CANONICAL_KEY
    assert canonical["metadata"]["exercise_id"] == CANONICAL_EXERCISE_ID


def test_live_registry_has_no_legacy_entries_after_sequence_migration() -> None:
    """The live repository no longer exposes legacy entries after the migration."""
    registry = build_exercise_registry()
    legacy = [entry for entry in registry if entry["layout"]
              == ExerciseLayout.LEGACY.value]
    assert legacy == []


def test_canonical_entries_come_before_legacy_entries() -> None:
    """Canonical entries appear before legacy entries in the registry."""
    registry = build_exercise_registry()
    layouts = [entry["layout"] for entry in registry]
    _assert_canonical_before_legacy(
        layouts,
        canonical_values={ExerciseLayout.CANONICAL.value},
        legacy_values={ExerciseLayout.LEGACY.value},
        item_name="entry layout",
    )


def test_get_canonical_exercise_keys_returns_only_canonical() -> None:
    """``get_canonical_exercise_keys()`` returns only canonical exercise keys."""
    assert get_canonical_exercise_keys() == _expected_canonical_keys()


def test_get_all_exercise_keys_returns_all_manifest_keys() -> None:
    """``get_all_exercise_keys()`` returns every exercise key from the manifest."""
    keys = get_all_exercise_keys()
    assert set(keys) == set(_expected_all_keys())
    assert CANONICAL_KEY in keys


def test_get_all_exercise_keys_canonical_first() -> None:
    """Canonical keys appear before legacy keys in ``get_all_exercise_keys()``."""
    keys = get_all_exercise_keys()
    canonical_keys = set(_expected_canonical_keys())
    legacy_keys = {
        key
        for key, entry in _get_manifest_exercises().items()
        if entry["layout"] == ExerciseLayout.LEGACY.value
    }
    _assert_canonical_before_legacy(
        keys,
        canonical_values=canonical_keys,
        legacy_values=legacy_keys,
        item_name="key",
    )


def test_build_exercise_catalogue_orders_by_exercise_id() -> None:
    """The catalogue order follows metadata exercise IDs."""
    catalogue = build_exercise_catalogue()
    assert [entry["exercise_id"] for entry in catalogue] == [2, 3, 4, 5, 6, 7]
    assert [entry["exercise_key"]
            for entry in catalogue] == _expected_all_keys()


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
        assert "layout" in entry
        assert "metadata" in entry


def test_canonical_exercise_with_missing_exercise_json_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """Canonical exercises still fail hard when metadata is missing."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
    )
    empty_root = tmp_path / "exercises"
    empty_root.mkdir()

    with pytest.raises(RuntimeError, match="Failed to load metadata for canonical exercise"):
        build_exercise_registry(
            manifest_path=manifest_path, exercises_root=empty_root)


def test_canonical_exercise_with_mismatched_metadata_key_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """Canonical metadata must match the manifest exercise_key exactly."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
    )
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
        build_exercise_registry(
            manifest_path=manifest_path,
            exercises_root=tmp_path / "exercises",
        )

    message = str(exc_info.value)
    assert "Failed to load metadata for canonical exercise" in message
    assert "has exercise_key 'ex999_sequence_wrong_identity'" in message
    assert "expected 'ex004_sequence_debug_syntax'" in message


def test_canonical_exercise_with_mismatched_construct_raises_runtime_error(
    tmp_path: Path,
) -> None:
    """Canonical metadata construct must match the canonical directory path."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
    )
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
        build_exercise_registry(
            manifest_path=manifest_path,
            exercises_root=tmp_path / "exercises",
        )

    message = str(exc_info.value)
    assert "Failed to load metadata for canonical exercise" in message
    assert "has construct 'selection'" in message
    assert "expected 'sequence'" in message


def test_canonical_exercise_rejects_legacy_only_metadata_location(
    tmp_path: Path,
) -> None:
    """Canonical exercises do not fall back to legacy construct/type metadata paths."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
    )
    legacy_dir = tmp_path / "exercises" / "sequence" / \
        "debug" / "ex004_sequence_debug_syntax"
    make_exercise_json(
        legacy_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex004_sequence_debug_syntax",
            "exercise_id": 4,
            "slug": "ex004_sequence_debug_syntax",
            "title": "Debug Syntax Errors",
            "construct": "sequence",
            "exercise_type": "debug",
            "parts": 10,
        },
    )

    with pytest.raises(RuntimeError) as exc_info:
        build_exercise_registry(
            manifest_path=manifest_path,
            exercises_root=tmp_path / "exercises",
        )

    message = str(exc_info.value)
    assert "Failed to load metadata for canonical exercise" in message
    assert "Canonical exercise directory not found" in message
    assert "must not include an exercise_type segment" in message


def test_unknown_exercise_key_in_manifest_raises_key_error(tmp_path: Path) -> None:
    """``get_exercise_layout()`` raises ``KeyError`` for unknown exercise keys."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex002_sequence_modify_basics": {"layout": "legacy"}},
    )

    with pytest.raises(KeyError, match="ex999_nonexistent"):
        get_exercise_layout("ex999_nonexistent", manifest_path)


def test_build_registry_with_only_legacy_exercises(tmp_path: Path) -> None:
    """``build_exercise_registry()`` still works when all exercises are legacy."""
    exercises = {
        "ex002_sequence_modify_basics": {"layout": "legacy"},
        "ex003_sequence_modify_variables": {"layout": "legacy"},
    }
    manifest_path = make_manifest(tmp_path, exercises)
    exercises_root = tmp_path / "exercises"
    exercises_root.mkdir()
    registry = build_exercise_registry(
        manifest_path=manifest_path, exercises_root=exercises_root)

    assert len(registry) == len(exercises)
    for entry in registry:
        assert entry["layout"] == ExerciseLayout.LEGACY.value
        assert entry["metadata"] is None


def test_build_exercise_catalogue_requires_legacy_metadata(tmp_path: Path) -> None:
    """The stricter catalogue fails when a manifest exercise lacks metadata."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex002_sequence_modify_basics": {"layout": "legacy"}},
    )

    with pytest.raises(RuntimeError, match="requires metadata"):
        build_exercise_catalogue(
            manifest_path=manifest_path, exercises_root=tmp_path / "exercises")


def test_build_exercise_catalogue_loads_legacy_metadata_from_canonical_directory(
    tmp_path: Path,
) -> None:
    """Legacy exercises still load metadata when it exists in the canonical home."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex002_sequence_modify_basics": {"layout": "legacy"}},
    )
    exercise_dir = tmp_path / "exercises" / \
        "sequence" / "ex002_sequence_modify_basics"
    make_exercise_json(
        exercise_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex002_sequence_modify_basics",
            "exercise_id": 2,
            "slug": "ex002_sequence_modify_basics",
            "title": "Sequence Modify Basics",
            "construct": "sequence",
            "exercise_type": "modify",
            "parts": 10,
        },
    )

    catalogue = build_exercise_catalogue(
        manifest_path=manifest_path, exercises_root=tmp_path / "exercises")

    assert catalogue == [
        {
            "exercise_key": "ex002_sequence_modify_basics",
            "exercise_id": 2,
            "slug": "ex002_sequence_modify_basics",
            "title": "Sequence Modify Basics",
            "display_label": "ex002 Sequence Modify Basics",
            "construct": "sequence",
            "exercise_type": "modify",
            "parts": 10,
            "layout": "legacy",
        }
    ]


def test_build_exercise_catalogue_rejects_duplicate_exercise_ids(tmp_path: Path) -> None:
    """The metadata-backed catalogue fails fast when exercise_id values collide."""
    manifest_path = make_manifest(
        tmp_path,
        {
            "ex101_sequence_first": {"layout": "canonical"},
            "ex102_sequence_second": {"layout": "canonical"},
        },
    )
    exercises_root = tmp_path / "exercises"

    for exercise_key, title in (
        ("ex101_sequence_first", "First Exercise"),
        ("ex102_sequence_second", "Second Exercise"),
    ):
        make_exercise_json(
            exercises_root / "sequence" / exercise_key,
            {
                "schema_version": 1,
                "exercise_key": exercise_key,
                "exercise_id": 101,
                "slug": exercise_key,
                "title": title,
                "construct": "sequence",
                "exercise_type": "modify",
                "parts": 1,
            },
        )

    with pytest.raises(RuntimeError, match="requires unique exercise_id values"):
        build_exercise_catalogue(
            manifest_path=manifest_path,
            exercises_root=exercises_root,
        )

def test_build_registry_ignores_non_canonical_metadata_location_for_legacy_exercise(
    tmp_path: Path,
) -> None:
    """Legacy metadata outside the canonical home is ignored by the registry."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex002_sequence_modify_basics": {"layout": "legacy"}},
    )
    legacy_dir = tmp_path / "exercises" / "sequence" / \
        "modify" / "ex002_sequence_modify_basics"
    make_exercise_json(
        legacy_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex002_sequence_modify_basics",
            "exercise_id": 2,
            "slug": "ex002_sequence_modify_basics",
            "title": "Sequence Modify Basics",
            "construct": "sequence",
            "exercise_type": "modify",
            "parts": 10,
        },
    )

    registry = build_exercise_registry(
        manifest_path=manifest_path,
        exercises_root=tmp_path / "exercises",
    )

    assert registry == [
        {
            "exercise_key": "ex002_sequence_modify_basics",
            "layout": "legacy",
            "metadata": None,
        }
    ]


def test_build_exercise_catalogue_rejects_non_canonical_metadata_location(
    tmp_path: Path,
) -> None:
    """The catalogue does not accept metadata discovered from legacy layout paths."""
    manifest_path = make_manifest(
        tmp_path,
        {"ex002_sequence_modify_basics": {"layout": "legacy"}},
    )
    legacy_dir = tmp_path / "exercises" / "sequence" / \
        "modify" / "ex002_sequence_modify_basics"
    make_exercise_json(
        legacy_dir,
        {
            "schema_version": 1,
            "exercise_key": "ex002_sequence_modify_basics",
            "exercise_id": 2,
            "slug": "ex002_sequence_modify_basics",
            "title": "Sequence Modify Basics",
            "construct": "sequence",
            "exercise_type": "modify",
            "parts": 10,
        },
    )

    with pytest.raises(RuntimeError, match="requires metadata"):
        build_exercise_catalogue(
            manifest_path=manifest_path,
            exercises_root=tmp_path / "exercises",
        )


def test_registry_entry_keys_are_strings() -> None:
    """All registry key fields are strings."""
    registry = build_exercise_registry()
    for entry in registry:
        assert isinstance(entry["exercise_key"], str)
        assert isinstance(entry["layout"], str)
