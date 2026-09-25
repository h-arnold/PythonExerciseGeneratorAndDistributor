"""Student-checker support for ex004 debug syntax."""

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

_EXERCISE_KEY = "ex004_sequence_debug_syntax"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a static exercise cell produces its exact expected output."""
    expected = _ex.EX004_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except RuntimeError as exc:
        return [str(exc)]
    if output != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output!r}"
        ]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every deterministic input case produces its exact output."""
    errors: list[str] = []
    cases = _ex.EX004_INPUT_CASES[exercise_no]
    for case_no, case in enumerate(cases, start=1):
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=exercise_tag(exercise_no),
                inputs=list(case["inputs"]),
            )
        except RuntimeError as exc:
            errors.append(f"Exercise {exercise_no} case {case_no}: {exc}")
            continue
        expected = case["expected_output"]
        if output != expected:
            errors.append(
                f"Exercise {exercise_no} case {case_no}: expected {expected!r}, "
                f"got {output!r}."
            )
    return errors


def _check_explanation(exercise_no: int) -> list[str]:
    """Verify the exercise explanation contains meaningful student text."""
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        min_length=_ex.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX004_PLACEHOLDER_PHRASES,
    )


def _make_output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build the output check appropriate to the exercise's input mode."""
    if exercise_no in _ex.EX004_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


CHECKS: list[ExerciseCheckDefinition] = [
    _make_output_check(1, "Print a message"),
    build_exercise_check(1, "Explain what went wrong", _check_explanation),
    _make_output_check(2, "Print a greeting"),
    build_exercise_check(2, "Explain what went wrong", _check_explanation),
    _make_output_check(3, "Join two words"),
    build_exercise_check(3, "Explain what went wrong", _check_explanation),
    _make_output_check(4, "Calculate a result"),
    build_exercise_check(4, "Explain what went wrong", _check_explanation),
    _make_output_check(5, "Print a greeting with a variable"),
    build_exercise_check(5, "Explain what went wrong", _check_explanation),
    _make_output_check(6, "Store and print a message"),
    build_exercise_check(6, "Explain what went wrong", _check_explanation),
    _make_output_check(7, "String concatenation"),
    build_exercise_check(7, "Explain what went wrong", _check_explanation),
    _make_output_check(8, "Read user input"),
    build_exercise_check(8, "Explain what went wrong", _check_explanation),
    _make_output_check(9, "Print a phrase"),
    build_exercise_check(9, "Explain what went wrong", _check_explanation),
    _make_output_check(10, "Ask and respond"),
    build_exercise_check(10, "Explain what went wrong", _check_explanation),
]
