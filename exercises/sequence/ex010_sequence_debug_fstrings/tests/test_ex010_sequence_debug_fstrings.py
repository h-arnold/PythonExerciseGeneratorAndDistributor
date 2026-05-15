from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.execution_variant import get_active_variant
from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import is_valid_explanation
from exercise_runtime_support.exercise_test_support import load_exercise_test_module


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


_EXERCISE_KEY = "ex010_sequence_debug_fstrings"
ex010 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_ACTIVE_VARIANT = get_active_variant(default="student")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(
    _EXERCISE_KEY,
    variant=_ACTIVE_VARIANT,
)
_CACHE = RuntimeCache()


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
        variant=_ACTIVE_VARIANT,
    )


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
        variant=_ACTIVE_VARIANT,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
        variant=_ACTIVE_VARIANT,
    )
    return ast.parse(code)


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
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _exercise_output(1) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _has_f_string(tree), "Exercise 1 must use an f-string"
    assert "name" in _name_ids(tree)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _exercise_output(2) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    names = _name_ids(tree)
    assert _has_f_string(tree), "Exercise 2 must use an f-string"
    assert "pet" in names
    assert "animal" not in names


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _exercise_output(3) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    assert _has_f_string(tree), "Exercise 3 must use an f-string"
    assert {"person", "hobby"} <= _name_ids(tree)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _exercise_output(4) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    assert _has_f_string(tree), "Exercise 4 must use an f-string"
    assert "lesson" in _name_ids(tree)


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    case = ex010.EX010_INPUT_CASES[5]
    assert _exercise_output_with_inputs(
        5, list(case["inputs"])) == case["expected_output"]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    assert _has_call(tree, "input"), "Exercise 5 must use input()"
    assert _has_f_string(tree), "Exercise 5 must use an f-string"


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    case = ex010.EX010_INPUT_CASES[6]
    assert _exercise_output_with_inputs(
        6, list(case["inputs"])) == case["expected_output"]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    input_calls = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
    )
    assert input_calls == 2, "Exercise 6 must use two input() calls"
    assert _has_f_string(tree), "Exercise 6 must use an f-string"
    assert "town" in _name_ids(tree)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    assert _exercise_output(7) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[7]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _has_f_string(tree), "Exercise 7 must use an f-string"
    assert "goals" in _name_ids(tree)


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    assert _exercise_output(8) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _has_binop(tree, ast.Add), "Exercise 8 must add the ticket values"
    assert _has_f_string(tree), "Exercise 8 must use an f-string"


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _exercise_output(9) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _has_binop(tree, ast.Add), "Exercise 9 must add the page values"
    assert _has_f_string(tree), "Exercise 9 must use an f-string"
    assert not _has_call(tree, "int"), "Exercise 9 should not use casting"
    assert not _has_call(tree, "float"), "Exercise 9 should not use casting"


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    assert _exercise_output(10) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[10]


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    assert _has_binop(
        tree, ast.Mult), "Exercise 10 must multiply price by amount"
    assert _has_f_string(tree), "Exercise 10 must use an f-string"
    assert not _has_call(tree, "int"), "Exercise 10 should not use casting"
    assert not _has_call(tree, "float"), "Exercise 10 should not use casting"


@pytest.mark.parametrize(
    "exercise_no",
    [
        pytest.param(exercise_no, marks=pytest.mark.task(taskno=exercise_no))
        for exercise_no in range(1, 11)
    ],
)
def test_explanations_have_content(exercise_no: int) -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH,
        tag=_explanation_tag(exercise_no),
        variant=_ACTIVE_VARIANT,
    )
    assert is_valid_explanation(
        explanation,
        min_length=ex010.EX010_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex010.EX010_PLACEHOLDER_PHRASES,
    )
