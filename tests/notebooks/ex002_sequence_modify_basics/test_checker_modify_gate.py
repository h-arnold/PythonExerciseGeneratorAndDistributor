from __future__ import annotations

import pytest

from tests.exercise_framework.expectations import Ex002CheckDefinition
from tests.student_checker import CheckStatus
from tests.student_checker import checks as student_checks
from tests.student_checker.checks import ex002 as ex002_checks
from tests.student_checker.test_helpers_modify_gate import (
    check_with_counter,
    not_started_gate,
)


def test_ex002_untouched_cell_returns_not_started_and_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex002_checks,
        "EX002_CHECKS",
        [
            Ex002CheckDefinition(
                exercise_no=1,
                title="Logic",
                check=check_with_counter(counter),
            ),
            Ex002CheckDefinition(
                exercise_no=1,
                title="Construct",
                check=check_with_counter(counter),
            ),
        ],
    )
    monkeypatch.setattr(
        ex002_checks,
        "check_modify_exercise_started",
        not_started_gate,
    )

    results = student_checks.run_ex002_checks()

    assert len(results) == 1
    assert results[0].title == "Started"
    assert results[0].passed is False
    assert results[0].status == CheckStatus.NOT_STARTED
    assert results[0].issues == ["Exercise 1: NOT STARTED."]
    assert counter["calls"] == 0
