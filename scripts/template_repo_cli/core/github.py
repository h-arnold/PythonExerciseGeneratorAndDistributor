"""GitHub operations."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class GitHubClient:
    """GitHub operations client."""

    def __init__(self, dry_run: bool = False):
        """Initialize GitHub client.
        
        Args:
            dry_run: If True, don't execute commands.
        """
        self.dry_run = dry_run

    def build_create_command(
        self,
        repo_name: str,
        public: bool = True,
        template: bool = True,
        org: str | None = None,
        description: str | None = None,
    ) -> list[str]:
        """Build gh repo create command.
        
        Args:
            repo_name: Repository name.
            public: Whether repository should be public.
            template: Whether to mark as template repository.
            org: Organization name (if creating in org).
            description: Repository description.
            
        Returns:
            Command as list of strings.
        """
        cmd = ["gh", "repo", "create"]
        
        # Add repo name (with org prefix if specified)
        if org:
            cmd.append(f"{org}/{repo_name}")
        else:
            cmd.append(repo_name)
        
        # Add visibility flag
        if public:
            cmd.append("--public")
        else:
            cmd.append("--private")
        
        # Add template flag
        if template:
            cmd.append("--template")
        
        # Add description if provided
        if description:
            cmd.extend(["--description", description])
        
        return cmd

    def execute_command(self, cmd: list[str]) -> dict[str, Any]:
        """Execute a gh command.
        
        Args:
            cmd: Command as list of strings.
            
        Returns:
            Dictionary with 'success' and optional 'output', 'error'.
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
            }
        except (OSError, subprocess.SubprocessError) as e:
            return {"success": False, "error": str(e)}

    def check_gh_installed(self) -> bool:
        """Check if gh CLI is installed.
        
        Returns:
            True if installed, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gh", "--version"], capture_output=True, check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_authentication(self) -> bool:
        """Check gh authentication status.
        
        Returns:
            True if authenticated, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def parse_json_output(self, output: str) -> dict:
        """Parse JSON output from gh.
        
        Args:
            output: JSON string.
            
        Returns:
            Parsed dictionary.
            
        Raises:
            ValueError: If output is not valid JSON.
        """
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

    def create_repository(
        self, repo_name: str, workspace: Path, push: bool = False
    ) -> dict[str, Any]:
        """Create a GitHub repository.
        
        Args:
            repo_name: Repository name.
            workspace: Workspace directory.
            push: Whether to push initial commit.
            
        Returns:
            Result dictionary.
        """
        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "Dry run - no repository created",
            }
        
        # Build create command
        cmd = self.build_create_command(repo_name)
        
        # Execute command
        result = self.execute_command(cmd)
        
        # If push requested and creation successful
        if push and result["success"]:
            # Initialize git, commit, and push
            self.init_git_repo(workspace)
            self.commit_files(workspace, "Initial commit")
            # Push would require knowing the remote URL
        
        return result

    def init_git_repo(self, workspace: Path) -> None:
        """Initialize git repository.
        
        Args:
            workspace: Workspace directory.
        """
        subprocess.run(
            ["git", "init"], cwd=workspace, capture_output=True, check=True
        )

    def commit_files(self, workspace: Path, message: str) -> None:
        """Commit files.
        
        Args:
            workspace: Workspace directory.
            message: Commit message.
            
        Raises:
            RuntimeError: If git user configuration is missing.
        """
        # Check if git is configured
        user_name = subprocess.run(
            ["git", "config", "user.name"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        user_email = subprocess.run(
            ["git", "config", "user.email"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if not user_name.stdout.strip() or not user_email.stdout.strip():
            raise RuntimeError(
                "Git user configuration is missing. "
                "Please configure git with 'git config --global user.name' "
                "and 'git config --global user.email'"
            )
        
        # Add all files
        subprocess.run(
            ["git", "add", "."], cwd=workspace, capture_output=True, check=True
        )
        
        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=workspace,
            capture_output=True,
            check=True,
        )

    def push_to_remote(self, workspace: Path, remote_url: str) -> None:
        """Push to remote.
        
        Args:
            workspace: Workspace directory.
            remote_url: Remote repository URL.
        """
        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=workspace,
            capture_output=True,
            check=True,
        )
        
        # Push
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=workspace,
            capture_output=True,
            check=True,
        )
