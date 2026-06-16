"""Exercise-local student checker definitions for ex001_selection_modify_basics."""
from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex001_selection_modify_basics"
ex001 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = run_cell_and_capture_output(
        _EXERCISE_KEY, tag=exercise_tag(exercise_no))
    expected = ex001.EX001_EXPECTED_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(
            f"Exercise {exercise_no}: expected '{expected}' but got '{output}'.")
    return errors


def _check_input_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    details = ex001.EX001_INPUT_CASES[exercise_no]
    inputs = details["inputs"]
    output = run_cell_with_input(
        _EXERCISE_KEY, tag=exercise_tag(exercise_no), inputs=inputs)

    prompt_contains = details["prompt_contains"]
    output_contains = details["output_contains"]

    if prompt_contains not in output:
        errors.append(
            f"Exercise {exercise_no}: expected prompt containing "
            f"'{prompt_contains}' was not found in output."
        )
    if output_contains not in output:
        errors.append(
            f"Exercise {exercise_no}: expected message "
            f"'{output_contains}' was not found in output."
        )
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    input_exercises = set(ex001.EX001_INPUT_CASES)
    static_exercises = set(ex001.EX001_EXPECTED_OUTPUTS) - input_exercises
    for exercise_no in sorted(static_exercises):
        checks.append(build_exercise_check(
            exercise_no, "Static output", _check_static_output))
    for exercise_no in sorted(input_exercises):
        checks.append(build_exercise_check(
            exercise_no, "Prompt flow", _check_input_flow))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
