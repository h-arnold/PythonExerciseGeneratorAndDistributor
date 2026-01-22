"""Tests for template packager."""

from __future__ import annotations

from pathlib import Path

from scripts.template_repo_cli.core.packager import TemplatePackager


class TestCreateTempDirectory:
    """Tests for temporary directory creation."""

    def test_create_temp_directory(self, repo_root: Path) -> None:
        """Test temporary workspace creation."""
        packager = TemplatePackager(repo_root)
        temp_path = packager.create_workspace()

        assert temp_path.exists()
        assert temp_path.is_dir()

    def test_create_temp_directory_unique(self, repo_root: Path) -> None:
        """Test that each workspace is unique."""
        packager = TemplatePackager(repo_root)
        temp1 = packager.create_workspace()
        temp2 = packager.create_workspace()

        assert temp1 != temp2


class TestCopyFiles:
    """Tests for copying files to workspace."""

    def test_copy_notebooks(self, repo_root: Path, temp_dir: Path) -> None:
        """Test copying notebooks to temp directory."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            }
        }

        packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "notebooks/ex001_sanity.ipynb").exists()

    def test_copy_tests(self, repo_root: Path, temp_dir: Path) -> None:
        """Test copying test files to temp directory."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            }
        }

        packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "tests/test_ex001_sanity.py").exists()

    def test_copy_template_files(self, repo_root: Path, temp_dir: Path) -> None:
        """Test copying base template files."""
        packager = TemplatePackager(repo_root)
        packager.copy_template_base_files(temp_dir)

        # Check that base files are copied
        assert (temp_dir / "pyproject.toml").exists()
        assert (temp_dir / "pytest.ini").exists()
        assert (temp_dir / ".gitignore").exists()

    def test_copy_preserves_structure(self, repo_root: Path, temp_dir: Path) -> None:
        """Test that directory structure is maintained."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            }
        }

        packager.copy_exercise_files(temp_dir, files)

        # Structure should be preserved
        assert (temp_dir / "notebooks").exists()
        assert (temp_dir / "tests").exists()


class TestGenerateFiles:
    """Tests for generating template files."""

    def test_generate_readme(self, repo_root: Path, temp_dir: Path) -> None:
        """Test creating custom README with exercise list."""
        packager = TemplatePackager(repo_root)
        exercises = ["ex001_sanity", "ex002_sequence_modify_basics"]

        packager.generate_readme(temp_dir, "Test Template", exercises)

        readme = temp_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Template" in content
        assert "ex001_sanity" in content

    def test_generate_gitignore(self, repo_root: Path, temp_dir: Path) -> None:
        """Test creating appropriate .gitignore."""
        packager = TemplatePackager(repo_root)
        packager.copy_template_base_files(temp_dir)

        gitignore = temp_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "__pycache__" in content

    def test_generate_workflow(self, repo_root: Path, temp_dir: Path) -> None:
        """Test creating GitHub Actions workflow."""
        packager = TemplatePackager(repo_root)
        packager.copy_template_base_files(temp_dir)

        workflow = temp_dir / ".github/workflows/tests.yml"
        assert workflow.exists()


class TestPackageIntegrity:
    """Tests for package validation."""

    def test_package_integrity_check(self, repo_root: Path, temp_dir: Path) -> None:
        """Test validating package completeness."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            }
        }

        packager.copy_exercise_files(temp_dir, files)
        packager.copy_template_base_files(temp_dir)
        packager.generate_readme(temp_dir, "Test", ["ex001_sanity"])

        # Validate package
        is_valid = packager.validate_package(temp_dir)
        assert is_valid is True

    def test_package_integrity_missing_files(self, repo_root: Path, temp_dir: Path) -> None:
        """Test validation fails with missing required files."""
        packager = TemplatePackager(repo_root)

        # Don't copy all required files
        is_valid = packager.validate_package(temp_dir)
        assert is_valid is False

    def test_package_has_notebook_grader(self, repo_root: Path, temp_dir: Path) -> None:
        """Test that notebook_grader.py is copied from project tests when present."""
        packager = TemplatePackager(repo_root)
        packager.copy_template_base_files(temp_dir)

        grader = temp_dir / "tests/notebook_grader.py"
        repo_grader = repo_root / "tests/notebook_grader.py"
        if repo_grader.exists():
            assert grader.exists()
            assert grader.read_text() == repo_grader.read_text()
        else:
            assert not grader.exists()

    def test_copies_notebook_grader_when_present(self, repo_root: Path, temp_dir: Path) -> None:
        """Test that notebook_grader.py is present; project grader takes precedence over template grader."""
        template_tests_dir = repo_root / "template_repo_files" / "tests"
        template_tests_dir.mkdir(parents=True, exist_ok=True)
        grader_src = template_tests_dir / "notebook_grader.py"
        try:
            # Create a dummy grader in the template files directory
            grader_src.write_text("# grader helper")

            packager = TemplatePackager(repo_root)
            packager.copy_template_base_files(temp_dir)

            grader = temp_dir / "tests/notebook_grader.py"
            assert grader.exists()
            repo_grader = repo_root / "tests/notebook_grader.py"
            if repo_grader.exists():
                # The packager copies the project's grader, not the template one
                assert grader.read_text() == repo_grader.read_text()
            else:
                # When no project grader exists, the template grader should be used
                assert grader.read_text().startswith("# grader helper")
        finally:
            # Cleanup created files
            if grader_src.exists():
                grader_src.unlink()
            # Remove the temporary template tests directory if empty
            from contextlib import suppress

            with suppress(OSError):
                template_tests_dir.rmdir()


class TestPackageCleanup:
    """Tests for cleanup on error."""

    def test_package_cleanup_on_error(self, repo_root: Path) -> None:
        """Test cleaning up temp files on failure."""
        packager = TemplatePackager(repo_root)
        temp_path = packager.create_workspace()

        # Simulate error and cleanup
        packager.cleanup(temp_path)

        # Temp directory should be removed
        assert not temp_path.exists()


class TestPackageOptions:
    """Tests for package options."""

    def test_package_does_not_include_solutions(self, repo_root: Path, temp_dir: Path) -> None:
        """Test solutions are not included in the package."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            }
        }

        packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "notebooks/ex001_sanity.ipynb").exists()
        assert not (temp_dir / "notebooks/solutions/ex001_sanity.ipynb").exists()


class TestPackageMultipleExercises:
    """Tests for packaging multiple exercises."""

    def test_package_multiple_exercises(self, repo_root: Path, temp_dir: Path) -> None:
        """Test packaging multiple exercises together."""
        packager = TemplatePackager(repo_root)
        files = {
            "ex001_sanity": {
                "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
                "test": repo_root / "tests/test_ex001_sanity.py",
            },
            "ex002_sequence_modify_basics": {
                "notebook": repo_root / "notebooks/ex002_sequence_modify_basics.ipynb",
                "test": repo_root / "tests/test_ex002_sequence_modify_basics.py",
            },
        }

        packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "notebooks/ex001_sanity.ipynb").exists()
        assert (temp_dir / "notebooks/ex002_sequence_modify_basics.ipynb").exists()
