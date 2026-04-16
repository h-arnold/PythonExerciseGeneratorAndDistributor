"""Integration tests for template repository CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
from _pytest.capture import CaptureResult

GitHubCreateKwargs = dict[str, object | None]
GitHubCreateResult = dict[str, bool | str]
CommandSequence = Sequence[str]


def _create_shadow_exercise_metadata_package(
    root: Path,
    message: str,
) -> Path:
    shadow_root = root / "shadow_packages"
    shadow_package = shadow_root / "exercise_metadata"
    shadow_package.mkdir(parents=True)
    (shadow_package / "__init__.py").write_text("", encoding="utf-8")
    for module_name in ("registry.py", "resolver.py"):
        (shadow_package / module_name).write_text(
            f'raise RuntimeError("{message}")\n',
            encoding="utf-8",
        )
    return shadow_root


class TestEndToEndSingleConstruct:
    """Tests for end-to-end flow with single construct."""

    @patch("subprocess.run")
    def test_end_to_end_single_construct(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
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
    def test_end_to_end_multiple_constructs(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
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


class TestEndToEndSpecificExerciseKeys:
    """Tests for end-to-end flow with specific exercise keys."""

    @patch("subprocess.run")
    def test_end_to_end_specific_exercise_keys(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Test full flow for specific exercise keys."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0


class TestEndToEndWithPattern:
    """Tests for end-to-end flow with pattern matching."""

    @patch("subprocess.run")
    def test_end_to_end_with_exercise_key_pattern(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Test full flow with exercise-key pattern matching."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        result = main(
            [
                "--dry-run",
                "create",
                "--exercise-keys",
                "ex00*",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0


class TestLegacyNotebookFlagRejection:
    """Tests for rejecting removed notebook-oriented CLI flags."""

    def test_create_rejects_removed_notebooks_flag(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Passing --notebooks should fail clearly after the public cutover."""
        from scripts.template_repo_cli.cli import main

        argparse_usage_error = 2

        with pytest.raises(SystemExit) as exc_info:
            main(
                [
                    "create",
                    "--notebooks",
                    "ex002_sequence_modify_basics",
                    "--repo-name",
                    "test-repo",
                ]
            )

        captured = capsys.readouterr()
        assert exc_info.value.code == argparse_usage_error
        assert (
            "unrecognized arguments: --notebooks ex002_sequence_modify_basics"
            in captured.err
        )


class TestEndToEndDryRun:
    """Tests for end-to-end flow in dry-run mode."""

    @patch("subprocess.run")
    def test_end_to_end_dry_run(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
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

    def test_dry_run_workspace_self_check_command_succeeds(
        self,
        tmp_path: Path,
    ) -> None:
        """Test dry-run output can execute notebook self-check command."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged notebook self-check")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "student"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.student_checker import check_exercise; "
            "check_exercise('ex002_sequence_modify_basics')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert check.returncode == 0, (
            "Notebook self-check command failed in dry-run workspace:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )
        assert "Hello Python!" in check.stdout
        assert "Great work! Everything that can be checked here looks good." not in check.stdout
        assert "exercise_metadata must not be imported" not in check.stderr

    def test_dry_run_workspace_notebook_runtime_self_check_defaults_to_student_failures_without_variant_env(
        self,
        tmp_path: Path,
    ) -> None:
        """Packaged notebook runtime self-checks should default to the student slot."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged notebook runtime")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env.pop("PYTUTOR_ACTIVE_VARIANT", None)
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.student_checker import run_notebook_checks; "
            "run_notebook_checks('ex002_sequence_modify_basics')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"

        assert check.returncode == 0, (
            "Notebook runtime self-check failed in dry-run workspace without a variant override:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )
        assert "Hello Python!" in check.stdout
        assert "Great work! All exercise cells ran without errors." not in check.stdout
        assert "Great work! Everything that can be checked here looks good." not in check.stdout
        assert "Metadata-free packaged repositories do not include solution notebooks" not in combined_output
        assert "exercise_metadata must not be imported" not in combined_output

    def test_dry_run_workspace_sequence_notebook_self_checks_fail_until_solved(
        self,
        tmp_path: Path,
    ) -> None:
        """Packaged sequence student notebook self-check cells should fail by default."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = _create_shadow_exercise_metadata_package(
            tmp_path,
            "exercise_metadata must not be imported in packaged notebook self-check sweep",
        )

        env = os.environ.copy()
        env.pop("PYTUTOR_ACTIVE_VARIANT", None)
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "\n".join(
                [
                    "import contextlib",
                    "import io",
                    "import json",
                    "import re",
                    "import sys",
                    "from pathlib import Path",
                    "from exercise_runtime_support.student_checker.checks import has_exercise_checks, run_exercise_checks",
                    "summary = {",
                    "    'notebook_count': 0,",
                    "    'missing_self_check_cells': [],",
                    "    'unsupported_exercises': [],",
                    "    'unexpected_passes': [],",
                    "    'execution_errors': [],",
                    "    'failing_exercises': [],",
                    "}",
                    "for notebook_path in sorted(Path.cwd().glob('exercises/*/*/notebooks/student.ipynb')):",
                    "    summary['notebook_count'] += 1",
                    "    notebook = json.loads(notebook_path.read_text(encoding='utf-8'))",
                    "    sources = []",
                    "    for cell in notebook.get('cells', []):",
                    "        if cell.get('cell_type') != 'code':",
                    "            continue",
                    "        source = cell.get('source', '')",
                    "        joined = ''.join(source) if isinstance(source, list) else str(source)",
                    "        if 'run_notebook_checks(' in joined:",
                    "            sources.append(joined)",
                    "    if not sources:",
                    "        summary['missing_self_check_cells'].append(notebook_path.parent.parent.name)",
                    "        continue",
                    "    source = sources[-1]",
                    "    match = re.search(r\"run_notebook_checks\\('([^']+)'\\)\", source)",
                    "    if match is None:",
                    "        summary['execution_errors'].append(f\"{notebook_path.parent.parent.name}: could not extract exercise key\")",
                    "        continue",
                    "    exercise_key = match.group(1)",
                    "    namespace = {'__name__': '__main__'}",
                    "    try:",
                    "        with contextlib.redirect_stdout(io.StringIO()):",
                    "            exec(compile(source, str(notebook_path), 'exec'), namespace, namespace)",
                    "    except Exception as exc:",
                    "        summary['execution_errors'].append(f\"{exercise_key}: {exc}\")",
                    "        continue",
                    "    if not has_exercise_checks(exercise_key):",
                    "        summary['unsupported_exercises'].append(exercise_key)",
                    "        continue",
                    "    results = run_exercise_checks(exercise_key)",
                    "    if all(result.passed for result in results):",
                    "        summary['unexpected_passes'].append(exercise_key)",
                    "        continue",
                    "    summary['failing_exercises'].append(exercise_key)",
                    "print(json.dumps(summary, sort_keys=True))",
                    "sys.exit(0 if not any((summary['missing_self_check_cells'], summary['unsupported_exercises'], summary['unexpected_passes'], summary['execution_errors'])) else 1)",
                ]
            ),
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert check.returncode == 0, (
            "Packaged sequence notebook self-check sweep failed:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )

        summary = cast(dict[str, Any], json.loads(
            check.stdout.strip().splitlines()[-1]))
        notebook_count = cast(int, summary["notebook_count"])
        failing_exercises = cast(list[str], summary["failing_exercises"])

        assert notebook_count > 0
        assert summary["missing_self_check_cells"] == []
        assert summary["unsupported_exercises"] == []
        assert summary["unexpected_passes"] == []
        assert summary["execution_errors"] == []
        assert len(failing_exercises) == notebook_count

    def test_dry_run_workspace_packaged_sequence_test_runs_against_student_slot(
        self,
        tmp_path: Path,
    ) -> None:
        """Packaged exercise tests should execute against the packaged student notebook slot."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        source_solution = (
            Path(__file__).resolve().parents[2]
            / "exercises"
            / "sequence"
            / "ex002_sequence_modify_basics"
            / "notebooks"
            / "solution.ipynb"
        )
        packaged_student = (
            output_dir
            / "exercises"
            / "sequence"
            / "ex002_sequence_modify_basics"
            / "notebooks"
            / "student.ipynb"
        )
        shutil.copyfile(source_solution, packaged_student)

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "resolver.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged pytest execution")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "student"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-m",
            "pytest",
            "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
            "-q",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert check.returncode == 0, (
            "Packaged exercise pytest run failed in dry-run workspace:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )

    def test_dry_run_workspace_subset_export_rejects_excluded_notebook_early(
        self,
        tmp_path: Path,
    ) -> None:
        """Subset exports reject unsupported notebooks before any notebook file lookup."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged subset checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "student"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.student_checker import check_exercise; "
            "check_exercise('ex003_sequence_modify_variables')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"

        assert check.returncode != 0
        assert (
            "Unknown exercise key 'ex003_sequence_modify_variables'. Available: "
            "ex002_sequence_modify_basics"
        ) in combined_output
        assert "No such file or directory" not in combined_output
        assert "exercise_metadata must not be imported" not in combined_output

    def test_dry_run_workspace_subset_framework_api_rejects_excluded_notebook_early(
        self,
        tmp_path: Path,
    ) -> None:
        """Subset exports reject unsupported notebooks through the framework API too."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex002_sequence_modify_basics",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged framework checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "student"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.exercise_framework import run_notebook_check; "
            "run_notebook_check('ex003_sequence_modify_variables')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"

        assert check.returncode != 0
        assert (
            "Unknown notebook 'ex003_sequence_modify_variables'. Available: "
            "ex002_sequence_modify_basics"
        ) in combined_output
        assert "No such file or directory" not in combined_output
        assert "exercise_metadata must not be imported" not in combined_output

    def test_repo_canonical_ex004_defaults_to_solution_in_development_mode(
        self,
        repo_root: Path,
    ) -> None:
        """Test canonical ex004 resolves to the solution notebook by default in development."""

        env = os.environ.copy()
        env.pop("PYTUTOR_ACTIVE_VARIANT", None)

        command = [
            sys.executable,
            "-c",
            "\n".join(
                [
                    "import importlib.util",
                    "from pathlib import Path",
                    "from exercise_runtime_support.exercise_framework import resolve_exercise_notebook_path",
                    "module_path = (",
                    "    Path.cwd()",
                    "    / 'exercises'",
                    "    / 'sequence'",
                    "    / 'ex004_sequence_debug_syntax'",
                    "    / 'tests'",
                    "    / 'test_ex004_sequence_debug_syntax.py'",
                    ").resolve()",
                    "expected = (",
                    "    Path.cwd()",
                    "    / 'exercises'",
                    "    / 'sequence'",
                    "    / 'ex004_sequence_debug_syntax'",
                    "    / 'notebooks'",
                    "    / 'solution.ipynb'",
                    ").resolve()",
                    "spec = importlib.util.spec_from_file_location('repo_ex004_test_module', module_path)",
                    "assert spec is not None and spec.loader is not None",
                    "module = importlib.util.module_from_spec(spec)",
                    "spec.loader.exec_module(module)",
                    "assert resolve_exercise_notebook_path('ex004_sequence_debug_syntax') == expected",
                    "assert module._exercise_ast(1)",
                ]
            ),
        ]

        check = subprocess.run(
            command,
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert check.returncode == 0, (
            "Canonical ex004 default solution-mode resolution failed:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )

    def test_dry_run_workspace_canonical_ex004_uses_exercise_local_export(
        self,
        repo_root: Path,
    ) -> None:
        """Test packaged canonical ex004 exports exercise-local support under exercises/."""
        from scripts.template_repo_cli.cli import main

        with tempfile.TemporaryDirectory(dir=repo_root) as tmpdir:
            output_dir = Path(tmpdir) / "template_output"
            source_expectations = (
                repo_root
                / "exercises"
                / "sequence"
                / "ex004_sequence_debug_syntax"
                / "tests"
                / "expectations.py"
            ).resolve()

            result = main(
                [
                    "--dry-run",
                    "--output-dir",
                    str(output_dir),
                    "create",
                    "--exercise-keys",
                    "ex004_sequence_debug_syntax",
                    "--repo-name",
                    "test-repo",
                ]
            )

            assert result == 0
            assert output_dir.exists()
            assert (
                output_dir
                / "exercises"
                / "sequence"
                / "ex004_sequence_debug_syntax"
                / "notebooks"
                / "student.ipynb"
            ).exists()
            exported_test = (
                output_dir
                / "exercises"
                / "sequence"
                / "ex004_sequence_debug_syntax"
                / "tests"
                / "test_ex004_sequence_debug_syntax.py"
            )
            exported_expectations = exported_test.with_name("expectations.py")
            assert exported_test.exists()
            assert exported_expectations.exists()
            assert (output_dir / "exercises").is_dir()
            assert source_expectations.exists()

            shadow_root = Path(tmpdir) / "shadow_packages"
            shadow_package = shadow_root / "exercise_metadata"
            shadow_package.mkdir(parents=True)
            (shadow_package / "__init__.py").write_text("", encoding="utf-8")
            (shadow_package / "resolver.py").write_text(
                'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 test")\n',
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PYTUTOR_ACTIVE_VARIANT"] = "student"
            existing_pythonpath = env.get("PYTHONPATH")
            env["PYTHONPATH"] = (
                f"{shadow_root}{os.pathsep}{existing_pythonpath}"
                if existing_pythonpath
                else str(shadow_root)
            )

            command = [
                sys.executable,
                "-c",
                "\n".join(
                    [
                        "from pathlib import Path",
                        "import importlib.util",
                        "module_path = Path.cwd() / 'exercises' / 'sequence' / 'ex004_sequence_debug_syntax' / 'tests' / 'expectations.py'",
                        "spec = importlib.util.spec_from_file_location('packaged_ex004_expectations', module_path)",
                        "assert spec is not None and spec.loader is not None",
                        "module = importlib.util.module_from_spec(spec)",
                        "spec.loader.exec_module(module)",
                        f"source_expectations = Path({str(source_expectations)!r}).resolve()",
                        "assert source_expectations.exists()",
                        "assert module_path.resolve() != source_expectations",
                        "assert module.EX004_MIN_EXPLANATION_LENGTH == 50",
                        "assert module.EX004_EXPECTED_SINGLE_LINE[1] == 'Hello World!'",
                    ]
                ),
            ]

            check = subprocess.run(
                command,
                cwd=output_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            assert check.returncode == 0, (
                "Packaged canonical ex004 smoke check failed:\n"
                f"stdout:\n{check.stdout}\n"
                f"stderr:\n{check.stderr}"
            )

    def test_dry_run_workspace_ex004_subset_imports_checker_apis_without_ex002(
        self,
        tmp_path: Path,
    ) -> None:
        """Ex004-only exports can run checker APIs without importing source metadata."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex004_sequence_debug_syntax",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 subset checks")\n',
            encoding="utf-8",
        )
        (shadow_package / "resolver.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 subset checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "student"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "\n".join(
                [
                    "from exercise_runtime_support.exercise_framework import run_notebook_check",
                    "from exercise_runtime_support.student_checker import check_exercise",
                    "framework_results = run_notebook_check('ex004_sequence_debug_syntax')",
                    "assert len(framework_results) == 1, framework_results",
                    "assert framework_results[0].label, framework_results",
                    "check_exercise('ex004_sequence_debug_syntax')",
                ]
            ),
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"

        assert check.returncode == 0, (
            "Packaged ex004 subset checker import failed:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )
        assert "exercise_metadata must not be imported" not in combined_output
        assert "Exercise 1" in check.stdout

    def test_dry_run_workspace_ex004_solution_variant_uses_solution_mirror(
        self,
        tmp_path: Path,
    ) -> None:
        """Ex004-only exports can run solution checks from an added packaged mirror."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex004_sequence_debug_syntax",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        exported_notebook = (
            output_dir
            / "exercises"
            / "sequence"
            / "ex004_sequence_debug_syntax"
            / "notebooks"
            / "student.ipynb"
        )
        solution_mirror = (
            output_dir
            / "exercises"
            / "sequence"
            / "ex004_sequence_debug_syntax"
            / "notebooks"
            / "solution.ipynb"
        )
        solution_mirror.parent.mkdir(parents=True, exist_ok=True)
        solution_mirror.write_bytes(exported_notebook.read_bytes())
        exported_notebook.unlink()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )
        (shadow_package / "resolver.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "solution"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "\n".join(
                [
                    "from exercise_runtime_support.exercise_framework import run_notebook_check",
                    "from exercise_runtime_support.student_checker import check_exercise",
                    "framework_results = run_notebook_check('ex004_sequence_debug_syntax')",
                    "assert len(framework_results) == 1, framework_results",
                    "assert framework_results[0].label, framework_results",
                    "check_exercise('ex004_sequence_debug_syntax')",
                ]
            ),
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"

        assert check.returncode == 0, (
            "Packaged ex004 solution mirror checks failed:\n"
            f"stdout:\n{check.stdout}\n"
            f"stderr:\n{check.stderr}"
        )
        assert "exercise_metadata must not be imported" not in combined_output
        assert "Exercise 1" in check.stdout

    def test_dry_run_workspace_ex004_solution_variant_fails_without_solution_mirror(
        self,
        tmp_path: Path,
    ) -> None:
        """Packaged ex004 solution mode fails early when no solution mirror is exported."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex004_sequence_debug_syntax",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )
        (shadow_package / "resolver.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "solution"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.exercise_framework import run_notebook_check; "
            "run_notebook_check('ex004_sequence_debug_syntax')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"
        expected_solution_mirror = (
            output_dir
            / "exercises"
            / "sequence"
            / "ex004_sequence_debug_syntax"
            / "notebooks"
            / "solution.ipynb"
        )

        assert check.returncode != 0
        assert (
            "Metadata-free packaged repositories do not include solution notebooks"
            in combined_output
        )
        assert str(expected_solution_mirror) in combined_output
        assert "Notebook not found:" not in combined_output
        assert "No such file or directory" not in combined_output
        assert "exercise_metadata must not be imported" not in combined_output

    def test_dry_run_workspace_ex004_solution_variant_checker_api_fails_without_solution_mirror(
        self,
        tmp_path: Path,
    ) -> None:
        """Packaged ex004 solution mode fails early through the checker API too."""
        from scripts.template_repo_cli.cli import main

        output_dir = tmp_path / "template_output"

        result = main(
            [
                "--dry-run",
                "--output-dir",
                str(output_dir),
                "create",
                "--exercise-keys",
                "ex004_sequence_debug_syntax",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        assert output_dir.exists()

        shadow_root = tmp_path / "shadow_packages"
        shadow_package = shadow_root / "exercise_metadata"
        shadow_package.mkdir(parents=True)
        (shadow_package / "__init__.py").write_text("", encoding="utf-8")
        (shadow_package / "registry.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )
        (shadow_package / "resolver.py").write_text(
            'raise RuntimeError("exercise_metadata must not be imported in packaged ex004 solution checks")\n',
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTUTOR_ACTIVE_VARIANT"] = "solution"
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{shadow_root}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(shadow_root)
        )

        command = [
            sys.executable,
            "-c",
            "from exercise_runtime_support.student_checker import check_exercise; "
            "check_exercise('ex004_sequence_debug_syntax')",
        ]

        check = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{check.stdout}\n{check.stderr}"
        expected_solution_mirror = (
            output_dir
            / "exercises"
            / "sequence"
            / "ex004_sequence_debug_syntax"
            / "notebooks"
            / "solution.ipynb"
        )

        assert check.returncode != 0
        assert (
            "Metadata-free packaged repositories do not include solution notebooks"
            in combined_output
        )
        assert str(expected_solution_mirror) in combined_output
        assert "Notebook not found:" not in combined_output
        assert "No such file or directory" not in combined_output
        assert "exercise_metadata must not be imported" not in combined_output


class TestEndToEndErrorRecovery:
    """Tests for error handling in full flow."""

    @patch("subprocess.run")
    def test_end_to_end_error_recovery(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Test error handling in full flow."""
        from scripts.template_repo_cli.cli import main

        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error")

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

    def test_cli_list_command(
        self,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test list command output."""
        from scripts.template_repo_cli.cli import main

        result = main(["list"])

        assert result == 0

        # Should output some exercises
        captured: CaptureResult[str] = capsys.readouterr()
        assert len(captured.out) > 0

    def test_cli_list_with_construct_filter(
        self,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
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
    def test_cli_create_command(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
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
    def test_cli_create_defaults_to_template(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Create should mark repository as a template by default."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called: GitHubCreateKwargs = {}

        def fake_create(
            self: GitHubClient,
            repo_name: str,
            workspace: Path,
            **kwargs: object,
        ) -> GitHubCreateResult:
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with (
            patch.object(GitHubClient, "create_repository", new=fake_create),
            patch.object(GitHubClient, "check_gh_installed",
                         return_value=True),
            patch.object(
                GitHubClient,
                "check_scopes",
                return_value={
                    "authenticated": True,
                    "has_scopes": True,
                    "scopes": ["repo"],
                    "missing_scopes": [],
                },
            ),
            patch.object(GitHubClient, "check_authentication",
                         return_value=True),
        ):
            result = main(["create", "--construct", "sequence",
                          "--repo-name", "test-repo"])

        assert result == 0
        # By default the CLI should set template=True
        assert called.get("template") is True
        assert called.get("template_repo") is None

    @patch("subprocess.run")
    def test_cli_create_with_no_template_flag(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Passing --no-template should disable template creation."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called: GitHubCreateKwargs = {}

        def fake_create(
            self: GitHubClient,
            repo_name: str,
            workspace: Path,
            **kwargs: object,
        ) -> GitHubCreateResult:
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with (
            patch.object(GitHubClient, "create_repository", new=fake_create),
            patch.object(GitHubClient, "check_gh_installed",
                         return_value=True),
            patch.object(
                GitHubClient,
                "check_scopes",
                return_value={
                    "authenticated": True,
                    "has_scopes": True,
                    "scopes": ["repo"],
                    "missing_scopes": [],
                },
            ),
            patch.object(GitHubClient, "check_authentication",
                         return_value=True),
        ):
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
    def test_cli_create_with_template_repo_argument(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        """Passing --template-repo should forward the value."""
        from scripts.template_repo_cli.cli import main
        from scripts.template_repo_cli.core.github import GitHubClient

        called: GitHubCreateKwargs = {}

        def fake_create(
            self: GitHubClient,
            repo_name: str,
            workspace: Path,
            **kwargs: object,
        ) -> GitHubCreateResult:
            called.update(kwargs)
            return {"success": True, "dry_run": True}

        with (
            patch.object(GitHubClient, "create_repository", new=fake_create),
            patch.object(GitHubClient, "check_gh_installed",
                         return_value=True),
            patch.object(
                GitHubClient,
                "check_scopes",
                return_value={
                    "authenticated": True,
                    "has_scopes": True,
                    "scopes": ["repo"],
                    "missing_scopes": [],
                },
            ),
            patch.object(GitHubClient, "check_authentication",
                         return_value=True),
        ):
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
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_permission_hint(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_create: MagicMock,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Display guidance when GitHub rejects repo creation for integrations."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
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
        captured: CaptureResult[str] = capsys.readouterr()
        assert "GitHub authentication token cannot create repositories" in captured.err

    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_permission_hint_unset_env_token(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_create: MagicMock,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Hint to unset GITHUB_TOKEN when it blocks login."""
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_create.return_value = {
            "success": False,
            "error": "GraphQL: Resource not accessible by integration (createRepository)",
        }

        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "ghu_fake"}, clear=True),
            patch("builtins.input", return_value="n"),
        ):
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
        captured: CaptureResult[str] = capsys.readouterr()
        assert "unset github_token" in captured.err.lower()

    @patch("builtins.input", return_value="y")
    @patch("scripts.template_repo_cli.cli.subprocess.run")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.create_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_permission_hint_reauth_flow(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_create: MagicMock,
        mock_subprocess_run: MagicMock,
        mock_input: MagicMock,
        repo_root: Path,
    ) -> None:
        """Offer to unset token and rerun `gh auth login`."""
        from scripts.template_repo_cli.cli import main

        # First prerequisite check: scopes present
        # After error: check scopes again (missing)
        # Second prerequisite check: scopes present
        mock_scopes.side_effect = [
            {
                "authenticated": True,
                "has_scopes": True,
                "scopes": ["repo"],
                "missing_scopes": [],
            },  # First prereq check
            {
                "authenticated": True,
                "has_scopes": False,
                "scopes": [],
                "missing_scopes": ["repo"],
            },  # After first create error
            {
                "authenticated": True,
                "has_scopes": True,
                "scopes": ["repo"],
                "missing_scopes": [],
            },  # Second prereq check
        ]
        mock_create.side_effect = [
            {
                "success": False,
                "error": "GraphQL: Resource not accessible by integration (createRepository)",
            },
            {"success": True, "html_url": "https://github.com/user/test-repo"},
        ]

        def fake_subprocess_run(
            cmd: CommandSequence,
            **kwargs: object,
        ) -> MagicMock:
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
        EXPECT_CREATE_CALLS = 2
        assert mock_create.call_count == EXPECT_CREATE_CALLS
        mock_subprocess_run.assert_any_call(
            ["gh", "auth", "login"], check=False)

    @patch("subprocess.run")
    def test_cli_create_with_all_options(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
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
    def test_cli_verbose_mode(
        self,
        mock_run: MagicMock,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
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
        captured: CaptureResult[str] = capsys.readouterr()
        assert len(captured.out) > 0


class TestCliOutputDir:
    """Tests for custom output directory."""

    @patch("subprocess.run")
    def test_cli_custom_output_dir(
        self,
        mock_run: MagicMock,
        repo_root: Path,
        temp_dir: Path,
    ) -> None:
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


class TestCliUpdateRepo:
    """Tests for update-repo command."""

    @patch("subprocess.run")
    def test_cli_update_dry_run(
        self,
        mock_run: MagicMock,
        repo_root: Path,
    ) -> None:
        from scripts.template_repo_cli.cli import main

        result = main(
            [
                "--dry-run",
                "update-repo",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.push_to_existing_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_update_calls_push_when_repo_exists(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_push: MagicMock,
        mock_check_exists: MagicMock,
        repo_root: Path,
    ) -> None:
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True
        mock_push.return_value = {"success": True}

        result = main(
            [
                "update-repo",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 0
        mock_check_exists.assert_called_once()
        mock_push.assert_called_once()

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.push_to_existing_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_update_fails_when_repo_missing(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_push: MagicMock,
        mock_check_exists: MagicMock,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = False

        result = main(
            [
                "update-repo",
                "--construct",
                "sequence",
                "--repo-name",
                "missing-repo",
            ]
        )

        assert result == 1
        mock_push.assert_not_called()
        captured: CaptureResult[str] = capsys.readouterr()
        assert "does not exist" in captured.err.lower()

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.push_to_existing_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_update_allows_owner_prefixed_repo_name(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_push: MagicMock,
        mock_check_exists: MagicMock,
        repo_root: Path,
    ) -> None:
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True
        mock_push.return_value = {"success": True}

        result = main(
            [
                "update-repo",
                "--construct",
                "sequence",
                "--repo-name",
                "owner/test-repo",
            ]
        )

        assert result == 0
        mock_push.assert_called_once()

    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_repository_exists")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.push_to_existing_repository")
    @patch("scripts.template_repo_cli.core.github.GitHubClient.check_scopes")
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_authentication",
        return_value=True,
    )
    @patch(
        "scripts.template_repo_cli.core.github.GitHubClient.check_gh_installed",
        return_value=True,
    )
    def test_cli_update_prompts_for_owner_when_remote_missing(  # noqa: PLR0913
        self,
        mock_installed: MagicMock,
        mock_auth: MagicMock,
        mock_scopes: MagicMock,
        mock_push: MagicMock,
        mock_check_exists: MagicMock,
        repo_root: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from scripts.template_repo_cli.cli import main

        mock_scopes.return_value = {
            "authenticated": True,
            "has_scopes": True,
            "scopes": ["repo"],
            "missing_scopes": [],
        }
        mock_check_exists.return_value = True
        mock_push.return_value = {
            "success": False,
            "error": "push failed",
            "remote_url": "https://github.com/test-repo.git",
        }

        result = main(
            [
                "update-repo",
                "--construct",
                "sequence",
                "--repo-name",
                "test-repo",
            ]
        )

        assert result == 1
        captured: CaptureResult[str] = capsys.readouterr()
        assert "owner" in captured.err.lower()
        assert "owner/repo" in captured.err.lower()
