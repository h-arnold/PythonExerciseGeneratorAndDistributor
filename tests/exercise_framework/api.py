"""Stable public API for the exercise testing framework.

This module provides structured, renderer-agnostic access to notebook checks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from tests.exercise_expectations import (
    EX001_FUNCTION_NAME,
    EX001_NOTEBOOK_PATH,
    EX001_TAG,
    EX003_NOTEBOOK_PATH,
    EX004_NOTEBOOK_PATH,
    EX005_NOTEBOOK_PATH,
    EX006_NOTEBOOK_PATH,
)
from tests.exercise_framework.expectations import EX002_CHECKS
from tests.notebook_grader import NotebookGradingError

from . import runtime

RawNotebookResult = tuple[str, bool, list[str]]

EX001_SLUG = "ex001_sanity"
EX002_SLUG = "ex002_sequence_modify_basics"
EX003_SLUG = "ex003_sequence_modify_variables"
EX004_SLUG = "ex004_sequence_debug_syntax"
EX005_SLUG = "ex005_sequence_debug_logic"
EX006_SLUG = "ex006_sequence_modify_casting"

NOTEBOOK_ORDER: Final[list[str]] = [
    EX001_SLUG,
    EX002_SLUG,
    EX003_SLUG,
    EX004_SLUG,
    EX005_SLUG,
    EX006_SLUG,
]


@dataclass(frozen=True)
class NotebookCheckResult:
    """Structured result for a single notebook-level check."""

    label: str
    passed: bool
    issues: list[str]


@dataclass(frozen=True)
class ExerciseCheckResult:
    """Structured result for a single per-exercise check item."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]


@dataclass(frozen=True)
class NotebookCheckDefinition:
    """Structured notebook check definition for API orchestration."""

    label: str
    runner: Callable[[], list[str]]


def _to_notebook_results(raw_results: list[RawNotebookResult]) -> list[NotebookCheckResult]:
    return [
        NotebookCheckResult(label=label, passed=passed, issues=issues)
        for label, passed, issues in raw_results
    ]


def _run_definitions(definitions: list[NotebookCheckDefinition]) -> list[RawNotebookResult]:
    raw_results: list[RawNotebookResult] = []
    for definition in definitions:
        try:
            issues = definition.runner()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        raw_results.append((definition.label, len(issues) == 0, issues))
    return raw_results


def _check_ex001() -> list[str]:
    errors: list[str] = []
    namespace = runtime.exec_tagged_code(EX001_NOTEBOOK_PATH, tag=EX001_TAG)
    example = namespace.get(EX001_FUNCTION_NAME)
    if example is None or not callable(example):
        return ["The `example` function is missing."]

    result = example()
    if not isinstance(result, str):
        errors.append("The `example` function must return a string.")
    elif result == "":
        errors.append("The `example` function should not return an empty string.")
    return errors


def _check_ex002_summary() -> list[str]:
    results = run_detailed_ex002_check()
    return [issue for result in results for issue in result.issues]


def _check_notebook_can_execute_first_exercise(notebook_path: str) -> list[str]:
    runtime.run_cell_and_capture_output(notebook_path, tag="exercise1")
    return []


def _get_check_definitions() -> dict[str, NotebookCheckDefinition]:
    return {
        EX001_SLUG: NotebookCheckDefinition("ex001 Sanity", _check_ex001),
        EX002_SLUG: NotebookCheckDefinition("ex002 Sequence Modify Basics", _check_ex002_summary),
        EX003_SLUG: NotebookCheckDefinition(
            "ex003 Sequence Modify Variables",
            lambda: _check_notebook_can_execute_first_exercise(EX003_NOTEBOOK_PATH),
        ),
        EX004_SLUG: NotebookCheckDefinition(
            "ex004 Debug Syntax Errors",
            lambda: _check_notebook_can_execute_first_exercise(EX004_NOTEBOOK_PATH),
        ),
        EX005_SLUG: NotebookCheckDefinition(
            "ex005 Debug Logical Errors",
            lambda: _check_notebook_can_execute_first_exercise(EX005_NOTEBOOK_PATH),
        ),
        EX006_SLUG: NotebookCheckDefinition(
            "ex006 Casting and Type Conversion",
            lambda: _check_notebook_can_execute_first_exercise(EX006_NOTEBOOK_PATH),
        ),
    }


def run_all_checks() -> list[NotebookCheckResult]:
    """Run all notebook checks and return structured results."""
    checks = _get_check_definitions()
    ordered_definitions = [checks[slug] for slug in NOTEBOOK_ORDER]
    return _to_notebook_results(_run_definitions(ordered_definitions))


def run_notebook_check(notebook_slug: str) -> list[NotebookCheckResult]:
    """Run a single notebook-level check and return structured results."""
    checks = _get_check_definitions()
    check = checks.get(notebook_slug)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown notebook '{notebook_slug}'. Available: {available}")

    return _to_notebook_results(_run_definitions([check]))


def run_detailed_ex002_check() -> list[ExerciseCheckResult]:
    """Run detailed ex002 checks and return per-check structured results."""
    results: list[ExerciseCheckResult] = []
    for check in EX002_CHECKS:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            ExerciseCheckResult(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results
