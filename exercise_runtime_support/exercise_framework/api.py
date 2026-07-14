"""Stable public API for the exercise testing framework.

This module provides structured, renderer-agnostic access to notebook checks.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from exercise_runtime_support.exercise_catalogue import (
    get_catalogue_entry,
    get_exercise_catalogue,
)
from exercise_runtime_support.exercise_framework.expectations import get_ex002_checks
from exercise_runtime_support.notebook_grader import NotebookGradingError
from exercise_runtime_support.support_matrix import SupportRole, has_support_role

from . import runtime

_MAX_SMOKE_INPUTS = 10


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


def _run_definitions(
    definitions: list[NotebookCheckDefinition],
) -> list[NotebookCheckResult]:
    results: list[NotebookCheckResult] = []
    for definition in definitions:
        try:
            issues = definition.runner()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            NotebookCheckResult(
                label=definition.label,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def _check_ex002_summary() -> list[str]:
    results = run_detailed_ex002_check()
    return [issue for result in results for issue in result.issues]


def _count_direct_input_calls(code: str) -> int:
    """Return the number of direct ``input()`` calls in *code*."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "input")
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "input"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "builtins"
            )
        )
    )


def _check_notebook_can_execute_first_exercise(exercise_key: str) -> list[str]:
    """Run the first exercise of *exercise_key* and ensure it executes cleanly.

    Some exercises (e.g. user-input modify tasks) call ``input()`` in their
    first exercise, so we provide mocked input values rather than letting the
    check fail on a closed stdin under the active variant.
    """
    input_count = _count_direct_input_calls(
        runtime.extract_tagged_code(exercise_key, tag="exercise1")
    )
    if input_count == 0:
        runtime.run_cell_and_capture_output(exercise_key, tag="exercise1")
        return []

    required = max(input_count, 1)
    while True:
        try:
            runtime.run_cell_with_input(
                exercise_key, tag="exercise1", inputs=["2"] * required
            )
            return []
        except RuntimeError as exc:  # input() called more times than provided
            if str(exc) != "Test expected more input values" or required >= _MAX_SMOKE_INPUTS:
                raise
            required += 1


def _get_supported_check_definitions() -> dict[str, NotebookCheckDefinition]:
    """Return supported checks keyed by exercise key in catalogue order."""
    definitions: dict[str, NotebookCheckDefinition] = {}
    for entry in get_exercise_catalogue():
        if has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_DETAILED):
            runner: Callable[[], list[str]] = _check_ex002_summary
        elif has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_SMOKE):
            runner = partial(
                _check_notebook_can_execute_first_exercise,
                entry.exercise_key,
            )
        else:
            continue
        definitions[entry.exercise_key] = NotebookCheckDefinition(
            entry.display_label,
            runner,
        )
    return definitions


def run_all_checks() -> list[NotebookCheckResult]:
    """Run all notebook checks and return structured results."""
    checks = _get_supported_check_definitions()
    return _run_definitions(list(checks.values()))


def run_notebook_check(exercise_key: str) -> list[NotebookCheckResult]:
    """Run a single notebook-level check for an exercise key and return structured results."""
    checks = _get_supported_check_definitions()
    catalogue_entry = get_catalogue_entry(exercise_key)
    check = checks.get(catalogue_entry.exercise_key)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown exercise key '{exercise_key}'. Available: {available}")

    return _run_definitions([check])


def run_detailed_ex002_check() -> list[ExerciseCheckResult]:
    """Run detailed ex002 checks and return per-check structured results."""
    results: list[ExerciseCheckResult] = []
    for check in get_ex002_checks():
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
