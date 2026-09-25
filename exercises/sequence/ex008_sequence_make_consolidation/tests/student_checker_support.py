"""Student-checker support for ex008 sequence make consolidation."""

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
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_CHECK_RUNTIME_ERRORS = (
    ArithmeticError,
    AttributeError,
    LookupError,
    NameError,
    RuntimeError,
    TypeError,
    ValueError,
)


def _check_static_output(exercise_no: int) -> list[str]:
    expected = _ex.EX008_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except _CHECK_RUNTIME_ERRORS as exc:
        return [str(exc)]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    for case in _ex.EX008_INPUT_CASES[exercise_no]:
        inputs = list(case["inputs"])
        expected = case["expected_output"]
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=exercise_tag(exercise_no),
                inputs=inputs,
            )
        except _CHECK_RUNTIME_ERRORS as exc:
            return [f"Case {case['id']}: {exc}"]
        if output != expected:
            return [f"Case {case['id']}: expected {expected!r}, got {output!r}"]
    return []


def _make_output_check(exercise_no: int) -> ExerciseCheckDefinition:
    if exercise_no in _ex.EX008_EXPECTED_STATIC_OUTPUTS:
        return build_exercise_check(exercise_no, "Static output", _check_static_output)
    return build_exercise_check(exercise_no, "Prompt flow", _check_input_output)


_EXERCISE_NUMBERS = sorted(set(_ex.EX008_EXPECTED_STATIC_OUTPUTS) | set(_ex.EX008_INPUT_CASES))
CHECKS: list[ExerciseCheckDefinition] = [
    _make_output_check(exercise_no) for exercise_no in _EXERCISE_NUMBERS
]
