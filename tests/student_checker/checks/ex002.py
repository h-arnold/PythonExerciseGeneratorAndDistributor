"""Checks for the ex002 notebook."""

from __future__ import annotations

from tests.exercise_framework.expectations import EX002_CHECKS
from tests.notebook_grader import NotebookGradingError

from ..models import Ex002CheckResult


def check_ex002_summary() -> list[str]:
    """Run summary checks for ex002."""
    return [issue for result in run_ex002_checks() for issue in result.issues]


def run_ex002_checks() -> list[Ex002CheckResult]:
    """Run detailed checks for ex002."""
    results: list[Ex002CheckResult] = []
    for check in EX002_CHECKS:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            Ex002CheckResult(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


__all__ = ["check_ex002_summary", "run_ex002_checks"]
