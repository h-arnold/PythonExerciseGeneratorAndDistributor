"""Student-checker support for ex006 sequence modify casting."""

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

_EXERCISE_KEY = "ex006_sequence_modify_casting"
ex006 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _check_static_output(exercise_no: int) -> list[str]:
    expected = ex006.EX006_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except (NotebookGradingError, RuntimeError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    if output != expected:
        return [f"Exercise {exercise_no}: expected {expected!r}, got {output!r}."]
    return _check_data_flow(exercise_no)


def _check_interactive_output(exercise_no: int) -> list[str]:
    cases = ex006.EX006_INPUT_CASES[exercise_no]
    issues: list[str] = []
    for case in cases:
        inputs = list(case["inputs"])
        try:
            output = run_cell_with_input(
                _EXERCISE_KEY,
                tag=exercise_tag(exercise_no),
                inputs=inputs,
            )
        except (NotebookGradingError, RuntimeError) as exc:
            return [f"Exercise {exercise_no} with inputs {inputs!r}: {exc}"]
        if output != case["expected_output"]:
            issues.append(
                f"Exercise {exercise_no} with inputs {inputs!r}: "
                f"expected {case['expected_output']!r}, got {output!r}."
            )
    if issues:
        return issues
    return _check_data_flow(exercise_no)


def _check_data_flow(exercise_no: int) -> list[str]:
    try:
        code = extract_tagged_code(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
        tree = ast.parse(code)
    except (NotebookGradingError, RuntimeError, SyntaxError) as exc:
        return [f"Exercise {exercise_no}: {exc}"]
    return _construct_checks.required_flow_issues(tree, exercise_no)


CHECKS: list[ExerciseCheckDefinition] = [
    build_exercise_check(1, "Output and data flow", _check_static_output),
    build_exercise_check(2, "Output and data flow", _check_static_output),
    build_exercise_check(3, "Output and data flow", _check_static_output),
    build_exercise_check(4, "Output and data flow", _check_static_output),
    build_exercise_check(5, "Output and data flow", _check_static_output),
    build_exercise_check(6, "Exact prompt flow and data flow", _check_interactive_output),
    build_exercise_check(7, "Exact prompt flow and data flow", _check_interactive_output),
    build_exercise_check(8, "Output and data flow", _check_static_output),
    build_exercise_check(9, "Output and data flow", _check_static_output),
    build_exercise_check(10, "Exact prompt flow and data flow", _check_interactive_output),
]
