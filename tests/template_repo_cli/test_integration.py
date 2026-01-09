"""Integration tests for template repository CLI."""

from __future__ import annotations

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
