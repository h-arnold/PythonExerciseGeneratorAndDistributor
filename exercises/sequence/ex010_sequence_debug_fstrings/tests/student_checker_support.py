"""Exercise-local student checker definitions for ex010 sequence debug f-strings."""

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

_EXERCISE_KEY = "ex010_sequence_debug_fstrings"
_STUDENT_VARIANT = "student"
ex010 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        variant=_STUDENT_VARIANT,
    )
    try:
        return ast.parse(code)
    except SyntaxError as exc:
        raise NotebookGradingError(
            f"Exercise {exercise_no}: code could not be parsed: {exc.msg}."
        ) from exc


def _has_f_string(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _has_binop(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


def _name_ids(tree: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _formatted_name_ids(tree: ast.AST) -> set[str]:
    formatted_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        for value in node.values:
            if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
                formatted_names.add(value.value.id)
    return formatted_names


def _fstring_text_fragments(tree: ast.AST) -> list[str]:
    fragments: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                fragments.append(value.value)
    return fragments


def _check_static_output(exercise_no: int) -> list[str]:
    expected = ex010.EX010_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        variant=_STUDENT_VARIANT,
    )
    if output != expected:
        return [f"Exercise {exercise_no}: output does not match expected text."]
    return []


def _check_prompt_flow(exercise_no: int) -> list[str]:
    case = ex010.EX010_INPUT_CASES[exercise_no]
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=list(case["inputs"]),
        variant=_STUDENT_VARIANT,
    )
    if output != case["expected_output"]:
        return [
            f"Exercise {exercise_no}: output does not match the expected prompt flow."
        ]
    return []


def _check_construct(exercise_no: int) -> list[str]:
    tree = _exercise_ast(exercise_no)
    names = _name_ids(tree)
    formatted_names = _formatted_name_ids(tree)
    issues: list[str] = []

    if not _has_f_string(tree):
        issues.append(
            f"Exercise {exercise_no}: use an f-string in the final output.")

    if exercise_no == 2 and "animal" in names:
        issues.append("Exercise 2: use 'pet', not 'animal'.")

    if exercise_no == 5 and not _has_call(tree, "input"):
        issues.append("Exercise 5: include one input() call.")

    required_formatted_names: dict[int, set[str]] = {
        1: {"name"},
        2: {"pet"},
        3: {"person", "hobby"},
        4: {"lesson"},
        5: {"snack"},
        6: {"name", "town"},
        7: {"goals"},
        8: {"total_tickets"},
        9: {"total_pages"},
        10: {"amount", "total_cost"},
    }
    missing_formatted = required_formatted_names.get(
        exercise_no, set()) - formatted_names
    if missing_formatted:
        missing_list = ", ".join(sorted(missing_formatted))
        issues.append(
            f"Exercise {exercise_no}: interpolate variable(s) in the f-string: {missing_list}."
        )

    if exercise_no == 6:
        input_calls = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        )
        if input_calls != 2:
            issues.append("Exercise 6: include two input() calls.")

    if exercise_no == 8 and not _has_binop(tree, ast.Add):
        issues.append("Exercise 8: add the ticket values with +.")

    if exercise_no == 9 and not _has_binop(tree, ast.Add):
        issues.append("Exercise 9: add the page values with +.")

    if exercise_no == 10 and not _has_binop(tree, ast.Mult):
        issues.append("Exercise 10: multiply price by amount with *.")

    if exercise_no == 7:
        fragments = _fstring_text_fragments(tree)
        if not any("goals" in fragment for fragment in fragments):
            issues.append(
                "Exercise 7: use the plural word 'goals' in the final sentence.")

    return issues


def _check_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _EXERCISE_KEY,
        exercise_no,
        ex010.EX010_MIN_EXPLANATION_LENGTH,
        ex010.EX010_PLACEHOLDER_PHRASES,
        variant=_STUDENT_VARIANT,
    )


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 11):
        if exercise_no in ex010.EX010_EXPECTED_STATIC_OUTPUTS:
            checks.append(build_exercise_check(
                exercise_no, "Output", _check_static_output))
        if exercise_no in ex010.EX010_INPUT_CASES:
            checks.append(build_exercise_check(
                exercise_no, "Prompt flow", _check_prompt_flow))
        checks.append(build_exercise_check(
            exercise_no, "Construct", _check_construct))
        checks.append(build_exercise_check(
            exercise_no, "Explanation", _check_explanation))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
