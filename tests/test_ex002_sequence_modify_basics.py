from __future__ import annotations

import ast

import pytest

from tests.notebook_grader import extract_tagged_code, run_cell_and_capture_output

NOTEBOOK_PATH = "notebooks/ex002_sequence_modify_basics.ipynb"

EXPECTED_SINGLE_LINE = {
    1: "Hello Python!",
    2: "I go to Bassaleg School",
    3: "15",
    4: "Good Morning Everyone",
    5: "5.0",
    7: "The result is 100",
    8: "24",
    10: "Welcome to Python programming!",
}

EXPECTED_MULTI_LINE = {
    6: ["Learning", "to", "code rocks"],
    9: ["10 minus 3 equals", "7"],
}

EXPECTED_NUMERIC = {
    3: int(EXPECTED_SINGLE_LINE[3]),
    5: float(EXPECTED_SINGLE_LINE[5]),
    8: int(EXPECTED_SINGLE_LINE[8]),
    9: int(EXPECTED_MULTI_LINE[9][1]),
}

EXPECTED_PRINT_CALLS = {
    4: 1,
    6: 3,
    9: 2,
}


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )
    return ast.parse(code)


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert "Hello World" not in output, "Should not print 'Hello World' - change it to 'Hello Python!'"
    assert "Hello Python!" in output, "Should print 'Hello Python!' instead"


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{EXPECTED_SINGLE_LINE[1]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[1]}' with nothing else"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Hello Python!" in strings, "The string 'Hello Python!' should appear in your code"


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert "Bassaleg School" in output, "Should print 'Bassaleg School'"
    assert "Greenfield" not in output, "Should not print 'Greenfield' - change it to 'Bassaleg School'"


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == f"{EXPECTED_SINGLE_LINE[2]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[2]}'"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("Bassaleg School" in s for s in strings), "The text 'Bassaleg School' should appear in your code"


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    value = int(output.strip())
    assert value == EXPECTED_NUMERIC[3], f"Expected {EXPECTED_NUMERIC[3]} (5 * 3), but got {value}"


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == f"{EXPECTED_SINGLE_LINE[3]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[3]}'"


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_multiplication, "Must use multiplication (*) operator, not addition"


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    words = output.strip().split()
    assert words == ["Good", "Morning", "Everyone"], f"Expected 'Good Morning Everyone', but got '{output.strip()}'"


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output(4)
    assert output == f"{EXPECTED_SINGLE_LINE[4]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[4]}'"


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
    assert len(print_calls) == EXPECTED_PRINT_CALLS[4], f"Should use exactly {EXPECTED_PRINT_CALLS[4]} print() call, not {len(print_calls)}"
    # Verify string content includes required words
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("Good" in s for s in strings), "Missing 'Good' in string constants"
    assert any(
        "Morning" in s for s in strings), "Missing 'Morning' in string constants"
    assert any(
        "Everyone" in s for s in strings), "Missing 'Everyone' in string constants"


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(5)
    value = float(output.strip())
    assert value == EXPECTED_NUMERIC[5], f"Expected {EXPECTED_NUMERIC[5]} (10 ÷ 2), but got {value}"


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output(5)
    assert output == f"{EXPECTED_SINGLE_LINE[5]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[5]}'"


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    has_division = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) for node in ast.walk(tree)
    )
    assert has_division, "Must use division (/) operator, not subtraction"


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    lines = output.strip().splitlines()
    assert lines == EXPECTED_MULTI_LINE[6], f"Expected three lines: {EXPECTED_MULTI_LINE[6]}, but got: {lines}"


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output(6)
    expected = "\n".join(EXPECTED_MULTI_LINE[6]) + "\n"
    assert output == expected, "Expected three separate lines printing 'Learning', 'to', and 'code rocks'"


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
    assert len(print_calls) == EXPECTED_PRINT_CALLS[6], f"Must use exactly {EXPECTED_PRINT_CALLS[6]} print() statements (one is already provided)"


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert "The result" in output, "Should print 'The result is 100'"
    assert "100" in output, "Should include '100' in the output"


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output(7)
    assert output == f"{EXPECTED_SINGLE_LINE[7]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[7]}' on one line"


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert any("100" in s for s in strings), "The text '100' should appear as a string in your code (use concatenation)"


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    value = int(output.strip())
    assert value == EXPECTED_NUMERIC[8], f"Expected {EXPECTED_NUMERIC[8]} (2 * 3 * 4), but got {value}"


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    output = _exercise_output(8)
    assert output == f"{EXPECTED_SINGLE_LINE[8]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[8]}'"


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    has_multiplication = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) for node in ast.walk(tree)
    )
    assert has_multiplication, "Must use multiplication (*) operator, not addition"


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    lines = output.strip().splitlines()
    assert lines[0] == "10 minus 3 equals", f"First line should be '10 minus 3 equals', got '{lines[0] if lines else '(empty)'}'"
    assert int(lines[1]) == EXPECTED_NUMERIC[9], f"Second line should be {EXPECTED_NUMERIC[9]} (the result of 10-3)"


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    expected = "\n".join(EXPECTED_MULTI_LINE[9]) + "\n"
    assert output == expected, "Should print two separate lines: '10 minus 3 equals' and '7'"


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
    assert has_subtraction, "Must perform the calculation 10 - 3 inside print()"
    assert len(print_calls) == EXPECTED_PRINT_CALLS[9], f"Should use exactly {EXPECTED_PRINT_CALLS[9]} print() statements"


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert "Welcome" in output, "Should include 'Welcome' in the message"
    assert "Python programming" in output, "Should include 'Python programming' in the message"


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    output = _exercise_output(10)
    assert output == f"{EXPECTED_SINGLE_LINE[10]}\n", f"Expected exactly '{EXPECTED_SINGLE_LINE[10]}'"


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Welcome to Python programming!" in strings, "Should build the complete message using string concatenation (+)"
