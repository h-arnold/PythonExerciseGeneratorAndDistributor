"""Student-checker support for ex014 advanced arithmetic."""

from __future__ import annotations

import ast
from typing import Final

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

_EXERCISE_KEY = "ex014_sequence_gaps_advanced_arithmetic"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
_EXERCISE_TITLES: Final[tuple[tuple[int, str], ...]] = (
    (1, "Square a number"),
    (2, "Cube a number"),
    (3, "Square root"),
    (4, "Power of a number"),
    (5, "Area of a square"),
    (6, "Area of a rectangle"),
    (7, "Volume of a cube"),
    (8, "Square root with input"),
    (9, "Area of a circle"),
    (10, "Power calculator"),
)


def _semantic_issues(exercise_no: int) -> list[str]:
    """Return conservative grammar and data-flow issues for one exercise cell."""
    try:
        source = extract_tagged_code(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
        tree = ast.parse(source)
    except (NotebookGradingError, SyntaxError) as exc:
        return [str(exc)]
    return _construct_checks.required_flow_issues(tree, exercise_no)


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive cell produces the exact expected output."""
    issues = _semantic_issues(exercise_no)
    if issues:
        return ["Fix the required code flow before checking output: " + " ".join(issues)]
    expected = _ex.EX014_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except NotebookGradingError as exc:
        return [str(exc)]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive cell produces the exact primary-case transcript."""
    issues = _semantic_issues(exercise_no)
    if issues:
        return ["Fix the required code flow before checking output: " + " ".join(issues)]
    case = _ex.EX014_INPUT_CASES[exercise_no][0]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=case["inputs"],
        )
    except NotebookGradingError as exc:
        return [str(exc)]
    expected = case["expected_output"]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_required_flow(exercise_no: int) -> list[str]:
    """Verify the conservative straight-line semantic data flow."""
    return _semantic_issues(exercise_no)


def _checks_for(exercise_no: int, title: str) -> tuple[ExerciseCheckDefinition, ...]:
    """Build interleaved exact-output and semantic checks for one exercise."""
    output_check = (
        _check_input_output
        if exercise_no in _ex.EX014_INPUT_CASES
        else _check_static_output
    )
    return (
        build_exercise_check(exercise_no, f"{title}: required code flow", _check_required_flow),
        build_exercise_check(exercise_no, f"{title}: exact output", output_check),
    )


CHECKS: list[ExerciseCheckDefinition] = [
    check
    for exercise_no, title in _EXERCISE_TITLES
    for check in _checks_for(exercise_no, title)
]
