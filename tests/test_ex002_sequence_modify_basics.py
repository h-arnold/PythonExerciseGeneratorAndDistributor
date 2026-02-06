from __future__ import annotations

import ast

import pytest

from tests.exercise_expectations.ex002_sequence_modify_basics_exercise_expectations import (
    EX002_EXPECTED_MULTI_LINE,
    EX002_EXPECTED_NUMERIC,
    EX002_EXPECTED_PRINT_CALLS,
    EX002_EXPECTED_SINGLE_LINE,
    EX002_NOTEBOOK_PATH,
)
from tests.notebook_grader import extract_tagged_code, run_cell_and_capture_output


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        EX002_NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        EX002_NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )
    return ast.parse(code)


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert "Hello World" not in output
    assert "Hello Python!" in output


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[1]}\n"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Hello Python!" in strings


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert "Bassaleg School" in output
    assert "Greenfield" not in output


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[2]}\n"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("Bassaleg School" in s for s in strings)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    value = int(output.strip())
    assert value == EX002_EXPECTED_NUMERIC[3]


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[3]}\n"


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_multiplication


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    words = output.strip().split()
    assert words == ["Good", "Morning", "Everyone"]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output(4)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[4]}\n"


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert len(print_calls) == EX002_EXPECTED_PRINT_CALLS[4]
    # Verify string content includes required words
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("Good" in s for s in strings), "Missing 'Good' in string constants"
    assert any("Morning" in s for s in strings), "Missing 'Morning' in string constants"
    assert any("Everyone" in s for s in strings), "Missing 'Everyone' in string constants"


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(5)
    value = float(output.strip())
    assert value == EX002_EXPECTED_NUMERIC[5]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output(5)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[5]}\n"


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    has_division = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) for node in ast.walk(tree)
    )
    assert has_division


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    lines = output.strip().splitlines()
    assert lines == EX002_EXPECTED_MULTI_LINE[6]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output(6)
    expected = "\n".join(EX002_EXPECTED_MULTI_LINE[6]) + "\n"
    assert output == expected


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert len(print_calls) == EX002_EXPECTED_PRINT_CALLS[6]


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert "The result" in output
    assert "100" in output


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output(7)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[7]}\n"


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("100" in s for s in strings)


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    value = int(output.strip())
    assert value == EX002_EXPECTED_NUMERIC[8]


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    output = _exercise_output(8)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[8]}\n"


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_multiplication


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    lines = output.strip().splitlines()
    assert lines[0] == "10 minus 3 equals"
    assert int(lines[1]) == EX002_EXPECTED_NUMERIC[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    expected = "\n".join(EX002_EXPECTED_MULTI_LINE[9]) + "\n"
    assert output == expected


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    has_subtraction = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub) for node in ast.walk(tree)
    )
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert has_subtraction
    assert len(print_calls) == EX002_EXPECTED_PRINT_CALLS[9]


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert "Welcome" in output
    assert "Python programming" in output


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    output = _exercise_output(10)
    assert output == f"{EX002_EXPECTED_SINGLE_LINE[10]}\n"


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Welcome to Python programming!" in strings
