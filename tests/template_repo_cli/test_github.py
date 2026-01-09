"""Tests for GitHub operations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.template_repo_cli.core.github import GitHubClient


class TestBuildCreateRepoCommand:
    """Tests for building gh repo create command."""

    def test_build_create_repo_command_basic(self, repo_root: Path) -> None:
        """Test building basic gh repo create command."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", public=True, template=True)

        assert "gh" in cmd
        assert "repo" in cmd
        assert "create" in cmd
        assert "test-repo" in cmd
        assert "--public" in cmd
        assert "--template" in cmd

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

    def test_build_create_template(self, repo_root: Path) -> None:
        """Test building command with template repository flag."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", template=True)

        assert "--template" in cmd

    def test_build_create_with_description(self, repo_root: Path) -> None:
        """Test building command with description."""
        client = GitHubClient()
        cmd = client.build_create_command("test-repo", description="Test description")

        assert "--description" in cmd or "-d" in cmd


class TestExecuteGhCommand:
    """Tests for executing gh commands."""

    @patch("subprocess.run")
    def test_execute_gh_command_success(self, mock_run: MagicMock) -> None:
        """Test successful execution of gh command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"name": "test-repo"}', stderr=""
        )

        client = GitHubClient()
        result = client.execute_command(["gh", "repo", "create", "test-repo"])

        assert result["success"] is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_execute_gh_command_failure(self, mock_run: MagicMock) -> None:
        """Test failed execution of gh command."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error occurred"
        )

        client = GitHubClient()
        result = client.execute_command(["gh", "repo", "create", "test-repo"])

        assert result["success"] is False

    @patch("subprocess.run")
    def test_execute_gh_command_auth_error(self, mock_run: MagicMock) -> None:
        """Test handling authentication failure."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="authentication required"
        )

        client = GitHubClient()
        result = client.execute_command(["gh", "auth", "status"])

        assert result["success"] is False
        assert "authentication" in result.get("error", "").lower()

    @patch("subprocess.run")
    def test_execute_gh_command_rate_limit(self, mock_run: MagicMock) -> None:
        """Test handling rate limit error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="API rate limit exceeded"
        )

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
        mock_run.return_value = MagicMock(returncode=0, stdout="gh version 2.0.0")

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
            returncode=0, stdout="Logged in to github.com"
        )

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

        parsed = client.parse_json_output(output)

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
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"name": "test-repo", "html_url": "https://github.com/user/test-repo"}',
            stderr="",
        )

        client = GitHubClient()
        result = client.create_repository("test-repo", temp_dir)

        assert result["success"] is True

    @patch("subprocess.run")
    def test_create_repository_with_push(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test repository creation with initial push."""
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        # Create a dummy file in temp_dir
        (temp_dir / "README.md").write_text("Test")

        client = GitHubClient()
        client.create_repository("test-repo", temp_dir, push=True)

        # Should have called git commands
        assert mock_run.call_count >= 1


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
    def test_commit_files(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test committing files."""
        mock_run.return_value = MagicMock(returncode=0)

        (temp_dir / "test.txt").write_text("test")

        client = GitHubClient()
        client.commit_files(temp_dir, "Initial commit")

        # Should call git add and git commit
        assert mock_run.call_count >= 2

    @patch("subprocess.run")
    def test_push_to_remote(self, mock_run: MagicMock, temp_dir: Path) -> None:
        """Test pushing to remote."""
        mock_run.return_value = MagicMock(returncode=0)

        client = GitHubClient()
        client.push_to_remote(temp_dir, "https://github.com/user/test-repo")

        # Should call git push
        assert any("push" in str(call) for call in mock_run.call_args_list)
