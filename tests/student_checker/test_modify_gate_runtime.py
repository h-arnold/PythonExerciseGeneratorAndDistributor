from __future__ import annotations

import pytest

from tests.student_checker import ExerciseCheckResult
from tests.student_checker.checks.base import check_modify_exercise_started
from tests.student_checker.reporting import print_ex003_results


def test_not_started_is_visible_in_checker_output(capsys: pytest.CaptureFixture[str]) -> None:
    print_ex003_results(
        [
            ExerciseCheckResult(
                exercise_no=4,
                title="Started",
                passed=False,
                issues=["Exercise 4: NOT STARTED."],
            )
        ]
    )

    output = capsys.readouterr().out
    assert "NOT STARTED" in output
    assert "NOT STARTED." in output


def test_missing_baseline_mapping_returns_actionable_issue() -> None:
    issues = check_modify_exercise_started(
        "notebooks/ex002_sequence_modify_basics.ipynb",
        4,
        {},
    )

    assert issues == [
        "Exercise 4: missing starter baseline for 'exercise4'. "
        "Update the exercise expectations baseline mapping."
    ]
