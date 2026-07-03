"""Exercise-local student checker definitions for ex002_selection_debug_if_then_else."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)
from exercise_runtime_support.student_checker.checks.base import (
    check_explanation_cell as _check_explanation_cell,
)

_EXERCISE_KEY = "ex002_selection_debug_if_then_else"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the correct output."""
    case = _ex.EX002_INPUT_CASES[exercise_no]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=case["inputs"],
        )
    except Exception as exc:
        return [f"Runtime error: {exc}"]
    expected = case["expected_output"]
    if output != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output!r}"
        ]
    return []


def _check_explanation(exercise_no: int) -> list[str]:
    """Verify the explanation cell has been filled in."""
    return _check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


def _make_output_check(exercise_no: int) -> ExerciseCheckDefinition:
    """Build an output-verification check for the given exercise."""
    return build_exercise_check(
        exercise_no,
        "Correct output",
        _check_input_output,
    )


def _make_explanation_check(exercise_no: int) -> ExerciseCheckDefinition:
    """Build an explanation-verification check for the given exercise."""
    return build_exercise_check(
        exercise_no,
        "Explain what went wrong",
        _check_explanation,
    )


# ---------------------------------------------------------------------------
# Public CHECKS list — interleaved by exercise
# Each exercise's output check and explanation check are adjacent so the
# reporting table groups them under a single "Exercise N" row.
# ---------------------------------------------------------------------------
CHECKS: list[ExerciseCheckDefinition] = []
for ex_no in range(1, 21):
    CHECKS.append(_make_output_check(ex_no))
    CHECKS.append(_make_explanation_check(ex_no))
