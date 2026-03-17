"""Checks for the ex007 notebook."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_framework.ex007_construct_checks import (
    has_binop,
    has_call,
    interactive_construct_issues,
)
from exercise_runtime_support.notebook_grader import (
    NotebookGradingError,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from tests.exercise_expectations import ex007_sequence_debug_casting as ex007

from ..models import ExerciseCheckResult
from .base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    check_explanation_cell,
    exercise_tag,
)

_AVERAGE_DISTANCE_EXERCISE = 4
_EX007_EXERCISE_KEY = "ex007_sequence_debug_casting"


def check_ex007() -> list[str]:
    """Run checks for ex007."""
    return [issue for result in run_ex007_checks() for issue in result.issues]


def run_ex007_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex007."""
    results: list[ExerciseCheckResult] = []
    for check in _EX007_CHECKS:
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


def _check_ex007_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    expected = ex007.EX007_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EX007_EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_ex007_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    for case_no, case in enumerate(ex007.EX007_INPUT_CASES[exercise_no], start=1):
        output = run_cell_with_input(
            _EX007_EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=list(case["inputs"]),
        )
        expected_output = case["expected_output"]
        if output != expected_output:
            errors.append(
                f"Exercise {exercise_no}: sample {case_no} does not match the expected prompt flow."
            )
    return errors


def _check_ex007_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EX007_EXERCISE_KEY,
        exercise_no,
        ex007.EX007_MIN_EXPLANATION_LENGTH,
        ex007.EX007_PLACEHOLDER_PHRASES,
    )


def _check_ex007_construct(exercise_no: int) -> list[str]:
    tree = _exercise_ast(exercise_no)

    if exercise_no in {1, 2}:
        if has_call(tree, "str"):
            return []
        return [
            f"Exercise {exercise_no}: use str() so the number is turned into text before printing."
        ]

    if exercise_no == _AVERAGE_DISTANCE_EXERCISE:
        errors: list[str] = []
        if not has_binop(tree, ast.Div):
            errors.append(
                f"Exercise {_AVERAGE_DISTANCE_EXERCISE}: use / for the average calculation."
            )
        if has_binop(tree, ast.FloorDiv):
            errors.append(
                f"Exercise {_AVERAGE_DISTANCE_EXERCISE}: do not use // for the average calculation."
            )
        return errors

    rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
    issues = interactive_construct_issues(
        tree,
        expected_input_count=len(ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
        required_calls=rules.get("required_calls", ()),
        required_ops=rules.get("required_ops", ()),
        forbidden_ops=rules.get("forbidden_ops", ()),
    )
    return [f"Exercise {exercise_no}: {issue}" for issue in issues]


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EX007_EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _build_ex007_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = range(1, 11)
    for exercise_no in exercise_numbers:
        if exercise_no in ex007.EX007_EXPECTED_STATIC_OUTPUTS:
            checks.append(
                build_exercise_check(exercise_no, "Static output", _check_ex007_static_output)
            )
        if exercise_no in ex007.EX007_INPUT_CASES:
            checks.append(
                build_exercise_check(exercise_no, "Prompt flow", _check_ex007_prompt_flow)
            )
        checks.append(build_exercise_check(exercise_no, "Construct", _check_ex007_construct))
        checks.append(build_exercise_check(exercise_no, "Explanation", _check_ex007_explanation))
    return checks


_EX007_CHECKS: list[ExerciseCheckDefinition] = _build_ex007_checks()
EX007_CHECKS = _EX007_CHECKS


__all__ = [
    "EX007_CHECKS",
    "_EX007_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex007",
    "run_ex007_checks",
]
