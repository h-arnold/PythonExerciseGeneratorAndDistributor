"""File collector."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from exercise_metadata import resolve_exercise_dir
from exercise_metadata.resolver import resolve_notebook_path
from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
)


class ExerciseFiles(TypedDict):
    """Typed mapping returned by FileCollector.collect_files()."""

    notebook: Path
    notebook_export: Path
    test: Path
    tests_export_dir: Path


class FileCollector:
    """Collect source files and export targets for exercises."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize collector.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root: Path = repo_root
        self.exercises_dir: Path = repo_root / "exercises"
        self.manifest_path: Path = self.exercises_dir / "migration_manifest.json"

    def _canonical_test_path(self, exercise_id: str) -> Path:
        exercise_dir = resolve_exercise_dir(exercise_id, self.exercises_dir)
        return exercise_dir / "tests" / f"test_{exercise_id}.py"

    def _canonical_tests_export_dir(self, exercise_id: str) -> Path:
        exercise_dir = resolve_exercise_dir(exercise_id, self.exercises_dir)
        return Path("exercises") / exercise_dir.relative_to(self.exercises_dir) / "tests"

    def _canonical_notebook_export_path(self, exercise_id: str) -> Path:
        exercise_dir = resolve_exercise_dir(exercise_id, self.exercises_dir)
        return (
            Path("exercises")
            / exercise_dir.relative_to(self.exercises_dir)
            / "notebooks"
            / "student.ipynb"
        )

    def _raise_for_duplicate_test_sources(self, exercise_id: str) -> None:
        candidate_paths: list[Path] = []
        candidate_paths.extend(
            path.relative_to(self.repo_root)
            for path in self.exercises_dir.rglob(f"test_{exercise_id}.py")
            if path.is_file()
        )

        duplicates = find_duplicate_exercise_test_sources(candidate_paths)
        duplicate_paths = duplicates.get(exercise_id)
        if duplicate_paths:
            duplicate_list = "\n".join(str(path) for path in duplicate_paths)
            raise FileExistsError(
                "Duplicate exercise test sources found for "
                f"{exercise_id!r}. Keep exactly one of:\n{duplicate_list}"
            )

    def collect_files(self, exercise_id: str) -> ExerciseFiles:
        """Collect all files for an exercise.

        Args:
            exercise_id: The exercise ID (for example, ``"ex004_sequence_debug_syntax"``).

        Returns:
            Dictionary with source paths and exported workspace targets.

        Raises:
            FileNotFoundError: If required source files are missing.
            ValueError: If exercise_id is empty.
            FileExistsError: If duplicate exercise-local test sources exist.
        """
        if not exercise_id:
            raise ValueError("Exercise ID cannot be empty")

        self._raise_for_duplicate_test_sources(exercise_id)

        # Resolve canonical notebook path
        notebook_path = resolve_notebook_path(
            exercise_id,
            variant="student",
            exercises_root=self.exercises_dir,
            manifest_path=self.manifest_path,
        )

        # Resolve canonical test path
        test_path = self._canonical_test_path(exercise_id)
        if not test_path.exists():
            raise FileNotFoundError(
                f"Canonical exercise test not found: {test_path}")

        return ExerciseFiles(
            notebook=notebook_path,
            notebook_export=self._canonical_notebook_export_path(exercise_id),
            test=test_path,
            tests_export_dir=self._canonical_tests_export_dir(exercise_id),
        )

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
