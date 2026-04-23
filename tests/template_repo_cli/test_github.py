"""Tests for GitHub operations."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.template_repo_cli.core.github import (
    ExecResult,
    GitHubClient,
)
from tests.template_repo_cli.github_test_helpers import (
    check_authentication,
    is_command_sequence,
    parse_json_output,
)


class TestBuildCreateRepoCommand:
    """Tests for building gh repo create command."""

    def test_build_create_repo_command_basic(self, repo_root: Path) -> None:
        """Test building basic gh repo create command."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", public=True)

        assert "gh" in cmd
        assert "repo" in cmd
        assert "create" in cmd
        assert "test-repo" in cmd
        assert "--public" in cmd
        # No --template flag when no template repo is provided
        assert "--template" not in cmd

    def test_build_create_with_org(self, repo_root: Path) -> None:
        """Test building command with organization option."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", org="my-org")

        assert "my-org/test-repo" in " ".join(cmd)

    def test_build_create_private(self, repo_root: Path) -> None:
        """Test building command for private repository."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", public=False)

        assert "--private" in cmd

    def test_build_create_with_description(self, repo_root: Path) -> None:
        """Test building command with description."""
        client = GitHubClient()
        cmd = client.build_create_command(
            "test-repo", description="Test description")

        assert "--description" in cmd
        assert "Test description" in cmd

    def test_build_create_with_template_repo(self, repo_root: Path) -> None:
        """Test building command with template repository."""
        client = GitHubClient()
        cmd = client.build_create_command(
            "test-repo", template_repo="owner/template-repo"
        )

        assert "--template" in cmd
        assert "owner/template-repo" in cmd

    def test_build_create_with_source_path(self, repo_root: Path) -> None:
        """Test building command with source path."""
        client = GitHubClient()
        cmd = client.build_create_command(
            "test-repo", source_path="/tmp/workspace")

        assert "--source" in cmd
        assert "/tmp/workspace" in cmd
        assert "--push" in cmd


class TestValidateGhInstalled:
    """Tests for checking gh CLI installation."""

    @patch("subprocess.run")
    def test_validate_gh_installed(self, mock_run: MagicMock) -> None:
        """Test checking gh CLI is installed."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="gh version 2.0.0")

        client = GitHubClient()
        is_installed = client.check_gh_installed()

        assert is_installed is True

    @patch("subprocess.run")
    def test_validate_gh_not_installed(self, mock_run: MagicMock) -> None:
        """Test detecting missing gh CLI."""
        mock_run.side_effect = FileNotFoundError("gh not found")

        client = GitHubClient()
        is_installed = client.check_gh_installed()

        assert is_installed is False


class TestValidateGhAuthenticated:
    """Tests for checking gh authentication status."""

    @patch("subprocess.run")
    def test_validate_gh_authenticated(self, mock_run: MagicMock) -> None:
        """Test checking gh authentication status."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Logged in to github.com")

        is_authenticated = check_authentication()

        assert is_authenticated is True

    @patch("subprocess.run")
    def test_validate_gh_not_authenticated(self, mock_run: MagicMock) -> None:
        """Test detecting unauthenticated state."""
        mock_run.return_value = MagicMock(returncode=1, stderr="not logged in")

        is_authenticated = check_authentication()

        assert is_authenticated is False


class TestParseGhOutput:
    """Tests for parsing gh JSON output."""

    def test_parse_gh_json_output(self) -> None:
        """Test parsing JSON response from gh."""
        output = '{"name": "test-repo", "html_url": "https://github.com/user/test-repo"}'

        parsed: dict[str, Any] = parse_json_output(output)

        assert parsed["name"] == "test-repo"
        assert "html_url" in parsed

    def test_parse_gh_invalid_json(self) -> None:
        """Test handling invalid JSON."""
        output = "Not valid JSON"

        with pytest.raises(ValueError):
            parse_json_output(output)


class TestCreateRepository:
    """Tests for repository creation."""

    @patch("subprocess.run")
    def test_create_repository_success(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test successful repository creation."""
        # Return value that works for all subprocess calls
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result: ExecResult = client.create_repository(
            "test-repo",
            temp_dir,
            public=True,
            template=True,
        )

        assert result["success"] is True
        assert result.get("dry_run") is False

    @patch("subprocess.run")
    def test_create_repository_dry_run(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test repository creation in dry-run mode."""
        client = GitHubClient(dry_run=True)
        result: ExecResult = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True
        assert result.get("dry_run") is True
        # Should not call subprocess.run in dry-run mode
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_create_repository_auth_error(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test handling authentication errors during repository creation."""
        # Mock successful git operations
        git_success = MagicMock(returncode=0, stdout="", stderr="")

        # Mock failed gh authentication with token hint marker
        gh_auth_error = MagicMock(
            returncode=1,
            stdout="",
            stderr="current github authentication token cannot create repositories",
        )

        # Side effect: return success for git commands, error for gh command
        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if cmd and len(cmd) > 0 and cmd[0] == "gh":
                return gh_auth_error
            return git_success

        mock_run.side_effect = side_effect

        client = GitHubClient()
        result: ExecResult = client.create_repository("test-repo", temp_dir)

        assert result["success"] is False
        assert "Authentication failed" in (result.get("error") or "")


class TestCommandTypeGuards:
    """Tests for command type guard helpers."""

    def test_is_command_sequence_positive(self) -> None:
        """Sequence of strings should be recognised as a command sequence."""
        assert is_command_sequence(["git", "push"]) is True
        assert is_command_sequence(("git", "push")) is True

    def test_is_command_sequence_negative(self) -> None:
        """Non-sequence or mixed-type sequences should not be recognised."""
        assert is_command_sequence("git push") is False
        assert is_command_sequence(["git", 1]) is False


class TestAuthRetryDetection:
    """Tests for auth error detection."""

    def test_should_retry_with_integration_permission_error(self) -> None:
        """Test detection of integration permission errors."""
        client = GitHubClient()
        result: ExecResult = {
            "success": False,
            "error": "Error creating repository: GraphQL: Resource not accessible by integration (createRepository)",
        }

        should_retry = client.should_retry_with_fresh_auth(result)
        assert should_retry is True

    def test_should_retry_with_auth_token_hint(self) -> None:
        """Test detection of auth token hint errors."""
        client = GitHubClient()
        result: ExecResult = {
            "success": False,
            "error": "current github authentication token cannot create repositories",
            "output": "",
        }

        should_retry = client.should_retry_with_fresh_auth(result)
        assert should_retry is True

    def test_should_not_retry_with_generic_error(self) -> None:
        """Test that generic errors do not trigger retry."""
        client = GitHubClient()
        result: ExecResult = {
            "success": False,
            "error": "generic error message",
            "output": "",
        }

        should_retry = client.should_retry_with_fresh_auth(result)
        assert should_retry is False


class TestRepositoryExistence:
    """Tests for checking repository existence."""

    @patch("subprocess.run")
    def test_check_repository_exists_success(self, mock_run: MagicMock) -> None:
        """Test checking repository existence successfully."""
        mock_run.return_value = MagicMock(returncode=0)

        client = GitHubClient()
        exists = client.check_repository_exists("test-repo")

        assert exists is True

    @patch("subprocess.run")
    def test_check_repository_exists_failure(self, mock_run: MagicMock) -> None:
        """Test checking repository existence when repository doesn't exist."""
        mock_run.return_value = MagicMock(returncode=1)

        client = GitHubClient()
        exists = client.check_repository_exists("nonexistent-repo")

        assert exists is False

    @patch("subprocess.run")
    def test_check_repository_exists_dry_run(self, mock_run: MagicMock) -> None:
        """Test checking repository existence in dry-run mode."""
        client = GitHubClient(dry_run=True)
        exists = client.check_repository_exists("test-repo")

        assert exists is False  # Dry-run assumes absent


class TestScopesChecking:
    """Tests for checking GitHub authentication scopes."""

    @patch("subprocess.run")
    def test_check_scopes_authenticated_with_scopes(self, mock_run: MagicMock) -> None:
        """Test checking scopes when authenticated with required scopes."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="  - Token scopes: 'repo', 'workflow', 'admin:org'",
        )

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is True
        assert result["has_scopes"] is True
        assert "repo" in result["scopes"]
        assert result["missing_scopes"] == []

    @patch("subprocess.run")
    def test_check_scopes_authenticated_missing_scopes(self, mock_run: MagicMock) -> None:
        """Test checking scopes when authenticated but missing required scopes."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="  - Token scopes: 'workflow', 'admin:org'",
        )

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is True
        assert result["has_scopes"] is False
        assert "repo" in result["missing_scopes"]

    @patch("subprocess.run")
    def test_check_scopes_not_authenticated(self, mock_run: MagicMock) -> None:
        """Test checking scopes when not authenticated."""
        mock_run.return_value = MagicMock(returncode=1)

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is False
        assert result["has_scopes"] is False


class TestRepositoryOperations:
    """Tests for repository operations."""

    @patch("subprocess.run")
    def test_mark_repository_as_template_success(self, mock_run: MagicMock) -> None:
        """Test marking repository as template successfully."""
        mock_run.return_value = MagicMock(returncode=0)

        client = GitHubClient()
        result: ExecResult = client.mark_repository_as_template("test-repo")

        assert result["success"] is True

    @patch("subprocess.run")
    def test_mark_repository_as_template_failure(self, mock_run: MagicMock) -> None:
        """Test marking repository as template failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        client = GitHubClient()
        result: ExecResult = client.mark_repository_as_template("test-repo")

        assert result["success"] is False


class TestGitOperations:
    """Tests for git operations."""

    @patch("subprocess.run")
    def test_init_git_repo(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test initializing git repository."""
        client = GitHubClient()
        client.init_git_repo(temp_dir)

        # Should call git init
        mock_run.assert_called_with(
            ["git", "init"], cwd=temp_dir, capture_output=True, text=True, check=True)

    @patch("subprocess.run")
    def test_commit_files(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test committing files."""
        from unittest.mock import call

        # Mock git config to return empty values (no global config)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # user.name
            MagicMock(returncode=0, stdout=""),  # user.email
            MagicMock(returncode=0),  # git config user.name
            MagicMock(returncode=0),  # git config user.email
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
        ]

        client = GitHubClient()
        client.commit_files(temp_dir, "Test commit")

        # Should set local git config and commit
        expected_calls = [
            call(["git", "config", "user.name", "Template CLI"],
                 cwd=temp_dir, capture_output=True, text=True, check=True),
            call(["git", "config", "user.email", "template-cli@example.com"],
                 cwd=temp_dir, capture_output=True, text=True, check=True),
            call(["git", "add", "."], cwd=temp_dir,
                 capture_output=True, text=True, check=False),
            call(["git", "commit", "-m", "Test commit"], cwd=temp_dir,
                 capture_output=True, text=True, check=False),
        ]
        mock_run.assert_has_calls(expected_calls, any_order=False)


class TestPushOperations:
    """Tests for push operations."""

    @patch("subprocess.run")
    def test_push_to_remote(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test pushing to remote repository."""
        from unittest.mock import call

        # Mock git operations
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # current branch
            MagicMock(returncode=0),  # git remote remove
            MagicMock(returncode=0),  # git remote add
            MagicMock(returncode=0),  # git push with force
        ]

        client = GitHubClient()
        client.push_to_remote(temp_dir, "https://github.com/user/repo.git")

        # Should get current branch, add remote and push with force
        expected_calls = [
            call(["git", "branch", "--show-current"], cwd=temp_dir,
                 capture_output=True, text=True, check=False),
            call(["git", "remote", "remove", "origin"], cwd=temp_dir,
                 capture_output=True, text=True, check=False),
            call(["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
                 cwd=temp_dir, capture_output=True, text=True, check=True),
            call(["git", "push", "-u", "origin", "main", "--force"],
                 cwd=temp_dir, capture_output=True, text=True, check=True),
        ]
        mock_run.assert_has_calls(expected_calls, any_order=False)


class TestPushToExistingRepository:
    """Tests for pushing to existing repositories."""

    @patch("subprocess.run")
    def test_push_to_existing_repository_success(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test pushing to existing repository successfully."""
        # Mock git operations
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="user/repo\n"),  # resolve repo ref
            MagicMock(returncode=0),  # git init
            MagicMock(returncode=0, stdout=""),  # git config user.name (empty)
            # git config user.email (empty)
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0),  # git config user.name (set)
            MagicMock(returncode=0),  # git config user.email (set)
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            MagicMock(returncode=0, stdout="main\n"),  # git branch
            MagicMock(returncode=0),  # git remote remove
            MagicMock(returncode=0),  # git remote add
            MagicMock(returncode=0),  # git push
        ]

        client = GitHubClient()
        result: ExecResult = client.push_to_existing_repository(
            "user/repo", temp_dir)

        assert result["success"] is True
        assert result.get("remote_url") == "https://github.com/user/repo.git"

    @patch("subprocess.run")
    def test_push_to_existing_repository_permission_error(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test handling permission errors when pushing to existing repository."""
        # Mock permission error
        error = subprocess.CalledProcessError(1, "git push")
        error.stdout = ""
        error.stderr = "remote: Permission denied (403)"

        def side_effect(cmd: object, **kwargs: Any) -> MagicMock:
            if is_command_sequence(cmd) and cmd[:3] == ["git", "push", "-u"]:
                raise error

            if is_command_sequence(cmd) and cmd[:4] == ["gh", "api", "user", "--jq"]:
                return MagicMock(returncode=0, stdout="user\n", stderr="")

            if is_command_sequence(cmd) and cmd[:3] == ["git", "branch", "--show-current"]:
                return MagicMock(returncode=0, stdout="main\n", stderr="")

            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        client = GitHubClient()
        result: ExecResult = client.push_to_existing_repository(
            "repo", temp_dir)

        assert result["success"] is False
        error_text = result.get("error") or ""
        assert "Permission denied" in error_text
        assert "GITHUB_TOKEN" in error_text
