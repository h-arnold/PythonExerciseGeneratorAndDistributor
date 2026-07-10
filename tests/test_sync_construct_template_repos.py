"""Tests for the construct template repository sync script."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# 1.1 TestDiscoverConstructs — 5 tests
# =============================================================================


class TestDiscoverConstructs:
    """Tests for ``discover_constructs()``."""

    def test_discover_constructs_returns_list_of_constructs(self, repo_root: Path) -> None:
        """Discovering constructs returns a list of construct names."""
        from scripts.sync_construct_template_repos import discover_constructs

        constructs = discover_constructs(repo_root)

        assert isinstance(constructs, list)
        assert len(constructs) > 0

    def test_discover_constructs_finds_sequence(self, repo_root: Path) -> None:
        """The 'sequence' construct directory is discovered."""
        from scripts.sync_construct_template_repos import discover_constructs

        constructs = discover_constructs(repo_root)

        assert "sequence" in constructs

    def test_discover_constructs_returns_empty_list_when_no_exercises_dir(
        self, temp_dir: Path
    ) -> None:
        """When exercises dir is missing, an empty list is returned."""
        from scripts.sync_construct_template_repos import discover_constructs

        constructs = discover_constructs(temp_dir)

        assert constructs == []

    def test_discover_constructs_excludes_non_directory_entries(self, tmp_path: Path) -> None:
        """Non-directory entries inside exercises/ are excluded."""
        from scripts.sync_construct_template_repos import discover_constructs

        # Create exercises dir with a file alongside a real subdirectory
        exercises_dir = tmp_path / "exercises"
        exercises_dir.mkdir()
        (exercises_dir / "not_a_dir.txt").write_text("")
        (exercises_dir / "real_construct").mkdir()

        constructs = discover_constructs(tmp_path)

        assert "not_a_dir" not in constructs
        assert "real_construct" in constructs

    def test_discover_constructs_excludes_hidden_and_dunder_directories(
        self, tmp_path: Path
    ) -> None:
        """Hidden and dunder directories inside exercises/ are excluded."""
        from scripts.sync_construct_template_repos import discover_constructs

        exercises_dir = tmp_path / "exercises"
        exercises_dir.mkdir()
        (exercises_dir / ".hidden").mkdir()
        (exercises_dir / "__pycache__").mkdir()
        (exercises_dir / "visible").mkdir()

        constructs = discover_constructs(tmp_path)

        assert ".hidden" not in constructs
        assert "__pycache__" not in constructs
        assert "visible" in constructs


# =============================================================================
# 1.2 TestSyncViaRepoman — delegates build + push to repoman (mock subprocess)
# =============================================================================


def _ok(stdout: str = "", stderr: str = "") -> MagicMock:
    return MagicMock(returncode=0, stdout=stdout, stderr=stderr)


def _fail(stderr: str, stdout: str = "") -> MagicMock:
    return MagicMock(returncode=1, stdout=stdout, stderr=stderr)


class TestSyncViaRepoman:
    """Tests for ``_sync_via_repoman()`` (delegation to repoman)."""

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_update_success_invokes_repoman(self, mock_run: MagicMock, repo_root: Path) -> None:
        """A successful repoman update syncs the construct without create."""
        from scripts.sync_construct_template_repos import _sync_via_repoman

        mock_run.return_value = _ok()

        success, error = _sync_via_repoman("sequence", repo_root)

        assert success is True
        assert error is None
        cmd = mock_run.call_args.args[0]
        assert "-m" in cmd and "scripts.template_repo_cli" in cmd
        assert "update" in cmd
        assert "--repo-name" in cmd and "python-exercises-sequence" in cmd
        assert "--construct" in cmd and "sequence" in cmd
        assert mock_run.call_args.kwargs.get("cwd") == repo_root
        # No create fallback when update succeeds
        assert "create" not in cmd

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_falls_back_to_create_when_repo_missing(
        self, mock_run: MagicMock, repo_root: Path
    ) -> None:
        """A missing-repo update failure triggers a repoman create fallback."""

        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "update" in cmd:
                return _fail(
                    "Error: Repository 'python-exercises-sequence' does not exist. "
                    "Run the create command first to create it."
                )
            return _ok()

        from scripts.sync_construct_template_repos import _sync_via_repoman

        mock_run.side_effect = side_effect

        success, error = _sync_via_repoman("sequence", repo_root)

        assert success is True
        assert error is None
        commands = [call.args[0] for call in mock_run.call_args_list]
        assert any("update" in c for c in commands)
        assert any("create" in c for c in commands)

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_no_create_fallback_on_auth_error(
        self, mock_run: MagicMock, repo_root: Path
    ) -> None:
        """An auth error bubbles up without attempting create."""
        from scripts.sync_construct_template_repos import _sync_via_repoman

        mock_run.return_value = _fail(
            "ERROR: not authenticated with GitHub. Run 'gh auth login' first."
        )

        success, error = _sync_via_repoman("sequence", repo_root)

        assert success is False
        assert error is not None
        assert "gh auth" in error.lower()
        commands = [call.args[0] for call in mock_run.call_args_list]
        assert all("create" not in c for c in commands)

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_no_fallback_on_other_failure(
        self, mock_run: MagicMock, repo_root: Path
    ) -> None:
        """An unrelated failure is reported without a create fallback."""
        from scripts.sync_construct_template_repos import _sync_via_repoman

        mock_run.return_value = _fail("Some unexpected validation error")

        success, error = _sync_via_repoman("sequence", repo_root)

        assert success is False
        assert error is not None
        commands = [call.args[0] for call in mock_run.call_args_list]
        assert all("create" not in c for c in commands)

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_dry_run_only_attempts_update(
        self, mock_run: MagicMock, repo_root: Path
    ) -> None:
        """In dry-run, a missing repo does not trigger create."""
        from scripts.sync_construct_template_repos import _sync_via_repoman

        # repoman update --dry-run never contacts GitHub, so a missing-repo
        # message is treated as non-fatal.
        mock_run.return_value = _fail("Run the create command first")

        success, error = _sync_via_repoman("sequence", repo_root, dry_run=True)

        assert success is True
        assert error is None
        commands = [call.args[0] for call in mock_run.call_args_list]
        assert len(commands) == 1
        assert "update" in commands[0]
        assert "--dry-run" in commands[0]

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_org_forwarded_to_repoman(self, mock_run: MagicMock, repo_root: Path) -> None:
        """The org argument is forwarded to repoman as --org."""
        from scripts.sync_construct_template_repos import _sync_via_repoman

        mock_run.return_value = _ok()

        success, _ = _sync_via_repoman("sequence", repo_root, org="myorg")

        assert success is True
        cmd = mock_run.call_args.args[0]
        assert "--org" in cmd
        assert cmd[cmd.index("--org") + 1] == "myorg"

    def test_check_gh_auth_true_when_authenticated(self, repo_root: Path) -> None:
        """``_check_gh_auth`` returns True when ``gh auth status`` succeeds."""
        from scripts.sync_construct_template_repos import _check_gh_auth

        with patch(
            "scripts.sync_construct_template_repos.subprocess.run",
            return_value=_ok(),
        ):
            assert _check_gh_auth() is True

    def test_check_gh_auth_false_when_not_authenticated(self, repo_root: Path) -> None:
        """``_check_gh_auth`` returns False when ``gh auth status`` fails."""
        from scripts.sync_construct_template_repos import _check_gh_auth

        with patch(
            "scripts.sync_construct_template_repos.subprocess.run",
            return_value=_fail("not authenticated"),
        ):
            assert _check_gh_auth() is False


# =============================================================================
# 1.3 TestGenerateDocsPage — 7 tests
# =============================================================================


class TestGenerateDocsPage:
    """Tests for ``generate_docs_page()`` and ``write_docs_page()``."""

    def test_generate_docs_page_has_title(self, repo_root: Path) -> None:
        """The generated docs page has an H1 title."""
        from scripts.sync_construct_template_repos import generate_docs_page

        constructs = ["sequence"]
        content = generate_docs_page(constructs, repo_root)

        assert content.startswith("# ")

    def test_generate_docs_page_has_table(self, repo_root: Path) -> None:
        """The generated docs page contains a markdown table."""
        from scripts.sync_construct_template_repos import generate_docs_page

        constructs = ["sequence"]
        content = generate_docs_page(constructs, repo_root)

        assert "|" in content
        assert "---" in content

    def test_generate_docs_page_lists_constructs(self, repo_root: Path) -> None:
        """Each construct appears in the docs page."""
        from scripts.sync_construct_template_repos import generate_docs_page

        constructs = ["sequence"]
        content = generate_docs_page(constructs, repo_root)

        assert "sequence" in content

    def test_generate_docs_page_includes_timestamp(self, repo_root: Path) -> None:
        """The generated docs page contains a timestamp."""
        from scripts.sync_construct_template_repos import generate_docs_page

        constructs = ["sequence"]
        content = generate_docs_page(constructs, repo_root)

        # Should contain a date-like pattern
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}", content)

    def test_generate_docs_page_includes_template_repo_links(self, repo_root: Path) -> None:
        """The docs page includes links to template repos on GitHub."""
        from scripts.sync_construct_template_repos import generate_docs_page

        constructs = ["sequence"]
        content = generate_docs_page(constructs, repo_root)

        assert "github.com" in content

    def test_write_docs_page_writes_to_path(self, temp_dir: Path) -> None:
        """write_docs_page writes content to the specified path."""
        from scripts.sync_construct_template_repos import write_docs_page

        output_path = temp_dir / "test-docs.md"
        write_docs_page("# Test Content", output_path)

        assert output_path.exists()
        assert output_path.read_text() == "# Test Content\n"

    def test_write_docs_page_creates_parent_directory(self, temp_dir: Path) -> None:
        """write_docs_page creates parent directories if they don't exist."""
        from scripts.sync_construct_template_repos import write_docs_page

        output_path = temp_dir / "subdir" / "nested" / "test-docs.md"
        write_docs_page("# Test", output_path)

        assert output_path.exists()
        assert output_path.read_text() == "# Test\n"


# =============================================================================
# 1.4 TestMainCLI — 5 tests
# =============================================================================


def _main_side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
    """Side effect for ``main`` tests: repoman succeeds, ``gh`` may fail."""
    if "scripts.template_repo_cli" in cmd:
        return _ok()
    if "gh" in cmd:
        return _fail("Not authenticated")
    return _ok()


class TestMainCLI:
    """Tests for the CLI entry point ``main()``."""

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_help(self, mock_run: MagicMock) -> None:
        """The CLI accepts --help without error."""
        from scripts.sync_construct_template_repos import main

        mock_run.return_value = _ok()

        # Just check it doesn't raise for help text
        with pytest.raises(SystemExit):
            main(["--help"])

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_dry_run_flag(self, mock_run: MagicMock, repo_root: Path, temp_dir: Path) -> None:
        """The --dry-run flag prevents actual gh operations."""
        from scripts.sync_construct_template_repos import main

        mock_run.side_effect = _main_side_effect

        exit_code = main(["--dry-run", "--docs-output-path", str(temp_dir / "docs.md")])

        assert exit_code == 0

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_docs_output_path(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """The --docs-output-path flag controls where the docs page is written."""
        from scripts.sync_construct_template_repos import main

        mock_run.side_effect = _main_side_effect

        docs_path = temp_dir / "custom" / "docs.md"
        exit_code = main(
            [
                "--dry-run",
                "--docs-output-path",
                str(docs_path),
            ]
        )

        assert exit_code == 0
        assert docs_path.exists()

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_verbose_flag(self, mock_run: MagicMock, repo_root: Path, temp_dir: Path) -> None:
        """The --verbose flag is accepted and produces output."""
        from scripts.sync_construct_template_repos import main

        mock_run.side_effect = _main_side_effect

        exit_code = main(
            [
                "--dry-run",
                "--verbose",
                "--docs-output-path",
                str(temp_dir / "verbose-docs.md"),
            ]
        )

        assert exit_code == 0

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_dry_run_succeeds_even_when_gh_fails(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """Dry-run mode succeeds even when gh authentication fails."""
        from scripts.sync_construct_template_repos import main

        # repoman update --dry-run does not contact GitHub, so gh auth
        # failures are non-fatal.
        mock_run.side_effect = _main_side_effect

        exit_code = main(
            [
                "--dry-run",
                "--docs-output-path",
                str(temp_dir / "error-docs.md"),
            ]
        )

        assert exit_code == 0

    @patch("scripts.sync_construct_template_repos.subprocess.run")
    def test_main_aborts_when_not_authenticated(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """A non-dry-run sync aborts with exit code 1 when not authenticated."""
        from scripts.sync_construct_template_repos import main

        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "auth" in cmd and "status" in cmd:
                return _fail("not authenticated")
            if "scripts.template_repo_cli" in cmd:
                return _ok()
            return _ok()

        mock_run.side_effect = side_effect

        exit_code = main(["--docs-output-path", str(temp_dir / "docs.md")])

        assert exit_code == 1


# =============================================================================
# 1.5 TestRunSync — 6 tests (direct unit tests of run_sync, bypassing main())
# =============================================================================


@pytest.fixture
def patched_run_sync() -> Iterator[SimpleNamespace]:
    """Patch all six ``run_sync`` dependencies, exposing each mock by name.

    The returned namespace exposes: ``mock_disc`` (discover_constructs),
    ``mock_sync`` (_sync_via_repoman), ``mock_auth`` (_check_gh_auth),
    ``mock_owner`` (_get_authenticated_owner), ``mock_docs`` (generate_docs_page)
    and ``mock_write`` (write_docs_page). Tests set ``.return_value`` /
    ``.side_effect`` and make assertions directly on these mocks.
    """
    with (
        patch("scripts.sync_construct_template_repos.discover_constructs") as mock_disc,
        patch("scripts.sync_construct_template_repos._sync_via_repoman") as mock_sync,
        patch("scripts.sync_construct_template_repos._check_gh_auth") as mock_auth,
        patch("scripts.sync_construct_template_repos._get_authenticated_owner") as mock_owner,
        patch("scripts.sync_construct_template_repos.generate_docs_page") as mock_docs,
        patch("scripts.sync_construct_template_repos.write_docs_page") as mock_write,
    ):
        yield SimpleNamespace(
            mock_disc=mock_disc,
            mock_sync=mock_sync,
            mock_auth=mock_auth,
            mock_owner=mock_owner,
            mock_docs=mock_docs,
            mock_write=mock_write,
        )


class TestRunSync:
    """Tests for ``run_sync()`` — the public orchestration entry point."""

    # ------------------------------------------------------------------
    # Success path
    # ------------------------------------------------------------------

    def test_run_sync_returns_0_on_success_and_emits_sync_message(
        self,
        capsys: pytest.CaptureFixture[str],
        patched_run_sync: SimpleNamespace,
    ) -> None:
        """run_sync returns 0 when all constructs sync and prints success."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_auth = patched_run_sync.mock_auth
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs

        mock_disc.return_value = ["sequence", "selection"]
        mock_sync.return_value = (True, None)
        mock_auth.return_value = True
        mock_owner.return_value = "test-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=False,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
        )

        assert exit_code == 0
        assert "Sync complete: 2 construct(s) synced successfully." in capsys.readouterr().out

    # ------------------------------------------------------------------
    # Failure path
    # ------------------------------------------------------------------

    def test_run_sync_returns_1_when_construct_fails_and_no_success_message(
        self,
        capsys: pytest.CaptureFixture[str],
        patched_run_sync: SimpleNamespace,
    ) -> None:
        """run_sync returns 1 when a construct fails; no success message printed."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_auth = patched_run_sync.mock_auth
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs
        mock_write = patched_run_sync.mock_write

        mock_disc.return_value = ["sequence", "selection"]
        # First construct succeeds, second fails
        mock_sync.side_effect = [
            (True, None),
            (False, "Network error"),
        ]
        mock_auth.return_value = True
        mock_owner.return_value = "test-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=False,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
        )

        assert exit_code == 1
        assert "Sync complete:" not in capsys.readouterr().out
        # Should still generate and write docs
        mock_docs.assert_called_once()
        mock_write.assert_called_once()

    # ------------------------------------------------------------------
    # Dry-run skips gh auth
    # ------------------------------------------------------------------

    def test_run_sync_dry_run_skips_gh_auth_check(
        self, patched_run_sync: SimpleNamespace
    ) -> None:
        """In dry-run mode, _check_gh_auth is NOT called."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_auth = patched_run_sync.mock_auth
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs

        mock_disc.return_value = ["sequence"]
        mock_sync.return_value = (True, None)
        mock_owner.return_value = "test-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=True,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
        )

        assert exit_code == 0
        mock_auth.assert_not_called()

    # ------------------------------------------------------------------
    # github_owner passthrough
    # ------------------------------------------------------------------

    def test_run_sync_passes_github_owner_to_generate_docs_page(
        self, patched_run_sync: SimpleNamespace
    ) -> None:
        """The github_owner parameter is forwarded to generate_docs_page."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_auth = patched_run_sync.mock_auth
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs

        mock_disc.return_value = ["sequence"]
        mock_sync.return_value = (True, None)
        mock_auth.return_value = True
        mock_owner.return_value = "custom-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=True,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
            github_owner="custom-owner",
            org=None,
        )

        assert exit_code == 0
        # _get_authenticated_owner should be called with owner=custom-owner
        mock_owner.assert_called_once_with(owner="custom-owner")
        # generate_docs_page should receive constructs, repo_root, and github_owner
        assert mock_docs.call_count == 1
        args, kwargs = mock_docs.call_args
        assert args[0] == ["sequence"]
        assert kwargs.get("github_owner") == "custom-owner"

    # ------------------------------------------------------------------
    # org passthrough
    # ------------------------------------------------------------------

    def test_run_sync_passes_org_to_sync_via_repoman(
        self, patched_run_sync: SimpleNamespace
    ) -> None:
        """The org parameter is forwarded to _sync_via_repoman."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_auth = patched_run_sync.mock_auth
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs

        mock_disc.return_value = ["sequence", "selection"]
        mock_sync.return_value = (True, None)
        mock_auth.return_value = True
        mock_owner.return_value = "test-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=True,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
            github_owner=None,
            org="myorg",
        )

        assert exit_code == 0
        # Each _sync_via_repoman call should receive org="myorg"
        for call_args in mock_sync.call_args_list:
            assert call_args.kwargs.get("org") == "myorg"

    # ------------------------------------------------------------------
    # No constructs discovered (edge case)
    # ------------------------------------------------------------------

    def test_run_sync_no_constructs_returns_0(
        self, patched_run_sync: SimpleNamespace
    ) -> None:
        """When no constructs are discovered, run_sync returns 0."""
        from scripts.sync_construct_template_repos import run_sync

        mock_disc = patched_run_sync.mock_disc
        mock_sync = patched_run_sync.mock_sync
        mock_owner = patched_run_sync.mock_owner
        mock_docs = patched_run_sync.mock_docs

        mock_disc.return_value = []
        mock_owner.return_value = "test-owner"
        mock_docs.return_value = "# mock docs"

        exit_code = run_sync(
            dry_run=False,
            verbose=False,
            docs_output_path="/tmp/test-docs.md",
        )

        assert exit_code == 0
        # No constructs means no sync calls
        mock_sync.assert_not_called()
