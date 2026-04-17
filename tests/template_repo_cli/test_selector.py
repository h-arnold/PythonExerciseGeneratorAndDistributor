"""Tests for exercise selector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.core.selector import ExerciseSelector
from tests.exercise_metadata_helpers import make_exercise_json, make_manifest


class TestSelectByConstruct:
    """Tests for selecting exercises by construct."""

    def test_select_by_single_construct(self, repo_root: Path) -> None:
        """Construct selection includes metadata-backed canonical exercises."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct(["sequence"])

        assert "ex004_sequence_debug_syntax" in exercises
        assert "ex002_sequence_modify_basics" in exercises

    def test_select_by_multiple_constructs(self, repo_root: Path) -> None:
        """Test selecting from multiple constructs."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct(["sequence", "selection"])

        assert len(exercises) > 0
        # Should contain exercises from both constructs

    def test_select_invalid_construct(self, repo_root: Path) -> None:
        """Test selecting invalid construct raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="Invalid construct"):
            selector.select_by_construct(["invalid_construct"])

    def test_select_empty_construct_list(self, repo_root: Path) -> None:
        """Test selecting with empty construct list raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="At least one construct"):
            selector.select_by_construct([])


class TestSelectByType:
    """Tests for selecting exercises by type."""

    def test_select_by_single_type(self, repo_root: Path) -> None:
        """Type selection includes canonical exercises via metadata, not path."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_type(["modify"])

        assert "ex002_sequence_modify_basics" in exercises
        assert "ex004_sequence_debug_syntax" not in exercises

    def test_select_by_type_includes_metadata_backed_canonical_exercise(
        self, repo_root: Path
    ) -> None:
        """Canonical exercises remain selectable after removing the type path segment."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_type(["debug"])

        assert "ex004_sequence_debug_syntax" in exercises

    def test_select_by_multiple_types(self, repo_root: Path) -> None:
        """Test selecting exercises by multiple types."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_type(["modify", "debug"])

        assert len(exercises) > 0

    def test_select_invalid_type(self, repo_root: Path) -> None:
        """Test selecting invalid type raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="Invalid type"):
            selector.select_by_type(["invalid_type"])

    def test_select_empty_type_list(self, repo_root: Path) -> None:
        """Test selecting with empty type list raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="At least one type"):
            selector.select_by_type([])


class TestSelectByConstructAndType:
    """Tests for selecting exercises by construct AND type."""

    def test_select_by_construct_and_type(self, repo_root: Path) -> None:
        """Construct/type selection intersects canonical metadata correctly."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct_and_type(constructs=["sequence"], types=["modify"])

        assert "ex002_sequence_modify_basics" in exercises
        assert "ex004_sequence_debug_syntax" not in exercises

    def test_select_by_construct_and_type_includes_canonical_metadata_match(
        self,
        repo_root: Path,
    ) -> None:
        """Construct/type selection finds canonical exercises without scanning type folders."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct_and_type(constructs=["sequence"], types=["debug"])

        assert "ex004_sequence_debug_syntax" in exercises

    def test_select_multiple_constructs_and_types(self, repo_root: Path) -> None:
        """Test multiple constructs and types."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct_and_type(
            constructs=["sequence", "selection"], types=["modify", "debug"]
        )

        assert isinstance(exercises, list)


class TestSelectBySpecificExerciseKeys:
    """Tests for selecting specific exercise keys."""

    def test_select_specific_exercise_keys(self, repo_root: Path) -> None:
        """Test selecting an explicit exercise-key list."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_keys(["ex002_sequence_modify_basics"])

        assert len(exercises) == 1
        assert "ex002_sequence_modify_basics" in exercises[0]

    def test_select_multiple_exercise_keys(self, repo_root: Path) -> None:
        """Test selecting multiple specific exercise keys."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_keys(
            ["ex002_sequence_modify_basics", "ex004_sequence_debug_syntax"]
        )

        EXPECTED_SELECTION_COUNT = 2
        assert len(exercises) == EXPECTED_SELECTION_COUNT

    def test_select_nonexistent_exercise_key(self, repo_root: Path) -> None:
        """Test selecting a nonexistent exercise key raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="Exercise key not found"):
            selector.select_by_exercise_keys(["ex999_nonexistent"])

    def test_select_empty_exercise_key_list(self, repo_root: Path) -> None:
        """Test selecting with an empty exercise-key list raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="At least one exercise key"):
            selector.select_by_exercise_keys([])


class TestSelectByPattern:
    """Tests for selecting exercise keys by pattern."""

    def test_select_by_pattern_asterisk(self, repo_root: Path) -> None:
        """Test glob pattern matching with asterisk."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_key_pattern("ex00*")

        assert len(exercises) > 0
        assert all(ex.startswith("ex00") for ex in exercises)

    def test_select_by_pattern_question_mark(self, repo_root: Path) -> None:
        """Test glob pattern matching with question mark."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_key_pattern("ex00?_*")

        assert len(exercises) > 0

    def test_select_by_pattern_no_matches(self, repo_root: Path) -> None:
        """Test pattern with no matches returns empty list."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_key_pattern("ex999*")

        assert len(exercises) == 0

    def test_select_by_pattern_invalid_pattern(self, repo_root: Path) -> None:
        """Test invalid pattern raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="Invalid pattern"):
            selector.select_by_exercise_key_pattern("notebooks/ex002")


class TestMetadataBackedSelection:
    """Regression tests for metadata-backed selector behaviour."""

    def test_selector_uses_metadata_for_legacy_stub_without_legacy_layout_paths(
        self,
        tmp_path: Path,
    ) -> None:
        """Selector falls back to registry metadata when legacy path scans cannot help."""
        repo_root = tmp_path
        exercises_root = repo_root / "exercises"
        exercises_root.mkdir()

        exercise_key = "ex123_sequence_modify_metadata_stub"
        make_manifest(
            exercises_root,
            {exercise_key: {"layout": "legacy"}},
        )
        make_exercise_json(
            exercises_root / "sequence" / exercise_key,
            {
                "schema_version": 1,
                "exercise_key": exercise_key,
                "exercise_id": 123,
                "slug": "sequence_modify_metadata_stub",
                "title": "Sequence Modify Metadata Stub",
                "construct": "sequence",
                "exercise_type": "modify",
                "parts": 1,
            },
        )

        selector = ExerciseSelector(repo_root)

        assert not (repo_root / "notebooks").exists()
        assert not (exercises_root / "sequence" / "modify").exists()
        assert selector.get_all_exercise_keys() == [exercise_key]
        assert selector.select_by_construct(["sequence"]) == [exercise_key]
        assert selector.select_by_type(["modify"]) == [exercise_key]
        assert selector.select_by_construct_and_type(["sequence"], ["modify"]) == [exercise_key]

    def test_selector_ignores_path_only_entries_when_manifest_exists(
        self,
        tmp_path: Path,
    ) -> None:
        """Selector stays metadata-only when a manifest is available."""
        repo_root = tmp_path
        exercises_root = repo_root / "exercises"
        exercises_root.mkdir()
        notebooks_dir = repo_root / "notebooks"
        notebooks_dir.mkdir()

        metadata_key = "ex123_sequence_modify_manifest"
        path_only_key = "ex999_sequence_modify_path_only"
        make_manifest(
            exercises_root,
            {metadata_key: {"layout": "legacy"}},
        )
        make_exercise_json(
            exercises_root / "sequence" / metadata_key,
            {
                "schema_version": 1,
                "exercise_key": metadata_key,
                "exercise_id": 123,
                "slug": "sequence_modify_manifest",
                "title": "Sequence Modify Manifest",
                "construct": "sequence",
                "exercise_type": "modify",
                "parts": 1,
            },
        )
        (notebooks_dir / f"{path_only_key}.ipynb").write_text("{}", encoding="utf-8")
        (exercises_root / "sequence" / "modify" / path_only_key).mkdir(parents=True)

        selector = ExerciseSelector(repo_root)

        assert selector.get_all_exercise_keys() == [metadata_key]
        assert selector.select_by_construct(["sequence"]) == [metadata_key]
        assert selector.select_by_type(["modify"]) == [metadata_key]
        assert selector.select_by_construct_and_type(["sequence"], ["modify"]) == [metadata_key]


class TestSelectEmptyResult:
    """Tests for handling empty selection results."""

    def test_select_returns_empty_gracefully(self, repo_root: Path) -> None:
        """Test empty result handled gracefully."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_key_pattern("nonexistent*")

        assert exercises == []
        assert isinstance(exercises, list)
