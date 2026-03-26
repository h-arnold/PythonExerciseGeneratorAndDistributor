"""Generic check entry points backed by exercise-local test support modules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from exercise_runtime_support.exercise_test_support import (
    load_exercise_test_module,
    resolve_exercise_tests_dir,
)
from exercise_runtime_support.notebook_grader import NotebookGradingError

from ..models import ExerciseCheckResult
from .base import ExerciseCheckDefinition

_CHECK_CACHE: dict[str, list[Any]] = {}

__all__ = [
    "ExerciseCheckDefinition",
    "check_exercise_summary",
    "has_exercise_checks",
    "run_exercise_checks",
]


def has_exercise_checks(exercise_key: str) -> bool:
    """Return whether an exercise exposes student-checker support."""

    try:
        tests_dir = resolve_exercise_tests_dir(exercise_key)
    except FileNotFoundError:
        return False
    return (tests_dir / "student_checker_support.py").is_file()


def _load_check_list(exercise_key: str) -> list[Any]:
    module = load_exercise_test_module(exercise_key, "student_checker_support")
    return list(module.CHECKS)


def _get_check_list(exercise_key: str) -> list[Any]:
    checks = _CHECK_CACHE.get(exercise_key)
    if checks is None:
        checks = _load_check_list(exercise_key)
        _CHECK_CACHE[exercise_key] = checks
    return checks


def _build_result(check: Any, issues: list[str]) -> ExerciseCheckResult:
    return ExerciseCheckResult(
        exercise_no=check.exercise_no,
        title=check.title,
        passed=len(issues) == 0,
        issues=issues,
    )


def _run_checks(checks: list[Any]) -> list[ExerciseCheckResult]:
    results: list[ExerciseCheckResult] = []
    for check in checks:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(_build_result(check, issues))
    return results


def _summary(results: Sequence[ExerciseCheckResult]) -> list[str]:
    return [issue for result in results for issue in result.issues]


def check_exercise_summary(exercise_key: str) -> list[str]:
    """Run summary checks for a single exercise key."""

    return _summary(run_exercise_checks(exercise_key))


def run_exercise_checks(exercise_key: str) -> list[ExerciseCheckResult]:
    """Run detailed student-checker checks for a single exercise key."""

    return _run_checks(_get_check_list(exercise_key))
