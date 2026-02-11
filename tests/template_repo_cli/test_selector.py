"""Tests for exercise selector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.core.selector import ExerciseSelector


class TestSelectByConstruct:
    """Tests for selecting exercises by construct."""

    def test_select_by_single_construct(self, repo_root: Path) -> None:
        """Test selecting all exercises in one construct."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct(["sequence"])

        assert len(exercises) > 0
        assert all("sequence" in str(ex).lower() for ex in exercises)

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
        """Test selecting exercises by single type."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_type(["modify"])

        assert len(exercises) > 0
        # All returned exercises should be modify type

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
        """Test intersection of construct and type."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct_and_type(constructs=["sequence"], types=["modify"])

        assert len(exercises) > 0
        # All should be sequence AND modify

    def test_select_multiple_constructs_and_types(self, repo_root: Path) -> None:
        """Test multiple constructs and types."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_construct_and_type(
            constructs=["sequence", "selection"], types=["modify", "debug"]
        )

        assert isinstance(exercises, list)


class TestSelectBySpecificNotebooks:
    """Tests for selecting specific notebooks."""

    def test_select_specific_notebooks(self, repo_root: Path) -> None:
        """Test selecting explicit notebook list."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_notebooks(["ex001_sanity"])

        assert len(exercises) == 1
        assert "ex001_sanity" in exercises[0]

    def test_select_multiple_notebooks(self, repo_root: Path) -> None:
        """Test selecting multiple specific notebooks."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_notebooks(["ex001_sanity", "ex002_sequence_modify_basics"])

        EXPECTED_SELECTION_COUNT = 2
        assert len(exercises) == EXPECTED_SELECTION_COUNT

    def test_select_nonexistent_notebook(self, repo_root: Path) -> None:
        """Test selecting nonexistent notebook raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="not found"):
            selector.select_by_notebooks(["ex999_nonexistent"])

    def test_select_empty_notebook_list(self, repo_root: Path) -> None:
        """Test selecting with empty notebook list raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="At least one notebook"):
            selector.select_by_notebooks([])


class TestSelectByPattern:
    """Tests for selecting notebooks by pattern."""

    def test_select_by_pattern_asterisk(self, repo_root: Path) -> None:
        """Test glob pattern matching with asterisk."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_pattern("ex00*")

        assert len(exercises) > 0
        assert all(ex.startswith("ex00") for ex in exercises)

    def test_select_by_pattern_question_mark(self, repo_root: Path) -> None:
        """Test glob pattern matching with question mark."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_pattern("ex00?_*")

        assert len(exercises) > 0

    def test_select_by_pattern_no_matches(self, repo_root: Path) -> None:
        """Test pattern with no matches returns empty list."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_pattern("ex999*")

        assert len(exercises) == 0

    def test_select_by_pattern_invalid_pattern(self, repo_root: Path) -> None:
        """Test invalid pattern raises ValueError."""
        selector = ExerciseSelector(repo_root)

        with pytest.raises(ValueError, match="Invalid pattern"):
            selector.select_by_pattern("notebooks/ex001")


class TestSelectEmptyResult:
    """Tests for handling empty selection results."""

    def test_select_returns_empty_gracefully(self, repo_root: Path) -> None:
        """Test empty result handled gracefully."""
        selector = ExerciseSelector(repo_root)
        exercises = selector.select_by_pattern("nonexistent*")

        assert exercises == []
        assert isinstance(exercises, list)
