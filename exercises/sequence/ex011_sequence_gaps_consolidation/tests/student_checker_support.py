"""Exercise-local student checker definitions for ex011 sequence gaps consolidation."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    NotebookGradingError,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex011_sequence_gaps_consolidation"
ex011 = load_exercise_test_module(_EXERCISE_KEY, "expectations")

_FSTRING_CHECK_EXERCISE_NO = 7


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _check_static_output(exercise_no: int) -> list[str]:
    expected = ex011.EX011_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    if output != expected:
        return [f"Exercise {exercise_no}: output does not match expected text."]
    return []


def _check_prompt_flow(exercise_no: int) -> list[str]:
    case = ex011.EX011_INPUT_CASES[exercise_no]
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=case["inputs"],
    )
    if output != case["expected_output"]:
        return [
            f"Exercise {exercise_no}: output does not match the expected prompt flow."
        ]
    return []


def _check_exercise7_fstring(exercise_no: int) -> list[str]:
    """Exercise 7 must use an f-string."""
    tree = _exercise_ast(exercise_no)
    has_f_string = any(isinstance(node, ast.JoinedStr)
                       for node in ast.walk(tree))
    if not has_f_string:
        return ["Exercise 7: use an f-string for the final output."]
    return []


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in ex011.EX011_EXPECTED_STATIC_OUTPUTS:
            checks.append(build_exercise_check(
                exercise_no, "Output", _check_static_output))
        if exercise_no in ex011.EX011_INPUT_CASES:
            checks.append(build_exercise_check(
                exercise_no, "Prompt flow", _check_prompt_flow))
        if exercise_no == _FSTRING_CHECK_EXERCISE_NO:
            checks.append(build_exercise_check(
                exercise_no, "Construct", _check_exercise7_fstring))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
