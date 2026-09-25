"""Exercise-local student checker definitions for ex010 sequence debug f-strings."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_framework import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import NotebookGradingError
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    check_explanation_cell,
    exercise_tag,
)

_EXERCISE_KEY = "ex010_sequence_debug_fstrings"
ex010 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _exercise_ast(exercise_no: int) -> ast.Module:
    """Parse the tagged cell used by the construct check."""
    code = extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _check_construct(exercise_no: int) -> list[str]:
    """Verify the conservative sequence surface and task-specific data flow."""
    try:
        issues = _construct_checks.construct_issues(
            _exercise_ast(exercise_no),
            exercise_no,
        )
    except (NotebookGradingError, RuntimeError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    return [f"Exercise {exercise_no}: {issue}" for issue in issues]


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive cell against its exact expected output."""
    expected = ex010.EX010_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except Exception as exc:  # noqa: BLE001 — show any student runtime failure
        return [f"Exercise {exercise_no}: {exc}"]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every exact interactive transcript for a cell."""
    cases = ex010.EX010_INPUT_CASES[exercise_no]
    expected = [case["expected_output"] for case in cases]
    actual: list[str] = []
    for case in cases:
        try:
            actual.append(
                run_cell_with_input(
                    _EXERCISE_KEY,
                    tag=exercise_tag(exercise_no),
                    inputs=list(case["inputs"]),
                )
            )
        except Exception as exc:  # noqa: BLE001 — show any student runtime failure
            actual.append(f"<error: {exc}>")
    if actual != expected:
        return [f"Expected: {expected!r}\n     Got: {actual!r}"]
    return []


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex010.EX010_MIN_EXPLANATION_LENGTH,
        ex010.EX010_PLACEHOLDER_PHRASES,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    """Interleave each part's output, construct, and explanation checks."""
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in ex010.EX010_INPUT_CASES:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Prompt flow (all cases)",
                    _check_input_output,
                )
            )
        else:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Correct output",
                    _check_static_output,
                )
            )
        checks.append(
            build_exercise_check(exercise_no, "Construct", _check_construct)
        )
        checks.append(
            build_exercise_check(
                exercise_no,
                "Explanation",
                _check_explanation,
            )
        )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()

__all__ = ["CHECKS"]
