from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Sequence
from pathlib import Path

import pytest

CLI_SCRIPT = Path(__file__).resolve(
).parents[1] / "scripts" / "build_autograde_payload.py"
REPO_ROOT = CLI_SCRIPT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_autograde_payload  # noqa: E402

PLUGIN_FLAG = "-p tests.autograde_plugin"


def _write_test_file(tmp_path: Path, content: str, *, name: str = "test_suite.py") -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


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


def _execute_cli(  # noqa: PLR0913
    cwd: Path,
    pytest_chunks: Iterable[str],
    *,
    env_overrides: dict[str, str | None] | None = None,
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
        env=_prepare_env(env_overrides),
        check=False,
        text=True,
        capture_output=True,
    )
    return completed, results_path, output_path, summary_path


def _set_cli_env(monkeypatch: pytest.MonkeyPatch) -> None:
    current = os.environ.get("PYTHONPATH")
    pythonpath = f"{REPO_ROOT}{os.pathsep}{current}" if current else str(
        REPO_ROOT)
    monkeypatch.setenv("PYTHONPATH", pythonpath)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks")


def test_cli_runs_pytest_successfully(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
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


def test_cli_validates_environment(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": None},
    )
    assert completed.returncode == 0
    assert "Environment: PYTUTOR_NOTEBOOKS_DIR=<unset>" in completed.stdout


def test_cli_rejects_wrong_notebook_dir(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
        env_overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"},
        results_path=results_path,
    )
    assert completed.returncode == 1
    assert "Error: PYTUTOR_NOTEBOOKS_DIR must be unset or 'notebooks'" in completed.stderr
    assert not results_path.exists()


def test_cli_creates_output_directories(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    results_path = tmp_path / "nested" / "dir" / "results.json"
    output_path = tmp_path / "another" / "dir" / "payload.txt"
    summary_path = tmp_path / "summary" / "dir" / "data.json"
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
        results_path=results_path,
        output_path=output_path,
        summary_path=summary_path,
    )
    assert completed.returncode == 0
    assert results_path.is_file()
    assert output_path.is_file()
    assert summary_path.is_file()


def test_cli_writes_base64_payload(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    completed, _, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
    )
    assert completed.returncode == 0
    payload_text = output_path.read_text(encoding="utf-8")
    assert payload_text.endswith("\n")
    encoded = payload_text.strip()
    assert encoded
    base64.b64decode(encoded)


def test_cli_writes_summary_json(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    summary_path = tmp_path / "tmp" / "autograde" / "summary.json"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
        summary_path=summary_path,
    )
    assert completed.returncode == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "pass"
    assert len(summary["tests"]) == 1


def test_cli_prints_summary_table(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
    )
    assert completed.returncode == 0
    stdout = completed.stdout
    assert "=== Autograde Summary ===" in stdout
    assert "Task Breakdown:" in stdout
    assert "Tests Passed: 1/1" in stdout


def test_cli_writes_github_outputs(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    gh_output = tmp_path / "gh_output.txt"
    completed, _, _, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
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
) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    output_path = tmp_path / "tmp" / "autograde" / "payload.txt"

    original_run_pytest = build_autograde_payload.run_pytest

    def run_pytest_and_remove(pytest_args: Sequence[str], path: Path) -> int:
        code = original_run_pytest(pytest_args, path)
        if path.exists():
            path.unlink()
        return code

    monkeypatch.setattr(build_autograde_payload,
                        "run_pytest", run_pytest_and_remove)
    _set_cli_env(monkeypatch)

    exit_code = build_autograde_payload.main(
        [
            f"--results-json={results_path}",
            f"--output={output_path}",
            f"--pytest-args={PLUGIN_FLAG}",
            f"--pytest-args={test_file}",
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
) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    results_path = tmp_path / "tmp" / "autograde" / "results.json"
    output_path = tmp_path / "tmp" / "autograde" / "payload.txt"

    original_run_pytest = build_autograde_payload.run_pytest

    def run_pytest_and_corrupt(pytest_args: Sequence[str], path: Path) -> int:
        code = original_run_pytest(pytest_args, path)
        path.write_text("{ invalid json", encoding="utf-8")
        return code

    monkeypatch.setattr(build_autograde_payload,
                        "run_pytest", run_pytest_and_corrupt)
    _set_cli_env(monkeypatch)

    exit_code = build_autograde_payload.main(
        [
            f"--results-json={results_path}",
            f"--output={output_path}",
            f"--pytest-args={PLUGIN_FLAG}",
            f"--pytest-args={test_file}",
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


def test_cli_decodes_base64_correctly(tmp_path: Path) -> None:
    test_file = _write_test_file(
        tmp_path,
        """
        def test_ok() -> None:
            assert True
        """,
    )
    completed, results_path, output_path, _ = _execute_cli(
        tmp_path,
        [PLUGIN_FLAG, str(test_file)],
    )
    assert completed.returncode == 0
    encoded = output_path.read_text(encoding="utf-8").strip()
    decoded = base64.b64decode(encoded)
    payload = json.loads(decoded)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["max_score"] == results["max_score"]
    assert len(payload["tests"]) == len(results["tests"])
