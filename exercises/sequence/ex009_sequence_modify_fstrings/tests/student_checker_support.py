"""Student-checker support for ex009 sequence modify f-strings."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    NotebookGradingError,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex009_sequence_modify_fstrings"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive exercise cell produces its exact output."""

    expected = _ex.EX009_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except (NotebookGradingError, RuntimeError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    if output != expected:
        return [f"Exercise {exercise_no}: expected {expected!r}, got {output!r}."]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every deterministic input transcript for an interactive cell."""

    cases = _ex.EX009_INPUT_CASES[exercise_no]
    expected = [case["expected_output"] for case in cases]
    actual: list[str] = []
    for case in cases:
        inputs = list(case["inputs"])
        try:
            actual.append(
                run_cell_with_input(
                    _EXERCISE_KEY,
                    tag=exercise_tag(exercise_no),
                    inputs=inputs,
                )
            )
        except (NotebookGradingError, RuntimeError) as exc:
            return [f"Exercise {exercise_no} with inputs {inputs!r}: {exc}"]
    if actual != expected:
        return [f"Exercise {exercise_no}: expected {expected!r}, got {actual!r}."]
    return []


def _check_construct(exercise_no: int) -> list[str]:
    """Verify the final f-string and conservative sequence provenance."""

    try:
        code = extract_tagged_code(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
        tree = ast.parse(code)
    except (NotebookGradingError, RuntimeError, SyntaxError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    issues = _construct_checks.construct_issues(tree, exercise_no)
    return [f"Exercise {exercise_no}: {issue}" for issue in issues]


def _output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build the output check appropriate to the exercise."""

    if exercise_no in _ex.EX009_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


CHECKS: list[ExerciseCheckDefinition] = [
    _output_check(1, "Exact output"),
    build_exercise_check(1, "Straight-line f-string provenance", _check_construct),
    _output_check(2, "Exact output"),
    build_exercise_check(2, "Straight-line f-string provenance", _check_construct),
    _output_check(3, "Exact output"),
    build_exercise_check(3, "Straight-line f-string provenance", _check_construct),
    _output_check(4, "Exact output"),
    build_exercise_check(4, "Straight-line f-string provenance", _check_construct),
    _output_check(5, "Exact input output"),
    build_exercise_check(5, "Straight-line f-string provenance", _check_construct),
    _output_check(6, "Exact input output"),
    build_exercise_check(6, "Straight-line f-string provenance", _check_construct),
    _output_check(7, "Exact output"),
    build_exercise_check(7, "Straight-line f-string provenance", _check_construct),
    _output_check(8, "Exact output"),
    build_exercise_check(8, "Straight-line f-string provenance", _check_construct),
    _output_check(9, "Exact input output"),
    build_exercise_check(9, "Straight-line f-string provenance", _check_construct),
    _output_check(10, "Exact input output"),
    build_exercise_check(10, "Straight-line f-string provenance", _check_construct),
]


__all__ = ["CHECKS"]
