from __future__ import annotations

import ast

import pytest

from tests.exercise_expectations import ex006_sequence_modify_casting as ex006
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)


def _tag(n: int) -> str:
    return f"exercise{n}"


_NOTEBOOK_PATH = resolve_notebook_path(ex006.EX006_NOTEBOOK_PATH)
_CACHE = RuntimeCache()


def _run(n: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(n),
        cache=_CACHE,
    )


def _run_with_inputs(n: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(n),
        inputs=inputs,
        cache=_CACHE,
    )


def _ast(n: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(n),
        cache=_CACHE,
    )
    return ast.parse(code)


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _has_binop(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _run(1)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _ast(1)
    assert _has_call(tree, "int")


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _run(2)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _ast(2)
    assert _has_call(tree, "float")


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _run(3)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _ast(3)
    assert _has_call(tree, "int")


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _run(4)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _ast(4)
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _run(5)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _ast(5)
    assert _has_call(tree, "int")


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _run_with_inputs(6, list(ex006.EX006_INPUT_EXPECTATIONS[6]["inputs"]))
    assert ex006.EX006_INPUT_EXPECTATIONS[6]["prompt_contains"] in output
    # final line should be 12
    last = output.strip().splitlines()[-1]
    expected_last = ex006.EX006_INPUT_EXPECTATIONS[6].get("last_line")
    assert expected_last is not None
    assert last == expected_last


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _run_with_inputs(7, list(ex006.EX006_INPUT_EXPECTATIONS[7]["inputs"]))
    assert ex006.EX006_INPUT_EXPECTATIONS[7]["prompt_contains"] in output
    expected_output = ex006.EX006_INPUT_EXPECTATIONS[7].get("output_contains")
    assert expected_output is not None
    assert expected_output in output


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _run(8)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _ast(8)
    assert _has_binop(tree, ast.Mult)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _run(9)
    assert output == ex006.EX006_EXPECTED_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _ast(9)
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _run_with_inputs(10, list(ex006.EX006_INPUT_EXPECTATIONS[10]["inputs"]))
    assert ex006.EX006_INPUT_EXPECTATIONS[10]["prompt_contains"] in output
    expected_output = ex006.EX006_INPUT_EXPECTATIONS[10].get("output_contains")
    assert expected_output is not None
    assert expected_output in output
