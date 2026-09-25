"""Student-checker support for ex013 sequence debug maths operators."""

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
    check_explanation_cell,
)

_EXERCISE_KEY = "ex013_sequence_debug_maths_operators"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    expected = _ex.EX013_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
    except (NotebookGradingError, RuntimeError) as exc:
        return [str(exc)]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    issues: list[str] = []
    cases = _ex.EX013_INPUT_CASES[exercise_no]
    for case_number, case in enumerate(cases, start=1):
        inputs = list(case["inputs"])
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=f"exercise{exercise_no}",
                inputs=inputs,
            )
        except (NotebookGradingError, RuntimeError) as exc:
            issues.append(f"Case {case_number} {inputs!r}: {exc}")
            continue
        if output != case["expected_output"]:
            issues.append(
                f"Case {case_number} {inputs!r}: expected {case['expected_output']!r}, "
                f"got {output!r}"
            )
    return issues


def _check_construct(exercise_no: int) -> list[str]:
    try:
        source = extract_tagged_code(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
        tree = ast.parse(source)
    except (NotebookGradingError, SyntaxError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    return [
        f"Exercise {exercise_no}: {issue}"
        for issue in _construct_checks.construct_issues(tree, exercise_no)
    ]


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


def _make_output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    if exercise_no in _ex.EX013_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


# Keep each part's output, construct, and reflection checks adjacent.
CHECKS: list[ExerciseCheckDefinition] = [
    _make_output_check(1, "Full groups only"),
    build_exercise_check(1, "Live final binding and data flow", _check_construct),
    build_exercise_check(1, "Explain what went wrong", _check_explanation),
    _make_output_check(2, "Find the leftover"),
    build_exercise_check(2, "Live final binding and data flow", _check_construct),
    build_exercise_check(2, "Explain what went wrong", _check_explanation),
    _make_output_check(3, "Round an average"),
    build_exercise_check(3, "Live final binding and data flow", _check_construct),
    build_exercise_check(3, "Explain what went wrong", _check_explanation),
    _make_output_check(4, "Teams from input"),
    build_exercise_check(4, "Live final binding and data flow", _check_construct),
    build_exercise_check(4, "Explain what went wrong", _check_explanation),
    _make_output_check(5, "Round money to 2 decimal places"),
    build_exercise_check(5, "Live final binding and data flow", _check_construct),
    build_exercise_check(5, "Explain what went wrong", _check_explanation),
    _make_output_check(6, "Split minutes"),
    build_exercise_check(6, "Live final binding and data flow", _check_construct),
    build_exercise_check(6, "Explain what went wrong", _check_explanation),
    _make_output_check(7, "Pence to pounds"),
    build_exercise_check(7, "Live final binding and data flow", _check_construct),
    build_exercise_check(7, "Explain what went wrong", _check_explanation),
    _make_output_check(8, "Area of a square"),
    build_exercise_check(8, "Live final binding and data flow", _check_construct),
    build_exercise_check(8, "Explain what went wrong", _check_explanation),
    _make_output_check(9, "Apples into bags"),
    build_exercise_check(9, "Live final binding and data flow", _check_construct),
    build_exercise_check(9, "Explain what went wrong", _check_explanation),
    _make_output_check(10, "Mixed challenge"),
    build_exercise_check(10, "Live final binding and data flow", _check_construct),
    build_exercise_check(10, "Explain what went wrong", _check_explanation),
]


__all__ = ["CHECKS"]
