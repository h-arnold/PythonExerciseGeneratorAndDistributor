"""Exercise-local student checker definitions for ex012 sequence modify maths operators."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import run_cell_and_capture_output
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex012_sequence_modify_maths_operators"
ex012 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    expected = ex012.EX012_EXPECTED_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY, tag=exercise_tag(exercise_no))
    if output != expected:
        errors.append(
            f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in sorted(ex012.EX012_EXPECTED_OUTPUTS):
        checks.append(build_exercise_check(
            exercise_no, "Static output", _check_static_output))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
