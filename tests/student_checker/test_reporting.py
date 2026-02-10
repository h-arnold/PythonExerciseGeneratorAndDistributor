from __future__ import annotations

import tests.student_checker.checks as student_checks
from tests.notebook_grader import NotebookGradingError
from tests.student_checker import DetailedCheckResult, Ex002CheckResult, Ex006CheckResult
from tests.student_checker.reporting import (
    print_detailed_results,
    print_ex002_results,
    print_ex006_results,
    print_notebook_detailed_results,
)


def test_print_detailed_results_discards_success_message_when_failures(capsys) -> None:
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


def test_print_ex002_results_still_reports_success_message(capsys) -> None:
    results = [
        Ex002CheckResult(exercise_no=1, title="Logic", passed=True, issues=[]),
        Ex002CheckResult(exercise_no=2, title="Formatting", passed=True, issues=[]),
    ]

    print_ex002_results(results)
    output = capsys.readouterr().out

    assert "Great work! Everything that can be checked here looks good." in output
    assert "| Logic" in output
    assert "| Formatting" in output


def test_print_notebook_detailed_results_handles_notebook_grading_error(capsys) -> None:
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


def test_print_ex006_results_shows_per_exercise_labels(capsys) -> None:
    results = [
        Ex006CheckResult(exercise_no=1, title="Static output", passed=True, issues=[]),
        Ex006CheckResult(exercise_no=10, title="Prompt flow", passed=False, issues=["Oops"]),
    ]

    print_ex006_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 10" in output


def test_run_ex006_checks_continues_after_notebook_grading_error(monkeypatch, capsys) -> None:
    def broken_check() -> list[str]:
        raise NotebookGradingError("Cell failure.")

    def working_check() -> list[str]:
        return []

    monkeypatch.setattr(
        student_checks,
        "_EX006_CHECKS",
        [
            student_checks.Ex006CheckDefinition(
                exercise_no=1,
                title="Broken",
                check=broken_check,
            ),
            student_checks.Ex006CheckDefinition(
                exercise_no=2,
                title="Working",
                check=working_check,
            ),
        ],
    )

    results = student_checks.run_ex006_checks()
    print_ex006_results(results)
    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Exercise 2" in output
