"""Student-checker support for ex012 sequence modify maths operators."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    NotebookGradingError,
    extract_tagged_code,
    run_cell_and_capture_output,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex012_sequence_modify_maths_operators"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify one static cell against its exact canonical output."""
    expected = _ex.EX012_EXPECTED_OUTPUTS[exercise_no]
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


def _check_construct(exercise_no: int) -> list[str]:
    """Verify straight-line structure, live bindings, and positional output flow."""
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


# Keep output and construct checks next to one another for each part.
CHECKS: list[ExerciseCheckDefinition] = [
    build_exercise_check(1, "Exact output", _check_static_output),
    build_exercise_check(1, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(2, "Exact output", _check_static_output),
    build_exercise_check(2, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(3, "Exact output", _check_static_output),
    build_exercise_check(3, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(4, "Exact output", _check_static_output),
    build_exercise_check(4, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(5, "Exact output", _check_static_output),
    build_exercise_check(5, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(6, "Exact output", _check_static_output),
    build_exercise_check(6, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(7, "Exact output", _check_static_output),
    build_exercise_check(7, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(8, "Exact output", _check_static_output),
    build_exercise_check(8, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(9, "Exact output", _check_static_output),
    build_exercise_check(9, "Straight-line calculation and output flow", _check_construct),
    build_exercise_check(10, "Exact output", _check_static_output),
    build_exercise_check(10, "Straight-line calculation and output flow", _check_construct),
]

__all__ = ["CHECKS"]
