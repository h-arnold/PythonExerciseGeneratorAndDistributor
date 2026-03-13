"""Tests for the exercise_metadata package - Phase 2.

Covers resolver, loader, and manifest functionality.  All error-case tests use
isolated tmp_path fixtures so they do not depend on the live filesystem.

Contract under test:
- exercise_key is the ONLY supported resolver input.
- PYTUTOR_NOTEBOOKS_DIR is NOT used anywhere in these tests.
- Path-based inputs are rejected with TypeError.
- Legacy exercises cause resolve_notebook_path to fail hard.
- Missing canonical notebook files cause resolve_notebook_path to fail hard.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from exercise_metadata import (
    ExerciseLayout,
    load_exercise_metadata,
    load_migration_manifest,
    resolve_exercise_dir,
    resolve_notebook_path,
)
from exercise_metadata.manifest import get_exercise_layout
from tests.exercise_metadata_helpers import make_exercise_json, make_manifest

# ---------------------------------------------------------------------------
# Resolver tests - resolve_exercise_dir
# ---------------------------------------------------------------------------


class TestResolveExerciseDir:
    """Tests for resolve_exercise_dir()."""

    def test_returns_correct_path_for_pilot_exercise(self) -> None:
        """resolve_exercise_dir finds the live ex004 directory."""
        result = resolve_exercise_dir("ex004_sequence_debug_syntax")
        assert result.is_dir()
        assert result == Path("exercises/sequence/ex004_sequence_debug_syntax").resolve()

    def test_raises_type_error_for_path_input(self) -> None:
        """Passing a Path instead of str must raise TypeError immediately."""
        with pytest.raises(TypeError, match="exercise_key must be a str"):
            resolve_exercise_dir(Path("ex004_sequence_debug_syntax"))  # type: ignore[arg-type]

    def test_raises_lookup_error_for_nonexistent_exercise(self, tmp_path: Path) -> None:
        """A nonexistent exercise_key raises LookupError."""
        with pytest.raises(LookupError, match="Canonical exercise directory not found"):
            resolve_exercise_dir("ex999_sequence_nonexistent", exercises_root=tmp_path)

    def test_uses_exercises_root_override(self, tmp_path: Path) -> None:
        """exercises_root override is respected for canonical path derivation."""
        exercise_dir = tmp_path / "sequence" / "ex999_sequence_fake_exercise"
        exercise_dir.mkdir(parents=True)
        result = resolve_exercise_dir("ex999_sequence_fake_exercise", exercises_root=tmp_path)
        assert result == exercise_dir

    def test_rejects_legacy_type_segment_path_for_canonical_resolution(
        self, tmp_path: Path
    ) -> None:
        """Legacy construct/type paths are not accepted as canonical matches."""
        legacy_dir = tmp_path / "sequence" / "debug" / "ex004_sequence_debug_syntax"
        legacy_dir.mkdir(parents=True)

        with pytest.raises(LookupError, match="must not include an exercise_type segment"):
            resolve_exercise_dir("ex004_sequence_debug_syntax", exercises_root=tmp_path)


# ---------------------------------------------------------------------------
# Resolver tests - resolve_notebook_path
# ---------------------------------------------------------------------------


class TestResolveNotebookPath:
    """Tests for resolve_notebook_path()."""

    def test_student_notebook_exists_for_pilot(self) -> None:
        """resolve_notebook_path returns an existing student.ipynb for ex004."""
        result = resolve_notebook_path("ex004_sequence_debug_syntax", "student")
        assert result.exists()
        assert result.name == "student.ipynb"

    def test_solution_notebook_exists_for_pilot(self) -> None:
        """resolve_notebook_path returns an existing solution.ipynb for ex004."""
        result = resolve_notebook_path("ex004_sequence_debug_syntax", "solution")
        assert result.exists()
        assert result.name == "solution.ipynb"

    def test_raises_type_error_for_path_input(self) -> None:
        """Passing a Path instead of str must raise TypeError immediately."""
        with pytest.raises(TypeError, match="exercise_key must be a str"):
            resolve_notebook_path(Path("ex004_sequence_debug_syntax"), "student")  # type: ignore[arg-type]

    def test_raises_lookup_error_for_legacy_exercise(self, tmp_path: Path) -> None:
        """Legacy exercises must cause resolve_notebook_path to fail hard."""
        manifest_path = make_manifest(
            tmp_path,
            {"ex001_sanity": {"layout": "legacy"}},
        )
        with pytest.raises(LookupError, match="layout='legacy'"):
            resolve_notebook_path("ex001_sanity", "student", manifest_path=manifest_path)

    def test_raises_lookup_error_for_unknown_manifest_key(self, tmp_path: Path) -> None:
        """Unknown exercise keys are reported as LookupError by resolve_notebook_path."""
        manifest_path = make_manifest(tmp_path, {"ex001_sanity": {"layout": "legacy"}})

        with pytest.raises(LookupError, match="not in the migration manifest"):
            resolve_notebook_path("ex999_nonexistent", "student", manifest_path=manifest_path)

    def test_raises_value_error_for_invalid_variant(self) -> None:
        """An invalid variant string raises ValueError."""
        with pytest.raises(ValueError, match="variant must be 'student' or 'solution'"):
            resolve_notebook_path("ex004_sequence_debug_syntax", "invalid")  # type: ignore[arg-type]

    def test_raises_lookup_error_when_notebook_missing_for_canonical(self, tmp_path: Path) -> None:
        """Canonical exercise with missing notebook files raises LookupError."""
        # Create the canonical exercise directory but NOT the notebooks sub-directory.
        exercise_dir = tmp_path / "sequence" / "ex004_sequence_debug_syntax"
        exercise_dir.mkdir(parents=True)

        manifest_path = make_manifest(
            tmp_path,
            {"ex004_sequence_debug_syntax": {"layout": "canonical"}},
        )

        with pytest.raises(LookupError, match="expected notebook is missing"):
            resolve_notebook_path(
                "ex004_sequence_debug_syntax",
                "student",
                exercises_root=tmp_path,
                manifest_path=manifest_path,
            )


# ---------------------------------------------------------------------------
# Loader tests - load_exercise_metadata
# ---------------------------------------------------------------------------


class TestLoadExerciseMetadata:
    """Tests for load_exercise_metadata()."""

    _VALID_DATA: ClassVar[dict[str, int | str]] = {
        "schema_version": 1,
        "exercise_key": "ex004_sequence_debug_syntax",
        "exercise_id": 4,
        "slug": "ex004_sequence_debug_syntax",
        "title": "Debug Syntax Errors",
        "construct": "sequence",
        "exercise_type": "debug",
        "parts": 10,
    }

    def test_loads_valid_exercise_json(self, tmp_path: Path) -> None:
        """load_exercise_metadata returns correct ExerciseMetadata for valid JSON."""
        make_exercise_json(tmp_path, self._VALID_DATA)
        meta = load_exercise_metadata(tmp_path)
        assert meta["exercise_key"] == "ex004_sequence_debug_syntax"
        assert meta["exercise_id"] == 4  # noqa: PLR2004
        assert meta["schema_version"] == 1
        assert meta["parts"] == 10  # noqa: PLR2004

    def test_loads_live_pilot_exercise_json(self) -> None:
        """load_exercise_metadata successfully loads the live ex004 exercise.json."""
        exercise_dir = resolve_exercise_dir("ex004_sequence_debug_syntax")
        meta = load_exercise_metadata(exercise_dir)
        assert meta["exercise_key"] == "ex004_sequence_debug_syntax"
        assert meta["construct"] == "sequence"
        assert meta["exercise_type"] == "debug"

    def test_raises_file_not_found_when_json_missing(self, tmp_path: Path) -> None:
        """Missing exercise.json raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match=r"exercise\.json not found"):
            load_exercise_metadata(tmp_path)

    def test_raises_value_error_for_missing_required_field(self, tmp_path: Path) -> None:
        """exercise.json missing a required field raises ValueError."""
        incomplete = {k: v for k, v in self._VALID_DATA.items() if k != "parts"}
        make_exercise_json(tmp_path, incomplete)
        with pytest.raises(ValueError, match="missing required fields"):
            load_exercise_metadata(tmp_path)

    def test_raises_value_error_for_wrong_schema_version(self, tmp_path: Path) -> None:
        """exercise.json with wrong schema_version raises ValueError."""
        bad_version = {**self._VALID_DATA, "schema_version": 99}
        make_exercise_json(tmp_path, bad_version)
        with pytest.raises(ValueError, match="unsupported schema_version"):
            load_exercise_metadata(tmp_path)


# ---------------------------------------------------------------------------
# Manifest tests - load_migration_manifest and get_exercise_layout
# ---------------------------------------------------------------------------


class TestLoadMigrationManifest:
    """Tests for load_migration_manifest()."""

    def test_loads_real_manifest_successfully(self) -> None:
        """load_migration_manifest() loads the live manifest without error."""
        manifest = load_migration_manifest()
        assert manifest["schema_version"] == 1
        assert "exercises" in manifest
        assert "ex004_sequence_debug_syntax" in manifest["exercises"]

    def test_raises_file_not_found_for_missing_manifest(self, tmp_path: Path) -> None:
        """Missing manifest file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Migration manifest not found"):
            load_migration_manifest(tmp_path / "does_not_exist.json")

    def test_raises_value_error_for_wrong_schema_version(self, tmp_path: Path) -> None:
        """Manifest with wrong schema_version raises ValueError."""
        path = make_manifest(tmp_path, exercises={}, schema_version=42)
        with pytest.raises(ValueError, match="Unsupported migration manifest schema_version"):
            load_migration_manifest(path)


class TestGetExerciseLayout:
    """Tests for get_exercise_layout()."""

    def test_returns_canonical_for_ex004(self) -> None:
        """ex004_sequence_debug_syntax is marked canonical in the live manifest."""
        layout = get_exercise_layout("ex004_sequence_debug_syntax")
        assert layout == ExerciseLayout.CANONICAL

    def test_returns_legacy_for_ex001(self) -> None:
        """ex001_sanity is marked legacy in the live manifest."""
        layout = get_exercise_layout("ex001_sanity")
        assert layout == ExerciseLayout.LEGACY

    def test_raises_key_error_for_nonexistent_exercise(self, tmp_path: Path) -> None:
        """Nonexistent exercise_key raises KeyError."""
        manifest_path = make_manifest(tmp_path, {"ex001_sanity": {"layout": "legacy"}})
        with pytest.raises(KeyError, match="not in the migration manifest"):
            get_exercise_layout("nonexistent_xyz", manifest_path=manifest_path)
