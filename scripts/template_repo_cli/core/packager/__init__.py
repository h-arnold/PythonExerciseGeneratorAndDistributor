"""Template packager, including Classroom autograding support files."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from scripts.template_repo_cli.core.collector import ExerciseFiles
from scripts.template_repo_cli.utils.filesystem import safe_copy_directory, safe_copy_file

from . import _helpers, _readme


class TemplatePackager:
    """Package templates for GitHub."""

    _CONSTRUCT_DIR_DEPTH = 1
    _EXERCISE_DIR_DEPTH = 2
    _SUBDIR_INDEX = 2

    COPY_EXCLUDE_PATTERNS: tuple[str, ...] = (
        "__pycache__",
        "*.pyc",
        "test_*.py",
        "*_test.py",
    )
    EXERCISE_TEST_COPY_EXCLUDE_PATTERNS: tuple[str, ...] = (
        "__pycache__",
        "*.pyc",
        "test_repo_*.py",
    )

    REQUIRED_TEST_FILES: tuple[str, ...] = (
        "__init__.py",
        "autograde_plugin.py",
        "helpers.py",
        "test_autograde_plugin.py",
        "test_build_autograde_payload.py",
    )

    REQUIRED_TEST_DIRECTORIES: tuple[str, ...] = ("exercise_framework",)

    REQUIRED_PACKAGE_DIRECTORIES: tuple[str, ...] = (
        "exercise_metadata",
        "exercise_runtime_support",
    )

    FORBIDDEN_AUTHORING_FILENAMES: tuple[str, ...] = ("solution.ipynb",)
    REQUIRED_SCRIPTS: tuple[str, ...] = (
        "build_autograde_payload.py",
        "jupyter_watchdog.py",
    )
    _ALLOWED_EXERCISE_SUBDIRECTORIES: tuple[str, ...] = (
        "notebooks",
        "tests",
        "additional-resources",
    )
    _CONSTRUCT_RESOURCE_DIRNAME = "additional-resources"
    _STUDENT_NOTEBOOK_FILENAME = "student.ipynb"
    _EXERCISE_METADATA_FILENAME = "exercise.json"
    _FLATTENED_TEST_GLOB = "test_ex[0-9]*_*.py"

    def __init__(self, repo_root: Path):
        """Initialize packager.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root = repo_root
        self.template_files_dir = repo_root / "template_repo_files"

    def create_workspace(self) -> Path:
        """Create temporary workspace.

        Returns:
            Path to temporary workspace directory.
        """
        temp_dir = tempfile.mkdtemp(prefix="template_repo_")
        return Path(temp_dir)

    def copy_exercise_files(
        self,
        workspace: Path,
        files: dict[str, ExerciseFiles],
    ) -> None:
        """Copy exercise files to workspace.

        Args:
            workspace: Workspace directory.
            files: Dictionary mapping exercise ID to file paths.
        """
        for file_dict in files.values():
            safe_copy_file(
                file_dict["exercise_json"], workspace / file_dict["exercise_json_export"]
            )
            safe_copy_file(file_dict["notebook"], workspace / file_dict["notebook_export"])
            tests_export_dir = workspace / file_dict["tests_export_dir"]
            safe_copy_directory(
                file_dict["test"].parent,
                tests_export_dir,
                ignore_patterns=self.EXERCISE_TEST_COPY_EXCLUDE_PATTERNS,
            )

    def _resolve_exercise_construct(self, exercise_key: str) -> str:
        """Resolve the raw construct slug for an exercise key.

        Args:
            exercise_key: The exercise key.

        Returns:
            The construct string (e.g. "sequence").

        Raises:
            ValueError: If the exercise metadata cannot be read.
        """
        try:
            metadata = _helpers.load_exercise_metadata(self.repo_root, exercise_key)
            construct = metadata.get("construct")
            if not isinstance(construct, str) or not construct.strip():
                raise ValueError("missing or invalid construct metadata")
            return construct
        except ValueError as cause:
            raise ValueError(
                f"Failed to resolve construct for exercise '{exercise_key}': {cause}"
            ) from cause

    def _construct_has_additional_resources(self, construct: str) -> bool:
        """Return whether a construct has an additional-resources folder in the source repo.

        Args:
            construct: Raw construct slug (e.g. "sequence").

        Returns:
            True if the folder exists in the source repo.
        """
        resource_dir = self.repo_root / "exercises" / construct / self._CONSTRUCT_RESOURCE_DIRNAME
        return resource_dir.exists() and resource_dir.is_dir()

    def copy_construct_resources(self, workspace: Path, exercises: list[str]) -> None:
        """Copy construct-level additional-resources folders to the workspace.

        For each unique construct derived from the exercise keys, copies the
        ``additional-resources/`` directory from the source repo into the
        workspace if it exists. Constructs without this folder are silently
        skipped.

        Args:
            workspace: Workspace directory.
            exercises: List of exercise keys.
        """
        constructs: set[str] = set()
        for exercise_key in exercises:
            construct = self._resolve_exercise_construct(exercise_key)
            constructs.add(construct)

        for construct in constructs:
            if not self._construct_has_additional_resources(construct):
                continue
            src = self.repo_root / "exercises" / construct / self._CONSTRUCT_RESOURCE_DIRNAME
            dest = workspace / "exercises" / construct / self._CONSTRUCT_RESOURCE_DIRNAME
            safe_copy_directory(src, dest)

    def _copy_directory(self, dirname: str, workspace: Path) -> None:
        """Copy a template directory if it exists.

        Args:
            dirname: Name of the directory to copy.
            workspace: Destination workspace directory.
        """
        src = self.template_files_dir / dirname
        if src.exists():
            safe_copy_directory(src, workspace / dirname)

    def _get_missing_required_sources(self) -> list[Path]:
        """Return missing source paths required for packaging."""
        tests_source_dir = self.repo_root / "tests"
        required_paths: list[Path] = [
            self.template_files_dir / "pyproject.toml",
            self.template_files_dir / "pytest.ini",
            self.template_files_dir / ".gitignore",
            self.template_files_dir / ".github" / "workflows" / "classroom.yml",
        ]
        required_paths.extend(
            self.repo_root / "scripts" / script for script in self.REQUIRED_SCRIPTS
        )
        required_paths.extend(
            tests_source_dir / required_file for required_file in self.REQUIRED_TEST_FILES
        )
        required_paths.extend(
            tests_source_dir / required_dir for required_dir in self.REQUIRED_TEST_DIRECTORIES
        )
        required_paths.extend(
            self.repo_root / required_dir for required_dir in self.REQUIRED_PACKAGE_DIRECTORIES
        )
        return [path for path in required_paths if not path.exists()]

    def _raise_for_missing_required_sources(self) -> None:
        """Raise with all missing required source paths."""
        missing_paths = self._get_missing_required_sources()
        if not missing_paths:
            return

        missing_list = "\n".join(f"- {path}" for path in missing_paths)
        raise FileNotFoundError(f"Missing required packaging source assets:\n{missing_list}")

    def _required_script_copy_pairs(self, workspace: Path) -> list[tuple[Path, Path]]:
        """Return (source, dest) copy pairs for the required bundled scripts.

        Args:
            workspace: Destination workspace directory.

        Returns:
            List of source/destination path tuples for ``REQUIRED_SCRIPTS``.
        """
        return [
            (self.repo_root / "scripts" / script, workspace / "scripts" / script)
            for script in self.REQUIRED_SCRIPTS
        ]

    def copy_template_base_files(
        self,
        workspace: Path,
    ) -> None:
        """Copy base template files.

        Args:
            workspace: Workspace directory.
        """
        if not self.template_files_dir.exists():
            raise FileNotFoundError(
                "Template files directory missing at"
                f" {self.template_files_dir}. Run the repository setup so"
                " template_repo_files/ is populated before packaging."
            )

        self._raise_for_missing_required_sources()

        file_pairs = [
            (self.template_files_dir / "pyproject.toml", workspace / "pyproject.toml"),
            (self.template_files_dir / "pytest.ini", workspace / "pytest.ini"),
            (self.template_files_dir / ".gitignore", workspace / ".gitignore"),
        ]
        file_pairs.extend(self._required_script_copy_pairs(workspace))

        optional_file_pairs = [
            (self.template_files_dir / "INSTRUCTIONS.md", workspace / "INSTRUCTIONS.md"),
        ]

        tests_source_dir = self.repo_root / "tests"
        tests_dest_dir = workspace / "tests"
        for required_file in self.REQUIRED_TEST_FILES:
            file_pairs.append((tests_source_dir / required_file, tests_dest_dir / required_file))

        for src, dest in file_pairs:
            safe_copy_file(src, dest)

        for src, dest in optional_file_pairs:
            if src.exists():
                safe_copy_file(src, dest)

        for required_dir in self.REQUIRED_TEST_DIRECTORIES:
            safe_copy_directory(
                tests_source_dir / required_dir,
                tests_dest_dir / required_dir,
                ignore_patterns=self.COPY_EXCLUDE_PATTERNS,
            )

        for required_dir in self.REQUIRED_PACKAGE_DIRECTORIES:
            safe_copy_directory(
                self.repo_root / required_dir,
                workspace / required_dir,
                ignore_patterns=self.COPY_EXCLUDE_PATTERNS,
            )

        self._copy_directory(".devcontainer", workspace)
        self._copy_directory(".github", workspace)

    def generate_readme(self, workspace: Path, template_name: str, exercises: list[str]) -> None:
        """Generate README file.

        Args:
            workspace: Workspace directory.
            template_name: Name of the template.
            exercises: List of exercise keys.
        """
        _readme.generate_readme(
            self.repo_root,
            self.template_files_dir,
            workspace,
            template_name,
            exercises,
            self._construct_has_additional_resources,
        )

    def _is_valid_packaged_exercise_path(self, path: Path, exercises_dir: Path) -> bool:
        """Return whether a path fits the packaged exercises tree."""
        relative_parts = path.relative_to(exercises_dir).parts
        part_count = len(relative_parts)

        # Exercise directory or canonical exercise.json metadata file
        if (
            part_count in (self._CONSTRUCT_DIR_DEPTH, self._EXERCISE_DIR_DEPTH) and path.is_dir()
        ) or (
            part_count == self._SUBDIR_INDEX + 1
            and path.is_file()
            and path.name == self._EXERCISE_METADATA_FILENAME
        ):
            return True

        # Construct-level additional-resources directories and their contents.
        # These live at depth 2 (same as exercise dirs) but with a well-known name,
        # so files/folders within them bypass the exercise-subdirectory index check.
        # We accept any file type here because _contains_authoring_only_assets already
        # globally bans solution.ipynb across the whole workspace.
        if part_count >= self._EXERCISE_DIR_DEPTH and (
            relative_parts[self._EXERCISE_DIR_DEPTH - 1] == self._CONSTRUCT_RESOURCE_DIRNAME
        ):
            return True

        # For paths deeper than the subdirectory level, validate inside known subdirectories
        if part_count > self._SUBDIR_INDEX:
            subdirectory = relative_parts[self._SUBDIR_INDEX]
            if subdirectory in self._ALLOWED_EXERCISE_SUBDIRECTORIES:
                if part_count == self._SUBDIR_INDEX + 1:
                    return path.is_dir()
                if subdirectory == "notebooks":
                    return self._is_valid_packaged_notebook_path(path, part_count)
                return self._is_valid_packaged_tests_path(path)

        return False

    def _is_valid_packaged_notebook_path(self, path: Path, part_count: int) -> bool:
        """Return whether a path is the allowed exercise-local student notebook."""
        expected_depth = self._SUBDIR_INDEX + 2
        if part_count != expected_depth:
            return False
        return path.is_file() and path.name == self._STUDENT_NOTEBOOK_FILENAME

    @staticmethod
    def _is_valid_packaged_tests_path(path: Path) -> bool:
        """Return whether a path is valid under the packaged exercise tests subtree."""
        return not (path.is_file() and path.suffix == ".ipynb")

    def _has_invalid_exercises_tree(self, workspace: Path) -> bool:
        """Return whether the packaged exercises tree contains invalid assets."""
        exercises_dir = workspace / "exercises"
        if not exercises_dir.exists():
            return False
        if not exercises_dir.is_dir():
            return True

        for path in exercises_dir.rglob("*"):
            if path.name in self.FORBIDDEN_AUTHORING_FILENAMES:
                return True
            if not self._is_valid_packaged_exercise_path(path, exercises_dir):
                return True

        return False

    def _contains_flattened_mirrors(self, workspace: Path) -> bool:
        """Return whether the workspace contains flattened notebook or test mirrors."""
        if (workspace / "notebooks").exists():
            return True

        tests_dir = workspace / "tests"
        return tests_dir.exists() and any(tests_dir.glob(self._FLATTENED_TEST_GLOB))

    def _contains_authoring_only_assets(self, workspace: Path) -> bool:
        """Return whether a packaged workspace still contains authoring-only assets."""
        if self._contains_flattened_mirrors(workspace):
            return True
        if self._has_invalid_exercises_tree(workspace):
            return True

        return any(
            next(workspace.rglob(filename), None) is not None
            for filename in self.FORBIDDEN_AUTHORING_FILENAMES
        )

    def _has_required_packaged_exercise_metadata(self, workspace: Path) -> bool:
        """Return whether every exported exercise has its canonical metadata file."""
        exercises_dir = workspace / "exercises"
        if not exercises_dir.exists():
            return False

        for exercise_dir in exercises_dir.glob("*/*"):
            if not exercise_dir.is_dir():
                continue
            # Skip construct-level resource directories (e.g. additional-resources)
            if exercise_dir.name == self._CONSTRUCT_RESOURCE_DIRNAME:
                continue
            if not (exercise_dir / "exercise.json").is_file():
                return False

        return True

    def _has_required_packaged_assets(self, workspace: Path) -> bool:
        """Return whether the workspace contains all required packaged surfaces."""
        required_files = [
            workspace / "pyproject.toml",
            workspace / "pytest.ini",
            workspace / "README.md",
            workspace / ".github" / "workflows" / "classroom.yml",
            workspace / "exercise_metadata" / "__init__.py",
        ]
        required_files.extend(
            workspace / "scripts" / script for script in self.REQUIRED_SCRIPTS
        )

        tests_dir = workspace / "tests"
        required_files.extend(
            tests_dir / required_file for required_file in self.REQUIRED_TEST_FILES
        )
        for required_file in required_files:
            if not required_file.exists():
                return False

        required_dirs = [
            workspace / "exercises",
            tests_dir,
            workspace / "exercise_metadata",
        ]
        required_dirs.extend(
            tests_dir / required_dir for required_dir in self.REQUIRED_TEST_DIRECTORIES
        )
        required_dirs.extend(
            workspace / required_dir for required_dir in self.REQUIRED_PACKAGE_DIRECTORIES
        )
        for required_dir in required_dirs:
            if not required_dir.exists() or not required_dir.is_dir():
                return False

        return self._has_required_packaged_exercise_metadata(workspace)

    def validate_package(self, workspace: Path) -> bool:
        """Validate package integrity.

        Args:
            workspace: Workspace directory.

        Returns:
            True if package is valid, False otherwise.
        """
        if self._contains_authoring_only_assets(workspace):
            return False
        return self._has_required_packaged_assets(workspace)

    def _is_safe_workspace(self, workspace: Path) -> bool:
        """Check whether the given path looks like a valid temporary workspace."""
        workspace_path = Path(workspace).resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()

        try:
            workspace_path.relative_to(temp_root)
        except ValueError:
            return False

        if not workspace_path.name.startswith("template_repo_"):
            return False

        return workspace_path.is_dir()

    def cleanup(self, workspace: Path) -> None:
        """Clean up workspace.

        Args:
            workspace: Workspace directory to remove.
        """
        workspace_path = Path(workspace)
        if not self._is_safe_workspace(workspace_path):
            return

        if workspace_path.exists():
            shutil.rmtree(workspace_path)
