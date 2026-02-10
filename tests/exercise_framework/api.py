"""Stable public API for the exercise testing framework.

This module provides structured, renderer-agnostic access to notebook checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from tests import student_checker

RawNotebookResult = tuple[str, bool, list[str]]


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


EX002_SLUG: Final[str] = "ex002_sequence_modify_basics"


def _to_notebook_results(raw_results: list[RawNotebookResult]) -> list[NotebookCheckResult]:
    return [
        NotebookCheckResult(label=label, passed=passed, issues=issues)
        for label, passed, issues in raw_results
    ]


def run_all_checks() -> list[NotebookCheckResult]:
    """Run all notebook checks and return structured results."""
    raw_results = student_checker._run_checks(list(student_checker._get_checks().values()))
    return _to_notebook_results(raw_results)


def run_notebook_check(notebook_slug: str) -> list[NotebookCheckResult]:
    """Run a single notebook-level check and return structured results."""
    checks = student_checker._get_checks()
    check = checks.get(notebook_slug)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown notebook '{notebook_slug}'. Available: {available}")

    raw_results = student_checker._run_checks([check])
    return _to_notebook_results(raw_results)


def run_detailed_ex002_check() -> list[ExerciseCheckResult]:
    """Run detailed ex002 checks and return per-check structured results."""
    raw_results = student_checker._run_ex002_checks()
    return [
        ExerciseCheckResult(
            exercise_no=result.exercise_no,
            title=result.title,
            passed=result.passed,
            issues=result.issues,
        )
        for result in raw_results
    ]
