"""Exercise selector."""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from pathlib import Path

from exercise_metadata import ExerciseLayout, RegistryEntry, build_exercise_registry
from exercise_metadata.schema import ExerciseMetadata
from scripts.template_repo_cli.utils.validation import (
    validate_construct_name,
    validate_notebook_pattern,
    validate_type_name,
)


class ExerciseSelector:
    """Select exercises based on various criteria."""

    def __init__(self, repo_root: Path):
        """Initialize selector.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root = repo_root
        self.notebooks_dir = repo_root / "notebooks"
        self.exercises_dir = repo_root / "exercises"
        self.manifest_path = self.exercises_dir / "migration_manifest.json"

    def _get_registry(self) -> list[RegistryEntry]:
        """Return the metadata-backed exercise registry when available."""
        if not self.manifest_path.exists():
            return []
        return build_exercise_registry(self.manifest_path, self.exercises_dir)

    def _all_metadata_exercise_keys(self) -> list[str]:
        """Return every exercise key backed by registry metadata."""
        return self._filter_metadata_exercise_keys(lambda _exercise_key, _metadata: True)

    @staticmethod
    def _needs_legacy_path_fallback(entry: RegistryEntry) -> bool:
        """Return True when a legacy manifest entry still lacks metadata."""
        return entry["layout"] == ExerciseLayout.LEGACY.value and entry["metadata"] is None

    def get_all_notebooks(self) -> list[str]:
        """Get all notebook IDs from metadata or the notebooks directory.

        Returns:
            List of notebook IDs (without .ipynb extension).
        """
        notebooks = self._all_metadata_exercise_keys()
        if self.manifest_path.exists():
            return sorted(set(notebooks))

        notebooks = []
        if self.notebooks_dir.exists():
            for nb_file in self.notebooks_dir.glob("ex*.ipynb"):
                notebooks.append(nb_file.stem)
        return notebooks

    def _validate_constructs(self, constructs: list[str]) -> None:
        """Validate construct names.

        Args:
            constructs: List of construct names.

        Raises:
            ValueError: If list is empty or contains invalid construct.
        """
        if not constructs:
            raise ValueError("At least one construct must be specified")

        for construct in constructs:
            if not validate_construct_name(construct):
                raise ValueError(f"Invalid construct: {construct}")

    def _validate_types(self, types: list[str]) -> None:
        """Validate type names.

        Args:
            types: List of exercise types.

        Raises:
            ValueError: If list is empty or contains invalid type.
        """
        if not types:
            raise ValueError("At least one type must be specified")

        for type_name in types:
            if not validate_type_name(type_name):
                raise ValueError(f"Invalid type: {type_name}")

    def _legacy_exercise_keys(self) -> set[str] | None:
        """Return legacy exercise keys that still need path-based fallback."""
        if not self.manifest_path.exists():
            return None
        return {
            entry["exercise_key"]
            for entry in self._get_registry()
            if self._needs_legacy_path_fallback(entry)
        }

    def _filter_metadata_exercise_keys(
        self,
        predicate: Callable[[str, ExerciseMetadata], bool],
    ) -> list[str]:
        """Return metadata-backed exercise keys selected via the registry."""
        matches: list[str] = []
        for entry in self._get_registry():
            metadata = entry["metadata"]
            if metadata is None:
                continue
            if predicate(entry["exercise_key"], metadata):
                matches.append(entry["exercise_key"])
        return matches

    def _find_legacy_exercises_in_construct(self, construct: str) -> list[str]:
        """Find legacy exercises in a construct by scanning legacy type folders.

        Args:
            construct: Construct name.

        Returns:
            List of legacy exercise IDs found.
        """
        exercises: list[str] = []
        construct_dir = self.exercises_dir / construct
        legacy_keys = self._legacy_exercise_keys()

        if construct_dir.exists():
            for type_dir in construct_dir.iterdir():
                if type_dir.is_dir() and validate_type_name(type_dir.name):
                    for ex_dir in type_dir.iterdir():
                        if (
                            ex_dir.is_dir()
                            and ex_dir.name.startswith("ex")
                            and (legacy_keys is None or ex_dir.name in legacy_keys)
                        ):
                            exercises.append(ex_dir.name)

        return exercises

    def _find_legacy_exercises_by_type(self, type_name: str) -> list[str]:
        """Find legacy exercises of a specific type.

        Args:
            type_name: Exercise type.

        Returns:
            List of legacy exercise IDs found.
        """
        exercises: list[str] = []
        legacy_keys = self._legacy_exercise_keys()

        for construct_dir in self.exercises_dir.iterdir():
            if construct_dir.is_dir():
                type_dir = construct_dir / type_name
                if type_dir.exists() and type_dir.is_dir():
                    for ex_dir in type_dir.iterdir():
                        if (
                            ex_dir.is_dir()
                            and ex_dir.name.startswith("ex")
                            and (legacy_keys is None or ex_dir.name in legacy_keys)
                        ):
                            exercises.append(ex_dir.name)

        return exercises

    def select_by_construct(self, constructs: list[str]) -> list[str]:
        """Select exercises by construct.

        Args:
            constructs: List of construct names.

        Returns:
            List of exercise IDs.

        Raises:
            ValueError: If no constructs provided or invalid construct.
        """
        self._validate_constructs(constructs)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: metadata["construct"] in constructs,
        )
        if self.manifest_path.exists():
            return sorted(set(exercises))

        for construct in constructs:
            exercises.extend(self._find_legacy_exercises_in_construct(construct))

        return sorted(set(exercises))

    def select_by_type(self, types: list[str]) -> list[str]:
        """Select exercises by type.

        Args:
            types: List of exercise types.

        Returns:
            List of exercise IDs.

        Raises:
            ValueError: If no types provided or invalid type.
        """
        self._validate_types(types)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: metadata["exercise_type"] in types,
        )
        if self.manifest_path.exists():
            return sorted(set(exercises))

        for type_name in types:
            exercises.extend(self._find_legacy_exercises_by_type(type_name))

        return sorted(set(exercises))

    def _find_legacy_exercises_in_type_dir(self, construct: str, type_name: str) -> list[str]:
        """Find legacy exercises in a specific construct/type directory.

        Args:
            construct: Construct name.
            type_name: Exercise type name.

        Returns:
            List of exercise IDs found.
        """
        exercises: list[str] = []
        construct_dir = self.exercises_dir / construct
        legacy_keys = self._legacy_exercise_keys()

        if not construct_dir.exists():
            return exercises

        type_dir = construct_dir / type_name
        if not type_dir.exists():
            return exercises

        for ex_dir in type_dir.iterdir():
            if (
                ex_dir.is_dir()
                and ex_dir.name.startswith("ex")
                and (legacy_keys is None or ex_dir.name in legacy_keys)
            ):
                exercises.append(ex_dir.name)

        return exercises

    def select_by_construct_and_type(self, constructs: list[str], types: list[str]) -> list[str]:
        """Select exercises by construct AND type.

        Args:
            constructs: List of construct names.
            types: List of exercise types.

        Returns:
            List of exercise IDs matching both criteria.
        """
        self._validate_constructs(constructs)
        self._validate_types(types)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: (
                metadata["construct"] in constructs
                and metadata["exercise_type"] in types
            ),
        )
        if self.manifest_path.exists():
            return sorted(set(exercises))

        for construct in constructs:
            for type_name in types:
                exercises.extend(self._find_legacy_exercises_in_type_dir(construct, type_name))

        return sorted(set(exercises))

    def select_by_notebooks(self, notebooks: list[str]) -> list[str]:
        """Select specific notebooks.

        Args:
            notebooks: List of notebook IDs.

        Returns:
            List of exercise IDs (validated to exist).

        Raises:
            ValueError: If no notebooks provided or notebook not found.
        """
        if not notebooks:
            raise ValueError("At least one notebook must be specified")

        available = self.get_all_notebooks()

        for notebook in notebooks:
            if notebook not in available:
                raise ValueError(f"Notebook not found: {notebook}")

        return sorted(notebooks)

    def select_by_pattern(self, pattern: str) -> list[str]:
        """Select notebooks by pattern.

        Args:
            pattern: Glob pattern for matching notebooks.

        Returns:
            List of matching exercise IDs (may be empty).

        Raises:
            ValueError: If pattern is invalid.
        """
        if not validate_notebook_pattern(pattern):
            raise ValueError(f"Invalid pattern: {pattern}")

        all_notebooks = self.get_all_notebooks()
        matching = [nb for nb in all_notebooks if fnmatch.fnmatch(nb, pattern)]

        return sorted(matching)
