"""Student self-check definitions for ex005 sequence debug logic."""

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
    exercise_tag,
)

_EXERCISE_KEY = "ex005_sequence_debug_logic"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive cell against its exact expected output."""
    expected = _ex.EX005_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except Exception as exc:  # noqa: BLE001 — report runtime errors to students
        return [f"Exercise {exercise_no}: {exc}"]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every deterministic input case for an interactive cell."""
    cases = _ex.EX005_INPUT_CASES[exercise_no]
    expected = [case["expected_output"] for case in cases]
    actual: list[str] = []
    for case in cases:
        try:
            actual.append(
                run_cell_with_input(
                    _EXERCISE_KEY,
                    tag=exercise_tag(exercise_no),
                    inputs=list(case["inputs"]),
                )
            )
        except Exception as exc:  # noqa: BLE001 — report runtime errors to students
            actual.append(f"<error: {exc}>")
    if actual != expected:
        return [f"Expected: {expected!r}\n     Got: {actual!r}"]
    return []


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        _ex.EX005_MIN_EXPLANATION_LENGTH,
        _ex.EX005_PLACEHOLDER_PHRASES,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    """Interleave output and explanation rows for each exercise."""
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in _ex.EX005_INPUT_CASES:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Prompt flow (all cases)",
                    _check_input_output,
                )
            )
        else:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Correct output",
                    _check_static_output,
                )
            )
        checks.append(
            build_exercise_check(
                exercise_no,
                "Explain what went wrong",
                _check_explanation,
            )
        )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
