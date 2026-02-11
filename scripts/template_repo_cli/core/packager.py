"""Template packager, including Classroom autograding support files."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from scripts.template_repo_cli.core.collector import ExerciseFiles
from scripts.template_repo_cli.utils.filesystem import (
    safe_copy_directory,
    safe_copy_file,
)


class TemplatePackager:
    """Package templates for GitHub."""

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
        # Create a temporary directory
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
        for exercise_id, file_dict in files.items():
            # Copy student notebook
            if file_dict.get("notebook"):
                dest = workspace / "notebooks" / f"{exercise_id}.ipynb"
                safe_copy_file(file_dict["notebook"], dest)

            # Copy test file
            if file_dict.get("test"):
                dest = workspace / "tests" / f"test_{exercise_id}.py"
                safe_copy_file(file_dict["test"], dest)

    def _copy_directory(self, dirname: str, workspace: Path) -> None:
        """Copy a template directory if it exists.

        Args:
            dirname: Name of the directory to copy.
            workspace: Destination workspace directory.
        """
        src = self.template_files_dir / dirname
        if src.exists():
            safe_copy_directory(src, workspace / dirname)

    def copy_template_base_files(self, workspace: Path) -> None:
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

        file_pairs = [
            (
                self.template_files_dir / "pyproject.toml",
                workspace / "pyproject.toml",
            ),
            (
                self.template_files_dir / "pytest.ini",
                workspace / "pytest.ini",
            ),
            (
                self.template_files_dir / ".gitignore",
                workspace / ".gitignore",
            ),
            (
                self.template_files_dir / "INSTRUCTIONS.md",
                workspace / "INSTRUCTIONS.md",
            ),
            (
                self.repo_root / "tests" / "notebook_grader.py",
                workspace / "tests" / "notebook_grader.py",
            ),
            (
                self.repo_root / "scripts" / "build_autograde_payload.py",
                workspace / "scripts" / "build_autograde_payload.py",
            ),
            (
                self.repo_root / "tests" / "autograde_plugin.py",
                workspace / "tests" / "autograde_plugin.py",
            ),
        ]

        for src, dest in file_pairs:
            if src.exists():
                safe_copy_file(src, dest)

        # Copy directories
        self._copy_directory(".devcontainer", workspace)
        self._copy_directory(".github", workspace)

    def generate_readme(self, workspace: Path, template_name: str, exercises: list[str]) -> None:
        """Generate README file.

        Args:
            workspace: Workspace directory.
            template_name: Name of the template.
            exercises: List of exercise IDs.
        """
        # Read template
        template_path = self.template_files_dir / "README.md.template"
        if template_path.exists():
            template_content = template_path.read_text(encoding="utf-8")
        else:
            # Fallback template
            template_content = "# {TEMPLATE_NAME}\n\n{EXERCISE_LIST}\n"

        # Generate exercise list
        exercise_list = "\n".join([f"- {ex}" for ex in sorted(exercises)])

        # Replace placeholders
        content = template_content.replace("{TEMPLATE_NAME}", template_name)
        content = content.replace("{EXERCISE_LIST}", exercise_list)

        # Write README
        readme_path = workspace / "README.md"
        readme_path.write_text(content, encoding="utf-8")

    def validate_package(self, workspace: Path) -> bool:
        """Validate package integrity.

        Args:
            workspace: Workspace directory.

        Returns:
            True if package is valid, False otherwise.
        """
        # Check required files exist
        required_files = [
            workspace / "pyproject.toml",
            workspace / "pytest.ini",
            workspace / "README.md",
            workspace / "scripts" / "build_autograde_payload.py",
            workspace / "tests" / "autograde_plugin.py",
            workspace / ".github" / "workflows" / "classroom.yml",
        ]

        for required_file in required_files:
            if not required_file.exists():
                return False

        # Check required directories exist
        required_dirs = [
            workspace / "notebooks",
            workspace / "tests",
        ]

        for required_dir in required_dirs:
            if not required_dir.exists() or not required_dir.is_dir():
                return False

        return True

    def _is_safe_workspace(self, workspace: Path) -> bool:
        """Check whether the given path looks like a valid temporary workspace.

        A safe workspace is:
        - Located inside the system temporary directory, and
        - Has the expected prefix used by create_workspace(), and
        - Is an existing directory.
        """
        # Normalize and resolve paths to avoid traversal tricks.
        workspace_path = Path(workspace).resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()

        try:
            workspace_path.relative_to(temp_root)
        except ValueError:
            # Workspace is not inside the system temp directory.
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

        # Only remove directories that look like workspaces created by
        # create_workspace(). This helps prevent accidental deletion of
        # important non-temporary directories.
        if not self._is_safe_workspace(workspace_path):
            return

        if workspace_path.exists():
            shutil.rmtree(workspace_path)
