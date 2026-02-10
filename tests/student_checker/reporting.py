"""Rendering and execution helpers for student checker output."""

from __future__ import annotations

from collections.abc import Callable

from tests.exercise_framework.reporting import (
    normalise_issue_text,
    render_grouped_table_with_errors,
    render_table,
)
from tests.notebook_grader import NotebookGradingError

from .models import Ex002CheckResult, NotebookCheckSpec

CheckResult = tuple[str, bool, list[str]]


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
    rows: list[tuple[str, str, bool, str]] = []
    last_exercise: int | None = None
    for result in results:
        label = f"Exercise {result.exercise_no}" if result.exercise_no != last_exercise else ""
        error_message = "" if result.passed else normalise_issue_text(result.issues)
        rows.append((label, result.title, result.passed, error_message))
        last_exercise = result.exercise_no

    table = render_grouped_table_with_errors(rows)
    print(table)

    failures = [result for result in results if not result.passed]
    if not failures:
        print("\nGreat work! Everything that can be checked here looks good.")
