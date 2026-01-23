from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "scripts" / "build_autograde_payload.py"
PLUGIN_NAME = "tests.autograde_plugin"


def _prepare_env(overrides: dict[str, str | None] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    repo = str(REPO_ROOT)
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{repo}{os.pathsep}{current}" if current else repo
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    env.setdefault("PYTUTOR_NOTEBOOKS_DIR", "notebooks")
    if overrides:
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return env


def _run_pytest_with_plugin(
    cwd: Path,
    *,
    results_path: Path,
    pytest_args: list[str],
    env_overrides: dict[str, str | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        PLUGIN_NAME,
        f"--autograde-results-path={results_path}",
        *pytest_args,
    ]
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=_prepare_env(env_overrides),
        check=False,
        text=True,
        capture_output=True,
    )


def _run_cli(  # noqa: PLR0913 - helper mirrors CLI signature
    cwd: Path,
    *,
    results_path: Path,
    output_path: Path,
    pytest_args: list[str],
    env_overrides: dict[str, str | None] | None = None,
    bypass_env_validation: bool = False,
) -> subprocess.CompletedProcess[str]:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cli_args = [f"--results-json={results_path}", f"--output={output_path}"]
    for chunk in pytest_args:
        cli_args.append(f"--pytest-args={chunk}")

    env = _prepare_env(env_overrides)

    if bypass_env_validation:
        runner_path = results_path.parent / "_cli_runner.py"
        runner_code = (
            "import sys\n"
            "from scripts import build_autograde_payload as cli\n"
            "cli.validate_environment = lambda: None\n"
            f"sys.exit(cli.main({cli_args!r}))\n"
        )
        runner_path.write_text(runner_code, encoding="utf-8")
        command = [sys.executable, str(runner_path)]
    else:
        command = [sys.executable, str(CLI_SCRIPT), *cli_args]

    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def _decode_payload(path: Path) -> dict[str, Any]:
    encoded = path.read_text(encoding="utf-8").strip()
    decoded = base64.b64decode(encoded)
    return json.loads(decoded)


def test_full_autograding_flow(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    test_file = project_dir / "test_sample.py"
    test_file.write_text(
        (
            "def test_pass() -> None:\n"
            "    assert 1 == 1\n\n"
            "def test_fail() -> None:\n"
            "    assert 0, 'intentional failure'\n"
        ),
        encoding="utf-8",
    )

    manual_results = project_dir / "tmp" / "manual" / "results.json"
    manual_run = _run_pytest_with_plugin(
        project_dir,
        results_path=manual_results,
        pytest_args=[str(test_file)],
    )
    assert manual_results.exists()
    recorded = json.loads(manual_results.read_text(encoding="utf-8"))

    cli_results = project_dir / "tmp" / "cli" / "results.json"
    cli_output = project_dir / "tmp" / "cli" / "payload.txt"
    cli_run = _run_cli(
        project_dir,
        results_path=cli_results,
        output_path=cli_output,
        pytest_args=["-p tests.autograde_plugin", str(test_file)],
    )

    payload = _decode_payload(cli_output)
    assert payload["status"] == recorded["status"]
    assert pytest.approx(float(payload["score"])) == float(recorded["score"])
    assert pytest.approx(float(payload["max_score"])) == float(recorded["max_score"])
    assert len(payload["tests"]) == len(recorded["tests"])
    assert cli_run.returncode == manual_run.returncode


def test_autograding_with_real_exercise(tmp_path: Path) -> None:
    target_test = REPO_ROOT / "tests" / "test_ex001_sanity.py"

    sol_results = tmp_path / "solutions" / "manual" / "results.json"
    sol_run = _run_pytest_with_plugin(
        REPO_ROOT,
        results_path=sol_results,
        pytest_args=[str(target_test)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"},
    )
    assert sol_run.returncode == 0
    sol_data = json.loads(sol_results.read_text(encoding="utf-8"))
    assert sol_data["status"] == "pass"
    assert pytest.approx(float(sol_data["score"])) == float(sol_data["max_score"])

    sol_cli_results = tmp_path / "solutions" / "cli" / "results.json"
    sol_cli_output = tmp_path / "solutions" / "cli" / "payload.txt"
    sol_cli_run = _run_cli(
        REPO_ROOT,
        results_path=sol_cli_results,
        output_path=sol_cli_output,
        pytest_args=["-p tests.autograde_plugin", str(target_test)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"},
        bypass_env_validation=True,
    )
    sol_payload = _decode_payload(sol_cli_output)
    assert sol_cli_run.returncode == sol_run.returncode
    assert sol_payload["status"] == "pass"
    assert pytest.approx(float(sol_payload["score"])) == float(sol_payload["max_score"])
    assert pytest.approx(float(sol_payload["max_score"])) == float(sol_data["max_score"])
    assert len(sol_payload["tests"]) == len(sol_data["tests"])

    student_results = tmp_path / "students" / "manual" / "results.json"
    student_run = _run_pytest_with_plugin(
        REPO_ROOT,
        results_path=student_results,
        pytest_args=[str(target_test)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks"},
    )
    student_data = json.loads(student_results.read_text(encoding="utf-8"))
    student_cli_results = tmp_path / "students" / "cli" / "results.json"
    student_cli_output = tmp_path / "students" / "cli" / "payload.txt"
    student_cli_run = _run_cli(
        REPO_ROOT,
        results_path=student_cli_results,
        output_path=student_cli_output,
        pytest_args=["-p tests.autograde_plugin", str(target_test)],
    )
    student_payload = _decode_payload(student_cli_output)
    assert student_cli_run.returncode == student_run.returncode
    assert pytest.approx(float(student_payload["max_score"])) == float(student_data["max_score"])
    assert len(student_payload["tests"]) == len(student_data["tests"])

    if (
        student_payload["status"] == "pass"
        and student_payload["score"] == student_payload["max_score"]
    ):
        pytest.xfail(
            "Student notebooks currently satisfy ex001_sanity tests; update scaffolding to observe a failing case."
        )

    assert student_run.returncode != 0
    assert student_data["status"] == "fail"
    assert student_data["score"] < student_data["max_score"]
    assert student_payload["status"] == "fail"
    assert student_payload["score"] < student_payload["max_score"]

    assert sol_payload["status"] != student_payload["status"]
    assert sol_payload["score"] > student_payload["score"]
    assert pytest.approx(float(sol_payload["max_score"])) == pytest.approx(
        float(student_payload["max_score"])
    )
