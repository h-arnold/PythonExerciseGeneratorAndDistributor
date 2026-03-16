"""File collector."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from exercise_metadata import ExerciseLayout, get_exercise_layout, resolve_exercise_dir
from exercise_metadata.resolver import resolve_notebook_path
from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
)


class ExerciseFiles(TypedDict):
    """Typed mapping returned by FileCollector.collect_files()."""

    notebook: Path
    notebook_export: Path
    test: Path
    test_export: Path


class FileCollector:
    """Collect source files and export targets for exercises."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize collector.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root: Path = repo_root
        self.notebooks_dir: Path = repo_root / "notebooks"
        self.tests_dir: Path = repo_root / "tests"
        self.exercises_dir: Path = repo_root / "exercises"
        self.manifest_path: Path = self.exercises_dir / "migration_manifest.json"

    def _canonical_test_path(self, exercise_id: str) -> Path:
        exercise_dir = resolve_exercise_dir(exercise_id, self.exercises_dir)
        return exercise_dir / "tests" / f"test_{exercise_id}.py"

    def _legacy_notebook_path(self, exercise_id: str) -> Path:
        return self.notebooks_dir / f"{exercise_id}.ipynb"

    def _legacy_test_path(self, exercise_id: str) -> Path:
        return self.tests_dir / f"test_{exercise_id}.py"

    def _preferred_test_path_for_legacy_layout(self, exercise_id: str) -> Path:
        """Return the canonical test when available, otherwise the flat legacy test."""

        try:
            canonical_test = self._canonical_test_path(exercise_id)
        except LookupError:
            return self._legacy_test_path(exercise_id)

        if canonical_test.exists():
            return canonical_test
        return self._legacy_test_path(exercise_id)

    def _raise_for_duplicate_test_sources(self, exercise_id: str) -> None:
        legacy_test = self._legacy_test_path(exercise_id)
        candidate_paths: list[Path] = []
        if legacy_test.exists():
            candidate_paths.append(legacy_test.relative_to(self.repo_root))

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
            Dictionary with source paths and flattened export paths.

        Raises:
            FileNotFoundError: If required source files are missing.
            ValueError: If exercise_id is empty.
            FileExistsError: If both top-level and canonical exercise-local test sources exist.
        """
        if not exercise_id:
            raise ValueError("Exercise ID cannot be empty")

        self._raise_for_duplicate_test_sources(exercise_id)
        try:
            layout = get_exercise_layout(exercise_id, self.manifest_path)
        except KeyError as exc:
            raise FileNotFoundError(
                f"Exercise not found in migration manifest: {exercise_id}") from exc

        if layout == ExerciseLayout.CANONICAL:
            notebook_path = resolve_notebook_path(
                exercise_id,
                variant="student",
                exercises_root=self.exercises_dir,
                manifest_path=self.manifest_path,
            )
            test_path = self._canonical_test_path(exercise_id)
            if not test_path.exists():
                raise FileNotFoundError(
                    f"Canonical exercise test not found: {test_path}")
        else:
            notebook_path = self._legacy_notebook_path(exercise_id)
            if not notebook_path.exists():
                raise FileNotFoundError(
                    f"Student notebook not found: {exercise_id}")
            test_path = self._preferred_test_path_for_legacy_layout(
                exercise_id)
            if not test_path.exists():
                raise FileNotFoundError(f"Test file not found: {exercise_id}")

        return ExerciseFiles(
            notebook=notebook_path,
            notebook_export=Path("notebooks") / f"{exercise_id}.ipynb",
            test=test_path,
            test_export=Path("tests") / f"test_{exercise_id}.py",
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
