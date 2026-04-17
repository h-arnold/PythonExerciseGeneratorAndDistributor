"""Exercise-local student checker definitions for ex008 sequence make consolidation."""

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

_EXERCISE_KEY = "ex008_sequence_make_consolidation"
ex008 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    expected = ex008.EX008_EXPECTED_STATIC_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_interactive_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    for case in ex008.EX008_INTERACTIVE_CASES[exercise_no]:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=list(case["inputs"]),
        )
        if output != case["expected_output"]:
            errors.append(
                f"Exercise {exercise_no}: expected '{case['expected_output'].strip()}'."
            )
            break
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in sorted(ex008.EX008_EXPECTED_STATIC_OUTPUTS):
        checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
    for exercise_no in sorted(ex008.EX008_INTERACTIVE_CASES):
        checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_interactive_output))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
