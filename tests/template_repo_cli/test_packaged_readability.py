"""Offline regression checks for readability in exported student templates."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

from scripts.template_repo_cli.core.packager import TemplatePackager

_EXERCISE_KEY = "ex002_sequence_modify_basics"


def _export_exercise(repo_root: Path, output: Path) -> tuple[TemplatePackager, Path]:
    """Export one canonical exercise and return its packager and notebook path."""
    from scripts.template_repo_cli.core.collector import FileCollector

    packager = TemplatePackager(repo_root)
    files = FileCollector(repo_root).collect_multiple([_EXERCISE_KEY])
    packager.copy_exercise_files(output, files)
    packager.copy_construct_resources(output, [_EXERCISE_KEY])
    packager.copy_template_base_files(output)
    packager.generate_readme(output, "Test", [_EXERCISE_KEY])
    notebook = output / "exercises/sequence" / _EXERCISE_KEY / "notebooks/student.ipynb"
    return packager, notebook


def _run_exported_self_check(output: Path, exercise_key: str = _EXERCISE_KEY) -> str:
    """Run only exported checker modules in the test runner's Ruff environment."""
    env = os.environ.copy()
    env.pop("PYTUTOR_ACTIVE_VARIANT", None)
    env.pop("PYTHONPATH", None)
    command_source = "\n".join(
        [
            "import json",
            "import exercise_metadata.resolver as metadata_resolver",
            "import exercise_runtime_support.student_checker as student_checker",
            "import exercise_runtime_support.student_checker.readability as readability",
            "print('MODULE_ORIGINS=' + json.dumps({",
            "    'student_checker': student_checker.__file__,",
            "    'readability': readability.__file__,",
            "    'metadata_resolver': metadata_resolver.__file__,",
            "}, sort_keys=True))",
            "student_checker.run_notebook_checks(" + repr(exercise_key) + ")",
        ]
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            command_source,
        ],
        cwd=output,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    output_lines = result.stdout.splitlines()
    assert output_lines[0].startswith("MODULE_ORIGINS=")
    origins = cast(dict[str, str], json.loads(output_lines[0].removeprefix("MODULE_ORIGINS=")))
    assert all(Path(origin).is_relative_to(output) for origin in origins.values())
    return result.stdout


def _write_cell(notebook_path: Path, tag: str, source: str) -> None:
    notebook = cast(dict[str, Any], json.loads(notebook_path.read_text(encoding="utf-8")))
    for cell in cast(list[dict[str, Any]], notebook["cells"]):
        if tag in cell.get("metadata", {}).get("tags", []):
            cell["source"] = source.splitlines(keepends=True)
            notebook_path.write_text(json.dumps(notebook), encoding="utf-8")
            return
    raise AssertionError(f"Missing tagged cell {tag}")


def test_exported_default_student_self_check_shows_functional_and_readability_failures(
    repo_root: Path, tmp_path: Path
) -> None:
    """Export keeps the starter's functional failure and adds readability rows."""
    output = tmp_path / "student-template"
    output.mkdir()
    packager, notebook = _export_exercise(repo_root, output)
    _write_cell(notebook, "exercise1", 'greetingMessage = "Hello World!"\nprint(greetingMessage)\n')

    failing_text = _run_exported_self_check(output)

    assert "N816" in failing_text
    assert "Functional summary: 14 passed, 16 failed" in failing_text
    assert "Readability summary: 9 passed, 1 failed; 10 cells analysed; 0 syntax-blocked" in (
        failing_text
    )
    assert "Overall self-check: FAIL" in failing_text

    _write_cell(notebook, "exercise1", 'print("Hello World!")\n')
    corrected_text = _run_exported_self_check(output)

    assert "N816" not in corrected_text
    assert "Functional summary: 14 passed, 16 failed" in corrected_text
    assert "Readability summary: 10 passed, 0 failed; 10 cells analysed; 0 syntax-blocked" in (
        corrected_text
    )
    assert "Overall self-check: FAIL" in corrected_text
    assert packager.validate_package(output)
    assert not (output / "exercises/sequence" / _EXERCISE_KEY / "notebooks/solution.ipynb").exists()
    assert notebook.is_file()


def test_synthetic_export_reports_combined_pass_without_shipping_fixture_tests(
    repo_root: Path, tmp_path: Path
) -> None:
    """A minimal synthetic starter can pass both checks without fixture leakage."""
    from scripts.template_repo_cli.core.collector import ExerciseFiles

    key = "ex999_sequence_make_packaged_selfcheck"
    source_exercise = tmp_path / "source" / "exercises" / "sequence" / key
    (source_exercise / "notebooks").mkdir(parents=True)
    (source_exercise / "tests").mkdir()
    metadata = source_exercise / "exercise.json"
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exercise_key": key,
                "exercise_id": 999,
                "slug": key,
                "title": "Packaged Self Check",
                "construct": "sequence",
                "exercise_type": "make",
                "parts": 1,
            }
        ),
        encoding="utf-8",
    )
    notebook_source: dict[str, Any] = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ['print("Ready")\n'],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                    f"run_notebook_checks('{key}')\n",
                ],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook = source_exercise / "notebooks" / "student.ipynb"
    notebook.write_text(json.dumps(notebook_source), encoding="utf-8")
    test_file = source_exercise / "tests" / f"test_{key}.py"
    exercise_files: ExerciseFiles = {
        "exercise_json": metadata,
        "exercise_json_export": Path("exercises/sequence") / key / "exercise.json",
        "notebook": notebook,
        "notebook_export": Path("exercises/sequence") / key / "notebooks/student.ipynb",
        "test": test_file,
        "tests_export_dir": Path("exercises/sequence") / key / "tests",
    }
    output = tmp_path / "synthetic-template"
    output.mkdir()
    packager = TemplatePackager(repo_root)
    packager.copy_exercise_files(output, {key: exercise_files})
    packager.copy_template_base_files(output)
    (output / "README.md").write_text("# Synthetic template\n", encoding="utf-8")

    template_manifest = tomllib.loads((output / "pyproject.toml").read_text(encoding="utf-8"))
    assert template_manifest["project"]["dependencies"]
    assert "ruff==0.14.13" in template_manifest["project"]["dependencies"]
    assert (
        output / "exercise_runtime_support" / "student_checker" / "readability.py"
    ).read_bytes() == (
        repo_root / "exercise_runtime_support" / "student_checker" / "readability.py"
    ).read_bytes()

    text = _run_exported_self_check(output, key)

    assert "Functional summary: 1 passed, 0 failed" in text
    assert "Readability summary: 1 passed, 0 failed" in text
    assert "Overall self-check: PASS" in text
    exercise_dir = output / "exercises/sequence" / key
    assert (exercise_dir / "notebooks/student.ipynb").is_file()
    assert not (exercise_dir / "notebooks/solution.ipynb").exists()
    assert not list((exercise_dir / "tests").iterdir())
    assert packager.validate_package(output)


def test_explicit_solution_export_keeps_missing_solution_resolution_contract(
    repo_root: Path, tmp_path: Path
) -> None:
    """Packaged templates remain student-only; solution resolution still fails."""
    output = tmp_path / "student-template"
    output.mkdir()
    _, notebook = _export_exercise(repo_root, output)
    assert notebook.is_file()

    env = os.environ.copy()
    env["PYTUTOR_ACTIVE_VARIANT"] = "solution"
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from exercise_runtime_support.exercise_framework import resolve_exercise_notebook_path; "
            f"resolve_exercise_notebook_path('{_EXERCISE_KEY}')",
        ],
        cwd=output,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "expected notebook is missing" in result.stderr.lower()
    assert (
        str(output / "exercises/sequence" / _EXERCISE_KEY / "notebooks/solution.ipynb")
        in result.stderr
    )
    assert not (output / "exercises/sequence" / _EXERCISE_KEY / "notebooks/solution.ipynb").exists()
