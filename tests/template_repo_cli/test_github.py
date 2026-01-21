"""Tests for GitHub operations."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.template_repo_cli.core.github import GitHubClient


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

        assert "--description" in cmd or "-d" in cmd

    def test_build_create_with_template_repo_argument(self, repo_root: Path) -> None:
        """Test passing explicit template repository argument."""
        client = GitHubClient()
        cmd = client.build_create_command(
            "test-repo", template_repo="owner/template-repo")

        assert "--template" in cmd
        assert "owner/template-repo" in cmd

    def test_build_create_with_source_path(self, repo_root: Path) -> None:
        """Test building command with source path for pushing files."""
        client = GitHubClient()
        cmd = client.build_create_command(
            "test-repo", source_path="/tmp/workspace")

        assert "--source" in cmd
        assert "/tmp/workspace" in cmd
        assert "--push" in cmd

    def test_build_create_without_source_path(self, repo_root: Path) -> None:
        """Test building command without source path."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo")

        assert "--source" not in cmd
        assert "--push" not in cmd


class TestExecuteGhCommand:
    """Tests for executing gh commands."""

    @patch("subprocess.run")
    def test_execute_gh_command_success(self, mock_run: MagicMock) -> None:
        """Test successful execution of gh command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"name": "test-repo"}', stderr="")

        client = GitHubClient()
        result = client.execute_command(["gh", "repo", "create", "test-repo"])

        assert result["success"] is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_execute_gh_command_failure(self, mock_run: MagicMock) -> None:
        """Test failed execution of gh command."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error occurred")

        client = GitHubClient()
        result = client.execute_command(["gh", "repo", "create", "test-repo"])

        assert result["success"] is False

    @patch("subprocess.run")
    def test_execute_gh_command_auth_error(self, mock_run: MagicMock) -> None:
        """Test handling authentication failure."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="authentication required")

        client = GitHubClient()
        result = client.execute_command(["gh", "auth", "status"])

        assert result["success"] is False
        assert "authentication" in result.get("error", "").lower()

    @patch("subprocess.run")
    def test_execute_gh_command_rate_limit(self, mock_run: MagicMock) -> None:
        """Test handling rate limit error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="API rate limit exceeded")

        client = GitHubClient()
        result = client.execute_command(["gh", "api", "user"])

        assert result["success"] is False


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_execute(self) -> None:
        """Test dry run builds but doesn't run commands."""
        client = GitHubClient(dry_run=True)
        cmd = client.build_create_command("test-repo")

        # Dry run should return command without executing
        assert isinstance(cmd, list)
        assert "gh" in cmd

    @patch("subprocess.run")
    def test_dry_run_no_subprocess_call(self, mock_run: MagicMock) -> None:
        """Test that dry run doesn't call subprocess."""
        client = GitHubClient(dry_run=True)
        result = client.create_repository("test-repo", Path("/tmp/test"))

        # Should not call subprocess.run
        mock_run.assert_not_called()
        assert "dry_run" in result or result.get("success") is True


class TestValidateGh:
    """Tests for gh CLI validation."""

    @patch("subprocess.run")
    def test_validate_gh_installed(self, mock_run: MagicMock) -> None:
        """Test checking gh CLI availability."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="gh version 2.0.0")

        client = GitHubClient()
        is_installed = client.check_gh_installed()

        assert is_installed is True

    @patch("subprocess.run")
    def test_validate_gh_not_installed(self, mock_run: MagicMock) -> None:
        """Test handling missing gh CLI."""
        mock_run.side_effect = FileNotFoundError()

        client = GitHubClient()
        is_installed = client.check_gh_installed()

        assert is_installed is False

    @patch("subprocess.run")
    def test_validate_gh_authenticated(self, mock_run: MagicMock) -> None:
        """Test checking gh authentication status."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Logged in to github.com")

        client = GitHubClient()
        is_authenticated = client.check_authentication()

        assert is_authenticated is True

    @patch("subprocess.run")
    def test_validate_gh_not_authenticated(self, mock_run: MagicMock) -> None:
        """Test detecting unauthenticated state."""
        mock_run.return_value = MagicMock(returncode=1, stderr="not logged in")

        client = GitHubClient()
        is_authenticated = client.check_authentication()

        assert is_authenticated is False


class TestParseGhOutput:
    """Tests for parsing gh JSON output."""

    def test_parse_gh_json_output(self) -> None:
        """Test parsing JSON response from gh."""
        client = GitHubClient()
        output = '{"name": "test-repo", "html_url": "https://github.com/user/test-repo"}'

        parsed: dict[str, Any] = client.parse_json_output(output)

        assert parsed["name"] == "test-repo"
        assert "html_url" in parsed

    def test_parse_gh_invalid_json(self) -> None:
        """Test handling invalid JSON."""
        client = GitHubClient()
        output = "Not valid JSON"

        with pytest.raises(ValueError):
            client.parse_json_output(output)


class TestCreateRepository:
    """Tests for repository creation."""

    @patch("subprocess.run")
    def test_create_repository_success(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test successful repository creation."""
        # Return value that works for all subprocess calls
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True
        # Verify git init was called
        git_calls = [c for c in mock_run.call_args_list if "git" in str(c)]
        assert len(git_calls) > 0

    @patch("subprocess.run")
    def test_create_repository_initializes_git(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test that create_repository initializes git and commits files."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True
        # Verify git init was called
        git_init_call = [c for c in mock_run.call_args_list if "git" in str(
            c) and "init" in str(c)]
        assert len(git_init_call) > 0
        # Verify git commit was called
        git_commit_call = [
            c for c in mock_run.call_args_list if "commit" in str(c)]
        assert len(git_commit_call) > 0

    @patch("subprocess.run")
    def test_create_repository_skips_git_on_retry(
        self, mock_run: MagicMock, temp_dir: Path
    ) -> None:
        """Test that create_repository skips git operations when skip_git_operations=True."""
        mock_run.side_effect = [
            # gh repo create
            MagicMock(returncode=0, stdout='{"name": "test-repo"}', stderr=""),
            MagicMock(returncode=0, stdout="testuser\n",
                      stderr=""),  # gh api user
            # gh repo edit --template
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        client = GitHubClient()
        result = client.create_repository(
            "test-repo", temp_dir, skip_git_operations=True)

        assert result["success"] is True
        # Verify git init was NOT called
        git_init_calls = [
            c for c in mock_run.call_args_list if "init" in str(c)]
        assert len(git_init_calls) == 0

    @patch("subprocess.run")
    def test_create_repository_marks_template(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Ensure repositories are marked as templates when requested."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True
        # Verify gh repo edit was called with --template
        template_call = [
            c for c in mock_run.call_args_list if "--template" in str(c)]
        assert len(template_call) > 0

    @patch("subprocess.run")
    def test_create_repository_includes_source_and_push_flags(
        self, mock_run: MagicMock, temp_dir: Path
    ) -> None:
        """Test that gh repo create includes --source and --push flags."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True
        # Find the gh repo create call
        gh_create_calls = [
            c for c in mock_run.call_args_list if "gh" in str(c) and "create" in str(c)
        ]
        assert len(gh_create_calls) > 0
        # Verify it includes --source and --push
        create_call_args = str(gh_create_calls[0])
        assert "--source" in create_call_args
        assert "--push" in create_call_args

    @patch("subprocess.run")
    def test_create_repository_with_push(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test repository creation with initial push."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        # Create a dummy file in temp_dir
        (temp_dir / "README.md").write_text("Test")

        client = GitHubClient()
        client.create_repository("test-repo", temp_dir)

        # Should have called git commands
        assert mock_run.call_count >= 1

    @patch("subprocess.run")
    def test_create_repository_handles_token_auth_error(
        self,
        mock_run: MagicMock,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that repo creation returns helpful error on auth failure."""
        monkeypatch.setenv("GITHUB_TOKEN", "existing-token")

        error_message = "Error creating repository: GraphQL: Resource not accessible by integration (createRepository)"

        def make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
            return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)

        mock_run.side_effect = [
            make_result(),  # git init
            make_result(stdout="Test User\n"),  # git config --global user.name
            # git config --global user.email
            make_result(stdout="test@example.com\n"),
            make_result(),  # git add
            make_result(),  # git commit
            # gh repo create fails
            make_result(returncode=1, stderr=error_message),
        ]

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is False
        # Verify token is NOT unset (we don't modify the environment)
        assert "GITHUB_TOKEN" in os.environ
        assert "GH_TOKEN" not in os.environ
        # Verify error message instructs user on resolution
        assert "unset GITHUB_TOKEN" in result["error"]
        assert "gh auth login" in result["error"]
        assert "try again" in result["error"].lower()

        gh_repo_create_calls = [
            call
            for call in mock_run.call_args_list
            if call.args and tuple(call.args[0][:3]) == ("gh", "repo", "create")
        ]
        assert len(gh_repo_create_calls) == 1


class TestMarkRepositoryAsTemplate:
    """Tests for marking repositories as templates."""

    @patch("subprocess.run")
    def test_mark_repository_as_template_with_org(self, mock_run: MagicMock) -> None:
        """Ensure gh repo edit is invoked with org prefix."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        client = GitHubClient()
        result = client.mark_repository_as_template("test-repo", org="my-org")

        assert result["success"] is True
        mock_run.assert_called_with(
            ["gh", "repo", "edit", "my-org/test-repo", "--template"],
            cwd=None,
            capture_output=False,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    @patch("subprocess.run")
    def test_mark_repository_as_template_without_org_gets_user(self, mock_run: MagicMock) -> None:
        """Ensure gh repo edit gets authenticated user when no org specified."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="testuser\n",
                      stderr=""),  # gh api user
            MagicMock(returncode=0, stdout="", stderr=""),  # gh repo edit
        ]

        client = GitHubClient()
        result = client.mark_repository_as_template("test-repo")

        assert result["success"] is True
        # Verify gh api user was called
        assert mock_run.call_args_list[0][0][0] == [
            "gh", "api", "user", "--jq", ".login"]
        # Verify gh repo edit was called with username/repo
        assert mock_run.call_args_list[1][0][0] == [
            "gh",
            "repo",
            "edit",
            "testuser/test-repo",
            "--template",
        ]

    @patch("subprocess.run")
    def test_mark_repository_as_template_user_api_failure(self, mock_run: MagicMock) -> None:
        """Test handling failure to get authenticated user."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Not authenticated")

        client = GitHubClient()
        result = client.mark_repository_as_template("test-repo")

        assert result["success"] is False
        assert "Failed to get authenticated user" in result["error"]


class TestGitOperations:
    """Tests for git operations."""

    @patch("subprocess.run")
    def test_init_git_repo(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test initializing git repository."""
        mock_run.return_value = MagicMock(returncode=0)

        client = GitHubClient()
        client.init_git_repo(temp_dir)

        # Should call git init
        assert any("git" in str(call) for call in mock_run.call_args_list)

    @patch("subprocess.run")
    def test_commit_files_with_global_config(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test committing files with global git config."""
        mock_run.side_effect = [
            MagicMock(
                returncode=0, stdout="Test User\n", stderr=""
            ),  # git config --global user.name
            MagicMock(
                returncode=0, stdout="test@example.com\n", stderr=""
            ),  # git config --global user.email
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
        ]

        (temp_dir / "test.txt").write_text("test")

        client = GitHubClient()
        client.commit_files(temp_dir, "Initial commit")

        # Should call git add and git commit
        EXPECT_CALL_COUNT_FOR_COMMIT = 4
        assert mock_run.call_count == EXPECT_CALL_COUNT_FOR_COMMIT

    @patch("subprocess.run")
    def test_commit_files_sets_local_config_when_global_missing(
        self, mock_run: MagicMock, temp_dir: Path
    ) -> None:
        """Test that commit_files sets local config when global config is missing."""
        mock_run.side_effect = [
            # git config --global user.name (empty)
            MagicMock(returncode=0, stdout="", stderr=""),
            # git config --global user.email (empty)
            MagicMock(returncode=0, stdout="", stderr=""),
            # git config user.name (set local)
            MagicMock(returncode=0, stdout="", stderr=""),
            # git config user.email (set local)
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
        ]

        (temp_dir / "test.txt").write_text("test")

        client = GitHubClient()
        client.commit_files(temp_dir, "Initial commit")

        # Verify local git config was set
        local_config_calls = [
            c
            for c in mock_run.call_args_list
            if "git" in str(c) and "config" in str(c) and "user.name" in str(c)
        ]
        MIN_LOCAL_CONFIG_CALLS = 2  # One global check, one local set
        assert len(local_config_calls) >= MIN_LOCAL_CONFIG_CALLS

    @patch("subprocess.run")
    def test_commit_files_provides_detailed_error(
        self, mock_run: MagicMock, temp_dir: Path
    ) -> None:
        """Test that commit_files provides detailed error messages on failure."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Test User\n",
                      stderr=""),  # git config user.name
            MagicMock(
                returncode=0, stdout="test@example.com\n", stderr=""
            ),  # git config user.email
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(
                returncode=1, stdout="nothing to commit", stderr="fatal: no changes"
            ),  # git commit fails
        ]

        (temp_dir / "test.txt").write_text("test")

        client = GitHubClient()
        with pytest.raises(RuntimeError) as exc_info:
            client.commit_files(temp_dir, "Initial commit")

        assert "git commit failed" in str(exc_info.value)
        assert "nothing to commit" in str(exc_info.value)

    @patch("subprocess.run")
    def test_commit_files(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test committing files."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Test User\n", stderr=""),
            MagicMock(returncode=0, stdout="test@example.com\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        (temp_dir / "test.txt").write_text("test")

        client = GitHubClient()
        client.commit_files(temp_dir, "Initial commit")

        # Should call git add and git commit
        MIN_COMMIT_CALLS = 2
        assert mock_run.call_count >= MIN_COMMIT_CALLS

    @patch("subprocess.run")
    def test_push_to_remote(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test pushing to remote."""
        mock_run.return_value = MagicMock(returncode=0)

        client = GitHubClient()
        client.push_to_remote(temp_dir, "https://github.com/user/test-repo")

        # Should call git push
        assert any("push" in str(call) for call in mock_run.call_args_list)


class TestScopeChecking:
    """Tests for GitHub authentication scope checking."""

    @patch("subprocess.run")
    def test_check_scopes_with_required_scopes(self, mock_run: MagicMock) -> None:
        """Test scope checking when required scopes are present."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'",
        )

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is True
        assert result["has_scopes"] is True
        assert "repo" in result["scopes"]
        assert result["missing_scopes"] == []

    @patch("subprocess.run")
    def test_check_scopes_with_missing_scopes(self, mock_run: MagicMock) -> None:
        """Test scope checking when required scopes are missing."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="  - Token scopes: 'read:org'"
        )

        client = GitHubClient()
        result = client.check_scopes(["repo", "workflow"])

        assert result["authenticated"] is True
        assert result["has_scopes"] is False
        assert "read:org" in result["scopes"]
        assert "repo" in result["missing_scopes"]
        assert "workflow" in result["missing_scopes"]

    @patch("subprocess.run")
    def test_check_scopes_not_authenticated(self, mock_run: MagicMock) -> None:
        """Test scope checking when not authenticated."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is False
        assert result["has_scopes"] is False
        assert result["scopes"] == []
        assert "repo" in result["missing_scopes"]

    @patch("subprocess.run")
    def test_check_scopes_default_repo_scope(self, mock_run: MagicMock) -> None:
        """Test scope checking defaults to 'repo' scope."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="  - Token scopes: 'repo'"
        )

        client = GitHubClient()
        result = client.check_scopes()  # No scopes specified

        assert result["authenticated"] is True
        assert result["has_scopes"] is True
        assert "repo" in result["scopes"]

    @patch("subprocess.run")
    def test_check_scopes_parses_multiple_formats(self, mock_run: MagicMock) -> None:
        """Test scope parsing handles different quote styles."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="  - Token scopes: 'gist', \"read:org\", repo", stderr=""
        )

        client = GitHubClient()
        result = client.check_scopes(["repo"])

        assert result["authenticated"] is True
        assert "repo" in result["scopes"]
        assert "gist" in result["scopes"]
        assert "read:org" in result["scopes"]


class TestAuthRetryDetection:
    """Tests for auth error detection."""

    def test_should_retry_with_integration_permission_error(self) -> None:
        """Test detection of integration permission errors."""
        client = GitHubClient()
        result = {
            "success": False,
            "error": "Error creating repository: GraphQL: Resource not accessible by integration (createRepository)",
        }

        assert client._should_retry_with_fresh_auth(result) is True

    def test_should_retry_with_token_auth_error(self) -> None:
        """Test detection of token auth errors."""
        client = GitHubClient()
        result = {
            "success": False,
            "error": "Error: the current GitHub authentication token cannot create repositories",
        }

        assert client._should_retry_with_fresh_auth(result) is True

    def test_should_retry_with_unset_token_hint_error(self) -> None:
        """Test detection of unset token hint errors."""
        client = GitHubClient()
        result = {
            "success": False,
            "error": "Error: unset GITHUB_TOKEN before running gh auth login",
        }

        assert client._should_retry_with_fresh_auth(result) is True

    def test_should_not_retry_with_unrelated_error(self) -> None:
        """Test that unrelated errors are not detected as auth errors."""
        client = GitHubClient()
        result = {
            "success": False,
            "error": "Error: repository already exists",
        }

        assert client._should_retry_with_fresh_auth(result) is False

    def test_should_retry_case_insensitive(self) -> None:
        """Test that error detection is case-insensitive."""
        client = GitHubClient()
        result = {
            "success": False,
            "error": "ERROR CREATING REPOSITORY: GRAPHQL: RESOURCE NOT ACCESSIBLE BY INTEGRATION (CREATEREPOSITORY)",
        }

        assert client._should_retry_with_fresh_auth(result) is True


class TestCheckRepositoryExists:
    """Tests for checking if a repository exists."""

    @patch("subprocess.run")
    def test_check_repository_exists_returns_true_when_repo_exists(
        self, mock_run: MagicMock
    ) -> None:
        """Test check_repository_exists returns True when repository exists."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"name": "test-repo"}', stderr="")

        client = GitHubClient()
        result = client.check_repository_exists("test-repo")

        assert result is True
        # Verify gh repo view was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "repo" in call_args
        assert "view" in call_args
        assert "test-repo" in call_args

    @patch("subprocess.run")
    def test_check_repository_exists_returns_false_when_repo_not_found(
        self, mock_run: MagicMock
    ) -> None:
        """Test check_repository_exists returns False when repository not found."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="repository not found"
        )

        client = GitHubClient()
        result = client.check_repository_exists("test-repo")

        assert result is False

    @patch("subprocess.run")
    def test_check_repository_exists_with_org(self, mock_run: MagicMock) -> None:
        """Test check_repository_exists with organization."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"name": "test-repo"}', stderr="")

        client = GitHubClient()
        result = client.check_repository_exists("test-repo", org="my-org")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "my-org/test-repo" in call_args

    @patch("subprocess.run")
    def test_check_repository_exists_handles_subprocess_error(
        self, mock_run: MagicMock
    ) -> None:
        """Test check_repository_exists handles subprocess errors gracefully."""
        mock_run.side_effect = OSError("Command failed")

        client = GitHubClient()
        result = client.check_repository_exists("test-repo")

        assert result is False

    @patch("subprocess.run")
    def test_check_repository_exists_respects_dry_run(
        self, mock_run: MagicMock
    ) -> None:
        """Dry-run should not issue subprocess calls."""

        client = GitHubClient(dry_run=True)
        result = client.check_repository_exists("test-repo")

        assert result is False
        mock_run.assert_not_called()


class TestPushToExistingRepository:
    """Tests for pushing updates into an existing repository."""

    @patch("subprocess.run")
    def test_push_to_existing_repository_dry_run(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Dry run should not perform git operations."""

        client = GitHubClient(dry_run=True)
        result = client.push_to_existing_repository("test-repo", temp_dir)

        assert result["success"] is True
        assert result.get("dry_run") is True
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_push_to_existing_repository_force(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Force push should include --force flag."""

        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        (temp_dir / "README.md").write_text("Test")

        client = GitHubClient()
        result = client.push_to_existing_repository(
            "test-repo", temp_dir, branch="dev", force=True
        )

        assert result["success"] is True
        calls = " ".join(str(c) for c in mock_run.call_args_list)
        assert "push" in calls
        assert "--force" in calls
        assert "dev" in calls

    @patch("subprocess.run")
    def test_push_to_existing_repository_force_with_lease(
        self, mock_run: MagicMock, temp_dir: Path
    ) -> None:
        """Force-with-lease push should include the appropriate flag."""

        mock_run.return_value = MagicMock(
            returncode=0, stdout="testuser\n", stderr="")

        client = GitHubClient()
        result = client.push_to_existing_repository(
            "test-repo", temp_dir, force_with_lease=True
        )

        assert result["success"] is True
        calls = " ".join(str(c) for c in mock_run.call_args_list)
        assert "--force-with-lease" in calls
