"""Exercise-local student checker definitions for ex004 debug syntax."""

from __future__ import annotations

from collections.abc import Callable

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    check_explanation_cell,
    exercise_tag,
)

_EXERCISE_KEY = "ex004_sequence_debug_syntax"
ex004 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    expected = ex004.EX004_EXPECTED_SINGLE_LINE[exercise_no]
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _validate_prompt_7(exercise_key: str) -> list[str]:
    output = run_cell_with_input(exercise_key, tag=exercise_tag(7), inputs=["5"])
    if ex004.EX004_PROMPT_STRINGS[7] not in output or ex004.EX004_FORMAT_VALIDATION[7] not in output:
        return ["Exercise 7: output does not match the expected prompt flow."]
    return []


def _validate_prompt_8(exercise_key: str) -> list[str]:
    output = run_cell_with_input(exercise_key, tag=exercise_tag(8), inputs=["Alice"])
    expected = f"{ex004.EX004_PROMPT_STRINGS[8]} {ex004.EX004_FORMAT_VALIDATION[8]}\n"
    if output != expected:
        return ["Exercise 8: output does not match the expected prompt flow."]
    return []


def _validate_prompt_10(exercise_key: str) -> list[str]:
    output = run_cell_with_input(exercise_key, tag=exercise_tag(10), inputs=["Blue"])
    expected = f"{ex004.EX004_PROMPT_STRINGS[10]} {ex004.EX004_FORMAT_VALIDATION[10]}\n"
    if output != expected:
        return ["Exercise 10: output does not match the expected prompt flow."]
    return []


_PROMPT_FLOW_HANDLERS: dict[int, Callable[[str], list[str]]] = {
    7: _validate_prompt_7,
    8: _validate_prompt_8,
    10: _validate_prompt_10,
}


def _check_prompt_flow(exercise_no: int) -> list[str]:
    handler = _PROMPT_FLOW_HANDLERS.get(exercise_no)
    if handler is None:
        return []
    return handler(_EXERCISE_KEY)


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex004.EX004_MIN_EXPLANATION_LENGTH,
        ex004.EX004_PLACEHOLDER_PHRASES,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in ex004.EX004_EXPECTED_SINGLE_LINE:
            checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
        if exercise_no in _PROMPT_FLOW_HANDLERS:
            checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_prompt_flow))
        checks.append(build_exercise_check(exercise_no, "Explanation", _check_explanation))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
