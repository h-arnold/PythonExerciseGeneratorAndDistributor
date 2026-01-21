"""GitHub operations."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Literal

INTEGRATION_PERMISSION_ERROR_MARKERS = (
    "resource not accessible by integration",
    "createrepository",
)

AUTH_TOKEN_HINT_MARKERS = (
    "current github authentication token cannot create repositories",
    "unset github_token before running gh auth login",
)


def run_subprocess(
    cmd: list[str],
    *,
    cwd: Path | str | None = None,
    output_mode: Literal["capture", "stream", "silent"] = "capture",
    check: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess command with consistent handling.

    This wrapper provides a DRY way to execute subprocess commands with different
    output handling modes.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory for the command.
        output_mode: How to handle output:
            - "capture": Capture both stdout and stderr (default).
            - "stream": Stream stdout to console, capture stderr only.
              Note: result.stdout will be None in this mode.
            - "silent": Suppress all output (capture_output=False, no pipes).
              Note: Both result.stdout and result.stderr will be None in this mode.
        check: If True, raise CalledProcessError on non-zero exit.
        text: If True, decode output as text (default True).

    Returns:
        CompletedProcess instance with returncode, stdout, stderr.
        Note: stdout/stderr may be None depending on output_mode.

    Raises:
        subprocess.CalledProcessError: If check=True and command fails.
    """
    if output_mode == "capture":
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=text, check=check)
    elif output_mode == "stream":
        # Stream stdout to user for visibility, capture stderr for error handling
        # Note: stdout will be None in the returned CompletedProcess
        return subprocess.run(cmd, cwd=cwd, capture_output=False, stderr=subprocess.PIPE, text=text, check=check)
    elif output_mode == "silent":
        # Don't capture or stream anything
        # Note: Both stdout and stderr will be None in the returned CompletedProcess
        return subprocess.run(cmd, cwd=cwd, capture_output=False, text=text, check=check)
    else:
        raise ValueError(f"Invalid output_mode: {output_mode}")


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
            # Stream stdout to user for visibility and interactive prompts
            result = run_subprocess(cmd, output_mode="stream", check=False)

            return {
                "success": result.returncode == 0,
                "output": "",
                "error": result.stderr if result.returncode != 0 else "",
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
            result = run_subprocess(["gh", "--version"], check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_authentication(self) -> bool:
        """Check gh authentication status.

        Returns:
            True if authenticated, False otherwise.
        """
        try:
            result = run_subprocess(["gh", "auth", "status"], check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_repository_exists(self, repo_name: str, org: str | None = None) -> bool:
        """Check if a repository exists on GitHub.

        Args:
            repo_name: Repository name.
            org: Organization name (if None, checks user's repositories).

        Returns:
            True if repository exists, False otherwise.
        """
        if self.dry_run:
            # Avoid network calls in dry-run; assume absent so callers can decide how to proceed
            return False

        try:
            repo_ref = f"{org}/{repo_name}" if org else repo_name
            result = run_subprocess(
                ["gh", "repo", "view", repo_ref], check=False)
            return result.returncode == 0
        except (FileNotFoundError, OSError):
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
            auth_result = run_subprocess(["gh", "auth", "status"], check=False)

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
                        s.strip().strip("'").strip('"') for s in scopes_part.split(",") if s.strip()
                    ]
                    result["scopes"] = scopes
                    break

            # Check if all required scopes are present
            missing = [s for s in required_scopes if s not in result["scopes"]]
            result["missing_scopes"] = missing
            result["has_scopes"] = len(missing) == 0

            return result

        except OSError:
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

        if not result["success"] and self._should_retry_with_fresh_auth(result):
            # Return error with instructions for the user to resolve authentication
            return {
                "success": False,
                "error": (
                    "Authentication failed: The GITHUB_TOKEN or GH_TOKEN environment variable is "
                    "blocking authentication.\n\n"
                    "To resolve this, run:\n"
                    "  unset GITHUB_TOKEN\n"
                    "  unset GH_TOKEN\n"
                    "  gh auth login\n\n"
                    "Then try again."
                ),
                "output": result.get("output", ""),
                "returncode": result.get("returncode", 1),
            }

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

    def force_update_repository(
        self,
        repo_name: str,
        workspace: Path,
        *,
        public: bool = True,
        template: bool = True,
        template_repo: str | None = None,
        org: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Force update a repository by deleting and recreating it.

        Args:
            repo_name: Repository name.
            workspace: Workspace directory containing files to push.
            public: Whether repository should be public.
            template: Whether to mark the repository as a template after creation.
            template_repo: Optional template repository to base the new repository on.
            org: Organization name to create the repository in.
            description: Repository description used for gh command.

        Returns:
            Result dictionary.
        """
        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "Dry run - repository would be deleted and recreated",
            }

        # Build repository reference
        if org:
            repo_ref = f"{org}/{repo_name}"
        else:
            repo_ref = repo_name

        # Delete the existing repository
        delete_cmd = ["gh", "repo", "delete", repo_ref, "--yes"]
        delete_result = self.execute_command(delete_cmd)

        if not delete_result["success"]:
            return {
                "success": False,
                "error": f"Failed to delete existing repository: {delete_result.get('error', 'Unknown error')}",
                "output": delete_result.get("output"),
                "returncode": delete_result.get("returncode"),
            }

        # Create the repository with new content
        return self.create_repository(
            repo_name,
            workspace,
            public=public,
            template=template,
            template_repo=template_repo,
            org=org,
            description=description,
            skip_git_operations=False,
        )

    def mark_repository_as_template(self, repo_name: str, org: str | None = None) -> dict[str, Any]:
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
            user_result = run_subprocess(
                ["gh", "api", "user", "--jq", ".login"],
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
        run_subprocess(["git", "init"], cwd=workspace, check=True)

    def commit_files(self, workspace: Path, message: str) -> None:
        """Commit files.

        Args:
            workspace: Workspace directory.
            message: Commit message.

        Raises:
            RuntimeError: If git user configuration is missing or commit fails.
        """
        # Check if git is configured globally
        user_name = run_subprocess(
            ["git", "config", "--global", "user.name"],
            check=False,
        )
        user_email = run_subprocess(
            ["git", "config", "--global", "user.email"],
            check=False,
        )

        # If global config is missing, set local config in workspace
        if not user_name.stdout.strip():
            run_subprocess(
                ["git", "config", "user.name", "Template CLI"],
                cwd=workspace,
                check=True,
            )

        if not user_email.stdout.strip():
            run_subprocess(
                ["git", "config", "user.email", "template-cli@example.com"],
                cwd=workspace,
                check=True,
            )

        # Add all files
        add_result = run_subprocess(
            ["git", "add", "."],
            cwd=workspace,
            check=False,
        )
        if add_result.returncode != 0:
            raise RuntimeError(f"git add failed:\n{add_result.stderr}")

        # Commit
        commit_result = run_subprocess(
            ["git", "commit", "-m", message],
            cwd=workspace,
            check=False,
        )
        if commit_result.returncode != 0:
            raise RuntimeError(
                f"git commit failed:\nstdout: {commit_result.stdout}\nstderr: {commit_result.stderr}"
            )

    def push_to_remote(
        self,
        workspace: Path,
        remote_url: str,
        *,
        branch: str = "main",
        force: bool = False,
        force_with_lease: bool = False,
    ) -> None:
        """Push local workspace to a remote.

        Args:
            workspace: Workspace directory.
            remote_url: Remote repository URL.
            branch: Branch name to push.
            force: Whether to force push (destructive).
            force_with_lease: Whether to force-with-lease push (safer than force).
        """
        # Ensure we replace any existing origin to avoid failures
        run_subprocess(["git", "remote", "remove", "origin"],
                       cwd=workspace, check=False)
        run_subprocess(
            ["git", "remote", "add", "origin", remote_url],
            cwd=workspace,
            check=True,
        )

        push_cmd = ["git", "push", "-u", "origin", branch]
        if force_with_lease:
            push_cmd.append("--force-with-lease")
        elif force:
            push_cmd.append("--force")

        run_subprocess(push_cmd, cwd=workspace, check=True)

    def push_to_existing_repository(
        self,
        repo_name: str,
        workspace: Path,
        *,
        org: str | None = None,
        branch: str = "main",
        force: bool = False,
        force_with_lease: bool = False,
    ) -> dict[str, Any]:
        """Push updated contents into an existing repository.

        Args:
            repo_name: Repository name.
            workspace: Workspace directory containing files to push.
            org: Organization name (if None, uses user account).
            branch: Branch name to push.
            force: Whether to force push (destructive).
            force_with_lease: Whether to force-with-lease push.

        Returns:
            Result dictionary.
        """
        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": (
                    "Dry run - repository would be updated via push"
                ),
            }

        repo_ref = f"{org}/{repo_name}" if org else repo_name
        remote_url = f"https://github.com/{repo_ref}.git"

        try:
            self.init_git_repo(workspace)
            self.commit_files(workspace, "Update template contents")
            self.push_to_remote(
                workspace,
                remote_url,
                branch=branch,
                force=force,
                force_with_lease=force_with_lease,
            )
            return {"success": True}
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    def _should_retry_with_fresh_auth(self, result: dict[str, Any]) -> bool:
        """Determine if an authentication error was encountered."""
        message_parts = (
            (result.get("error") or "").lower(),
            (result.get("output") or "").lower(),
        )
        combined_message = " ".join(part for part in message_parts if part)

        if all(marker in combined_message for marker in INTEGRATION_PERMISSION_ERROR_MARKERS):
            return True

        return any(marker in combined_message for marker in AUTH_TOKEN_HINT_MARKERS)
