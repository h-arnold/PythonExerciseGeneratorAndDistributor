"""Tests for template packager."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

import pytest

from scripts.template_repo_cli.core.collector import ExerciseFiles
from scripts.template_repo_cli.core.packager import TemplatePackager

ExerciseFileMap: TypeAlias = dict[str, ExerciseFiles]
ExerciseFileMapBuilder: TypeAlias = Callable[..., ExerciseFileMap]


@pytest.fixture
def template_packager(repo_root: Path) -> TemplatePackager:
    """Provide a configured TemplatePackager for the repository."""

    return TemplatePackager(repo_root)


@pytest.fixture
def build_exercise_file_map(repo_root: Path) -> ExerciseFileMapBuilder:
    """Build exercise file mappings for one or more exercise identifiers."""

    def _build(*exercise_ids: str) -> ExerciseFileMap:
        if not exercise_ids:
            msg = "At least one exercise_id is required"
            raise ValueError(msg)
        return {
            exercise_id: ExerciseFiles(
                notebook=repo_root / f"notebooks/{exercise_id}.ipynb",
                test=repo_root / f"tests/test_{exercise_id}.py",
            )
            for exercise_id in exercise_ids
        }

    return _build


def _assert_base_template_files(temp_dir: Path) -> None:
    """Verify that baseline template files exist in the workspace copy."""

    assert (temp_dir / "pyproject.toml").exists()
    assert (temp_dir / "pytest.ini").exists()
    assert (temp_dir / ".gitignore").exists()
    scripts_dir = temp_dir / "scripts"
    assert scripts_dir.exists()
    assert scripts_dir.is_dir()


def _assert_autograde_script_copy(repo_root: Path, temp_dir: Path) -> None:
    """Verify copying behaviour for the autograde payload builder script."""

    autograde_src = repo_root / "scripts" / "build_autograde_payload.py"
    autograde_dest = temp_dir / "scripts" / "build_autograde_payload.py"
    if autograde_src.exists():
        assert autograde_dest.exists()
        assert autograde_dest.read_text() == autograde_src.read_text()
    else:
        assert not autograde_dest.exists()


def _assert_autograde_plugin_copy(repo_root: Path, temp_dir: Path) -> None:
    """Verify copying behaviour for the autograde plugin module."""

    plugin_src = repo_root / "tests" / "autograde_plugin.py"
    plugin_dest = temp_dir / "tests" / "autograde_plugin.py"
    if plugin_src.exists():
        assert plugin_dest.exists()
        assert plugin_dest.read_text() == plugin_src.read_text()
    else:
        assert not plugin_dest.exists()


def _assert_required_test_infrastructure_copy(repo_root: Path, temp_dir: Path) -> None:
    """Verify required test infrastructure files and directories are copied."""

    required_files = (
        "__init__.py",
        "autograde_plugin.py",
        "helpers.py",
        "notebook_grader.py",
        "test_autograde_plugin.py",
        "test_build_autograde_payload.py",
    )
    required_directories = (
        "exercise_expectations",
        "exercise_framework",
        "student_checker",
    )

    for filename in required_files:
        src = repo_root / "tests" / filename
        dest = temp_dir / "tests" / filename
        if src.exists():
            assert dest.exists()
        else:
            assert not dest.exists()

    for dirname in required_directories:
        src = repo_root / "tests" / dirname
        dest = temp_dir / "tests" / dirname
        if src.exists():
            assert dest.exists()
            assert dest.is_dir()
        else:
            assert not dest.exists()


class TestCreateTempDirectory:
    """Tests for temporary directory creation."""

    def test_create_temp_directory(self, template_packager: TemplatePackager) -> None:
        """Test temporary workspace creation."""
        temp_path = template_packager.create_workspace()

        assert temp_path.exists()
        assert temp_path.is_dir()

    def test_create_temp_directory_unique(self, template_packager: TemplatePackager) -> None:
        """Test that each workspace is unique."""
        temp1 = template_packager.create_workspace()
        temp2 = template_packager.create_workspace()

        assert temp1 != temp2


class TestCopyFiles:
    """Tests for copying files to workspace."""

    @pytest.mark.parametrize(
        "expected_relative_path",
        [
            pytest.param("notebooks/ex001_sanity.ipynb", id="notebook"),
            pytest.param("tests/test_ex001_sanity.py", id="test"),
        ],
    )
    def test_copy_exercise_files(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
        expected_relative_path: str,
    ) -> None:
        """Test copying exercise notebooks and tests to the workspace."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / expected_relative_path).exists()

    def test_copy_template_files(
        self,
        template_packager: TemplatePackager,
        repo_root: Path,
        temp_dir: Path,
    ) -> None:
        """Test copying base template files."""

        template_packager.copy_template_base_files(temp_dir)

        _assert_base_template_files(temp_dir)
        _assert_autograde_script_copy(repo_root, temp_dir)
        _assert_autograde_plugin_copy(repo_root, temp_dir)
        _assert_required_test_infrastructure_copy(repo_root, temp_dir)

    def test_required_test_directories_exclude_non_runtime_artefacts(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Test copied required test directories exclude tests and cache artefacts."""

        template_packager.copy_template_base_files(temp_dir)

        for dirname in template_packager.REQUIRED_TEST_DIRECTORIES:
            copied_dir = temp_dir / "tests" / dirname
            assert copied_dir.exists()
            assert not list(copied_dir.rglob("__pycache__"))
            assert not list(copied_dir.rglob("*.pyc"))
            assert not list(copied_dir.rglob("test_*.py"))
            assert not list(copied_dir.rglob("*_test.py"))

    def test_copy_preserves_structure(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test that directory structure is maintained."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)

        # Structure should be preserved
        assert (temp_dir / "notebooks").exists()
        assert (temp_dir / "tests").exists()


class TestGenerateFiles:
    """Tests for generating template files."""

    def test_generate_readme(self, template_packager: TemplatePackager, temp_dir: Path) -> None:
        """Test creating custom README with exercise list."""
        exercises = ["ex001_sanity", "ex002_sequence_modify_basics"]

        template_packager.generate_readme(temp_dir, "Test Template", exercises)

        readme = temp_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Template" in content
        assert "ex001_sanity" in content

    def test_generate_gitignore(self, template_packager: TemplatePackager, temp_dir: Path) -> None:
        """Test creating appropriate .gitignore."""
        template_packager.copy_template_base_files(temp_dir)

        gitignore = temp_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "__pycache__" in content


class TestPackageIntegrity:
    """Tests for package validation."""

    def test_package_integrity_check(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validating package completeness."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(temp_dir, "Test", ["ex001_sanity"])
        assert (temp_dir / "scripts").is_dir()

        # Validate package
        is_valid = template_packager.validate_package(temp_dir)
        assert is_valid

    def test_package_integrity_missing_files(
        self, template_packager: TemplatePackager, temp_dir: Path
    ) -> None:
        """Test validation fails with missing required files."""

        # Don't copy all required files
        is_valid = template_packager.validate_package(temp_dir)
        assert not is_valid

    def test_package_integrity_missing_autograde_script(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails without Classroom autograde script."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(temp_dir, "Test", ["ex001_sanity"])

        autograde_path = temp_dir / "scripts" / "build_autograde_payload.py"
        if not autograde_path.exists():
            pytest.skip("Autograde script not available in template copy")

        autograde_path.unlink()
        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_missing_autograde_plugin(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails without Classroom autograde plugin."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(temp_dir, "Test", ["ex001_sanity"])

        plugin_path = temp_dir / "tests" / "autograde_plugin.py"
        if not plugin_path.exists():
            pytest.skip("Autograde plugin not available in template copy")

        plugin_path.unlink()
        assert not template_packager.validate_package(temp_dir)

    @pytest.mark.parametrize(
        "missing_path",
        [
            pytest.param("tests/exercise_framework", id="exercise-framework"),
            pytest.param("tests/exercise_expectations",
                         id="exercise-expectations"),
            pytest.param("tests/student_checker", id="student-checker"),
            pytest.param("tests/helpers.py", id="helpers"),
            pytest.param("tests/test_autograde_plugin.py",
                         id="autograde-test"),
            pytest.param(
                "tests/test_build_autograde_payload.py",
                id="payload-test",
            ),
        ],
    )
    def test_package_integrity_missing_required_test_infrastructure(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
        missing_path: str,
    ) -> None:
        """Test validation fails when required test infrastructure is removed."""

        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(temp_dir, "Test", ["ex001_sanity"])

        path_to_remove = temp_dir / missing_path
        if not path_to_remove.exists():
            pytest.skip(
                f"Required path not available in template copy: {missing_path}")

        if path_to_remove.is_dir():
            shutil.rmtree(path_to_remove)
        else:
            path_to_remove.unlink()

        assert not template_packager.validate_package(temp_dir)

    def test_package_has_notebook_grader(
        self, template_packager: TemplatePackager, repo_root: Path, temp_dir: Path
    ) -> None:
        """Test that notebook_grader.py is copied from project tests when present."""
        template_packager.copy_template_base_files(temp_dir)

        grader = temp_dir / "tests/notebook_grader.py"
        repo_grader = repo_root / "tests/notebook_grader.py"
        if repo_grader.exists():
            assert grader.exists()
            assert grader.read_text() == repo_grader.read_text()
        else:
            assert not grader.exists()

    def test_copy_template_base_files_fails_fast_for_missing_required_sources(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test missing required source files and directories fail before copy."""

        missing_file = "test_missing_required_asset.py"
        missing_dir = "missing_required_directory"
        monkeypatch.setattr(
            template_packager,
            "REQUIRED_TEST_FILES",
            (*template_packager.REQUIRED_TEST_FILES, missing_file),
        )
        monkeypatch.setattr(
            template_packager,
            "REQUIRED_TEST_DIRECTORIES",
            (*template_packager.REQUIRED_TEST_DIRECTORIES, missing_dir),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            template_packager.copy_template_base_files(temp_dir)

        error_text = str(exc_info.value)
        assert f"tests/{missing_file}" in error_text
        assert f"tests/{missing_dir}" in error_text

    def test_packaged_workspace_pytest_smoke(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test minimal packaged workspace passes a focused pytest run."""

        files = build_exercise_file_map("ex001_sanity")
        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Smoke Test Template", ["ex001_sanity"])

        assert template_packager.validate_package(temp_dir)

        env = os.environ.copy()
        env["PYTUTOR_NOTEBOOKS_DIR"] = "notebooks"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_ex001_sanity.py",
            ],
            cwd=temp_dir,
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )

        assert result.returncode == 0, (
            "Packaged workspace smoke pytest failed:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    def test_copies_notebook_grader_when_present(
        self, template_packager: TemplatePackager, repo_root: Path, temp_dir: Path
    ) -> None:
        """Test that notebook_grader.py is present; project grader takes precedence over template grader."""
        template_tests_dir = repo_root / "template_repo_files" / "tests"
        template_tests_dir.mkdir(parents=True, exist_ok=True)
        grader_src = template_tests_dir / "notebook_grader.py"
        try:
            # Create a dummy grader in the template files directory
            grader_src.write_text("# grader helper")

            template_packager.copy_template_base_files(temp_dir)

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

    def test_package_cleanup_on_error(self, template_packager: TemplatePackager) -> None:
        """Test cleaning up temp files on failure."""
        temp_path = template_packager.create_workspace()

        # Simulate error and cleanup
        template_packager.cleanup(temp_path)

        # Temp directory should be removed
        assert not temp_path.exists()


class TestPackageOptions:
    """Tests for package options."""

    def test_package_does_not_include_solutions(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test solutions are not included in the package."""
        files = build_exercise_file_map("ex001_sanity")

        template_packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "notebooks/ex001_sanity.ipynb").exists()
        assert not (
            temp_dir / "notebooks/solutions/ex001_sanity.ipynb").exists()


class TestPackageMultipleExercises:
    """Tests for packaging multiple exercises."""

    def test_package_multiple_exercises(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test packaging multiple exercises together."""
        files = build_exercise_file_map(
            "ex001_sanity",
            "ex002_sequence_modify_basics",
        )

        template_packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "notebooks/ex001_sanity.ipynb").exists()
        assert (temp_dir / "notebooks/ex002_sequence_modify_basics.ipynb").exists()
