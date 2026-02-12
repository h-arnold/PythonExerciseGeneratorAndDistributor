"""Autograde parity checks for ex002 and payload builders."""

from __future__ import annotations

import copy
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from tests.helpers import build_autograde_env

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_autograde_payload  # noqa: E402
from scripts.build_autograde_payload import AutogradeResults  # noqa: E402

PLUGIN_NAME = "tests.autograde_plugin"
EX002_TEST_FILES = (
    "tests/notebooks/ex002_sequence_modify_basics/test_notebook.py",
)
EXPECTED_EX002_TEST_COUNT = 40
MIN_STATUS_MUTATION_TESTS = 2


def _run_ex002_autograde(tmp_path: Path) -> AutogradeResults:
    results_path = tmp_path / "autograde-results.json"
    env = build_autograde_env(
        overrides={"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"})
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        PLUGIN_NAME,
        f"--autograde-results-path={results_path}",
        *EX002_TEST_FILES,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert results_path.exists()
    return build_autograde_payload.load_results(results_path)


@pytest.fixture(scope="session")
def ex002_autograde_results(
    tmp_path_factory: pytest.TempPathFactory,
) -> AutogradeResults:
    tmp_path = tmp_path_factory.mktemp("autograde-ex002")
    return _run_ex002_autograde(tmp_path)


def _mutate_statuses(raw_results: AutogradeResults) -> AutogradeResults:
    mutated: AutogradeResults = copy.deepcopy(raw_results)
    tests = mutated.get("tests", [])
    if len(tests) < MIN_STATUS_MUTATION_TESTS:
        raise AssertionError(
            f"Expected at least {MIN_STATUS_MUTATION_TESTS} test entries for status mutation"
        )

    tests[0]["status"] = "fail"
    tests[0]["score"] = 0.0
    tests[0]["message"] = "Injected failure"

    tests[1]["status"] = "error"
    tests[1]["score"] = 0.0
    tests[1]["message"] = "Injected error"

    mutated["status"] = "error"
    return mutated


def test_autograde_plugin_ex002_status_and_task_metadata(
    ex002_autograde_results: AutogradeResults,
) -> None:
    assert ex002_autograde_results["status"] == "pass"
    tests = ex002_autograde_results["tests"]
    assert len(tests) == EXPECTED_EX002_TEST_COUNT
    assert all(test.get("status") == "pass" for test in tests)

    task_numbers = [test.get("taskno") for test in tests]
    assert all(isinstance(taskno, int) for taskno in task_numbers)
    assert set(task_numbers) == set(range(1, 11))
    assert Counter(task_numbers) == {task: 4 for task in range(1, 11)}


def test_payload_builder_full_preserves_status_and_task_metadata(
    monkeypatch: pytest.MonkeyPatch,
    ex002_autograde_results: AutogradeResults,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    raw_results = _mutate_statuses(ex002_autograde_results)
    payload = build_autograde_payload.build_payload(raw_results)

    assert payload["status"] == raw_results["status"]

    for raw_test, payload_test in zip(raw_results["tests"], payload["tests"], strict=True):
        assert payload_test["status"] == raw_test["status"]
        assert payload_test.get("task") == raw_test.get("taskno")
        assert payload_test.get("taskno") == raw_test.get("taskno")


def test_payload_builder_minimal_preserves_status_fields(
    monkeypatch: pytest.MonkeyPatch,
    ex002_autograde_results: AutogradeResults,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    raw_results = _mutate_statuses(ex002_autograde_results)
    payload = build_autograde_payload.build_payload(raw_results)
    minimal_payload = build_autograde_payload.minimize_payload(payload)

    assert minimal_payload["status"] == payload["status"]

    for minimal_test, full_test in zip(minimal_payload["tests"], payload["tests"], strict=True):
        assert minimal_test["status"] == full_test["status"]
        assert "task" not in minimal_test
        assert "taskno" not in minimal_test
