from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from tests.exercise_framework.expectations import EX002_CHECKS

EXPECTED_EX002_TEST_COUNT = len(EX002_CHECKS)
EXPECTED_TASK_DISTRIBUTION = Counter(
    check.exercise_no for check in EX002_CHECKS)
PLUGIN_NAME = "tests.autograde_plugin"


def test_ex002_autograde_task_distribution_and_count_parity(tmp_path: Path) -> None:
    results_path = tmp_path / "autograde-results.json"
    env = os.environ.copy()
    env["PYTUTOR_ACTIVE_VARIANT"] = "solution"
    env.pop("PYTUTOR_NOTEBOOKS_DIR", None)

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        PLUGIN_NAME,
        f"--autograde-results-path={results_path}",
        "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
    ]

    completed = subprocess.run(
        command, check=False, capture_output=True, text=True, env=env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert results_path.exists()

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    tests = payload["tests"]

    assert len(tests) == EXPECTED_EX002_TEST_COUNT

    task_counts = Counter(test.get("taskno") for test in tests)
    filtered_task_counts = {
        int(task): count for task, count in task_counts.items() if task is not None
    }

    assert filtered_task_counts == dict(EXPECTED_TASK_DISTRIBUTION)
