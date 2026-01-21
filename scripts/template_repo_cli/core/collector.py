"""File collector."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class ExerciseFiles(TypedDict):
    """Typed mapping returned by FileCollector.collect_files()."""

    notebook: Path
    test: Path


class FileCollector:
    """Collect files for exercises."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize collector.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root: Path = repo_root
        self.notebooks_dir: Path = repo_root / "notebooks"
        self.tests_dir: Path = repo_root / "tests"

    def collect_files(self, exercise_id: str) -> ExerciseFiles:
        """Collect all files for an exercise.

        Args:
            exercise_id: The exercise ID (e.g., 'ex001_sanity').

        Returns:
            Dictionary with keys: 'notebook', 'test'.

        Raises:
            FileNotFoundError: If notebook is not found.
            ValueError: If exercise_id is empty.
        """
        if not exercise_id:
            raise ValueError("Exercise ID cannot be empty")

        files = {}

        # Student notebook (required)
        notebook_path: Path = self.notebooks_dir / f"{exercise_id}.ipynb"
        if not notebook_path.exists():
            raise FileNotFoundError(
                f"Student notebook not found: {exercise_id}")
        files["notebook"] = notebook_path

        # Test file (required)
        test_path: Path = self.tests_dir / f"test_{exercise_id}.py"
        if not test_path.exists():
            raise FileNotFoundError(f"Test file not found: {exercise_id}")
        files["test"] = test_path

        return files

    def collect_multiple(self, exercise_ids: list[str]) -> dict[str, ExerciseFiles]:
        """Collect files for multiple exercises.

        Args:
            exercise_ids: List of exercise IDs.

        Returns:
            Dictionary mapping exercise ID to files dictionary.
        """
        if not exercise_ids:
            return {}

        all_files = {}
        for exercise_id in exercise_ids:
            all_files[exercise_id] = self.collect_files(exercise_id)

        return all_files
