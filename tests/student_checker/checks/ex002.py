"""Checks for the ex002 notebook."""

from __future__ import annotations

from tests.exercise_expectations import EX002_MODIFY_STARTER_BASELINES, EX002_NOTEBOOK_PATH
from tests.exercise_framework.expectations import EX002_CHECKS
from tests.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)
from tests.notebook_grader import NotebookGradingError

from ..models import CheckStatus, Ex002CheckResult
from .base import MODIFY_START_GATE_TITLE, check_modify_exercise_started


def check_ex002_summary() -> list[str]:
    """Run summary checks for ex002."""
    return [issue for result in run_ex002_checks() for issue in result.issues]


def run_ex002_checks() -> list[Ex002CheckResult]:
    """Run detailed checks for ex002."""
    results: list[Ex002CheckResult] = []
    untouched_exercises: set[int] = set()
    seen_exercises: set[int] = set()
    notebook_path = _resolve_ex002_notebook_path()
    for check in EX002_CHECKS:
        if check.exercise_no in untouched_exercises:
            continue
        if check.exercise_no not in seen_exercises:
            seen_exercises.add(check.exercise_no)
            gate_issues = check_modify_exercise_started(
                notebook_path,
                check.exercise_no,
                EX002_MODIFY_STARTER_BASELINES,
            )
            if gate_issues:
                gate_status = (
                    CheckStatus.NOT_STARTED
                    if any("NOT STARTED" in issue for issue in gate_issues)
                    else CheckStatus.FAILED
                )
                untouched_exercises.add(check.exercise_no)
                results.append(
                    Ex002CheckResult(
                        exercise_no=check.exercise_no,
                        title=MODIFY_START_GATE_TITLE,
                        passed=False,
                        issues=gate_issues,
                        status=gate_status,
                    )
                )
                continue
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


def _resolve_ex002_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX002_NOTEBOOK_PATH))


__all__ = ["check_ex002_summary", "run_ex002_checks"]
