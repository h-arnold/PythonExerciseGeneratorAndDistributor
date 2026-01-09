"""File collector."""

from __future__ import annotations

from pathlib import Path


class FileCollector:
    """Collect files for exercises."""

    def __init__(self, repo_root: Path):
        """Initialize collector.
        
        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root = repo_root
        self.notebooks_dir = repo_root / "notebooks"
        self.tests_dir = repo_root / "tests"
        self.exercises_dir = repo_root / "exercises"

    def _check_type_dir_for_metadata(
        self, type_dir: Path, exercise_id: str
    ) -> Path | None:
        """Check a type directory for exercise metadata.
        
        Args:
            type_dir: Type directory to search.
            exercise_id: Exercise ID to find.
            
        Returns:
            Path to README.md if found, None otherwise.
        """
        ex_dir = type_dir / exercise_id
        if ex_dir.exists():
            readme = ex_dir / "README.md"
            if readme.exists():
                return readme
        return None

    def _check_nested_metadata(self, exercise_id: str) -> Path | None:
        """Check for metadata in nested construct/type structure.
        
        Args:
            exercise_id: The exercise ID.
            
        Returns:
            Path to metadata file if found, None otherwise.
        """
        for construct_dir in self.exercises_dir.iterdir():
            if not construct_dir.is_dir():
                continue
            
            for type_dir in construct_dir.iterdir():
                if not type_dir.is_dir():
                    continue
                
                readme = self._check_type_dir_for_metadata(type_dir, exercise_id)
                if readme:
                    return readme
        
        return None

    def _find_metadata_path(self, exercise_id: str) -> Path | None:
        """Find metadata path for an exercise.
        
        Searches through exercises/construct/type/exercise_id/README.md
        
        Args:
            exercise_id: The exercise ID.
            
        Returns:
            Path to metadata file if found, None otherwise.
        """
        # Search through nested structure first
        nested_path = self._check_nested_metadata(exercise_id)
        if nested_path:
            return nested_path
        
        # Also check for flat structure (e.g., exercises/ex001_sanity/README.md)
        flat_path = self.exercises_dir / exercise_id / "README.md"
        if flat_path.exists():
            return flat_path
        
        return None

    def collect_files(self, exercise_id: str) -> dict[str, Path]:
        """Collect all files for an exercise.
        
        Args:
            exercise_id: The exercise ID (e.g., 'ex001_sanity').
            
        Returns:
            Dictionary with keys: 'notebook', 'solution', 'test', 'metadata'.
            
        Raises:
            FileNotFoundError: If notebook is not found.
            ValueError: If exercise_id is empty.
        """
        if not exercise_id:
            raise ValueError("Exercise ID cannot be empty")
        
        files = {}
        
        # Student notebook (required)
        notebook_path = self.notebooks_dir / f"{exercise_id}.ipynb"
        if not notebook_path.exists():
            raise FileNotFoundError(f"Student notebook not found: {exercise_id}")
        files["notebook"] = notebook_path
        
        # Solution notebook (required)
        solution_path = self.notebooks_dir / "solutions" / f"{exercise_id}.ipynb"
        if not solution_path.exists():
            raise FileNotFoundError(f"Solution notebook not found: {exercise_id}")
        files["solution"] = solution_path
        
        # Test file (required)
        test_path = self.tests_dir / f"test_{exercise_id}.py"
        if not test_path.exists():
            raise FileNotFoundError(f"Test file not found: {exercise_id}")
        files["test"] = test_path
        
        # Metadata (optional)
        metadata_path = self._find_metadata_path(exercise_id)
        files["metadata"] = metadata_path  # May be None
        
        return files

    def collect_multiple(self, exercise_ids: list[str]) -> dict[str, dict[str, Path]]:
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
