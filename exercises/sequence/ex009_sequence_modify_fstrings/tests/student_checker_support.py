"""Exercise-local student checker definitions for ex009 sequence modify f-strings."""

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

_EXERCISE_KEY = "ex009_sequence_modify_fstrings"
ex009 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    expected = ex009.EX009_EXPECTED_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY, tag=exercise_tag(exercise_no))
    if output != expected:
        errors.append(
            f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_input_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    case = ex009.EX009_INPUT_CASES[exercise_no]
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=case["inputs"],
    )
    if output != case["expected_output"]:
        errors.append(
            f"Exercise {exercise_no}: expected '{case['expected_output'].strip()}'."
        )
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = sorted(
        set(ex009.EX009_EXPECTED_OUTPUTS) | set(ex009.EX009_INPUT_CASES))
    for exercise_no in exercise_numbers:
        if exercise_no in ex009.EX009_EXPECTED_OUTPUTS:
            checks.append(build_exercise_check(
                exercise_no, "Static output", _check_static_output))
        if exercise_no in ex009.EX009_INPUT_CASES:
            checks.append(build_exercise_check(
                exercise_no, "Input output", _check_input_output))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
