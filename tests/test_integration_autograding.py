from __future__ import annotations

import base64
import json
import subprocess
import sys
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NotRequired, TypeAlias, TypedDict, cast

from pytest import approx  # pyright: ignore[reportUnknownVariableType]

from tests.helpers import build_autograde_env

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "scripts" / "build_autograde_payload.py"
PLUGIN_NAME = "tests.autograde_plugin"
PLUGIN_FLAG = f"-p {PLUGIN_NAME}"


EnvOverrides: TypeAlias = Mapping[str, str | None] | None


class AutogradeResultsDict(TypedDict):
    status: str
    max_score: float | int | str
    tests: list[dict[str, Any]]
    score: NotRequired[float | int | str | None]


class AutogradePayloadDict(TypedDict):
    status: str
    max_score: float | int | str
    score: float | int | str
    tests: list[dict[str, Any]]


def _run_pytest_with_plugin(
    cwd: Path,
    *,
    results_path: Path,
    pytest_args: list[str],
    env_overrides: EnvOverrides = None,
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
        env=build_autograde_env(overrides=env_overrides),
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
    env_overrides: EnvOverrides = None,
    bypass_env_validation: bool = False,
) -> subprocess.CompletedProcess[str]:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cli_args = [f"--results-json={results_path}", f"--output={output_path}"]
    for chunk in pytest_args:
        cli_args.append(f"--pytest-args={chunk}")

    env = build_autograde_env(overrides=env_overrides)

    if bypass_env_validation:
        override_code = textwrap.dedent(
            f"""
            import sys
            from scripts import build_autograde_payload as cli

            cli.validate_environment = lambda: None
            raise SystemExit(cli.main({cli_args!r}))
            """
        )
        command = [sys.executable, "-c", override_code]
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


NumericValue: TypeAlias = float | int | str
ScoreValue: TypeAlias = NumericValue | None


def _normalise_score(value: ScoreValue) -> float:
    return float(value) if value is not None else 0.0


def _load_results(path: Path) -> AutogradeResultsDict:
    return cast(AutogradeResultsDict, json.loads(path.read_text(encoding="utf-8")))


def _assert_payload_matches_results(
    payload: AutogradePayloadDict,
    results: AutogradeResultsDict,
) -> None:
    assert payload["status"] == results["status"]
    assert approx(_normalise_score(payload["max_score"])) == approx(
        _normalise_score(results["max_score"])
    )
    assert len(payload["tests"]) == len(results["tests"])

    recorded_score = _normalise_score(results.get("score"))
    assert approx(_normalise_score(payload["score"])) == approx(recorded_score)


def _assert_cli_alignment(
    cli_run: subprocess.CompletedProcess[str],
    manual_run: subprocess.CompletedProcess[str],
    payload: AutogradePayloadDict,
    results: AutogradeResultsDict,
) -> None:
    assert cli_run.returncode == manual_run.returncode
    _assert_payload_matches_results(payload, results)


def _expect_solution_success(
    manual_run: subprocess.CompletedProcess[str],
    payload: AutogradePayloadDict,
    results: AutogradeResultsDict,
) -> None:
    assert manual_run.returncode == 0
    assert payload["status"] == "pass"
    assert results["status"] == "pass"
    assert approx(_normalise_score(payload["score"])) == approx(
        _normalise_score(payload["max_score"])
    )
    assert approx(_normalise_score(results.get("score"))) == approx(
        _normalise_score(results["max_score"])
    )


def _expect_student_failure(
    manual_run: subprocess.CompletedProcess[str],
    payload: AutogradePayloadDict,
    results: AutogradeResultsDict,
) -> None:
    if payload["status"] == "pass" and _normalise_score(payload["score"]) == _normalise_score(
        payload["max_score"]
    ):
        raise AssertionError(
            "Student notebooks unexpectedly passed the failing fixture; update the fixture "
            "or ensure the student run uses the intended notebooks directory."
        )

    assert manual_run.returncode != 0
    assert results["status"] == "fail"
    assert payload["status"] == "fail"
    assert _normalise_score(results.get("score")) < _normalise_score(results["max_score"])
    assert _normalise_score(payload["score"]) < _normalise_score(payload["max_score"])


def _assert_solution_vs_student(
    solution_payload: AutogradePayloadDict,
    student_payload: AutogradePayloadDict,
) -> None:
    assert solution_payload["status"] != student_payload["status"]
    assert _normalise_score(solution_payload["score"]) > _normalise_score(student_payload["score"])
    assert approx(_normalise_score(solution_payload["max_score"])) == approx(
        _normalise_score(student_payload["max_score"])
    )


def _run_manual_autograde(
    working_dir: Path,
    target_test: Path,
    env_overrides: EnvOverrides,
) -> tuple[subprocess.CompletedProcess[str], AutogradeResultsDict]:
    results_path = working_dir / "manual" / "results.json"
    run = _run_pytest_with_plugin(
        REPO_ROOT,
        results_path=results_path,
        pytest_args=[str(target_test)],
        env_overrides=env_overrides,
    )
    return run, _load_results(results_path)


def _run_cli_autograde(
    working_dir: Path,
    target_test: Path,
    env_overrides: EnvOverrides,
    *,
    bypass_env_validation: bool = False,
) -> tuple[subprocess.CompletedProcess[str], AutogradePayloadDict]:
    results_path = working_dir / "cli" / "results.json"
    output_path = working_dir / "cli" / "payload.txt"
    run = _run_cli(
        REPO_ROOT,
        results_path=results_path,
        output_path=output_path,
        pytest_args=[PLUGIN_FLAG, str(target_test)],
        env_overrides=env_overrides,
        bypass_env_validation=bypass_env_validation,
    )
    return run, cast(AutogradePayloadDict, _decode_payload(output_path))


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
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": None},
    )
    assert manual_results.exists()
    recorded = _load_results(manual_results)

    cli_results = project_dir / "tmp" / "cli" / "results.json"
    cli_output = project_dir / "tmp" / "cli" / "payload.txt"
    cli_run = _run_cli(
        project_dir,
        results_path=cli_results,
        output_path=cli_output,
        pytest_args=[PLUGIN_FLAG, str(test_file)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": None},
    )

    payload = cast(AutogradePayloadDict, _decode_payload(cli_output))
    _assert_cli_alignment(cli_run, manual_run, payload, recorded)


def test_autograding_with_real_exercise(tmp_path: Path) -> None:
    target_test = tmp_path / "test_autograde_student_failure.py"
    target_test.write_text(
        textwrap.dedent(
            """
            import os


            def test_solution_notebook_env() -> None:
                assert os.environ.get("PYTUTOR_NOTEBOOKS_DIR") == "notebooks/solutions", (
                    "Solution autograding must run with PYTUTOR_NOTEBOOKS_DIR='notebooks/solutions'; "
                    "student runs intentionally fail when this is set to 'notebooks'."
                )
            """
        ).lstrip(),
        encoding="utf-8",
    )

    solution_env: EnvOverrides = {"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"}
    solution_dir = tmp_path / "solutions"
    sol_run, sol_results = _run_manual_autograde(solution_dir, target_test, solution_env)
    sol_cli_run, sol_payload = _run_cli_autograde(
        solution_dir,
        target_test,
        solution_env,
        bypass_env_validation=True,
    )

    _assert_cli_alignment(sol_cli_run, sol_run, sol_payload, sol_results)
    _expect_solution_success(sol_run, sol_payload, sol_results)

    student_env: EnvOverrides = {"PYTUTOR_NOTEBOOKS_DIR": "notebooks"}
    student_dir = tmp_path / "students"
    student_run, student_results = _run_manual_autograde(student_dir, target_test, student_env)
    student_cli_run, student_payload = _run_cli_autograde(student_dir, target_test, student_env)

    _assert_cli_alignment(student_cli_run, student_run, student_payload, student_results)
    _expect_student_failure(student_run, student_payload, student_results)

    _assert_solution_vs_student(sol_payload, student_payload)
