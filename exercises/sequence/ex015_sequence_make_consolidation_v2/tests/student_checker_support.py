"""Exercise-local student checker definitions for ex015_sequence_make_consolidation_v2."""
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

_EXERCISE_KEY = "ex015_sequence_make_consolidation_v2"
ex015 = load_exercise_test_module(_EXERCISE_KEY, "expectations")

# Static exercises: 1 and 2
_STATIC_EXERCISES = {1, 2}
# Interactive exercises: 3 through 10
_INTERACTIVE_EXERCISES = set(range(3, 11))


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    expected = ex015.EX015_EXPECTED_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_interactive_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    case = ex015.EX015_INPUT_CASES.get(exercise_no)
    if case is None:
        errors.append(f"Exercise {exercise_no}: no input case defined.")
        return errors
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=list(case["inputs"]),
    )
    if output != case["expected_output"]:
        errors.append(
            f"Exercise {exercise_no}: expected '{case['expected_output'].strip()}'."
        )
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in sorted(_STATIC_EXERCISES):
        checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
    for exercise_no in sorted(_INTERACTIVE_EXERCISES):
        checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_interactive_output))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
