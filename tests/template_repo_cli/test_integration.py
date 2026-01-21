"""Integration tests for template repository CLI."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestEndToEndSingleConstruct:
    """Tests for end-to-end flow with single construct."""

    @patch("subprocess.run")
    def test_end_to_end_single_construct(self, mock_run, repo_root: Path) -> None:
        """Test full flow for one construct."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        # CLI is now implemented - test it works in dry-run mode
        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )
        
        # Should succeed in dry-run mode
        assert result == 0


class TestEndToEndMultipleConstructs:
    """Tests for end-to-end flow with multiple constructs."""

    @patch("subprocess.run")
    def test_end_to_end_multiple_constructs(self, mock_run, repo_root: Path) -> None:
        """Test full flow for multiple constructs."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "sequence",
                "selection",
                "--repo-name",
                "test-repo",
            ]
        )
        
        # Should succeed (sequence construct has exercises)
        assert result == 0


class TestEndToEndSpecificNotebooks:
    """Tests for end-to-end flow with specific notebooks."""

    @patch("subprocess.run")
    def test_end_to_end_specific_notebooks(self, mock_run, repo_root: Path) -> None:
        """Test full flow for specific notebooks."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--notebooks",
                "ex001_sanity",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0


class TestEndToEndWithPattern:
    """Tests for end-to-end flow with pattern matching."""

    @patch("subprocess.run")
    def test_end_to_end_with_pattern(self, mock_run, repo_root: Path) -> None:
        """Test full flow with pattern matching."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--notebooks",
                "ex00*",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0


class TestEndToEndDryRun:
    """Tests for end-to-end flow in dry-run mode."""

    @patch("subprocess.run")
    def test_end_to_end_dry_run(self, mock_run, repo_root: Path) -> None:
        """Test full flow in dry-run mode."""
        from scripts.template_repo_cli.cli import main

        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0
        # In dry run, subprocess should not be called for gh commands
        # (but might be called for other things like git operations in tests)


class TestEndToEndErrorRecovery:
    """Tests for error handling in full flow."""

    @patch("subprocess.run")
    def test_end_to_end_error_recovery(self, mock_run, repo_root: Path) -> None:
        """Test error handling in full flow."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

        # Invalid construct should cause error
        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "invalid_construct",
                "--repo-name",
                "test-repo",
            ]
        )
        
        # Should fail with non-zero exit code
        assert result != 0


class TestCliHelpOutput:
    """Tests for CLI help text."""

    def test_cli_help_output(self) -> None:
        """Test help text generation."""
        from scripts.template_repo_cli.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        
        # --help should exit with 0
        assert exc_info.value.code == 0


class TestCliListCommand:
    """Tests for list command."""

    def test_cli_list_command(self, repo_root: Path, capsys) -> None:
        """Test list command output."""
        from scripts.template_repo_cli.cli import main

        result = main(["list"])
        
        assert result == 0
        
        # Should output some exercises
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_cli_list_with_construct_filter(self, repo_root: Path, capsys) -> None:
        """Test list command with construct filter."""
        from scripts.template_repo_cli.cli import main

        result = main(["list", "--construct", "sequence"])
        
        assert result == 0


class TestCliValidateCommand:
    """Tests for validate command."""

    def test_cli_validate_command(self, repo_root: Path) -> None:
        """Test validate command output."""
        from scripts.template_repo_cli.cli import main

        result = main(["validate", "--construct", "sequence"])
        
        # Should succeed if files exist
        assert result == 0

    def test_cli_validate_invalid_selection(self, repo_root: Path) -> None:
        """Test validate command with invalid selection."""
        from scripts.template_repo_cli.cli import main

        result = main(["validate", "--construct", "invalid_construct"])
        
        # Should fail
        assert result != 0


class TestCliCreateCommand:
    """Tests for create command."""

    @patch("subprocess.run")
    def test_cli_create_command(self, mock_run, repo_root: Path) -> None:
        """Test create command execution."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0

    @patch("subprocess.run")
    def test_cli_create_defaults_to_template(self, mock_run, repo_root: Path) -> None:
        """Create should mark repository as a template by default."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called = {}

        def fake_create(self, repo_name, workspace, **kwargs):
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with patch.object(GitHubClient, "create_repository", new=fake_create), \
            patch.object(GitHubClient, "check_gh_installed", return_value=True), \
            patch.object(GitHubClient, "check_scopes", return_value={"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []}), \
            patch.object(GitHubClient, "check_authentication", return_value=True):
            result = main(
                ["create", "--construct", "sequence", "--repo-name", "test-repo"]
            )

        assert result == 0
        # By default the CLI should set template=True
        assert called.get("template") is True
        assert called.get("template_repo") is None

    @patch("subprocess.run")
    def test_cli_create_with_no_template_flag(self, mock_run, repo_root: Path) -> None:
        """Passing --no-template should disable template creation."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called = {}

        def fake_create(self, repo_name, workspace, **kwargs):
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with patch.object(GitHubClient, "create_repository", new=fake_create), \
            patch.object(GitHubClient, "check_gh_installed", return_value=True), \
            patch.object(GitHubClient, "check_scopes", return_value={"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []}), \
            patch.object(GitHubClient, "check_authentication", return_value=True):
            result = main(
                [
                    "create",
                    "--construct",
                    "sequence",
                    "--repo-name",
                    "test-repo",
                    "--no-template",
                ]
            )

        assert result == 0
        assert called.get("template") is False

    @patch("subprocess.run")
    def test_cli_create_with_template_repo_argument(self, mock_run, repo_root: Path) -> None:
        """Passing --template-repo should forward the value."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called = {}

        def fake_create(self, repo_name, workspace, **kwargs):
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with patch.object(GitHubClient, "create_repository", new=fake_create), \
            patch.object(GitHubClient, "check_gh_installed", return_value=True), \
            patch.object(GitHubClient, "check_scopes", return_value={"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []}), \
            patch.object(GitHubClient, "check_authentication", return_value=True):
            result = main(
                [
                    "create",
                    "--construct",
                    "sequence",
                    "--repo-name",
                    "test-repo",
                    "--template-repo",
                    "owner/template-repo",
                ]
            )

        assert result == 0
        assert called.get("template") is True
        assert called.get("template_repo") == "owner/template-repo"

    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_permission_hint(self, mock_installed, mock_auth, mock_scopes, mock_create, repo_root: Path, capsys) -> None:
        """Display guidance when GitHub rejects repo creation for integrations."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []}
        mock_create.return_value = {
            "success": False,
            "error": "GraphQL: Resource not accessible by integration (createRepository)",
        }

        with patch.dict(os.environ, {}, clear=True):
            result = main(
                [
                    "create",
                    "--construct",
                    "sequence",
                    "--repo-name",
                    "test-repo",
                ]
            )

        assert result == 1
        captured = capsys.readouterr()
        assert "GitHub authentication token cannot create repositories" in captured.err

    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_permission_hint_unset_env_token(
        self, mock_installed, mock_auth, mock_scopes, mock_create, repo_root: Path, capsys
    ) -> None:
        """Hint to unset GITHUB_TOKEN when it blocks login."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []}
        mock_create.return_value = {
            "success": False,
            "error": "GraphQL: Resource not accessible by integration (createRepository)",
        }

        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghu_fake"}, clear=True), \
            patch("builtins.input", return_value="n"):
            result = main(
                [
                    "create",
                    "--construct",
                    "sequence",
                    "--repo-name",
                    "test-repo",
                ]
            )

        assert result == 1
        captured = capsys.readouterr()
        assert "unset github_token" in captured.err.lower()

    @patch("builtins.input", return_value="y")
    @patch("scripts.template_repo_cli.cli.subprocess.run")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_permission_hint_reauth_flow(
        self,
        mock_installed,
        mock_auth,
        mock_scopes,
        mock_create,
        mock_subprocess_run,
        mock_input,
        repo_root: Path,
    ) -> None:
        """Offer to unset token and rerun `gh auth login`."""
        from scripts.template_repo_cli.cli import main

        # First prerequisite check: scopes present
        # After error: check scopes again (missing)
        # Second prerequisite check: scopes present
        mock_scopes.side_effect = [
            {"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []},  # First prereq check
            {"authenticated": True, "has_scopes": False, "scopes": [], "missing_scopes": ["repo"]},  # After first create error
            {"authenticated": True, "has_scopes": True, "scopes": ["repo"], "missing_scopes": []},  # Second prereq check
        ]
        mock_create.side_effect = [
            {
                "success": False,
                "error": "GraphQL: Resource not accessible by integration (createRepository)",
            },
            {"success": True, "html_url": "https://github.com/user/test-repo"},
        ]

        def fake_subprocess_run(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_subprocess_run.side_effect = fake_subprocess_run

        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghu_fake"}, clear=True):
            result = main(
                [
                    "create",
                    "--construct",
                    "sequence",
                    "--repo-name",
                    "test-repo",
                ]
            )

        assert result == 0
        assert mock_create.call_count == 2
        mock_subprocess_run.assert_any_call(["gh", "auth", "login"], check=False)

    @patch("subprocess.run")
    def test_cli_create_with_all_options(self, mock_run, repo_root: Path) -> None:
        """Test create command with all options."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "--verbose",
                "create",
                "--construct",
                "sequence",
                "--type",
                "modify",
                "--repo-name",
                "test-repo",
                "--name",
                "Test Template",
                "--private",
                "--org",
                "my-org",
            ]
        )
        
        assert result == 0


class TestCliVerboseMode:
    """Tests for verbose mode."""

    @patch("subprocess.run")
    def test_cli_verbose_mode(self, mock_run, repo_root: Path, capsys) -> None:
        """Test verbose mode output."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "--verbose",
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0
        
        # In verbose mode, should print progress
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestCliOutputDir:
    """Tests for custom output directory."""

    @patch("subprocess.run")
    def test_cli_custom_output_dir(self, mock_run, repo_root: Path, temp_dir: Path) -> None:
        """Test using custom output directory."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(temp_dir),
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )
        
        assert result == 0
        # Output directory should have been created with content
        assert temp_dir.exists()


class TestCliForceFlag:
    """Tests for --force flag."""

    @patch("subprocess.run")
    def test_cli_create_with_force_flag_dry_run(self, mock_run, repo_root: Path) -> None:
        """Test create command with --force flag in dry-run mode."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
                "--force",
            ]
        )

        assert result == 0

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.force_update_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_force_flag_calls_force_update_when_repo_exists(
        self,
        mock_installed,
        mock_auth,
        mock_scopes,
        mock_force_update,
        mock_check_exists,
        repo_root: Path,
    ) -> None:
        """Test --force flag calls force_update_repository when repo exists."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True
        mock_force_update.return_value = {"success": True}

        result = main(
            [
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
                "--force",
            ]
        )

        assert result == 0
        # Verify check_repository_exists was called
        mock_check_exists.assert_called_once()
        # Verify force_update_repository was called since repo exists
        mock_force_update.assert_called_once()

    @patch("builtins.input", return_value="y")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.force_update_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_prompts_when_repo_exists_without_force(
        self,
        mock_installed,
        mock_auth,
        mock_scopes,
        mock_force_update,
        mock_check_exists,
        mock_input,
        repo_root: Path,
    ) -> None:
        """Test CLI prompts user when repo exists and --force not provided."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True
        mock_force_update.return_value = {"success": True}

        result = main(
            [
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        # Verify input was called (user was prompted)
        mock_input.assert_called_once()
        # Verify force_update_repository was called since user said yes
        mock_force_update.assert_called_once()

    @patch("builtins.input", return_value="n")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.force_update_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_aborts_when_user_declines_force_update(
        self,
        mock_installed,
        mock_auth,
        mock_scopes,
        mock_create,
        mock_force_update,
        mock_check_exists,
        mock_input,
        repo_root: Path,
        capsys,
    ) -> None:
        """Test CLI aborts when user declines force update."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True

        result = main(
            [
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 1
        # Verify input was called (user was prompted)
        mock_input.assert_called_once()
        # Verify force_update_repository was NOT called since user said no
        mock_force_update.assert_not_called()
        # Verify create_repository was also NOT called
        mock_create.assert_not_called()
        # Verify error message contains expected text
        captured = capsys.readouterr()
        assert "operation cancelled" in captured.err.lower()

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.force_update_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_authentication", return_value=True)
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed", return_value=True)
    def test_cli_calls_create_when_repo_does_not_exist(
        self,
        mock_installed,
        mock_auth,
        mock_scopes,
        mock_force_update,
        mock_create,
        mock_check_exists,
        repo_root: Path,
    ) -> None:
        """Test CLI calls create_repository when repo doesn't exist."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = False
        mock_create.return_value = {"success": True}

        result = main(
            [
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
                "--force",  # Force flag should be ignored if repo doesn't exist
            ]
        )

        assert result == 0
        # Verify create_repository was called since repo doesn't exist
        mock_create.assert_called_once()
        # Verify force_update_repository was NOT called
        mock_force_update.assert_not_called()
