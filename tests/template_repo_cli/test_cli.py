"""Tests for the template repository CLI (sync subcommand wiring)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

_UNEXPECTED_CODE = 42


# =============================================================================
# 2.1 TestSyncCommand — 3 tests
# =============================================================================


class TestSyncCommand:
    """Tests for ``sync_command()`` — the repoman sync subcommand handler."""

    def test_sync_command_calls_run_sync_with_correct_args(self) -> None:
        """sync_command delegates to run_sync with translated arguments."""
        import argparse

        from scripts.template_repo_cli.cli import sync_command

        args = argparse.Namespace(
            dry_run=True,
            verbose=False,
            docs_output_path="docs/teachers/custom.md",
            github_owner="my-owner",
            org="my-org",
        )

        with patch("scripts.template_repo_cli.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = 0
            result = sync_command(args)

        assert result == 0
        mock_run_sync.assert_called_once_with(
            dry_run=True,
            verbose=False,
            docs_output_path="docs/teachers/custom.md",
            github_owner="my-owner",
            org="my-org",
        )

    def test_sync_command_with_defaults(self) -> None:
        """sync_command passes default values when args are not provided."""
        import argparse

        from scripts.template_repo_cli.cli import sync_command

        args = argparse.Namespace(
            dry_run=False,
            verbose=False,
            docs_output_path="docs/teachers/construct-template-repos.md",
            github_owner=None,
            org=None,
        )

        with patch("scripts.template_repo_cli.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = 1
            result = sync_command(args)

        assert result == 1
        mock_run_sync.assert_called_once_with(
            dry_run=False,
            verbose=False,
            docs_output_path="docs/teachers/construct-template-repos.md",
            github_owner=None,
            org=None,
        )

    def test_sync_command_propagates_exit_code(self) -> None:
        """sync_command returns whatever run_sync returns."""
        import argparse

        from scripts.template_repo_cli.cli import sync_command

        args = argparse.Namespace(
            dry_run=False,
            verbose=True,
            docs_output_path="/tmp/d.md",
            github_owner=None,
            org=None,
        )

        with patch("scripts.template_repo_cli.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = _UNEXPECTED_CODE
            result = sync_command(args)

        assert result == _UNEXPECTED_CODE


# =============================================================================
# 2.2 TestMainDispatch — 2 tests
# =============================================================================


class TestMainDispatch:
    """Tests that ``main()`` dispatches the ``sync`` subcommand correctly."""

    @patch("scripts.template_repo_cli.cli.sync_command")
    def test_main_dispatches_sync_command(self, mock_cmd: MagicMock) -> None:
        """main() routes 'sync' subcommand to sync_command()."""
        from scripts.template_repo_cli.cli import main

        mock_cmd.return_value = 0

        # Global flags must precede the subcommand
        result = main(["--dry-run", "sync"])

        assert result == 0
        mock_cmd.assert_called_once()
        parsed = mock_cmd.call_args[0][0]
        assert parsed.dry_run is True
        assert parsed.verbose is False
        assert parsed.docs_output_path == "docs/teachers/construct-template-repos.md"
        assert parsed.github_owner is None
        assert parsed.org is None

    def test_main_sync_help_does_not_raise(self) -> None:
        """repoman sync --help prints help and exits cleanly."""
        from scripts.template_repo_cli.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["sync", "--help"])

        assert exc_info.value.code == 0
