"""Stable public API for the exercise testing framework.

This module provides structured, renderer-agnostic access to notebook checks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from exercise_runtime_support.exercise_catalogue import (
    ExerciseCatalogueEntry,
    get_catalogue_entry,
    get_exercise_catalogue,
)
from exercise_runtime_support.exercise_framework.expectations import EX002_CHECKS
from exercise_runtime_support.notebook_grader import NotebookGradingError
from exercise_runtime_support.support_matrix import SupportRole, has_support_role

from . import runtime

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


@dataclass(frozen=True)
class NotebookCheckDefinition:
    """Structured notebook check definition for API orchestration."""

    label: str
    runner: Callable[[], list[str]]


def _to_notebook_results(
    raw_results: list[RawNotebookResult],
) -> list[NotebookCheckResult]:
    return [
        NotebookCheckResult(label=label, passed=passed, issues=issues)
        for label, passed, issues in raw_results
    ]


def _run_definitions(
    definitions: list[NotebookCheckDefinition],
) -> list[RawNotebookResult]:
    raw_results: list[RawNotebookResult] = []
    for definition in definitions:
        try:
            issues = definition.runner()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        raw_results.append((definition.label, len(issues) == 0, issues))
    return raw_results


def _check_ex002_summary() -> list[str]:
    results = run_detailed_ex002_check()
    return [issue for result in results for issue in result.issues]


def _check_notebook_can_execute_first_exercise(exercise_key: str) -> list[str]:
    runtime.run_cell_and_capture_output(exercise_key, tag="exercise1")
    return []


def _get_check_runners() -> dict[str, Callable[[], list[str]]]:
    runners: dict[str, Callable[[], list[str]]] = {}
    for entry in get_exercise_catalogue():
        if has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_DETAILED):
            runners[entry.exercise_key] = _check_ex002_summary
            continue
        if has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_SMOKE):
            runners[entry.exercise_key] = partial(
                _check_notebook_can_execute_first_exercise,
                entry.exercise_key,
            )
    return runners


def _get_check_definitions() -> dict[str, NotebookCheckDefinition]:
    runners = _get_check_runners()
    definitions: dict[str, NotebookCheckDefinition] = {}
    for entry in get_exercise_catalogue():
        runner = runners.get(entry.exercise_key)
        if runner is None:
            continue
        definitions[entry.exercise_key] = NotebookCheckDefinition(entry.display_label, runner)
    return definitions


def _get_supported_catalogue() -> list[ExerciseCatalogueEntry]:
    """Return ordered catalogue entries backed by framework runners."""
    supported_slugs = set(_get_check_runners())
    return [entry for entry in get_exercise_catalogue() if entry.exercise_key in supported_slugs]


def run_all_checks() -> list[NotebookCheckResult]:
    """Run all notebook checks and return structured results."""
    checks = _get_check_definitions()
    ordered_definitions = [checks[entry.exercise_key] for entry in _get_supported_catalogue()]
    return _to_notebook_results(_run_definitions(ordered_definitions))


def run_notebook_check(notebook_slug: str) -> list[NotebookCheckResult]:
    """Run a single notebook-level check and return structured results."""
    checks = _get_check_definitions()
    catalogue_entry = get_catalogue_entry(notebook_slug)
    check = checks.get(catalogue_entry.exercise_key)
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
