from __future__ import annotations

import pytest
from pytest import CaptureFixture, MonkeyPatch

import exercise_runtime_support.student_checker.checks as student_checks
from tests.notebook_grader import NotebookGradingError
from tests.student_checker import (
    DetailedCheckResult,
    ExerciseCheckResult,
)
from tests.student_checker.reporting import (
    print_detailed_results,
    print_exercise_results,
    print_notebook_detailed_results,
)


def _patch_generic_checks(
    monkeypatch: MonkeyPatch,
    *,
    exercise_key: str,
    checks: list[object],
) -> None:
    def fake_get_check_list(requested_exercise_key: str) -> list[object]:
        assert requested_exercise_key == exercise_key
        return checks

    monkeypatch.setattr(student_checks, "_get_check_list", fake_get_check_list)


def test_print_detailed_results_discards_success_message_when_failures(
    capsys: CaptureFixture[str],
) -> None:
    rows = [
        DetailedCheckResult(
            exercise_label="Exercise 1",
            check_label="Static output",
            passed=True,
            issues=[],
        ),
        DetailedCheckResult(
            exercise_label="Exercise 2",
            check_label="Prompt flow",
            passed=False,
            issues=["Exercise 2: output does not match expectation."],
        ),
    ]

    print_detailed_results(rows)
    output = capsys.readouterr().out

    assert "| Exercise 1" in output
    assert "| Static output" in output
    assert "🟢 OK" in output
    assert "🔴 NO" in output
    assert "output does not match expectation." in output
    assert "Great work! Everything that can be checked here looks good." not in output


def test_print_exercise_results_still_reports_success_message(
    capsys: CaptureFixture[str],
) -> None:
    results = [
        ExerciseCheckResult(exercise_no=1, title="Logic",
                            passed=True, issues=[]),
        ExerciseCheckResult(exercise_no=2, title="Formatting",
                            passed=True, issues=[]),
    ]

    print_exercise_results(results)
    output = capsys.readouterr().out

    assert "Great work! Everything that can be checked here looks good." in output
    assert "| Logic" in output
    assert "| Formatting" in output


def test_print_notebook_detailed_results_handles_notebook_grading_error(
    capsys: CaptureFixture[str],
) -> None:
    def broken_runner() -> list[str]:
        raise NotebookGradingError("Notebook parsing failed.")

    print_notebook_detailed_results(
        "Detailed check",
        broken_runner,
        exercise_label="Exercise X",
    )
    output = capsys.readouterr().out

    assert "Exercise X" in output
    assert "Detailed check" in output
    assert "Notebook parsing failed." in output
    assert "🔴 NO" in output
    assert "Great work! Everything that can be checked here looks good." not in output


def test_print_exercise_results_supports_ex006_rows(
    capsys: CaptureFixture[str],
) -> None:
    results = [
        ExerciseCheckResult(
            exercise_no=1, title="Static output", passed=True, issues=[]),
        ExerciseCheckResult(exercise_no=10, title="Prompt flow",
                            passed=False, issues=["Oops"]),
    ]

    print_exercise_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 10" in output


def test_print_exercise_results_shows_per_exercise_labels(
    capsys: CaptureFixture[str],
) -> None:
    results = [
        ExerciseCheckResult(
            exercise_no=1, title="Static output", passed=True, issues=[]),
        ExerciseCheckResult(exercise_no=10, title="Prompt flow",
                            passed=False, issues=["Oops"]),
    ]

    print_exercise_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 10" in output


@pytest.mark.parametrize(
    "exercise_key",
    [
        "ex003_sequence_modify_variables",
        "ex004_sequence_debug_syntax",
        "ex005_sequence_debug_logic",
        "ex007_sequence_debug_casting",
    ],
)
def test_run_exercise_checks_continues_after_notebook_grading_error(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    exercise_key: str,
) -> None:
    def broken_check() -> list[str]:
        raise NotebookGradingError("Cell failure.")

    def working_check() -> list[str]:
        return []

    _patch_generic_checks(
        monkeypatch,
        exercise_key=exercise_key,
        checks=[
            student_checks.ExerciseCheckDefinition(
                exercise_no=1,
                title="Broken",
                check=broken_check,
            ),
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Working",
                check=working_check,
            ),
        ],
    )

    results = student_checks.run_exercise_checks(exercise_key)
    print_exercise_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 2" in output


def test_run_exercise_checks_continues_after_notebook_grading_error_for_ex006_definitions(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    def broken_check() -> list[str]:
        raise NotebookGradingError("Cell failure.")

    def working_check() -> list[str]:
        return []

    _patch_generic_checks(
        monkeypatch,
        exercise_key="ex006_sequence_modify_casting",
        checks=[
            student_checks.ExerciseCheckDefinition(
                exercise_no=1,
                title="Broken",
                check=broken_check,
            ),
            student_checks.ExerciseCheckDefinition(
                exercise_no=2,
                title="Working",
                check=working_check,
            ),
        ],
    )

    results = student_checks.run_exercise_checks(
        "ex006_sequence_modify_casting")
    print_exercise_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 2" in output
