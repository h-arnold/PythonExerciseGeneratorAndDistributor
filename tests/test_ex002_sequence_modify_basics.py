from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.exercise_expectations import (
    ex002_sequence_modify_basics_exercise_expectations as ex002,
)
from tests.exercise_framework import (
    assertions,
    constructs,
    expected_output_lines,
    expected_output_text,
    expected_print_call_count,
    extract_tagged_code,
    resolve_notebook_path,
    run_cell_and_capture_output,
)
from tests.exercise_framework.expectations import EX002_NOTEBOOK_PATH


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _resolved_notebook_path() -> Path:
    return resolve_notebook_path(EX002_NOTEBOOK_PATH)


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _resolved_notebook_path(),
        tag=_exercise_tag(exercise_no),
    )


def _exercise_code(exercise_no: int) -> str:
    return extract_tagged_code(
        _resolved_notebook_path(),
        tag=_exercise_tag(exercise_no),
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    return ast.parse(_exercise_code(exercise_no))


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert "Hello World" not in output, "Old greeting 'Hello World' should be replaced"
    assert "Hello Python!" in output, "Should print 'Hello Python!' instead"


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == expected_output_text(
        1,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    code = _exercise_code(1)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=1,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(1)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Hello Python!" in strings, "The string 'Hello Python!' should appear in your code"
    assert "Hello World!" not in strings, "Old string 'Hello World!' should be replaced"


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert "Bassaleg School" in output, "Should print 'Bassaleg School'"
    assert "Greenfield" not in output, "Should not print 'Greenfield' - change it to 'Bassaleg School'"


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == expected_output_text(
        2,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    code = _exercise_code(2)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=2,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(2)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any(
        "Bassaleg School" in s for s in strings), "The text 'Bassaleg School' should appear in your code"
    assert not any(
        "Greenfield" in s for s in strings), "Old value 'Greenfield' should be replaced"


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    value = int(output.strip())
    assert value == ex002.EX002_EXPECTED_NUMERIC[3]


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == expected_output_text(
        3,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    has_addition = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) for node in ast.walk(tree)
    )
    assert has_multiplication, "Must use multiplication (*) operator"
    assert not has_addition, "Should replace addition (+) with multiplication"


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    words = output.strip().split()
    assert words == ["Good", "Morning",
                     "Everyone"], f"Expected 'Good Morning Everyone', but got '{output.strip()}'"


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output(4)
    assert output == expected_output_text(
        4,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    code = _exercise_code(4)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=4,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(4)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert len(print_calls) == expected_print_call_count(
        4,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )
    # Verify exact string content
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Good Morning Everyone" in strings, "Should build the message 'Good Morning Everyone'"
    assert not any(
        "Hello" in s for s in strings), "Old value 'Hello' should be removed"
    assert not any(
        "World" in s for s in strings), "Old value 'World' should be removed"


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(5)
    value = float(output.strip())
    assert value == ex002.EX002_EXPECTED_NUMERIC[5]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output(5)
    assert output == expected_output_text(
        5,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    has_division = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) for node in ast.walk(tree)
    )
    has_subtraction = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub) for node in ast.walk(tree)
    )
    assert has_division, "Must use division (/) operator"
    assert not has_subtraction, "Should replace subtraction (-) with division"


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    lines = output.strip().splitlines()
    assert lines == expected_output_lines(
        6,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output(6)
    expected = expected_output_text(
        6,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )
    assert output == expected


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    code = _exercise_code(6)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=6,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(6)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert len(print_calls) == expected_print_call_count(
        6,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert "The result" in output, "Should print 'The result is 100'"
    assert "100" in output, "Should include '100' in the output"


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output(7)
    assert output == expected_output_text(
        7,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    code = _exercise_code(7)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=7,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(7)
    # Check for concatenation operation
    has_concat = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
        for node in ast.walk(tree)
    )
    assert has_concat, "Should use string concatenation (+) to build the message"

    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any(
        "100" in s for s in strings), "The number 100 should appear as a string"
    assert any("result" in s.lower()
               for s in strings), "The word 'result' should appear in a string"


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    value = int(output.strip())
    assert value == ex002.EX002_EXPECTED_NUMERIC[8]


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    output = _exercise_output(8)
    assert output == expected_output_text(
        8,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    has_addition = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) for node in ast.walk(tree)
    )
    assert has_multiplication, "Must use multiplication (*) operator"
    assert not has_addition, "Should replace addition (+) with multiplication"


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    lines = output.strip().splitlines()
    assert lines[0] == "10 minus 3 equals"
    assert int(lines[1]) == ex002.EX002_EXPECTED_NUMERIC[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    expected = expected_output_text(
        9,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )
    assert output == expected


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    code = _exercise_code(9)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=9,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )
    assert (
        assertions.assert_uses_operator(
            exercise_no=9,
            operator="-",
            used=constructs.check_uses_operator(code, operator="-"),
        )
        == []
    )

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
    assert len(print_calls) == expected_print_call_count(
        9,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert "Welcome" in output, "Should include 'Welcome' in the message"
    assert "Python programming" in output, "Should include 'Python programming' in the message"


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    output = _exercise_output(10)
    assert output == expected_output_text(
        10,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    code = _exercise_code(10)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=10,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )

    tree = _exercise_ast(10)
    # Check for concatenation operation
    has_concat = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
        for node in ast.walk(tree)
    )
    assert has_concat, "Should use string concatenation (+) to join the message parts"

    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any(
        "Welcome" in s for s in strings), "Should include 'Welcome' in string constants"
    assert any(
        "Python programming" in s for s in strings), "Should include 'Python programming' in string constants"
