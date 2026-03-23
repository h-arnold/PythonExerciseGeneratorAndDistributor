"""Exercise-local student checker definitions for ex005 debug logic."""

from __future__ import annotations

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

_EXERCISE_KEY = "ex005_sequence_debug_logic"
ex005 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    expected = ex005.EX005_EXPECTED_SINGLE_LINE[exercise_no]
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        return [f"Exercise {exercise_no}: expected '{expected}'."]
    return []


def _check_prompt_flow(exercise_no: int) -> list[str]:
    if exercise_no == ex005.EX005_FULL_NAME_EXERCISE:
        inputs = ex005.EX005_EXERCISE_INPUTS[exercise_no]
        output = run_cell_with_input(_EXERCISE_KEY, tag=exercise_tag(exercise_no), inputs=inputs)
        prompt_first, prompt_second = ex005.EX005_INPUT_PROMPTS[exercise_no]
        expected = f"{prompt_first}{prompt_second}Maria Jones\n"
        if output != expected:
            return [f"Exercise {exercise_no}: output does not match the expected prompt flow."]
        return []

    if exercise_no == ex005.EX005_PROFILE_EXERCISE:
        inputs = ex005.EX005_EXERCISE_INPUTS[exercise_no]
        output = run_cell_with_input(_EXERCISE_KEY, tag=exercise_tag(exercise_no), inputs=inputs)
        prompt_first, prompt_second = ex005.EX005_INPUT_PROMPTS[exercise_no]
        age, city = inputs
        expected = f"{prompt_first}{prompt_second}You are {age} years old and live in {city}\n"
        if output != expected:
            return [f"Exercise {exercise_no}: output does not match the expected prompt flow."]
    return []


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex005.EX005_MIN_EXPLANATION_LENGTH,
        ex005.EX005_PLACEHOLDER_PHRASES,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    prompt_exercises = {ex005.EX005_FULL_NAME_EXERCISE, ex005.EX005_PROFILE_EXERCISE}
    for exercise_no in range(1, 11):
        if exercise_no in ex005.EX005_EXPECTED_SINGLE_LINE:
            checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
        if exercise_no in prompt_exercises:
            checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_prompt_flow))
        checks.append(build_exercise_check(exercise_no, "Explanation", _check_explanation))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
