from __future__ import annotations

import ast

import pytest

from tests.notebook_grader import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)

NOTEBOOK_PATH = 'notebooks/ex006_sequence_modify_casting.ipynb'


def _tag(n: int) -> str:
    return f"exercise{n}"


def _run(n: int) -> str:
    return run_cell_and_capture_output(NOTEBOOK_PATH, tag=_tag(n))


def _ast(n: int) -> ast.Module:
    code = extract_tagged_code(NOTEBOOK_PATH, tag=_tag(n))
    return ast.parse(code)


@pytest.mark.task(taskno=1)
def test_exercise1_output_and_construct() -> None:
    output = _run(1)
    assert output == "15\n"
    tree = _ast(1)
    has_int = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'int' for node in ast.walk(tree))
    assert has_int


@pytest.mark.task(taskno=2)
def test_exercise2_output_and_construct() -> None:
    output = _run(2)
    assert output == "6.0\n"
    tree = _ast(2)
    has_float = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'float' for node in ast.walk(tree))
    assert has_float


@pytest.mark.task(taskno=3)
def test_exercise3_output_and_construct() -> None:
    output = _run(3)
    assert output == "28\n"
    tree = _ast(3)
    has_int = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'int' for node in ast.walk(tree))
    assert has_int


@pytest.mark.task(taskno=4)
def test_exercise4_output_and_construct() -> None:
    output = _run(4)
    assert output == "Your score is 500\n"
    tree = _ast(4)
    has_str = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'str' for node in ast.walk(tree))
    assert has_str


@pytest.mark.task(taskno=5)
def test_exercise5_output_and_construct() -> None:
    output = _run(5)
    assert output == "25\n"
    tree = _ast(5)
    has_int = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'int' for node in ast.walk(tree))
    assert has_int


@pytest.mark.task(taskno=6)
def test_exercise6_with_input() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag=_tag(6), inputs=["6"])
    assert "Enter number" in output
    # final line should be 12
    last = output.strip().splitlines()[-1]
    assert last == "12"


@pytest.mark.task(taskno=7)
def test_exercise7_with_input() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag=_tag(7), inputs=["1.5"])
    assert "Enter price" in output
    assert "Two items cost: 3.0" in output


@pytest.mark.task(taskno=8)
def test_exercise8_output_and_construct() -> None:
    output = _run(8)
    assert output == "Area: 50\n"
    tree = _ast(8)
    has_mul = any(isinstance(node, ast.BinOp) and isinstance(
        node.op, ast.Mult) for node in ast.walk(tree))
    assert has_mul


@pytest.mark.task(taskno=9)
def test_exercise9_output_and_construct() -> None:
    output = _run(9)
    assert output == "The Burger costs £5.5\n"
    tree = _ast(9)
    has_str = any(isinstance(node, ast.Call) and isinstance(
        node.func, ast.Name) and node.func.id == 'str' for node in ast.walk(tree))
    assert has_str


@pytest.mark.task(taskno=10)
def test_exercise10_with_input() -> None:
    output = run_cell_with_input(
        NOTEBOOK_PATH, tag=_tag(10), inputs=["10", "20"])
    assert "Enter item 1" in output
    assert "Enter item 2" in output
    assert "Total: 30.0" in output
