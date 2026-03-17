"""Template packager, including Classroom autograding support files."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from exercise_runtime_support.exercise_catalogue import (
    get_catalogue_snapshot_path,
    load_catalogue_snapshot,
    write_catalogue_snapshot,
)
from scripts.template_repo_cli.core.collector import ExerciseFiles
from scripts.template_repo_cli.utils.filesystem import safe_copy_directory, safe_copy_file


class TemplatePackager:
    """Package templates for GitHub."""

    COPY_EXCLUDE_PATTERNS: tuple[str, ...] = (
        "__pycache__",
        "*.pyc",
        "test_*.py",
        "*_test.py",
    )

    REQUIRED_TEST_FILES: tuple[str, ...] = (
        "__init__.py",
        "autograde_plugin.py",
        "helpers.py",
        "notebook_grader.py",
        "test_autograde_plugin.py",
        "test_build_autograde_payload.py",
    )

    REQUIRED_TEST_DIRECTORIES: tuple[str, ...] = (
        "exercise_expectations",
        "exercise_framework",
        "student_checker",
    )

    REQUIRED_PACKAGE_DIRECTORIES: tuple[str, ...] = ("exercise_runtime_support",)

    FORBIDDEN_AUTHORING_FILENAMES: tuple[str, ...] = (
        "exercise.json",
        "solution.ipynb",
    )

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
            safe_copy_file(file_dict["notebook"], workspace / file_dict["notebook_export"])
            safe_copy_file(file_dict["test"], workspace / file_dict["test_export"])

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
            self.repo_root / "scripts" / "build_autograde_payload.py",
        ]
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

    def copy_template_base_files(
        self,
        workspace: Path,
        selected_exercise_keys: set[str] | None = None,
    ) -> None:
        """Copy base template files.

        Args:
            workspace: Workspace directory.
            selected_exercise_keys: Optional set of exercise keys to keep in the
                packaged runtime catalogue snapshot.
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
            (
                self.repo_root / "scripts" / "build_autograde_payload.py",
                workspace / "scripts" / "build_autograde_payload.py",
            ),
        ]

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

        write_catalogue_snapshot(
            get_catalogue_snapshot_path(workspace / "exercise_runtime_support"),
            exercise_keys=selected_exercise_keys,
        )

        self._copy_directory(".devcontainer", workspace)
        self._copy_directory(".github", workspace)

    def generate_readme(self, workspace: Path, template_name: str, exercises: list[str]) -> None:
        """Generate README file.

        Args:
            workspace: Workspace directory.
            template_name: Name of the template.
            exercises: List of exercise IDs.
        """
        template_path = self.template_files_dir / "README.md.template"
        if template_path.exists():
            template_content = template_path.read_text(encoding="utf-8")
        else:
            template_content = "# {TEMPLATE_NAME}\n\n{EXERCISE_LIST}\n"

        exercise_list = "\n".join(f"- {ex}" for ex in sorted(exercises))
        content = template_content.replace("{TEMPLATE_NAME}", template_name)
        content = content.replace("{EXERCISE_LIST}", exercise_list)
        readme_path = workspace / "README.md"
        readme_path.write_text(content, encoding="utf-8")

    def _contains_authoring_only_assets(self, workspace: Path) -> bool:
        """Return whether a packaged workspace still contains authoring-only assets."""
        if (workspace / "exercises").exists():
            return True

        return any(
            next(workspace.rglob(filename), None) is not None
            for filename in self.FORBIDDEN_AUTHORING_FILENAMES
        )

    def validate_package(self, workspace: Path) -> bool:
        """Validate package integrity.

        Args:
            workspace: Workspace directory.

        Returns:
            True if package is valid, False otherwise.
        """
        if self._contains_authoring_only_assets(workspace):
            return False

        snapshot_path = get_catalogue_snapshot_path(workspace / "exercise_runtime_support")
        required_files = [
            workspace / "pyproject.toml",
            workspace / "pytest.ini",
            workspace / "README.md",
            workspace / "scripts" / "build_autograde_payload.py",
            workspace / ".github" / "workflows" / "classroom.yml",
            snapshot_path,
        ]

        tests_dir = workspace / "tests"
        required_files.extend(
            tests_dir / required_file for required_file in self.REQUIRED_TEST_FILES
        )
        for required_file in required_files:
            if not required_file.exists():
                return False

        required_dirs = [workspace / "notebooks", tests_dir]
        required_dirs.extend(
            tests_dir / required_dir for required_dir in self.REQUIRED_TEST_DIRECTORIES
        )
        required_dirs.extend(
            workspace / required_dir for required_dir in self.REQUIRED_PACKAGE_DIRECTORIES
        )
        for required_dir in required_dirs:
            if not required_dir.exists() or not required_dir.is_dir():
                return False

        try:
            load_catalogue_snapshot(snapshot_path)
        except (OSError, TypeError, ValueError, KeyError):
            return False

        return True

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
