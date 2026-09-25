"""Student-checker support for ex015 sequence make consolidation."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex015_sequence_make_consolidation_v2"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a non-interactive cell against its exact static transcript."""
    expected = _ex.EX015_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except RuntimeError as exc:
        return [str(exc)]
    if output != expected:
        return [f"Expected {expected!r}; got {output!r}."]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every canonical interactive case for one part."""
    for case in _ex.EX015_INPUT_CASES[exercise_no]:
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=exercise_tag(exercise_no),
                inputs=list(case["inputs"]),
            )
        except RuntimeError as exc:
            return [f"Case {case['id']}: {exc}"]
        if output != case["expected_output"]:
            return [
                f"Case {case['id']}: expected {case['expected_output']!r}; got {output!r}."
            ]
    return []


def _check_constructs(exercise_no: int) -> list[str]:
    """Verify conservative grammar and semantic payload flow."""
    try:
        source = extract_tagged_code(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
        tree = ast.parse(source)
    except (RuntimeError, SyntaxError) as exc:
        return [str(exc)]
    return [
        *_checks.construct_issues(tree, exercise_no),
        *_checks.data_flow_issues(tree, exercise_no),
    ]


def _check_exercise(exercise_no: int) -> list[str]:
    """Run output and semantic checks for one part."""
    if exercise_no in _ex.EX015_EXPECTED_STATIC_OUTPUTS:
        output_issues = _check_static_output(exercise_no)
    else:
        output_issues = _check_input_output(exercise_no)
    return list(dict.fromkeys([*output_issues, *_check_constructs(exercise_no)]))


def _make_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build one interleaved self-check row."""
    return build_exercise_check(exercise_no, title, _check_exercise)


CHECKS: list[ExerciseCheckDefinition] = [
    _make_check(1, "Party supply calculation"),
    _make_check(2, "Paint coverage calculation"),
    _make_check(3, "Pet age conversion"),
    _make_check(4, "Pizza sharing"),
    _make_check(5, "Fuel cost"),
    _make_check(6, "Temperature conversion"),
    _make_check(7, "Savings goal"),
    _make_check(8, "Garden area"),
    _make_check(9, "Bill splitting"),
    _make_check(10, "Classroom supplies"),
]
