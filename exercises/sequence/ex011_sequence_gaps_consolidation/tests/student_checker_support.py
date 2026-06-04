"""Exercise-local student checker definitions for ex011 sequence gaps consolidation."""

from __future__ import annotations

import ast

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
_STUDENT_VARIANT = "student"

_EXPECTED_STATIC_OUTPUTS: dict[int, str] = {
    1: "Sequence is fun",
    2: "Hello Amina",
    4: "The total is 10",
    5: "Total cost: 7.5",
    6: "Average distance: 3.5 km",
    7: "Aisha enjoys drawing after school.",
}

_INPUT_CASES: dict[int, dict[str, object]] = {
    3: {"inputs": ["word with space"], "expected_output": "What is your favourite word?\nYou chose word with space"},
    8: {"inputs": ["Aisha", "St Asaph"], "expected_output": "Enter your first name:\nEnter your town:\nHello Aisha from St Asaph."},
    9: {"inputs": ["blue", "fox"], "expected_output": "Enter your favourite colour:\nEnter your favourite animal:\nMy favourite colour is blue and my favourite animal is fox."},
    10: {"inputs": ["Amina"], "expected_output": "Enter your name:\nWelcome to Sequence Supplies, Amina. Your total is £14.0."},
}


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        variant=_STUDENT_VARIANT,
    )
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _check_static_output(exercise_no: int) -> list[str]:
    expected = _EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        variant=_STUDENT_VARIANT,
    )
    if output != expected:
        return [f"Exercise {exercise_no}: output does not match expected text."]
    return []


def _check_prompt_flow(exercise_no: int) -> list[str]:
    case = _INPUT_CASES[exercise_no]
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=list(case["inputs"]),
        variant=_STUDENT_VARIANT,
    )
    if output != case["expected_output"]:
        return [
            f"Exercise {exercise_no}: output does not match the expected prompt flow."
        ]
    return []


def _check_exercise7_fstring(exercise_no: int) -> list[str]:
    """Exercise 7 must use an f-string."""
    tree = _exercise_ast(exercise_no)
    has_f_string = any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))
    if not has_f_string:
        return ["Exercise 7: use an f-string for the final output."]
    return []


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in _EXPECTED_STATIC_OUTPUTS:
            checks.append(build_exercise_check(
                exercise_no, "Output", _check_static_output))
        if exercise_no in _INPUT_CASES:
            checks.append(build_exercise_check(
                exercise_no, "Prompt flow", _check_prompt_flow))
        if exercise_no == 7:
            checks.append(build_exercise_check(
                exercise_no, "Construct", _check_exercise7_fstring))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
