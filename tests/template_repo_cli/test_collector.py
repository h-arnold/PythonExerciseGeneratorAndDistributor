"""Tests for file collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.core.collector import FileCollector


class TestCollectAllFiles:
    """Tests for collecting all files for an exercise."""

    def test_collect_all_files_for_migrated_exercise(self, repo_root: Path) -> None:
        """Test collecting a migrated canonical notebook plus exercise-local test source."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        assert files["notebook"] == (
            repo_root
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        )
        assert files["notebook_export"] == Path(
            "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb")
        assert files["test"] == (
            repo_root
            / "exercises/sequence/ex002_sequence_modify_basics/tests"
            / "test_ex002_sequence_modify_basics.py"
        )
        assert files["tests_export_dir"] == Path(
            "exercises/sequence/ex002_sequence_modify_basics/tests")

    def test_collect_all_files_for_canonical_exercise(self, repo_root: Path) -> None:
        """Test collecting canonical files from the exercise source tree."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex004_sequence_debug_syntax")

        assert files["notebook"] == (
            repo_root / "exercises/sequence/ex004_sequence_debug_syntax/notebooks/student.ipynb"
        )
        assert files["notebook_export"] == Path(
            "exercises/sequence/ex004_sequence_debug_syntax/notebooks/student.ipynb")
        assert files["test"] == (
            repo_root
            / "exercises/sequence/ex004_sequence_debug_syntax/tests"
            / "test_ex004_sequence_debug_syntax.py"
        )
        assert files["tests_export_dir"] == Path(
            "exercises/sequence/ex004_sequence_debug_syntax/tests")

    def test_collect_multiple_exercises(self, repo_root: Path) -> None:
        """Test batch collection of multiple exercises."""
        collector = FileCollector(repo_root)
        all_files = collector.collect_multiple(
            ["ex002_sequence_modify_basics", "ex004_sequence_debug_syntax"]
        )

        expected_count = 2
        assert len(all_files) == expected_count
        assert "ex002_sequence_modify_basics" in all_files
        assert "ex004_sequence_debug_syntax" in all_files


class TestCollectMissingFiles:
    """Tests for handling missing files."""

    def test_collect_missing_notebook(self, repo_root: Path) -> None:
        """Test handling missing student notebook."""
        collector = FileCollector(repo_root)

        with pytest.raises(FileNotFoundError, match="Exercise not found in migration manifest"):
            collector.collect_files("ex999_nonexistent")

    def test_collect_missing_test(self, repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test canonical exercises fail hard when the required test is missing."""
        collector = FileCollector(repo_root)

        def missing_test_path(_exercise_id: str) -> Path:
            return repo_root / "missing" / "test_ex004_sequence_debug_syntax.py"

        monkeypatch.setattr(
            collector,
            "_canonical_test_path",
            missing_test_path,
        )

        with pytest.raises(FileNotFoundError, match="Canonical exercise test not found"):
            collector.collect_files("ex004_sequence_debug_syntax")


class TestCollectValidation:
    """Tests for collection validation."""

    def test_collect_returns_dict(self, repo_root: Path) -> None:
        """Test that collect_files returns a dictionary."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        assert isinstance(files, dict)

    def test_collect_has_required_keys(self, repo_root: Path) -> None:
        """Test that returned dict has required keys."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        required_keys = [
            "notebook",
            "notebook_export",
            "test",
            "tests_export_dir",
        ]
        for key in required_keys:
            assert key in files

    def test_collect_all_paths_are_pathlib(self, repo_root: Path) -> None:
        """Test that all paths are Path objects."""
        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        for file_path in files.values():
            assert isinstance(file_path, Path)

    def test_collect_rejects_duplicate_top_level_and_canonical_test_sources(
        self,
        temp_dir: Path,
    ) -> None:
        """Test duplicate top-level and canonical sources fail fast."""
        repo_root = temp_dir
        (repo_root / "notebooks").mkdir()
        (repo_root / "tests").mkdir()
        (repo_root / "notebooks" / "ex004_sequence_debug_syntax.ipynb").write_text(
            "{}", encoding="utf-8"
        )
        (repo_root / "tests" / "test_ex004_sequence_debug_syntax.py").write_text(
            "", encoding="utf-8"
        )
        exercise_dir = repo_root / "exercises" / \
            "sequence" / "ex004_sequence_debug_syntax"
        (exercise_dir / "notebooks").mkdir(parents=True)
        (exercise_dir / "tests").mkdir(parents=True)
        (exercise_dir / "notebooks" /
         "student.ipynb").write_text("{}", encoding="utf-8")
        (exercise_dir / "notebooks" /
         "solution.ipynb").write_text("{}", encoding="utf-8")
        (exercise_dir / "tests" / "test_ex004_sequence_debug_syntax.py").write_text(
            "", encoding="utf-8"
        )
        (exercise_dir / "exercise.json").write_text(
            '{"schema_version": 1, "exercise_key": "ex004_sequence_debug_syntax", '
            '"exercise_id": 4, "slug": "ex004_sequence_debug_syntax", '
            '"title": "ex004", "construct": "sequence", '
            '"exercise_type": "debug", "parts": 10}',
            encoding="utf-8",
        )
        (repo_root / "exercises" / "migration_manifest.json").write_text(
            '{"schema_version": 1, "exercises": {"ex004_sequence_debug_syntax": {"layout": "canonical"}}}',
            encoding="utf-8",
        )

        collector = FileCollector(repo_root)
        with pytest.raises(FileExistsError, match="Duplicate exercise test sources"):
            collector.collect_files("ex004_sequence_debug_syntax")

    def test_collect_legacy_layout_falls_back_to_flat_test_when_canonical_test_is_absent(
        self,
        temp_dir: Path,
    ) -> None:
        """Test legacy layouts may source a flat test but export to exercise-local tests/."""
        repo_root = temp_dir
        (repo_root / "notebooks").mkdir()
        (repo_root / "tests").mkdir()
        (repo_root / "notebooks" / "ex002_sequence_modify_basics.ipynb").write_text(
            "{}", encoding="utf-8"
        )
        (repo_root / "tests" / "test_ex002_sequence_modify_basics.py").write_text(
            "", encoding="utf-8"
        )
        (repo_root / "exercises" / "sequence" / "ex002_sequence_modify_basics").mkdir(
            parents=True
        )
        (repo_root / "exercises" / "migration_manifest.json").write_text(
            '{"schema_version": 1, "exercises": {"ex002_sequence_modify_basics": {"layout": "legacy"}}}',
            encoding="utf-8",
        )

        collector = FileCollector(repo_root)
        files = collector.collect_files("ex002_sequence_modify_basics")

        assert files["test"] == repo_root / "tests" / \
            "test_ex002_sequence_modify_basics.py"
        assert files["tests_export_dir"] == Path(
            "exercises/sequence/ex002_sequence_modify_basics/tests"
        )


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

        with pytest.raises((FileNotFoundError, LookupError)):
            collector.collect_files("nonexistent_exercise")

    def test_collect_invalid_exercise_name(self, repo_root: Path) -> None:
        """Test collecting with invalid exercise name."""
        collector = FileCollector(repo_root)

        with pytest.raises((ValueError, FileNotFoundError, LookupError)):
            collector.collect_files("")
