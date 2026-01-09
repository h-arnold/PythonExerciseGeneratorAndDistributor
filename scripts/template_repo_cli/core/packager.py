"""Template packager."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from scripts.template_repo_cli.utils.filesystem import (
    create_directory_structure,
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
        files: dict[str, dict[str, Path]],
        include_solutions: bool = True,
    ) -> None:
        """Copy exercise files to workspace.
        
        Args:
            workspace: Workspace directory.
            files: Dictionary mapping exercise ID to file paths.
            include_solutions: Whether to include solution notebooks.
        """
        for exercise_id, file_dict in files.items():
            # Copy student notebook
            if "notebook" in file_dict and file_dict["notebook"]:
                dest = workspace / "notebooks" / f"{exercise_id}.ipynb"
                safe_copy_file(file_dict["notebook"], dest)
            
            # Copy solution notebook if requested
            if include_solutions and "solution" in file_dict and file_dict["solution"]:
                dest = workspace / "notebooks" / "solutions" / f"{exercise_id}.ipynb"
                safe_copy_file(file_dict["solution"], dest)
            
            # Copy test file
            if "test" in file_dict and file_dict["test"]:
                dest = workspace / "tests" / f"test_{exercise_id}.py"
                safe_copy_file(file_dict["test"], dest)
            
            # Copy metadata if it exists
            if "metadata" in file_dict and file_dict["metadata"]:
                # Preserve structure: exercises/construct/type/exercise_id/README.md
                # But for template, we can simplify to exercises/exercise_id/README.md
                dest = workspace / "exercises" / exercise_id / "README.md"
                safe_copy_file(file_dict["metadata"], dest)

    def copy_template_base_files(self, workspace: Path) -> None:
        """Copy base template files.
        
        Args:
            workspace: Workspace directory.
        """
        if not self.template_files_dir.exists():
            raise FileNotFoundError(
                f"Template files directory not found: {self.template_files_dir}"
            )
        
        # Copy pyproject.toml
        src = self.template_files_dir / "pyproject.toml"
        if src.exists():
            safe_copy_file(src, workspace / "pyproject.toml")
        
        # Copy pytest.ini
        src = self.template_files_dir / "pytest.ini"
        if src.exists():
            safe_copy_file(src, workspace / "pytest.ini")
        
        # Copy .gitignore
        src = self.template_files_dir / ".gitignore"
        if src.exists():
            safe_copy_file(src, workspace / ".gitignore")
        
        # Copy .vscode directory
        src = self.template_files_dir / ".vscode"
        if src.exists():
            safe_copy_directory(src, workspace / ".vscode")
        
        # Copy .github directory
        src = self.template_files_dir / ".github"
        if src.exists():
            safe_copy_directory(src, workspace / ".github")
        
        # Copy INSTRUCTIONS.md
        src = self.template_files_dir / "INSTRUCTIONS.md"
        if src.exists():
            safe_copy_file(src, workspace / "INSTRUCTIONS.md")
        
        # Copy notebook_grader.py to tests/
        src = self.repo_root / "tests" / "notebook_grader.py"
        if src.exists():
            dest = workspace / "tests" / "notebook_grader.py"
            safe_copy_file(src, dest)
        
        # Create tests/__init__.py
        (workspace / "tests" / "__init__.py").touch()

    def generate_readme(
        self, workspace: Path, template_name: str, exercises: list[str]
    ) -> None:
        """Generate README file.
        
        Args:
            workspace: Workspace directory.
            template_name: Name of the template.
            exercises: List of exercise IDs.
        """
        # Read template
        template_path = self.template_files_dir / "README.md.template"
        if template_path.exists():
            template_content = template_path.read_text()
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
        readme_path.write_text(content)

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
            workspace / "tests" / "notebook_grader.py",
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

    def cleanup(self, workspace: Path) -> None:
        """Clean up workspace.
        
        Args:
            workspace: Workspace directory to remove.
        """
        if workspace.exists():
            shutil.rmtree(workspace)
