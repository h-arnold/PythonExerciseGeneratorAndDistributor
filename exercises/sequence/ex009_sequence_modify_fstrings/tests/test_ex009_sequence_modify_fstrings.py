from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)

_EXERCISE_KEY = "ex009_sequence_modify_fstrings"
ex009 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _has_f_string(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))


def _has_print_string_concat(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "print":
            continue
        if any(isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add) for arg in node.args):
            return True
    return False


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(
            node.func, ast.Name) and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _has_binop(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _int_constants(tree: ast.AST) -> set[int]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    }


def _assert_strict_output(exercise_no: int, output: str, expected: str) -> None:
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact output {expected!r} but got {output!r}."
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _run(1)
    _assert_strict_output(1, output, ex009.EX009_EXPECTED_OUTPUTS[1])
    assert "Hello" not in output


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _ast(1)
    assert _has_f_string(tree), "Exercise 1 must use an f-string"


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _run(2)
    _assert_strict_output(2, output, ex009.EX009_EXPECTED_OUTPUTS[2])
    assert "cat" not in output


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _ast(2)
    constants = _string_constants(tree)
    assert _has_f_string(tree), "Exercise 2 must use an f-string"
    assert "cat" not in constants


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _run(3)
    _assert_strict_output(3, output, ex009.EX009_EXPECTED_OUTPUTS[3])
    assert "likes" not in output


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _ast(3)
    assert _has_f_string(tree), "Exercise 3 must use an f-string"


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _run(4)
    _assert_strict_output(4, output, ex009.EX009_EXPECTED_OUTPUTS[4])
    assert "science" not in output


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _ast(4)
    assert _has_f_string(tree), "Exercise 4 must use an f-string"
    assert not _has_print_string_concat(
        tree), "Exercise 4 must not use + concatenation in print"


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    case = ex009.EX009_INPUT_CASES[5]
    output = _run_with_inputs(5, list(case["inputs"]))
    _assert_strict_output(5, output, case["expected_output"])


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _ast(5)
    assert _has_call(tree, "input"), "Exercise 5 must use input()"
    assert _has_f_string(tree), "Exercise 5 must use an f-string"
    assert not _has_print_string_concat(
        tree), "Exercise 5 must not concatenate with + in print"


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    case = ex009.EX009_INPUT_CASES[6]
    output = _run_with_inputs(6, list(case["inputs"]))
    _assert_strict_output(6, output, case["expected_output"])


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _ast(6)
    input_calls = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
    )
    assert input_calls == 2, "Exercise 6 must use two input() calls"
    assert _has_f_string(tree), "Exercise 6 must use an f-string"
    assert not _has_print_string_concat(
        tree), "Exercise 6 must not concatenate with + in print"


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _run(7)
    _assert_strict_output(7, output, ex009.EX009_EXPECTED_OUTPUTS[7])
    assert "str(" not in output


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _ast(7)
    assert _has_f_string(tree), "Exercise 7 must use an f-string"
    assert not _has_call(tree, "str"), "Exercise 7 should not use str()"


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _run(8)
    _assert_strict_output(8, output, ex009.EX009_EXPECTED_OUTPUTS[8])
    assert "Tickets sold today" not in output


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _ast(8)
    assert _has_binop(
        tree, ast.Add), "Exercise 8 must add values to compute the total"
    assert _has_f_string(tree), "Exercise 8 must use an f-string"


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    case = ex009.EX009_INPUT_CASES[9]
    output = _run_with_inputs(9, list(case["inputs"]))
    _assert_strict_output(9, output, case["expected_output"])
    assert "Pages read today" not in output


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _ast(9)
    int_constants = _int_constants(tree)
    assert _has_call(tree, "int"), "Exercise 9 must cast input to int"
    assert _has_binop(
        tree, ast.Add), "Exercise 9 must add today and tomorrow pages"
    assert _has_f_string(tree), "Exercise 9 must use an f-string"
    assert 8 in int_constants, "Exercise 9 must set pages_tomorrow to 8"


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    case = ex009.EX009_INPUT_CASES[10]
    output = _run_with_inputs(10, list(case["inputs"]))
    _assert_strict_output(10, output, case["expected_output"])
    assert "You bought" not in output


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _ast(10)
    assert _has_call(tree, "float"), "Exercise 10 must cast price with float()"
    assert _has_call(tree, "int"), "Exercise 10 must cast amount with int()"
    assert _has_binop(
        tree, ast.Mult), "Exercise 10 must multiply price by amount"
    assert _has_f_string(tree), "Exercise 10 must use an f-string"
