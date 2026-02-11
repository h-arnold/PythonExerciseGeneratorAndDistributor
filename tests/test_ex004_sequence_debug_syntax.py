from __future__ import annotations

import ast

import pytest

from tests.exercise_expectations import ex004_sequence_debug_syntax as ex004
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from tests.exercise_framework.expectations_helpers import is_valid_explanation


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


_NOTEBOOK_PATH = resolve_notebook_path(ex004.EX004_NOTEBOOK_PATH)
_CACHE = RuntimeCache()


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_input(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _has_print_constant(tree: ast.AST, text: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and arg.value == text:
                    return True
    return False


def _assigns_constant(tree: ast.AST, name: str, value: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        if (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and node.value.value == value
        ):
            return True
    return False


def _print_uses_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id == name:
                    return True
    return False


def _has_call(tree: ast.AST, func_name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == func_name
        ):
            return True
    return False


def _assigns_call(tree: ast.AST, name: str, func_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        if isinstance(func, ast.Name) and func.id == func_name:
            return True
        if (
            isinstance(func, ast.Name)
            and func.id == "int"
            and value.args
            and isinstance(value.args[0], ast.Call)
            and isinstance(value.args[0].func, ast.Name)
            and value.args[0].func.id == func_name
        ):
            return True
    return False


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_constant(node: ast.AST, value: int) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _assigns_binop_sum(tree: ast.AST, target_name: str, variable: str, constant: int) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(_is_name(target, target_name) for target in node.targets):
            continue
        value = node.value
        if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Add):
            continue
        if (_is_name(value.left, variable) or _is_name(value.right, variable)) and (
            _is_constant(value.left, constant) or _is_constant(
                value.right, constant)
        ):
            return True
    return False


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[1]
    assert "TODO" not in output


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[1]}\n"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _has_print_constant(tree, ex004.EX004_EXPECTED_SINGLE_LINE[1])


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(1))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[2]


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[2]}\n"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _has_print_constant(tree, ex004.EX004_EXPECTED_SINGLE_LINE[2])


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(2))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[3]


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[3]}\n"


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    strings = _string_constants(tree)
    assert ex004.EX004_EXPECTED_SINGLE_LINE[3] in strings or (
        {"Learning", "Python"} <= strings)


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(3))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[4]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output(4)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[4]}\n"


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_multiplication


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(4))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(5)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[5]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output(5)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[5]}\n"


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    assert _assigns_constant(tree, "name", "Alice")
    assert _print_uses_name(tree, "name")


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(5))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[6]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output(6)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[6]}\n"


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    assert _assigns_constant(
        tree, "greeting", ex004.EX004_EXPECTED_SINGLE_LINE[6])
    assert _print_uses_name(tree, "greeting")


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(6))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output_with_input(7, ["5"])
    assert ex004.EX004_FORMAT_VALIDATION[7] in output
    assert ex004.EX004_PROMPT_STRINGS[7] in output


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output_with_input(7, ["5"])
    assert output.startswith(ex004.EX004_PROMPT_STRINGS[7])
    assert output.rstrip().endswith(ex004.EX004_FORMAT_VALIDATION[7])


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _assigns_call(tree, "apples", "input")
    assert _print_uses_name(tree, "apples")


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(7))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    name = "Alice"
    output = _exercise_output_with_input(8, [name])
    assert ex004.EX004_FORMAT_VALIDATION[8].replace("Alice", name) in output
    assert ex004.EX004_PROMPT_STRINGS[8] in output


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    name = "Alice"
    output = _exercise_output_with_input(8, [name])
    expected = f"{ex004.EX004_PROMPT_STRINGS[8]} {ex004.EX004_FORMAT_VALIDATION[8]}\n"
    assert output == expected


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _assigns_call(tree, "name", "input")
    assert _print_uses_name(tree, "name")


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(8))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[9]}\n"


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _has_print_constant(tree, ex004.EX004_EXPECTED_SINGLE_LINE[9])


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(9))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    colour = "Blue"
    output = _exercise_output_with_input(10, [colour])
    assert ex004.EX004_FORMAT_VALIDATION[10].replace("Blue", colour) in output
    assert ex004.EX004_PROMPT_STRINGS[10] in output


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    colour = "Blue"
    output = _exercise_output_with_input(10, [colour])
    expected = f"{ex004.EX004_PROMPT_STRINGS[10]} {ex004.EX004_FORMAT_VALIDATION[10]}\n"
    assert output == expected


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    assert _assigns_call(tree, "colour", "input")
    assert _print_uses_name(tree, "colour")


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH, tag=_explanation_tag(10))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )
