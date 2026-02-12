from __future__ import annotations

import pytest

from tests.student_checker import CheckStatus
from tests.student_checker import checks as student_checks
from tests.student_checker.checks import ex005 as ex005_checks
from tests.student_checker.test_helpers_modify_gate import (
    check_with_counter,
    not_started_gate,
)


def test_ex005_untouched_cell_returns_not_started_and_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex005_checks,
        "_EX005_CHECKS",
        [
            student_checks.ExerciseCheckDefinition(
                exercise_no=4,
                title="Static output",
                check=check_with_counter(counter),
            ),
            student_checks.ExerciseCheckDefinition(
                exercise_no=4,
                title="Explanation",
                check=check_with_counter(counter),
            ),
        ],
    )
    monkeypatch.setattr(
        ex005_checks,
        "check_modify_exercise_started",
        not_started_gate,
    )

    results = student_checks.run_ex005_checks()

    assert len(results) == 1
    assert results[0].title == "Started"
    assert results[0].passed is False
    assert results[0].status == CheckStatus.NOT_STARTED
    assert results[0].issues == ["Exercise 4: NOT STARTED."]
    assert counter["calls"] == 0
