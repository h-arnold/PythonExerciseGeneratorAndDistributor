"""Exercise-local student checker definitions for ex014_sequence_gaps_advanced_arithmetic."""
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

_EXERCISE_KEY = "ex014_sequence_gaps_advanced_arithmetic"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive exercise cell produces the correct output."""
    expected = _ex.EX014_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except Exception as exc:
        return [str(exc)]
    if output.strip() != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output.strip()!r}"
        ]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the correct output."""
    case = _ex.EX014_INPUT_CASES[exercise_no]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=case["inputs"],
        )
    except Exception as exc:
        return [str(exc)]
    expected = case["expected_output"]
    if output.strip() != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output.strip()!r}"
        ]
    return []


def _make_output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build an output-verification check for the given exercise."""
    if exercise_no >= 3:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


# ---------------------------------------------------------------------------
# Public CHECKS list — consumed by the student self-check cell
# ---------------------------------------------------------------------------

CHECKS: list[ExerciseCheckDefinition] = [
    _make_output_check(1, "Square a number"),
    _make_output_check(2, "Cube a number"),
    _make_output_check(3, "Square root"),
    _make_output_check(4, "Power of a number"),
    _make_output_check(5, "Area of a square"),
    _make_output_check(6, "Area of a rectangle"),
    _make_output_check(7, "Volume of a cube"),
    _make_output_check(8, "Square root with input"),
    _make_output_check(9, "Area of a circle"),
    _make_output_check(10, "Power calculator"),
]
