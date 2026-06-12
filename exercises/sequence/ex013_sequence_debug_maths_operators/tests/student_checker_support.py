"""Student-checker support for ex013 sequence debug maths operators.

Defines the CHECKS list consumed by the student self-check cell.
Each check verifies that the corrected student code produces the
expected output — catching logic bugs, not just runtime errors.
"""

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
)

_EXERCISE_KEY = "ex013_sequence_debug_maths_operators"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive exercise cell produces the correct output."""
    expected = _ex.EX013_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
    except Exception as exc:
        return [str(exc)]
    if output != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output!r}"
        ]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the correct output."""
    case = _ex.EX013_INPUT_CASES[exercise_no]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
            inputs=case["inputs"],
        )
    except Exception as exc:
        return [str(exc)]
    expected = case["expected_output"]
    if output != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output!r}"
        ]
    return []


def _check_explanation(exercise_no: int) -> list[str]:
    """Verify the explanation cell has been filled in."""
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


def _make_output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build an output-verification check for the given exercise."""
    if exercise_no in _ex.EX013_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


# ---------------------------------------------------------------------------
# Public CHECKS list — consumed by the student self-check cell
# ---------------------------------------------------------------------------

CHECKS: list[ExerciseCheckDefinition] = [
    _make_output_check(1, "Full groups only"),
    build_exercise_check(1, "Explain what went wrong", _check_explanation),
    _make_output_check(2, "Find the leftover"),
    build_exercise_check(2, "Explain what went wrong", _check_explanation),
    _make_output_check(3, "Round an average"),
    build_exercise_check(3, "Explain what went wrong", _check_explanation),
    _make_output_check(4, "Teams from input"),
    build_exercise_check(4, "Explain what went wrong", _check_explanation),
    _make_output_check(5, "Round money to 2 decimal places"),
    build_exercise_check(5, "Explain what went wrong", _check_explanation),
    _make_output_check(6, "Split minutes"),
    build_exercise_check(6, "Explain what went wrong", _check_explanation),
    _make_output_check(7, "Pence to pounds"),
    build_exercise_check(7, "Explain what went wrong", _check_explanation),
    _make_output_check(8, "Area of a square"),
    build_exercise_check(8, "Explain what went wrong", _check_explanation),
    _make_output_check(9, "Apples into bags"),
    build_exercise_check(9, "Explain what went wrong", _check_explanation),
    _make_output_check(10, "Mixed challenge"),
    build_exercise_check(10, "Explain what went wrong", _check_explanation),
]
