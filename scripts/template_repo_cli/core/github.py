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
        template_repo: str | None = None,
        org: str | None = None,
        description: str | None = None,
        source_path: str | None = None,
    ) -> list[str]:
        """Build gh repo create command.
        
        Args:
            repo_name: Repository name.
            public: Whether repository should be public.
            template_repo: Optional template repository (owner/name) to use as argument
                to the --template flag used to clone from an existing template.
            org: Organization name (if creating in org).
            description: Repository description.
            source_path: Path to local source directory to push to the repository.
            
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
        
        # Add template flag only when a source template repository is specified
        if template_repo:
            cmd.extend(["--template", template_repo])
        
        # Add description if provided
        if description:
            cmd.extend(["--description", description])
        
        # Add source path and push flag if source is provided
        if source_path:
            cmd.extend(["--source", source_path, "--push"])
        
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

    def check_scopes(self, required_scopes: list[str] | None = None) -> dict[str, Any]:
        """Check if current authentication has required scopes.
        
        Args:
            required_scopes: List of required scopes (e.g., ['repo']). 
                If None, defaults to ['repo'].
        
        Returns:
            Dictionary with:
                - 'authenticated': bool, whether authenticated at all
                - 'has_scopes': bool, whether all required scopes are present
                - 'scopes': list of strings, current scopes (empty if not authenticated)
                - 'missing_scopes': list of strings, scopes that are missing
        """
        if required_scopes is None:
            required_scopes = ["repo"]
        
        result = {
            "authenticated": False,
            "has_scopes": False,
            "scopes": [],
            "missing_scopes": required_scopes.copy(),
        }
        
        try:
            # Run gh auth status and capture stderr (where scopes are printed)
            auth_result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            # Check if authenticated
            if auth_result.returncode != 0:
                return result
            
            result["authenticated"] = True
            
            # Parse stderr to extract scopes
            # Format: "  - Token scopes: 'scope1', 'scope2', 'scope3'"
            output = auth_result.stderr + auth_result.stdout
            for line in output.split("\n"):
                if "Token scopes:" in line:
                    # Extract the scopes part after "Token scopes:"
                    scopes_part = line.split("Token scopes:", 1)[1].strip()
                    # Remove quotes and split by comma
                    scopes = [
                        s.strip().strip("'").strip('"')
                        for s in scopes_part.split(",")
                        if s.strip()
                    ]
                    result["scopes"] = scopes
                    break
            
            # Check if all required scopes are present
            missing = [s for s in required_scopes if s not in result["scopes"]]
            result["missing_scopes"] = missing
            result["has_scopes"] = len(missing) == 0
            
            return result
            
        except (FileNotFoundError, OSError):
            return result

    def parse_json_output(self, output: str) -> dict[str, Any]:
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
        self,
        repo_name: str,
        workspace: Path,
        *,
        public: bool = True,
        template: bool = True,
        template_repo: str | None = None,
        org: str | None = None,
        description: str | None = None,
        skip_git_operations: bool = False,
    ) -> dict[str, Any]:
        """Create a GitHub repository.
        
        Args:
            repo_name: Repository name.
            workspace: Workspace directory containing files to push.
            public: Whether repository should be public.
            template: Whether to mark the repository as a template after creation.
            template_repo: Optional template repository to base the new repository on.
            org: Organization name to create the repository in.
            description: Repository description used for gh command.
            skip_git_operations: Skip git init/commit (for retries).
            
        Returns:
            Result dictionary.
        """
        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "Dry run - no repository created",
            }
        
        # Only do git operations on first attempt
        if not skip_git_operations:
            # Initialize git repository in workspace (required for --source flag)
            self.init_git_repo(workspace)
            
            # Commit files (required for --push flag)
            self.commit_files(workspace, "Initial commit")
        
        # Build create command with workspace as source
        cmd = self.build_create_command(
            repo_name,
            public=public,
            template_repo=template_repo,
            org=org,
            description=description,
            source_path=str(workspace),
        )
        
        # Execute command (this will create repo and push files)
        result = self.execute_command(cmd)
        
        # Mark repository as a template if requested
        if result["success"] and template:
            template_result = self.mark_repository_as_template(repo_name, org)
            if not template_result["success"]:
                return {
                    "success": False,
                    "error": template_result.get("error", "Failed to mark repository as template"),
                    "output": template_result.get("output"),
                    "returncode": template_result.get("returncode"),
                }
        
        return result

    def mark_repository_as_template(
        self, repo_name: str, org: str | None = None
    ) -> dict[str, Any]:
        """Mark an existing repository as a template.
        
        Args:
            repo_name: Repository name.
            org: Organization name (if None, uses authenticated user).
            
        Returns:
            Result dictionary.
        """
        # If no org specified, get the authenticated user
        if org:
            repo_ref = f"{org}/{repo_name}"
        else:
            # Get authenticated user
            user_result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                check=False,
            )
            if user_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get authenticated user: {user_result.stderr}",
                }
            username = user_result.stdout.strip()
            repo_ref = f"{username}/{repo_name}"
        
        cmd = ["gh", "repo", "edit", repo_ref, "--template"]
        return self.execute_command(cmd)

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
            RuntimeError: If git user configuration is missing or commit fails.
        """
        # Check if git is configured globally
        user_name = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        user_email = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # If global config is missing, set local config in workspace
        if not user_name.stdout.strip():
            subprocess.run(
                ["git", "config", "user.name", "Template CLI"],
                cwd=workspace,
                capture_output=True,
                check=True,
            )
        
        if not user_email.stdout.strip():
            subprocess.run(
                ["git", "config", "user.email", "template-cli@example.com"],
                cwd=workspace,
                capture_output=True,
                check=True,
            )
        
        # Add all files
        add_result = subprocess.run(
            ["git", "add", "."], 
            cwd=workspace, 
            capture_output=True, 
            text=True,
            check=False,
        )
        if add_result.returncode != 0:
            raise RuntimeError(
                f"git add failed:\n{add_result.stderr}"
            )
        
        # Commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        if commit_result.returncode != 0:
            raise RuntimeError(
                f"git commit failed:\nstdout: {commit_result.stdout}\nstderr: {commit_result.stderr}"
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
