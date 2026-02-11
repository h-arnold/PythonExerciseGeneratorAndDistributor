from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

EXPECTED_EX002_TEST_COUNT = 60
EXPECTED_TASK_DISTRIBUTION = {task: 6 for task in range(1, 11)}
PLUGIN_NAME = "tests.autograde_plugin"


def test_ex002_autograde_task_distribution_and_count_parity(tmp_path: Path) -> None:
    results_path = tmp_path / "autograde-results.json"
    env = os.environ.copy()
    env["PYTUTOR_NOTEBOOKS_DIR"] = "notebooks/solutions"

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        PLUGIN_NAME,
        f"--autograde-results-path={results_path}",
        "tests/test_ex002_sequence_modify_basics.py",
        "tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py",
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert results_path.exists()

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    tests = payload["tests"]

    assert len(tests) == EXPECTED_EX002_TEST_COUNT

    task_counts = Counter(test.get("taskno") for test in tests)
    filtered_task_counts = {
        int(task): count for task, count in task_counts.items() if task is not None
    }

    assert filtered_task_counts == EXPECTED_TASK_DISTRIBUTION
