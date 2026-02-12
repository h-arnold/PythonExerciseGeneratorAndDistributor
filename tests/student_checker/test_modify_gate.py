from __future__ import annotations

from collections.abc import Callable, Mapping

import pytest

from tests.exercise_framework.expectations import Ex002CheckDefinition
from tests.student_checker import CheckStatus, ExerciseCheckResult
from tests.student_checker import checks as student_checks
from tests.student_checker.checks import ex002 as ex002_checks
from tests.student_checker.checks import ex003 as ex003_checks
from tests.student_checker.checks import ex006 as ex006_checks
from tests.student_checker.checks.base import check_modify_exercise_started
from tests.student_checker.reporting import print_ex003_results

EXPECTED_CHECK_CALLS = 2


def _check_with_counter(counter: dict[str, int], *, issues: list[str] | None = None) -> Callable[[], list[str]]:
    def _check() -> list[str]:
        counter["calls"] += 1
        return [] if issues is None else issues

    return _check


def _not_started_gate(_notebook_path: str, exercise_no: int, _starter_baselines: Mapping[str, str]) -> list[str]:
    return [f"Exercise {exercise_no}: NOT STARTED."]


def _started_gate(_notebook_path: str, _exercise_no: int, _starter_baselines: Mapping[str, str]) -> list[str]:
    return []


def test_ex002_untouched_cell_returns_not_started_and_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex002_checks,
        "EX002_CHECKS",
        [
            Ex002CheckDefinition(exercise_no=1, title="Logic",
                                 check=_check_with_counter(counter)),
            Ex002CheckDefinition(
                exercise_no=1,
                title="Construct",
                check=_check_with_counter(counter),
            ),
        ],
    )
    monkeypatch.setattr(
        ex002_checks,
        "check_modify_exercise_started",
        _not_started_gate,
    )

    results = student_checks.run_ex002_checks()

    assert len(results) == 1
    assert results[0].title == "Started"
    assert results[0].passed is False
    assert results[0].status == CheckStatus.NOT_STARTED
    assert results[0].issues == ["Exercise 1: NOT STARTED."]
    assert counter["calls"] == 0


def test_ex003_started_cell_runs_normal_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex003_checks,
        "_EX003_CHECKS",
        [
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Static output",
                check=_check_with_counter(counter),
            ),
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Prompt flow",
                check=_check_with_counter(
                    counter, issues=["Exercise 2: mismatch"]),
            ),
        ],
    )
    monkeypatch.setattr(
        ex003_checks,
        "check_modify_exercise_started",
        _started_gate,
    )

    results = student_checks.run_ex003_checks()

    assert [(result.title, result.passed) for result in results] == [
        ("Static output", True),
        ("Prompt flow", False),
    ]
    assert counter["calls"] == EXPECTED_CHECK_CALLS


def test_ex006_untouched_cell_returns_not_started_and_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = {"calls": 0}
    monkeypatch.setattr(
        ex006_checks,
        "_EX006_CHECKS",
        [
            student_checks.Ex006CheckDefinition(
                exercise_no=3,
                title="Static output",
                check=_check_with_counter(counter),
            ),
            student_checks.Ex006CheckDefinition(
                exercise_no=3,
                title="Construct",
                check=_check_with_counter(counter),
            ),
        ],
    )
    monkeypatch.setattr(
        ex006_checks,
        "check_modify_exercise_started",
        _not_started_gate,
    )

    results = student_checks.run_ex006_checks()

    assert len(results) == 1
    assert results[0].title == "Started"
    assert results[0].passed is False
    assert results[0].status == CheckStatus.NOT_STARTED
    assert results[0].issues == ["Exercise 3: NOT STARTED."]
    assert counter["calls"] == 0


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
