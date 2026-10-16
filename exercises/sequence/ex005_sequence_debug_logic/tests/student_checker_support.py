"""Exercise-local student checker definitions for ex005 debug logic."""

from __future__ import annotations

from collections.abc import Callable

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    extract_tagged_code,
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
_task_checks = load_exercise_test_module(_EXERCISE_KEY, "task_checks")


def _output(exercise_no: int, inputs: list[str] | None = None) -> str:
    if inputs is None:
        inputs = ex005.EX005_EXERCISE_INPUTS.get(exercise_no)
    if inputs is not None:
        return run_cell_with_input(_EXERCISE_KEY, tag=exercise_tag(exercise_no), inputs=inputs)
    return run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))


def _check_task(exercise_no: int) -> list[str]:
    code = extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(exercise_no))

    def output(inputs: list[str] | None) -> str:
        return _output(exercise_no, inputs)

    validate_task: Callable[[int, str, Callable[[list[str] | None], str]], list[str]] = (
        _task_checks.validate_task
    )
    return validate_task(exercise_no, code, output)


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex005.EX005_MIN_EXPLANATION_LENGTH,
        ex005.EX005_PLACEHOLDER_PHRASES,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        checks.append(
            build_exercise_check(exercise_no, "Correct output and data flow", _check_task)
        )
        checks.append(build_exercise_check(exercise_no, "Explanation", _check_explanation))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
