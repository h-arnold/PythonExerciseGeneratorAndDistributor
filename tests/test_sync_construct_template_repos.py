"""Tests for the construct template repository sync script."""

from __future__ import annotations

from pathlib import Path
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
# 1.2 TestBuildConstructWorkspace — 7 tests
# =============================================================================


class TestBuildConstructWorkspace:
    """Tests for ``build_construct_workspace()``."""

    def test_build_construct_workspace_creates_directory(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """Building a workspace creates the output directory."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        assert workspace.exists()
        assert workspace.is_dir()

    def test_build_construct_workspace_includes_notebooks(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """Student notebooks from construct exercises are present in the workspace."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        # At least one student notebook should be copied
        notebooks = list(workspace.rglob("student.ipynb"))
        assert len(notebooks) >= 1

    def test_build_construct_workspace_includes_tests(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """Exercise-local tests are present in the workspace."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        # At least one test file should be present
        test_files = list(workspace.rglob("test_*.py"))
        assert len(test_files) >= 1

    def test_build_construct_workspace_includes_exercise_json(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """exercise.json files are present in the workspace."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        json_files = list(workspace.rglob("exercise.json"))
        assert len(json_files) >= 1

    def test_build_construct_workspace_excludes_solution_notebooks(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """Solution notebooks are excluded from the workspace."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        solution_notebooks = list(workspace.rglob("solution.ipynb"))
        assert len(solution_notebooks) == 0

    def test_build_construct_workspace_raises_for_missing_construct(
        self, repo_root: Path, temp_dir: Path
    ) -> None:
        """A nonexistent construct raises FileNotFoundError."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        with pytest.raises(FileNotFoundError, match="not found"):
            build_construct_workspace(repo_root, "nonexistent_construct", temp_dir)

    def test_build_construct_workspace_returns_path(self, repo_root: Path, temp_dir: Path) -> None:
        """The returned value is a Path pointing to the workspace."""
        from scripts.sync_construct_template_repos import build_construct_workspace

        workspace = build_construct_workspace(repo_root, "sequence", temp_dir)

        assert isinstance(workspace, Path)


# =============================================================================
# 1.3 TestSyncConstruct — 8 tests
# =============================================================================


class TestSyncConstruct:
    """Tests for ``sync_construct()``."""

    def test_sync_construct_dry_run_returns_success(self, repo_root: Path, temp_dir: Path) -> None:
        """Dry-run mode returns a SyncResult with dry_run=True and success=True."""
        from scripts.sync_construct_template_repos import sync_construct

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=True, repo_root=repo_root)

        assert result["success"] is True
        assert result.get("dry_run") is True

    @patch("subprocess.run")
    def test_sync_construct_creates_repo(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """sync_construct calls gh repo create with the construct name."""
        from scripts.sync_construct_template_repos import sync_construct

        # Mock: gh api user succeeds, gh repo view fails (repo doesn't exist),
        # and git/gh repo create/gh repo edit succeed
        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "api" in cmd and "user" in cmd:
                return MagicMock(returncode=0, stdout="testuser\n", stderr="")
            if "view" in cmd:
                # Repo doesn't exist yet
                return MagicMock(returncode=1, stdout="", stderr="not found")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=False, repo_root=repo_root)

        assert result["success"] is True
        # gh repo create should have been called
        create_calls = [
            call
            for call in mock_run.call_args_list
            if "gh" in str(call) and "repo" in str(call) and "create" in str(call)
        ]
        assert len(create_calls) >= 1

    def test_sync_construct_returns_sync_result_type(self, repo_root: Path, temp_dir: Path) -> None:
        """The return value has the expected SyncResult keys."""
        from scripts.sync_construct_template_repos import sync_construct

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=True, repo_root=repo_root)

        assert "success" in result
        assert "construct" in result

    @patch("subprocess.run")
    def test_sync_construct_reports_error(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """When gh fails, sync_construct returns success=False with an error message."""
        from scripts.sync_construct_template_repos import sync_construct

        # Mock gh api user success, then gh repo create failure
        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "api" in cmd and "user" in cmd:
                return MagicMock(returncode=0, stdout="testuser\n", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Error creating repository")

        mock_run.side_effect = side_effect

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=False, repo_root=repo_root)

        assert result["success"] is False
        assert "error" in result

    @patch("subprocess.run")
    def test_sync_construct_owner_from_gh_api(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """The target owner is derived from gh api user --jq .login."""
        from scripts.sync_construct_template_repos import sync_construct

        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "api" in cmd and "user" in cmd:
                return MagicMock(returncode=0, stdout="custom-owner\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=False, repo_root=repo_root)

        assert result["success"] is True
        assert "custom-owner" in result.get("message", "")

    @patch("subprocess.run")
    def test_sync_construct_verbose_output(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """Verbose mode prints progress information."""
        from scripts.sync_construct_template_repos import sync_construct

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        # Should not raise
        result = sync_construct(
            "sequence", workspace, dry_run=True, repo_root=repo_root, verbose=True
        )

        assert result["success"] is True
        assert result.get("dry_run") is True

    @patch("subprocess.run")
    def test_sync_construct_handles_existing_repo(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """sync_construct handles the case where the repo already exists."""
        from scripts.sync_construct_template_repos import sync_construct

        def side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
            if "api" in cmd and "user" in cmd:
                return MagicMock(returncode=0, stdout="testuser\n", stderr="")
            if "view" in cmd:
                # Repo already exists
                return MagicMock(returncode=0, stdout="exists", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct(
            "sequence",
            workspace,
            dry_run=False,
            repo_root=repo_root,
        )

        assert result["success"] is True
        assert "successfully synced" in result.get("message", "").lower()

    @patch("subprocess.run")
    def test_sync_construct_repo_name_format(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """The repository name is derived from the construct name."""
        from scripts.sync_construct_template_repos import sync_construct

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

        workspace = temp_dir / "sequence"
        workspace.mkdir(parents=True)
        (workspace / "student.ipynb").write_text("{}")

        result = sync_construct("sequence", workspace, dry_run=True, repo_root=repo_root)

        assert result["success"] is True
        assert result.get("construct") == "sequence"


# =============================================================================
# 1.4 TestGenerateDocsPage — 7 tests
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
# 1.5 TestMainCLI — 5 tests
# =============================================================================


class TestMainCLI:
    """Tests for the CLI entry point ``main()``."""

    @patch("subprocess.run")
    def test_main_help(self, mock_run: MagicMock) -> None:
        """The CLI accepts --help without error."""
        from scripts.sync_construct_template_repos import main

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

        # Just check it doesn't raise for help text
        with pytest.raises(SystemExit):
            main(["--help"])

    @patch("subprocess.run")
    def test_main_dry_run_flag(self, mock_run: MagicMock, repo_root: Path, temp_dir: Path) -> None:
        """The --dry-run flag prevents actual gh operations."""
        from scripts.sync_construct_template_repos import main

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

        exit_code = main(["--dry-run", "--docs-output-path", str(temp_dir / "docs.md")])

        assert exit_code == 0

    @patch("subprocess.run")
    def test_main_docs_output_path(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """The --docs-output-path flag controls where the docs page is written."""
        from scripts.sync_construct_template_repos import main

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

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

    @patch("subprocess.run")
    def test_main_verbose_flag(self, mock_run: MagicMock, repo_root: Path, temp_dir: Path) -> None:
        """The --verbose flag is accepted and produces output."""
        from scripts.sync_construct_template_repos import main

        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n", stderr="")

        exit_code = main(
            [
                "--dry-run",
                "--verbose",
                "--docs-output-path",
                str(temp_dir / "verbose-docs.md"),
            ]
        )

        assert exit_code == 0

    @patch("subprocess.run")
    def test_main_dry_run_succeeds_even_when_gh_fails(
        self, mock_run: MagicMock, repo_root: Path, temp_dir: Path
    ) -> None:
        """Dry-run mode succeeds even when gh authentication fails."""
        from scripts.sync_construct_template_repos import main

        # Mock gh api user failure
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Not authenticated")

        exit_code = main(
            [
                "--dry-run",
                "--docs-output-path",
                str(temp_dir / "error-docs.md"),
            ]
        )

        # gh auth failure is non-fatal because dry-run mode skips gh
        # operations and docs generation falls back gracefully
        assert exit_code == 0
