"""Student-checker support for ex011 sequence gaps consolidation."""

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

_EXERCISE_KEY = "ex011_sequence_gaps_consolidation"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a static exercise cell produces the exact expected output."""

    expected = _ex.EX011_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except (NotebookGradingError, SyntaxError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    if output != expected:
        return [f"Exercise {exercise_no}: expected {expected!r}, got {output!r}."]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify every deterministic transcript for an interactive cell."""

    cases = _ex.EX011_INPUT_CASES[exercise_no]
    if len(cases) < _ex.EX011_MIN_INPUT_CASES:
        return [
            f"Exercise {exercise_no}: expected at least "
            f"{_ex.EX011_MIN_INPUT_CASES} deterministic input cases."
        ]
    for case in cases:
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=exercise_tag(exercise_no),
                inputs=list(case["inputs"]),
            )
        except (NotebookGradingError, SyntaxError) as exc:
            return [f"Exercise {exercise_no}: {exc}"]
        expected = case["expected_output"]
        if output != expected:
            return [
                f"Exercise {exercise_no} with inputs {case['inputs']!r}: "
                f"expected {expected!r}, got {output!r}."
            ]
    return []


def _check_semantics(exercise_no: int) -> list[str]:
    """Verify the conservative allowlist and unseen-case sensitivity."""

    try:
        code = extract_tagged_code(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
        tree = ast.parse(code)
    except (NotebookGradingError, SyntaxError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    issues = _construct_checks.required_flow_issues(tree, exercise_no)
    return [f"Exercise {exercise_no}: {issue}" for issue in issues]


def _output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build the output check for either a static or interactive part."""

    if exercise_no in _ex.EX011_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


def _construct_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build the semantic sensitivity check for one part."""

    return build_exercise_check(exercise_no, title, _check_semantics)


# Keep each part's output and semantic checks together so the student-facing
# table groups related feedback under one exercise number.
CHECKS: list[ExerciseCheckDefinition] = [
    _output_check(1, "Build a sentence"),
    _construct_check(1, "Check supplied-value sensitivity"),
    _output_check(2, "Combine the greeting and name"),
    _construct_check(2, "Check supplied-value sensitivity"),
    _output_check(3, "Read and echo a word"),
    _construct_check(3, "Check unseen input sensitivity"),
    _output_check(4, "Add two numbers"),
    _construct_check(4, "Check inline arithmetic sensitivity"),
    _output_check(5, "Find the total cost"),
    _construct_check(5, "Check inline arithmetic sensitivity"),
    _output_check(6, "Average distance"),
    _construct_check(6, "Check inline arithmetic sensitivity"),
    _output_check(7, "Share a hobby"),
    _construct_check(7, "Check final f-string sensitivity"),
    _output_check(8, "Greet a visitor"),
    _construct_check(8, "Check unseen input sensitivity"),
    _output_check(9, "Favourite things"),
    _construct_check(9, "Check unseen input sensitivity"),
    _output_check(10, "Sequence shop total"),
    _construct_check(10, "Check unseen input and arithmetic sensitivity"),
]
