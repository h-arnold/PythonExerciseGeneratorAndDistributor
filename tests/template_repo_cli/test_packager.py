"""Tests for template packager."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

import pytest

from exercise_metadata.registry import build_exercise_catalogue
from exercise_runtime_support.exercise_catalogue import get_catalogue_snapshot_path
from scripts.template_repo_cli.core.collector import ExerciseFiles, FileCollector
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

    collector = FileCollector(repo_root)

    def _build(*exercise_ids: str) -> ExerciseFileMap:
        if not exercise_ids:
            msg = "At least one exercise_id is required"
            raise ValueError(msg)
        return collector.collect_multiple(list(exercise_ids))

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
    """Verify required test infrastructure files, directories, and runtime package are copied."""

    required_files = (
        "__init__.py",
        "autograde_plugin.py",
        "helpers.py",
        "notebook_grader.py",
        "test_autograde_plugin.py",
        "test_build_autograde_payload.py",
    )
    required_directories = ("exercise_framework",)

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

    runtime_src = repo_root / "exercise_runtime_support"
    runtime_dest = temp_dir / "exercise_runtime_support"
    if runtime_src.exists():
        assert runtime_dest.exists()
        assert runtime_dest.is_dir()
        assert (runtime_dest / "exercise_framework" / "runtime.py").exists()
        assert get_catalogue_snapshot_path(runtime_dest).exists()
    else:
        assert not runtime_dest.exists()


def _create_valid_packaged_workspace(
    template_packager: TemplatePackager,
    temp_dir: Path,
    build_exercise_file_map: ExerciseFileMapBuilder,
) -> None:
    """Create a valid packaged workspace for packager validation tests."""

    files = build_exercise_file_map("ex002_sequence_modify_basics")
    template_packager.copy_exercise_files(temp_dir, files)
    template_packager.copy_template_base_files(temp_dir)
    template_packager.generate_readme(
        temp_dir,
        "Test",
        ["ex002_sequence_modify_basics"],
    )


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
            pytest.param(
                "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb",
                id="notebook",
            ),
            pytest.param(
                "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
                id="test",
            ),
            pytest.param(
                "exercises/sequence/ex002_sequence_modify_basics/tests/expectations.py",
                id="support-module",
            ),
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

        files = build_exercise_file_map("ex002_sequence_modify_basics")

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

    def test_copy_template_base_files_generates_runtime_catalogue_snapshot(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Test packaging emits the metadata-derived runtime catalogue snapshot."""

        template_packager.copy_template_base_files(temp_dir)

        snapshot_path = get_catalogue_snapshot_path(
            temp_dir / "exercise_runtime_support")
        assert snapshot_path.exists()
        assert json.loads(snapshot_path.read_text(
            encoding="utf-8")) == build_exercise_catalogue()

    def test_copy_exercise_files_uses_flat_destination_for_legacy_layout(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
    ) -> None:
        """Test legacy flat-layout exercises still export their test file into tests/."""

        legacy_test = temp_dir / "source" / "tests" / "test_ex999_legacy.py"
        legacy_test.parent.mkdir(parents=True)
        legacy_test.write_text(
            "def test_placeholder() -> None:\n    assert True\n", encoding="utf-8")

        legacy_notebook = temp_dir / "source" / "notebooks" / "ex999_legacy.ipynb"
        legacy_notebook.parent.mkdir(parents=True)
        legacy_notebook.write_text("{}", encoding="utf-8")

        files: ExerciseFileMap = {
            "ex999_legacy": ExerciseFiles(
                notebook=legacy_notebook,
                notebook_export=Path("exercises/legacy/ex999_legacy/notebooks/student.ipynb"),
                test=legacy_test,
                tests_export_dir=Path("tests"),
            )
        }

        template_packager.copy_exercise_files(temp_dir, files)

        assert (temp_dir / "tests" / "test_ex999_legacy.py").exists()

    def test_copy_template_base_files_filters_runtime_catalogue_snapshot_for_subset(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test packaged subset exports only publish their selected runtime catalogue entries."""

        files = build_exercise_file_map("ex002_sequence_modify_basics")
        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(
            temp_dir,
            selected_exercise_keys=set(files),
        )

        snapshot_path = get_catalogue_snapshot_path(
            temp_dir / "exercise_runtime_support")
        snapshot_entries = json.loads(
            snapshot_path.read_text(encoding="utf-8"))
        expected_entries = [
            entry for entry in build_exercise_catalogue() if entry["exercise_key"] in files
        ]

        assert snapshot_entries == expected_entries

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

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)

        # Structure should be preserved
        assert (
            temp_dir / "exercises/sequence/ex002_sequence_modify_basics/notebooks"
        ).exists()
        assert (
            temp_dir / "exercises/sequence/ex002_sequence_modify_basics/tests"
        ).exists()


class TestGenerateFiles:
    """Tests for generating template files."""

    def test_generate_readme(self, template_packager: TemplatePackager, temp_dir: Path) -> None:
        """Test creating custom README with exercise list."""
        exercises = ["ex002_sequence_modify_basics",
                     "ex004_sequence_debug_syntax"]

        template_packager.generate_readme(temp_dir, "Test Template", exercises)

        readme = temp_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Template" in content
        assert "ex002_sequence_modify_basics" in content

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
        """Test validating package completeness for canonical exercise-local exports."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )

        assert (temp_dir / "scripts").is_dir()
        runtime_support_dir = temp_dir / "exercise_runtime_support"
        assert runtime_support_dir.is_dir()
        assert get_catalogue_snapshot_path(runtime_support_dir).exists()
        assert template_packager.validate_package(temp_dir)

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

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Test", ["ex002_sequence_modify_basics"])

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

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Test", ["ex002_sequence_modify_basics"])

        plugin_path = temp_dir / "tests" / "autograde_plugin.py"
        if not plugin_path.exists():
            pytest.skip("Autograde plugin not available in template copy")

        plugin_path.unlink()
        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_missing_runtime_catalogue_snapshot(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails when the generated runtime catalogue snapshot is removed."""

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Test", ["ex002_sequence_modify_basics"])

        snapshot_path = get_catalogue_snapshot_path(
            temp_dir / "exercise_runtime_support")
        snapshot_path.unlink()

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_invalid_runtime_catalogue_snapshot(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails when the runtime catalogue snapshot is malformed."""

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Test", ["ex002_sequence_modify_basics"])

        snapshot_path = get_catalogue_snapshot_path(
            temp_dir / "exercise_runtime_support")
        snapshot_path.write_text(json.dumps(
            {"broken": True}) + "\n", encoding="utf-8")

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_rejects_exported_exercise_metadata(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails if exercise metadata leaks into the export."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )
        (
            temp_dir
            / "exercises"
            / "sequence"
            / "ex002_sequence_modify_basics"
            / "exercise.json"
        ).write_text("{}\n", encoding="utf-8")

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_rejects_exported_solution_notebook(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails if a solution notebook leaks into the export."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )
        (
            temp_dir
            / "exercises"
            / "sequence"
            / "ex002_sequence_modify_basics"
            / "notebooks"
            / "solution.ipynb"
        ).write_text("{}\n", encoding="utf-8")

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_allows_packaged_exercise_tree_with_student_notebook_and_tests(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation accepts the packaged exercises tree for Option A layout."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )

        assert (
            temp_dir / "exercises/sequence/ex002_sequence_modify_basics/tests"
        ).is_dir()
        assert (
            temp_dir
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        ).is_file()
        assert template_packager.validate_package(temp_dir)

    def test_package_integrity_rejects_exported_exercises_tree_non_allowed_notebook_asset(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails if the packaged exercises tree contains non-allowed notebook assets."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )
        exported_exercises_dir = (
            temp_dir / "exercises" / "sequence" / "ex002_sequence_modify_basics"
        )
        (exported_exercises_dir / "notebooks").mkdir(parents=True, exist_ok=True)
        (exported_exercises_dir / "notebooks" / "extra.ipynb").write_text(
            "{}\n", encoding="utf-8"
        )

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_rejects_notebook_leaked_into_packaged_tests_tree(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails if a notebook leaks into the packaged exercise tests tree."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )
        leaked_notebook = (
            temp_dir
            / "exercises"
            / "sequence"
            / "ex002_sequence_modify_basics"
            / "tests"
            / "student.ipynb"
        )
        leaked_notebook.write_text("{}\n", encoding="utf-8")

        assert not template_packager.validate_package(temp_dir)

    def test_package_integrity_rejects_packaged_tests_path_that_is_not_a_directory(
        self,
        template_packager: TemplatePackager,
        temp_dir: Path,
        build_exercise_file_map: ExerciseFileMapBuilder,
    ) -> None:
        """Test validation fails if the packaged tests node is not a directory."""

        _create_valid_packaged_workspace(
            template_packager,
            temp_dir,
            build_exercise_file_map,
        )
        tests_dir = (
            temp_dir / "exercises" / "sequence" / "ex002_sequence_modify_basics" / "tests"
        )
        shutil.rmtree(tests_dir)
        tests_dir.write_text("not a directory\n", encoding="utf-8")

        assert not template_packager.validate_package(temp_dir)

    @pytest.mark.parametrize(
        "missing_path",
        [
            pytest.param("tests/exercise_framework", id="exercise-framework"),
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

        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Test", ["ex002_sequence_modify_basics"])

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
        """Test minimal packaged workspace can collect the selected exercise tests."""

        files = build_exercise_file_map("ex002_sequence_modify_basics")
        template_packager.copy_exercise_files(temp_dir, files)
        template_packager.copy_template_base_files(temp_dir)
        template_packager.generate_readme(
            temp_dir, "Smoke Test Template", ["ex002_sequence_modify_basics"]
        )

        assert template_packager.validate_package(temp_dir)

        env = os.environ.copy()
        explicit_path_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
            ],
            cwd=temp_dir,
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        default_discovery_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
            ],
            cwd=temp_dir,
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )

        assert not (temp_dir / "exercise_runtime_support" /
                    "exercise.json").exists()
        assert get_catalogue_snapshot_path(
            temp_dir / "exercise_runtime_support").exists()
        assert (
            temp_dir / "exercises/sequence/ex002_sequence_modify_basics/tests"
        ).is_dir()
        assert (
            temp_dir
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        ).is_file()

        assert explicit_path_result.returncode == 0, (
            "Packaged workspace explicit-path smoke pytest failed:\n"
            f"stdout:\n{explicit_path_result.stdout}\n"
            f"stderr:\n{explicit_path_result.stderr}"
        )
        assert default_discovery_result.returncode == 0, (
            "Packaged workspace default-discovery smoke pytest failed:\n"
            f"stdout:\n{default_discovery_result.stdout}\n"
            f"stderr:\n{default_discovery_result.stderr}"
        )
        assert "test_ex002_sequence_modify_basics" in default_discovery_result.stdout, (
            "Default pytest discovery did not collect the packaged exercise test:\n"
            f"stdout:\n{default_discovery_result.stdout}\n"
            f"stderr:\n{default_discovery_result.stderr}"
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
        files = build_exercise_file_map("ex002_sequence_modify_basics")

        template_packager.copy_exercise_files(temp_dir, files)

        assert (
            temp_dir
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        ).exists()
        assert not (
            temp_dir
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/solution.ipynb"
        ).exists()


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
            "ex002_sequence_modify_basics",
            "ex003_sequence_modify_variables",
        )

        template_packager.copy_exercise_files(temp_dir, files)

        assert (
            temp_dir
            / "exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb"
        ).exists()
        assert (
            temp_dir
            / "exercises/sequence/ex003_sequence_modify_variables/notebooks/student.ipynb"
        ).exists()
