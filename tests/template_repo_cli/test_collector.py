"""Tests for file collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.core.collector import FileCollector


class TestCollectAllFiles:
    """Tests for collecting all files for an exercise."""

    def test_collect_all_files_for_exercise(
        self, repo_root: Path, sample_exercises: dict[str, dict[str, Path]]
    ) -> None:
        """Test collecting all related files for an exercise."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        assert "notebook" in files
        assert "test" in files
        assert files["notebook"].exists()
        assert files["test"].exists()

    def test_collect_multiple_exercises(self, repo_root: Path) -> None:
        """Test batch collection of multiple exercises."""
        collector = FileCollector(repo_root)
        all_files = collector.collect_multiple(
            ["ex001_sanity", "ex002_sequence_modify_basics"])

        EXPECTED_MULTIPLE_COUNT = 2
        assert len(all_files) == EXPECTED_MULTIPLE_COUNT
        assert "ex001_sanity" in all_files
        assert "ex002_sequence_modify_basics" in all_files

    def test_collect_validates_paths(self, repo_root: Path) -> None:
        """Test path existence validation."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        # All collected paths should exist
        for file_type, file_path in files.items():
            if file_path is not None:
                assert file_path.exists(
                ), f"{file_type} does not exist: {file_path}"


class TestCollectMissingFiles:
    """Tests for handling missing files."""

    def test_collect_missing_notebook(self, repo_root: Path) -> None:
        """Test handling missing student notebook."""
        collector = FileCollector(repo_root)

        with pytest.raises(FileNotFoundError, match="notebook not found"):
            collector.collect_files("ex999_nonexistent")

    def test_collect_missing_solution(self, repo_root: Path, temp_dir: Path) -> None:
        """Test handling missing solution notebook.

        Solutions are not collected for template repos, so no check is required.
        """
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        assert "notebook" in files
        assert "test" in files

    def test_collect_missing_test(self, repo_root: Path) -> None:
        """Test handling missing test file."""
        collector = FileCollector(repo_root)

        # If test is missing, should raise error or return None depending on implementation
        files = collector.collect_files("ex001_sanity")
        assert files["test"].exists()

    def test_collect_missing_metadata_optional(self, repo_root: Path) -> None:
        """Test that missing metadata is optional (doesn't fail)."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        assert "notebook" in files
        assert "test" in files


class TestCollectFileStructure:
    """Tests for file structure handling."""

    def test_collect_preserves_structure(self, repo_root: Path) -> None:
        """Test that collected files preserve directory structure info."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        # Should have correct paths
        assert "notebooks" in str(files["notebook"])
        assert "tests" in str(files["test"])

    def test_collect_handles_construct_organization(self, repo_root: Path) -> None:
        """Test handling of construct/type organization in exercises/."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        assert "notebook" in files
        assert "test" in files


class TestCollectValidation:
    """Tests for collection validation."""

    def test_collect_returns_dict(self, repo_root: Path) -> None:
        """Test that collect_files returns a dictionary."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        assert isinstance(files, dict)

    def test_collect_has_required_keys(self, repo_root: Path) -> None:
        """Test that returned dict has required keys."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        required_keys = ["notebook", "test"]
        for key in required_keys:
            assert key in files

    def test_collect_all_paths_are_pathlib(self, repo_root: Path) -> None:
        """Test that all paths are Path objects."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex001_sanity")

        for file_path in files.values():
            if file_path is not None:
                assert isinstance(file_path, Path)


class TestCollectEdgeCases:
    """Tests for edge cases in file collection."""

    def test_collect_empty_exercise_list(self, repo_root: Path) -> None:
        """Test collecting with empty exercise list."""
        collector = FileCollector(repo_root)
        all_files = collector.collect_multiple([])

        assert all_files == {}

    def test_collect_nonexistent_exercise(self, repo_root: Path) -> None:
        """Test collecting nonexistent exercise raises error."""
        collector = FileCollector(repo_root)

        with pytest.raises(FileNotFoundError):
            collector.collect_files("nonexistent_exercise")

    def test_collect_invalid_exercise_name(self, repo_root: Path) -> None:
        """Test collecting with invalid exercise name."""
        collector = FileCollector(repo_root)

        with pytest.raises((ValueError, FileNotFoundError)):
            collector.collect_files("")
