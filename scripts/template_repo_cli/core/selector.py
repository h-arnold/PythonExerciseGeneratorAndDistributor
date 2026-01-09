"""Exercise selector."""

from __future__ import annotations

import fnmatch
from pathlib import Path

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

    def _get_all_notebooks(self) -> list[str]:
        """Get all notebook IDs from the notebooks directory.
        
        Returns:
            List of notebook IDs (without .ipynb extension).
        """
        notebooks = []
        if self.notebooks_dir.exists():
            for nb_file in self.notebooks_dir.glob("ex*.ipynb"):
                # Extract notebook ID (filename without extension)
                notebooks.append(nb_file.stem)
        return notebooks

    def select_by_construct(self, constructs: list[str]) -> list[str]:
        """Select exercises by construct.
        
        Args:
            constructs: List of construct names.
            
        Returns:
            List of exercise IDs.
            
        Raises:
            ValueError: If no constructs provided or invalid construct.
        """
        if not constructs:
            raise ValueError("At least one construct must be specified")
        
        # Validate all constructs
        for construct in constructs:
            if not validate_construct_name(construct):
                raise ValueError(f"Invalid construct: {construct}")
        
        exercises = []
        # Look in exercises/construct/type/exercise structure
        for construct in constructs:
            construct_dir = self.exercises_dir / construct
            if construct_dir.exists():
                # Find all exercise directories under this construct
                for type_dir in construct_dir.iterdir():
                    if type_dir.is_dir():
                        for ex_dir in type_dir.iterdir():
                            if ex_dir.is_dir() and ex_dir.name.startswith("ex"):
                                exercises.append(ex_dir.name)
        
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
        if not types:
            raise ValueError("At least one type must be specified")
        
        # Validate all types
        for type_name in types:
            if not validate_type_name(type_name):
                raise ValueError(f"Invalid type: {type_name}")
        
        exercises = []
        # Look in exercises/construct/type/exercise structure
        for construct_dir in self.exercises_dir.iterdir():
            if construct_dir.is_dir():
                for type_dir in construct_dir.iterdir():
                    if type_dir.is_dir() and type_dir.name in types:
                        for ex_dir in type_dir.iterdir():
                            if ex_dir.is_dir() and ex_dir.name.startswith("ex"):
                                exercises.append(ex_dir.name)
        
        return sorted(set(exercises))

    def select_by_construct_and_type(
        self, constructs: list[str], types: list[str]
    ) -> list[str]:
        """Select exercises by construct AND type.
        
        Args:
            constructs: List of construct names.
            types: List of exercise types.
            
        Returns:
            List of exercise IDs matching both criteria.
        """
        # Validate inputs
        for construct in constructs:
            if not validate_construct_name(construct):
                raise ValueError(f"Invalid construct: {construct}")
        for type_name in types:
            if not validate_type_name(type_name):
                raise ValueError(f"Invalid type: {type_name}")
        
        exercises = []
        # Look in exercises/construct/type/exercise structure
        for construct in constructs:
            construct_dir = self.exercises_dir / construct
            if construct_dir.exists():
                for type_name in types:
                    type_dir = construct_dir / type_name
                    if type_dir.exists():
                        for ex_dir in type_dir.iterdir():
                            if ex_dir.is_dir() and ex_dir.name.startswith("ex"):
                                exercises.append(ex_dir.name)
        
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
        
        # Get all available notebooks
        available = self._get_all_notebooks()
        
        # Validate each notebook exists
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
        
        # Get all notebooks and filter by pattern
        all_notebooks = self._get_all_notebooks()
        matching = [nb for nb in all_notebooks if fnmatch.fnmatch(nb, pattern)]
        
        return sorted(matching)
