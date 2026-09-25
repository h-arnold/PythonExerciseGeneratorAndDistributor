"""Exercise-local student checker definitions for ex007 sequence debug casting."""

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
    exercise_tag,
)

_EXERCISE_KEY = "ex007_sequence_debug_casting"
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
ex007 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    expected = ex007.EX007_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    if output != expected:
        return [f"Exercise {exercise_no}: expected {expected!r}, got {output!r}."]
    return []


def _check_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    for case_no, case in enumerate(ex007.EX007_INPUT_CASES[exercise_no], start=1):
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=list(case["inputs"]),
        )
        if output != case["expected_output"]:
            errors.append(
                f"Exercise {exercise_no} case {case_no}: output does not match "
                "the expected prompt flow."
            )
    return errors


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex007.EX007_MIN_EXPLANATION_LENGTH,
        ex007.EX007_PLACEHOLDER_PHRASES,
    )


def _check_construct(exercise_no: int) -> list[str]:
    tree = _exercise_ast(exercise_no)
    if exercise_no in ex007.EX007_STATIC_CONSTRUCTS:
        rules = ex007.EX007_STATIC_CONSTRUCTS[exercise_no]
        issues = construct_checks.static_construct_issues(
            tree,
            required_calls=rules.get("required_calls", ()),
            required_ops=rules.get("required_ops", ()),
            forbidden_ops=rules.get("forbidden_ops", ()),
            relevant_names=rules.get("relevant_names", ()),
        )
    else:
        rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
        issues = construct_checks.interactive_construct_issues(
            tree,
            expected_input_count=len(ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
            required_calls=rules.get("required_calls", ()),
            required_ops=rules.get("required_ops", ()),
            forbidden_ops=rules.get("forbidden_ops", ()),
        )
    return [f"Exercise {exercise_no}: {issue}" for issue in issues]


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
    )
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in ex007.EX007_EXPECTED_STATIC_OUTPUTS:
            checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
        else:
            checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_prompt_flow))
        checks.append(build_exercise_check(exercise_no, "Construct", _check_construct))
        checks.append(build_exercise_check(exercise_no, "Explanation", _check_explanation))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
