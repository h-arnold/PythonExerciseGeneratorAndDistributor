"""Rendering and execution helpers for student checker output."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from tests.exercise_framework.reporting import (
    normalise_issue_text,
    render_grouped_table_with_errors,
    render_table,
)
from tests.notebook_grader import NotebookGradingError

from .models import (
    DetailedCheckResult,
    Ex002CheckResult,
    Ex006CheckResult,
    ExerciseCheckResult,
    NotebookCheckSpec,
)

CheckResult = tuple[str, bool, list[str]]


class _ExerciseCheckResult(Protocol):
    """Protocol covering the fields required for grouped rendering."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]


def run_check(check: NotebookCheckSpec) -> None:
    """Run a single notebook check and print results."""
    if check.detailed_printer is None:
        print_single_notebook_results(check.label, check.summary_runner)
        return
    try:
        check.detailed_printer()
    except NotebookGradingError as exc:
        print_results([(check.label, False, [str(exc)])])


def run_checks(checks: list[NotebookCheckSpec]) -> list[CheckResult]:
    """Run all notebook checks and return status rows."""
    results: list[CheckResult] = []
    for check in checks:
        results.append(safe_check_result(check.label, check.summary_runner))
    return results


def safe_check_result(label: str, runner: Callable[[], list[str]]) -> CheckResult:
    """Run a checker with consistent NotebookGradingError handling."""
    try:
        issues = runner()
    except NotebookGradingError as exc:
        issues = [str(exc)]
    return (label, len(issues) == 0, issues)


def print_single_notebook_results(label: str, runner: Callable[[], list[str]]) -> None:
    """Run and print one notebook result in the standard summary format."""
    print_results([safe_check_result(label, runner)])


def print_results(results: list[CheckResult]) -> None:
    """Print the standard notebook summary table."""
    table = render_table([(label, passed) for label, passed, _ in results])
    print(table)

    failures = [(label, issues) for label, passed, issues in results if not passed]
    if not failures:
        print("\nGreat work! Everything that can be checked here looks good.")


def print_ex002_results(results: list[Ex002CheckResult]) -> None:
    """Print grouped ex002 check results."""
    print_detailed_results(_grouped_exercise_rows(results))


def print_ex006_results(results: list[Ex006CheckResult]) -> None:
    """Print grouped ex006 check results."""
    print_detailed_results(_grouped_exercise_rows(results))


def print_ex003_results(results: list[ExerciseCheckResult]) -> None:
    """Print grouped ex003 check results."""
    _print_exercise_results(results)


def print_ex004_results(results: list[ExerciseCheckResult]) -> None:
    """Print grouped ex004 check results."""
    _print_exercise_results(results)


def print_ex005_results(results: list[ExerciseCheckResult]) -> None:
    """Print grouped ex005 check results."""
    _print_exercise_results(results)


def _print_exercise_results(results: Iterable[ExerciseCheckResult]) -> None:
    print_detailed_results(_grouped_exercise_rows(results))


def _grouped_exercise_rows(
    results: Iterable[_ExerciseCheckResult],
) -> list[DetailedCheckResult]:
    """Build grouped detailed rows for exercise checks."""
    rows: list[DetailedCheckResult] = []
    last_exercise: int | None = None
    for result in results:
        label = f"Exercise {result.exercise_no}" if result.exercise_no != last_exercise else ""
        rows.append(
            DetailedCheckResult(
                exercise_label=label,
                check_label=result.title,
                passed=result.passed,
                issues=result.issues,
            )
        )
        last_exercise = result.exercise_no
    return rows


def print_detailed_results(
    results: Iterable[DetailedCheckResult],
    success_message: str | None = None,
) -> None:
    """Render grouped rows with exercise/check statuses and errors."""
    detailed_results = list(results)
    rows = [
        (
            item.exercise_label,
            item.check_label,
            item.passed,
            "" if item.passed else normalise_issue_text(item.issues),
        )
        for item in detailed_results
    ]
    table = render_grouped_table_with_errors(rows)
    print(table)

    failures = [item for item in detailed_results if not item.passed]
    if not failures:
        message = success_message or "Great work! Everything that can be checked here looks good."
        print(f"\n{message}")


def print_notebook_detailed_results(
    label: str,
    runner: Callable[[], list[str]],
    *,
    exercise_label: str = "",
    success_message: str | None = None,
) -> None:
    """Run a notebook check runner and print its results as a grouped table."""

    label, passed, issues = safe_check_result(label, runner)
    print_detailed_results(
        [
            DetailedCheckResult(
                exercise_label=exercise_label,
                check_label=label,
                passed=passed,
                issues=issues,
            )
        ],
        success_message=success_message,
    )
