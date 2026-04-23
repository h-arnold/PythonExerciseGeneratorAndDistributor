"""Exercise selector."""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from pathlib import Path

from exercise_metadata import RegistryEntry, build_exercise_registry
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
        self.exercises_dir = repo_root / "exercises"
        self.manifest_path = self.exercises_dir / "migration_manifest.json"

    def _get_registry(self) -> list[RegistryEntry]:
        """Return the metadata-backed exercise registry."""
        return build_exercise_registry(self.manifest_path, self.exercises_dir)

    def _all_metadata_exercise_keys(self) -> list[str]:
        """Return every exercise key backed by registry metadata."""
        return self._filter_metadata_exercise_keys(lambda _exercise_key, _metadata: True)

    def get_all_exercise_keys(self) -> list[str]:
        """Get all available exercise keys.

        Returns:
            List of exercise keys.
        """
        exercise_keys = self._all_metadata_exercise_keys()
        return sorted(set(exercise_keys))

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

    def select_by_construct(self, constructs: list[str]) -> list[str]:
        """Select exercises by construct.

        Args:
            constructs: List of construct names.

        Returns:
            List of exercise keys.

        Raises:
            ValueError: If no constructs provided or invalid construct.
        """
        self._validate_constructs(constructs)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: metadata["construct"] in constructs,
        )
        return sorted(set(exercises))

    def select_by_type(self, types: list[str]) -> list[str]:
        """Select exercises by type.

        Args:
            types: List of exercise types.

        Returns:
            List of exercise keys.

        Raises:
            ValueError: If no types provided or invalid type.
        """
        self._validate_types(types)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: metadata["exercise_type"] in types,
        )
        return sorted(set(exercises))

    def select_by_construct_and_type(self, constructs: list[str], types: list[str]) -> list[str]:
        """Select exercises by construct AND type.

        Args:
            constructs: List of construct names.
            types: List of exercise types.

        Returns:
            List of exercise keys matching both criteria.
        """
        self._validate_constructs(constructs)
        self._validate_types(types)

        exercises = self._filter_metadata_exercise_keys(
            lambda _exercise_key, metadata: (
                metadata["construct"] in constructs and metadata["exercise_type"] in types
            ),
        )
        return sorted(set(exercises))

    def select_by_exercise_keys(self, exercise_keys: list[str]) -> list[str]:
        """Select specific exercise keys.

        Args:
            exercise_keys: List of exercise keys.

        Returns:
            List of exercise keys validated to exist.

        Raises:
            ValueError: If no exercise keys are provided or a key is not found.
        """
        if not exercise_keys:
            raise ValueError("At least one exercise key must be specified")

        available = self.get_all_exercise_keys()

        for exercise_key in exercise_keys:
            if exercise_key not in available:
                raise ValueError(f"Exercise key not found: {exercise_key}")

        return sorted(exercise_keys)

    def select_by_exercise_key_pattern(self, pattern: str) -> list[str]:
        """Select exercise keys by glob pattern.

        Args:
            pattern: Glob pattern for matching exercise keys.

        Returns:
            List of matching exercise keys.

        Raises:
            ValueError: If pattern is invalid.
        """
        if not validate_notebook_pattern(pattern):
            raise ValueError(f"Invalid pattern: {pattern}")

        all_exercise_keys = self.get_all_exercise_keys()
        matching = [
            exercise_key
            for exercise_key in all_exercise_keys
            if fnmatch.fnmatch(exercise_key, pattern)
        ]

        return sorted(matching)
