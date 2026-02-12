from __future__ import annotations

import pytest

from tests.student_checker import checks as student_checks
from tests.student_checker.checks import ex003 as ex003_checks
from tests.student_checker.test_helpers_modify_gate import (
    EXPECTED_CHECK_CALLS,
    check_with_counter,
    started_gate,
)


def test_ex003_started_cell_runs_normal_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex003_checks,
        "_EX003_CHECKS",
        [
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Static output",
                check=check_with_counter(counter),
            ),
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Prompt flow",
                check=check_with_counter(counter, issues=["Exercise 2: mismatch"]),
            ),
        ],
    )
    monkeypatch.setattr(
        ex003_checks,
        "check_modify_exercise_started",
        started_gate,
    )

    results = student_checks.run_ex003_checks()

    assert [(result.title, result.passed) for result in results] == [
        ("Static output", True),
        ("Prompt flow", False),
    ]
    assert counter["calls"] == EXPECTED_CHECK_CALLS
