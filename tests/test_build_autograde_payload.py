from __future__ import annotations

import base64
import json
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import TypeAlias, TypedDict

import pytest

from tests.helpers import build_autograde_env

CLI_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_autograde_payload.py"
REPO_ROOT = CLI_SCRIPT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_autograde_payload  # noqa: E402

PLUGIN_FLAG = "-p tests.autograde_plugin"

EnvOverrides: TypeAlias = Mapping[str, str | None] | None


def _write_test_file(tmp_path: Path, content: str, *, name: str = "test_suite.py") -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


@pytest.fixture
def passing_test_file(tmp_path: Path) -> Iterator[Path]:
    """Provide a simple passing pytest suite for CLI smoke tests."""
    path = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    yield path


class NotebookDirScenario(TypedDict):
    env_overrides: dict[str, str | None]
    expected_returncode: int
    results_should_exist: bool
    stdout_fragment: str | None
    stderr_fragment: str | None


def _execute_cli(  # noqa: PLR0913
    cwd: Path,
    pytest_chunks: Iterable[str],
    *,
    env_overrides: EnvOverrides = None,
    results_path: Path | None = None,
    output_path: Path | None = None,
    summary_path: Path | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path | None]:
    results_path = results_path or cwd / "tmp" / "autograde" / "results.json"
    output_path = output_path or cwd / "tmp" / "autograde" / "payload.txt"
    args = [
        sys.executable,
        str(CLI_SCRIPT),
        f"--results-json={results_path}",
        f"--output={output_path}",
    ]
    if summary_path is not None:
        args.append(f"--summary={summary_path}")
    for chunk in pytest_chunks:
        args.append(f"--pytest-args={chunk}")
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        env=build_autograde_env(overrides=env_overrides),
        check=False,
        text=True,
        capture_output=True,
    )
    return completed, results_path, output_path, summary_path


def _set_cli_env(monkeypatch: pytest.MonkeyPatch) -> None:
    base_env = build_autograde_env()
    for key in ("PYTHONPATH", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTUTOR_NOTEBOOKS_DIR"):
        monkeypatch.setenv(key, base_env[key])


def test_cli_runs_pytest_successfully(tmp_path: Path, passing_test_file: Path) -> None:
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
    )
    assert completed.returncode == 0
    assert results_path.is_file()
    assert output_path.is_file()
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert len(payload["tests"]) == 1


def test_cli_propagates_pytest_exit_code(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_failure() -> None:
            assert False
        """,
    )
    completed, results_path, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
    )
    assert completed.returncode == 1
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"


def test_cli_zeroes_scores_when_student_notebooks_fail(tmp_path: Path) -> None:
    """Verify that failing tests with PYTUTOR_NOTEBOOKS_DIR=notebooks yield zero scores."""
    test_file = _write_test_file(
        tmp_path,
        """
        def test_failure() -> None:
            assert False, "Expected failure"

        def test_another_failure() -> None:
            assert 1 == 2
        """,
    )
    completed, results_path, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks"},
    )
    assert completed.returncode == 1
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["score"] == 0.0
    for test in payload["tests"]:
        assert test["score"] == 0.0


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(
            {
                "env_overrides": {"PYTUTOR_NOTEBOOKS_DIR": None},
                "expected_returncode": 0,
                "results_should_exist": True,
                "stdout_fragment": "Environment: PYTUTOR_NOTEBOOKS_DIR=<unset>",
                "stderr_fragment": None,
            },
            id="unset",
        ),
        pytest.param(
            {
                "env_overrides": {"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"},
                "expected_returncode": 0,
                "results_should_exist": True,
                "stdout_fragment": None,
                "stderr_fragment": None,
            },
            id="solutions-posix",
        ),
        pytest.param(
            {
                "env_overrides": {"PYTUTOR_NOTEBOOKS_DIR": "notebooks\\solutions"},
                "expected_returncode": 0,
                "results_should_exist": True,
                "stdout_fragment": None,
                "stderr_fragment": None,
            },
            id="solutions-windows",
        ),
        pytest.param(
            {
                "env_overrides": {"PYTUTOR_NOTEBOOKS_DIR": "notebooks/custom"},
                "expected_returncode": 1,
                "results_should_exist": False,
                "stdout_fragment": None,
                "stderr_fragment": (
                    "Error: PYTUTOR_NOTEBOOKS_DIR must be unset or one of 'notebooks', 'notebooks/solutions'"
                ),
            },
            id="custom-invalid",
        ),
    ],
)
def test_cli_notebook_dir_validation(
    tmp_path: Path,
    passing_test_file: Path,
    scenario: NotebookDirScenario,
) -> None:
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
        env_overrides=scenario["env_overrides"],
        results_path=results_path,
    )
    assert completed.returncode == scenario["expected_returncode"]
    assert results_path.exists() is scenario["results_should_exist"]
    stdout_fragment = scenario["stdout_fragment"]
    if stdout_fragment is not None:
        assert stdout_fragment in completed.stdout
    stderr_fragment = scenario["stderr_fragment"]
    if stderr_fragment is not None:
        assert stderr_fragment in completed.stderr


def test_cli_creates_output_directories(tmp_path: Path, passing_test_file: Path) -> None:
    results_path = tmp_path / "nested" / "dir" / "results.json"
    output_path = tmp_path / "another" / "dir" / "payload.txt"
    summary_path = tmp_path / "summary" / "dir" / "data.json"
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
        results_path=results_path,
        output_path=output_path,
        summary_path=summary_path,
    )
    assert completed.returncode == 0
    assert results_path.is_file()
    assert output_path.is_file()
    assert summary_path.is_file()


def test_cli_writes_base64_payload(tmp_path: Path, passing_test_file: Path) -> None:
    completed, _, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
    )
    assert completed.returncode == 0
    payload_text = output_path.read_text(encoding="utf-8")
    assert payload_text.endswith("\n")
    encoded = payload_text.strip()
    assert encoded
    base64.b64decode(encoded)


def test_cli_writes_summary_json(tmp_path: Path, passing_test_file: Path) -> None:
    summary_path = tmp_path / "tmp" / "autograde" / "summary.json"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
        summary_path=summary_path,
    )
    assert completed.returncode == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "pass"
    assert len(summary["tests"]) == 1


def test_cli_prints_summary_table(tmp_path: Path, passing_test_file: Path) -> None:
    completed, results_path, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
    )
    assert completed.returncode == 0
    stdout = completed.stdout
    assert "=== Autograde Summary ===" in stdout
    assert "Task Breakdown:" in stdout
    results = json.loads(results_path.read_text(encoding="utf-8"))
    total = len(results["tests"])
    passed = sum(1 for test in results["tests"] if test["status"] == "pass")
    assert f"Tests Passed: {passed}/{total}" in stdout


def test_cli_writes_github_outputs(tmp_path: Path, passing_test_file: Path) -> None:
    gh_output = tmp_path / "gh_output.txt"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
        env_overrides={"GITHUB_OUTPUT": str(gh_output)},
    )
    assert completed.returncode == 0
    output_text = gh_output.read_text(encoding="utf-8")
    assert "encoded_payload=" in output_text
    assert "overall_status=pass" in output_text
    assert "earned_score=1.0" in output_text
    assert "max_score=1.0" in output_text


def test_cli_handles_missing_results_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    passing_test_file: Path,
) -> None:
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    output_path = tmp_path / "tmp" / "autograde" / "payload.txt"

    original_run_pytest = build_autograde_payload.run_pytest

    def run_pytest_and_remove(pytest_args: Sequence[str], path: Path) -> int:
        code = original_run_pytest(pytest_args, path)
        if path.exists():
            path.unlink()
        return code

    monkeypatch.setattr(build_autograde_payload, "run_pytest", run_pytest_and_remove)
    _set_cli_env(monkeypatch)

    exit_code = build_autograde_payload.main(
        [
            f"--results-json={results_path}",
            f"--output={output_path}",
            f"--pytest-args={PLUGIN_FLAG}",
            f"--pytest-args={passing_test_file}",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert f"Error: Autograde results not found at {results_path}" in captured.err
    assert not output_path.exists()


def test_cli_handles_malformed_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    passing_test_file: Path,
) -> None:
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    output_path = tmp_path / "tmp" / "autograde" / "payload.txt"

    original_run_pytest = build_autograde_payload.run_pytest

    def run_pytest_and_corrupt(pytest_args: Sequence[str], path: Path) -> int:
        code = original_run_pytest(pytest_args, path)
        path.write_text("{ invalid json", encoding="utf-8")
        return code

    monkeypatch.setattr(build_autograde_payload, "run_pytest", run_pytest_and_corrupt)
    _set_cli_env(monkeypatch)

    exit_code = build_autograde_payload.main(
        [
            f"--results-json={results_path}",
            f"--output={output_path}",
            f"--pytest-args={PLUGIN_FLAG}",
            f"--pytest-args={passing_test_file}",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Results JSON" in captured.err
    assert not output_path.exists()


def test_cli_forwards_pytest_args(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_first() -> None:
            assert True

        def test_second() -> None:
            assert False
        """,
    )
    completed, results_path, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, "-k", "test_first", str(test_file)],
    )
    assert completed.returncode == 0
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert len(payload["tests"]) == 1
    assert payload["tests"][0]["name"] == "first"


def test_cli_decodes_base64_correctly(tmp_path: Path, passing_test_file: Path) -> None:
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(passing_test_file)],
    )
    assert completed.returncode == 0
    encoded = output_path.read_text(encoding="utf-8").strip()
    decoded = base64.b64decode(encoded)
    payload = json.loads(decoded)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["max_score"] == results["max_score"]
    assert len(payload["tests"]) == len(results["tests"])
