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


def _print_call_count(tree: ast.AST) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert "Hello World" not in output
    assert "Hello Python!" in output


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
    assert "Hello Python!" in strings


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert "Bassaleg School" in output
    assert "Greenfield" not in output


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
    assert any("Bassaleg School" in s for s in strings)


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
    code = _exercise_code(3)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=3,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )
    assert (
        assertions.assert_uses_operator(
            exercise_no=3,
            operator="*",
            used=constructs.check_uses_operator(code, operator="*"),
        )
        == []
    )


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    words = output.strip().split()
    assert words == ["Good", "Morning", "Everyone"]


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
    assert _print_call_count(tree) == expected_print_call_count(
        4,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )
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
    code = _exercise_code(5)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=5,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )
    assert (
        assertions.assert_uses_operator(
            exercise_no=5,
            operator="/",
            used=constructs.check_uses_operator(code, operator="/"),
        )
        == []
    )


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
    assert output == expected_output_text(
        6,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


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
    assert _print_call_count(tree) == expected_print_call_count(
        6,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert "The result" in output
    assert "100" in output


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
    code = _exercise_code(8)
    assert (
        assertions.assert_has_print_statement(
            exercise_no=8,
            has_print=constructs.check_has_print_statement(code),
        )
        == []
    )
    assert (
        assertions.assert_uses_operator(
            exercise_no=8,
            operator="*",
            used=constructs.check_uses_operator(code, operator="*"),
        )
        == []
    )


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    lines = output.strip().splitlines()
    assert lines[0] == "10 minus 3 equals"
    assert int(lines[1]) == ex002.EX002_EXPECTED_NUMERIC[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    assert output == expected_output_text(
        9,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )


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
    assert _print_call_count(tree) == expected_print_call_count(
        9,
        expectations=ex002.EX002_EXPECTED_PRINT_CALLS,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert "Welcome" in output
    assert "Python programming" in output


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
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Welcome to Python programming!" in strings
