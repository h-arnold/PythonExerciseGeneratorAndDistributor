"""Generic check entry points backed by exercise-local test support modules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from exercise_runtime_support.exercise_catalogue import get_catalogue_key_for_exercise_id
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import NotebookGradingError

from ..models import Ex002CheckResult, Ex006CheckResult, ExerciseCheckResult
from .base import Ex006CheckDefinition, ExerciseCheckDefinition


def _load_ex002_checks() -> list[Any]:
    module = load_exercise_test_module(
        get_catalogue_key_for_exercise_id(2),
        "framework_support",
    )
    return list(module.EX002_CHECKS)


def _load_check_list(exercise_id: int) -> list[Any]:
    module = load_exercise_test_module(
        get_catalogue_key_for_exercise_id(exercise_id),
        "student_checker_support",
    )
    return list(module.CHECKS)


_CHECK_CACHE: dict[int, list[Any]] = {}

__all__ = [
    "Ex006CheckDefinition",
    "ExerciseCheckDefinition",
    "check_ex002_summary",
    "check_ex003",
    "check_ex004",
    "check_ex005",
    "check_ex006",
    "check_ex007",
    "run_ex002_checks",
    "run_ex003_checks",
    "run_ex004_checks",
    "run_ex005_checks",
    "run_ex006_checks",
    "run_ex007_checks",
]


def _get_check_list(exercise_id: int) -> list[Any]:
    checks = _CHECK_CACHE.get(exercise_id)
    if checks is None:
        checks = _load_check_list(exercise_id)
        _CHECK_CACHE[exercise_id] = checks
    return checks


ResultT = TypeVar("ResultT", Ex002CheckResult,
                  Ex006CheckResult, ExerciseCheckResult)


def _run_checks(
    checks: list[Any],
    result_type: type[ResultT],
) -> list[ResultT]:
    results: list[ResultT] = []
    for check in checks:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            result_type(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def _summary(
    results: Sequence[ExerciseCheckResult | Ex002CheckResult | Ex006CheckResult],
) -> list[str]:
    return [issue for result in results for issue in result.issues]


def check_ex002_summary() -> list[str]:
    """Run summary checks for ex002."""

    return _summary(run_ex002_checks())


def run_ex002_checks() -> list[Ex002CheckResult]:
    """Run detailed checks for ex002."""

    return _run_checks(_load_ex002_checks(), Ex002CheckResult)


def check_ex003() -> list[str]:
    """Run checks for ex003."""

    return _summary(run_ex003_checks())


def run_ex003_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex003."""

    return _run_checks(_get_check_list(3), ExerciseCheckResult)


def check_ex004() -> list[str]:
    """Run checks for ex004."""

    return _summary(run_ex004_checks())


def run_ex004_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex004."""

    return _run_checks(_get_check_list(4), ExerciseCheckResult)


def check_ex005() -> list[str]:
    """Run checks for ex005."""

    return _summary(run_ex005_checks())


def run_ex005_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex005."""

    return _run_checks(_get_check_list(5), ExerciseCheckResult)


def check_ex006() -> list[str]:
    """Run checks for ex006."""

    return _summary(run_ex006_checks())


def run_ex006_checks() -> list[Ex006CheckResult]:
    """Run detailed checks for ex006."""

    return _run_checks(_get_check_list(6), Ex006CheckResult)


def check_ex007() -> list[str]:
    """Run checks for ex007."""

    return _summary(run_ex007_checks())


def run_ex007_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex007."""

    return _run_checks(_get_check_list(7), ExerciseCheckResult)
