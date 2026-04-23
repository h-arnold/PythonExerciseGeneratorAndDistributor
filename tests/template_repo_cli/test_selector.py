"""Tests for exercise selector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.core.selector import ExerciseSelector


class TestMissingManifest:
    """Tests for selector-backed flows when the migration manifest is missing."""

    @pytest.mark.parametrize(
        ("method_name", "method_args"),
        [
            ("get_all_exercise_keys", ()),
            ("select_by_construct", (["sequence"],)),
            ("select_by_type", (["modify"],)),
            ("select_by_construct_and_type", (["sequence"], ["modify"])),
            ("select_by_exercise_keys", (["ex002_sequence_modify_basics"],)),
            ("select_by_exercise_key_pattern", ("ex00*",)),
        ],
    )
    def test_selector_flows_raise_file_not_found_when_manifest_is_missing(
        self,
        tmp_path: Path,
        method_name: str,
        method_args: tuple[object, ...],
    ) -> None:
        """Selector-backed flows must fail fast when the manifest is absent."""
        selector = ExerciseSelector(tmp_path)
        method = getattr(selector, method_name)

        with pytest.raises(FileNotFoundError, match="Migration manifest not found"):
            method(*method_args)


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


class TestSelectEmptyResult:
    """Tests for handling empty selection results."""

    def test_select_returns_empty_gracefully(self, repo_root: Path) -> None:
        """Test empty result handled gracefully."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_exercise_key_pattern("nonexistent*")

        assert exercises == []
        assert isinstance(exercises, list)
