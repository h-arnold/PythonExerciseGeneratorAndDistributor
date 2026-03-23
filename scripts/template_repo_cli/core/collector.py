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
            FileNotFoundError: If notebook or test file is not found.
            ValueError: If exercise_id is empty.
        """
        if not exercise_id:
            raise ValueError("Exercise ID cannot be empty")

        # Student notebook (required)
        notebook_path: Path = self.notebooks_dir / f"{exercise_id}.ipynb"
        if not notebook_path.exists():
            raise FileNotFoundError(f"Student notebook not found: {exercise_id}")

        # Test file: check legacy location first, then canonical exercises/ tree.
        # The canonical glob uses three wildcards (construct/type/exercise_key) rather
        # than ** for performance and to match the exact three-level canonical structure.
        legacy_test_path: Path = self.tests_dir / f"test_{exercise_id}.py"
        if legacy_test_path.exists():
            return ExerciseFiles(notebook=notebook_path, test=legacy_test_path)

        canonical_matches = list(
            self.repo_root.glob(f"exercises/*/*/*/tests/test_{exercise_id}.py")
        )
        if len(canonical_matches) > 1:
            paths = ", ".join(str(m) for m in canonical_matches)
            raise FileNotFoundError(
                f"Multiple canonical test files found for {exercise_id}: {paths}"
            )
        if canonical_matches:
            return ExerciseFiles(notebook=notebook_path, test=canonical_matches[0])

        raise FileNotFoundError(f"Test file not found: {exercise_id}")

    def collect_multiple(self, exercise_ids: list[str]) -> dict[str, ExerciseFiles]:
        """Collect files for multiple exercises.

        Args:
            exercise_ids: List of exercise IDs.

        Returns:
            Dictionary mapping exercise ID to files dictionary.
        """
        if not exercise_ids:
            return {}

        all_files: dict[str, ExerciseFiles] = {}
        for exercise_id in exercise_ids:
            all_files[exercise_id] = self.collect_files(exercise_id)

        return all_files
