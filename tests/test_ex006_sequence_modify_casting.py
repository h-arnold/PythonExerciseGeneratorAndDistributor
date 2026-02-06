from __future__ import annotations

import ast

import pytest

from tests.exercise_expectations import (
    EX006_EXPECTED_OUTPUTS,
    EX006_INPUT_EXPECTATIONS,
    EX006_NOTEBOOK_PATH,
)
from tests.notebook_grader import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)


def _tag(n: int) -> str:
    return f"exercise{n}"


def _run(n: int) -> str:
    return run_cell_and_capture_output(EX006_NOTEBOOK_PATH, tag=_tag(n))


def _ast(n: int) -> ast.Module:
    code = extract_tagged_code(EX006_NOTEBOOK_PATH, tag=_tag(n))
    return ast.parse(code)


@pytest.mark.task(taskno=1)
def test_exercise1_output_and_construct() -> None:
    output = _run(1)
    assert output == EX006_EXPECTED_OUTPUTS[1]
    tree = _ast(1)
    has_int = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int"
        for node in ast.walk(tree)
    )
    assert has_int


@pytest.mark.task(taskno=2)
def test_exercise2_output_and_construct() -> None:
    output = _run(2)
    assert output == EX006_EXPECTED_OUTPUTS[2]
    tree = _ast(2)
    has_float = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float"
        for node in ast.walk(tree)
    )
    assert has_float


@pytest.mark.task(taskno=3)
def test_exercise3_output_and_construct() -> None:
    output = _run(3)
    assert output == EX006_EXPECTED_OUTPUTS[3]
    tree = _ast(3)
    has_int = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int"
        for node in ast.walk(tree)
    )
    assert has_int


@pytest.mark.task(taskno=4)
def test_exercise4_output_and_construct() -> None:
    output = _run(4)
    assert output == EX006_EXPECTED_OUTPUTS[4]
    tree = _ast(4)
    has_str = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str"
        for node in ast.walk(tree)
    )
    assert has_str


@pytest.mark.task(taskno=5)
def test_exercise5_output_and_construct() -> None:
    output = _run(5)
    assert output == EX006_EXPECTED_OUTPUTS[5]
    tree = _ast(5)
    has_int = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int"
        for node in ast.walk(tree)
    )
    assert has_int


@pytest.mark.task(taskno=6)
def test_exercise6_with_input() -> None:
    output = run_cell_with_input(
        EX006_NOTEBOOK_PATH,
        tag=_tag(6),
        inputs=list(EX006_INPUT_EXPECTATIONS[6]["inputs"]),
    )
    assert EX006_INPUT_EXPECTATIONS[6]["prompt_contains"] in output
    # final line should be 12
    last = output.strip().splitlines()[-1]
    assert last == EX006_INPUT_EXPECTATIONS[6]["last_line"]


@pytest.mark.task(taskno=7)
def test_exercise7_with_input() -> None:
    output = run_cell_with_input(
        EX006_NOTEBOOK_PATH,
        tag=_tag(7),
        inputs=list(EX006_INPUT_EXPECTATIONS[7]["inputs"]),
    )
    assert EX006_INPUT_EXPECTATIONS[7]["prompt_contains"] in output
    assert EX006_INPUT_EXPECTATIONS[7]["output_contains"] in output


@pytest.mark.task(taskno=8)
def test_exercise8_output_and_construct() -> None:
    output = _run(8)
    assert output == EX006_EXPECTED_OUTPUTS[8]
    tree = _ast(8)
    has_mul = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_mul


@pytest.mark.task(taskno=9)
def test_exercise9_output_and_construct() -> None:
    output = _run(9)
    assert output == EX006_EXPECTED_OUTPUTS[9]
    tree = _ast(9)
    has_str = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str"
        for node in ast.walk(tree)
    )
    assert has_str


@pytest.mark.task(taskno=10)
def test_exercise10_with_input() -> None:
    output = run_cell_with_input(
        EX006_NOTEBOOK_PATH,
        tag=_tag(10),
        inputs=list(EX006_INPUT_EXPECTATIONS[10]["inputs"]),
    )
    assert EX006_INPUT_EXPECTATIONS[10]["prompt_contains"] in output
    assert EX006_INPUT_EXPECTATIONS[10]["output_contains"] in output
