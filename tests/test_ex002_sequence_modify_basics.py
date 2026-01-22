from __future__ import annotations

import math

import pytest

from tests.notebook_grader import run_cell_and_capture_output

# Named constants to avoid magic numbers flagged by linters
EXPECTED_15 = 15
NOT_ADDITION_5_3 = 8
EXPECTED_WORDS = 3
EXPECTED_LINES = 3
LAST_LINE_WORDS = 2
DIV_EXPECTED = 5.0
MULT_EXPECTED_24 = 24
NOT_ADDITION_2_3_4 = 9
EXPECTED_RESULT_7 = 7
MIN_SPACES = 3

NOTEBOOK_PATH = "notebooks/ex002_sequence_modify_basics.ipynb"


def _run_and_capture(tag: str) -> str:
    """Execute the tagged cell and capture its print output."""
    return run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)


# Exercise 1: Change greeting from "Hello World!" to "Hello Python!"
@pytest.mark.task(taskno=1)
def test_exercise1_prints_hello_python():
    output = _run_and_capture("exercise1")
    assert output.strip() == "Hello Python!", f"Expected 'Hello Python!' but got {output.strip()!r}"


@pytest.mark.task(taskno=1)
def test_exercise1_single_line():
    output = _run_and_capture("exercise1")
    lines = output.strip().split("\n")
    assert len(lines) == 1, "Should print exactly one line"


@pytest.mark.task(taskno=1)
def test_exercise1_exact_match():
    output = _run_and_capture("exercise1")
    assert "Hello Python!" in output, "Output must contain 'Hello Python!'"


# Exercise 2: Change school name to "Bassaleg School"
@pytest.mark.task(taskno=2)
def test_exercise2_prints_bassaleg():
    output = _run_and_capture("exercise2")
    assert output.strip() == "I go to Bassaleg School", (
        f"Expected 'I go to Bassaleg School' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=2)
def test_exercise2_contains_school():
    output = _run_and_capture("exercise2")
    assert "Bassaleg School" in output, "Output must mention 'Bassaleg School'"


@pytest.mark.task(taskno=2)
def test_exercise2_single_line():
    output = _run_and_capture("exercise2")
    lines = output.strip().split("\n")
    assert len(lines) == 1, "Should print exactly one line"


# Exercise 3: Change addition to multiplication (5 * 3 = 15)
@pytest.mark.task(taskno=3)
def test_exercise3_prints_15():
    output = _run_and_capture("exercise3")
    assert output.strip() == str(EXPECTED_15), (
        f"Expected '{EXPECTED_15}' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=3)
def test_exercise3_is_multiplication():
    output = _run_and_capture("exercise3")
    value = int(output.strip())
    assert value == EXPECTED_15, "5 * 3 should equal 15"


@pytest.mark.task(taskno=3)
def test_exercise3_not_addition():
    output = _run_and_capture("exercise3")
    value = int(output.strip())
    assert value != NOT_ADDITION_5_3, "Should not be addition (5 + 3 = 8)"


# Exercise 4: Concatenate "Good Morning Everyone"
@pytest.mark.task(taskno=4)
def test_exercise4_prints_good_morning():
    output = _run_and_capture("exercise4")
    assert output.strip() == "Good Morning Everyone", (
        f"Expected 'Good Morning Everyone' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=4)
def test_exercise4_has_spaces():
    output = _run_and_capture("exercise4")
    assert " " in output, "Words should be separated by spaces"


@pytest.mark.task(taskno=4)
def test_exercise4_three_words():
    output = _run_and_capture("exercise4")
    words = output.strip().split()
    assert len(words) == EXPECTED_WORDS, "Should contain exactly 3 words"


# Exercise 5: Division 10 / 2 = 5.0
@pytest.mark.task(taskno=5)
def test_exercise5_prints_5_point_0():
    output = _run_and_capture("exercise5")
    assert output.strip() == "5.0", f"Expected '5.0' but got {output.strip()!r}"


@pytest.mark.task(taskno=5)
def test_exercise5_is_division():
    output = _run_and_capture("exercise5")
    value = float(output.strip())
    assert math.isclose(value, 5.0), "10 / 2 should equal 5.0"


@pytest.mark.task(taskno=5)
def test_exercise5_is_float():
    output = _run_and_capture("exercise5")
    assert ".0" in output or "." in output, "Division should produce a float (decimal number)"


# Exercise 6: Three print statements - "Learning", "to", "code rocks"
@pytest.mark.task(taskno=6)
def test_exercise6_three_lines():
    output = _run_and_capture("exercise6")
    lines = [line for line in output.strip().split("\n") if line]
    assert len(lines) == EXPECTED_LINES, f"Expected {EXPECTED_LINES} lines but got {len(lines)}"


@pytest.mark.task(taskno=6)
def test_exercise6_correct_content():
    output = _run_and_capture("exercise6")
    lines = [line.strip() for line in output.strip().split("\n") if line]
    assert lines[0] == "Learning", f"First line should be 'Learning' but got {lines[0]!r}"
    assert lines[1] == "to", f"Second line should be 'to' but got {lines[1]!r}"
    assert lines[2] == "code rocks", f"Third line should be 'code rocks' but got {lines[2]!r}"


@pytest.mark.task(taskno=6)
def test_exercise6_last_line_two_words():
    output = _run_and_capture("exercise6")
    lines = [line.strip() for line in output.strip().split("\n") if line]
    last_words = lines[2].split()
    assert len(last_words) == LAST_LINE_WORDS, "Last line should contain two words"


# Exercise 7: Concatenation "The result is 100"
@pytest.mark.task(taskno=7)
def test_exercise7_prints_result_100():
    output = _run_and_capture("exercise7")
    assert output.strip() == "The result is 100", (
        f"Expected 'The result is 100' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=7)
def test_exercise7_contains_100():
    output = _run_and_capture("exercise7")
    assert "100" in output, "Output must contain '100'"


@pytest.mark.task(taskno=7)
def test_exercise7_contains_result():
    output = _run_and_capture("exercise7")
    assert "result" in output.lower(), "Output should mention 'result'"


# Exercise 8: Multiplication 2 * 3 * 4 = 24
@pytest.mark.task(taskno=8)
def test_exercise8_prints_24():
    output = _run_and_capture("exercise8")
    assert output.strip() == str(MULT_EXPECTED_24), (
        f"Expected '{MULT_EXPECTED_24}' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=8)
def test_exercise8_is_multiplication():
    output = _run_and_capture("exercise8")
    value = int(output.strip())
    assert value == MULT_EXPECTED_24, "2 * 3 * 4 should equal 24"


@pytest.mark.task(taskno=8)
def test_exercise8_not_addition():
    output = _run_and_capture("exercise8")
    value = int(output.strip())
    assert value != NOT_ADDITION_2_3_4, "Should not be addition (2 + 3 + 4 = 9)"


# Exercise 9: Two lines - "10 minus 3 equals" and "7"
@pytest.mark.task(taskno=9)
def test_exercise9_two_lines():
    output = _run_and_capture("exercise9")
    lines = [line for line in output.strip().split("\n") if line]
    EXPECTED_TWO_LINES = 2
    assert len(lines) == EXPECTED_TWO_LINES, (
        f"Expected {EXPECTED_TWO_LINES} lines but got {len(lines)}"
    )


@pytest.mark.task(taskno=9)
def test_exercise9_correct_content():
    output = _run_and_capture("exercise9")
    lines = [line.strip() for line in output.strip().split("\n") if line]
    assert lines[0] == "10 minus 3 equals", (
        f"First line should be '10 minus 3 equals' but got {lines[0]!r}"
    )
    assert lines[1] == "7", f"Second line should be '7' but got {lines[1]!r}"


@pytest.mark.task(taskno=9)
def test_exercise9_calculation_correct():
    output = _run_and_capture("exercise9")
    lines = [line.strip() for line in output.strip().split("\n") if line]
    result = int(lines[1])
    assert result == EXPECTED_RESULT_7, "10 - 3 should equal 7"


# Exercise 10: Concatenation "Welcome to Python programming!"
@pytest.mark.task(taskno=10)
def test_exercise10_prints_welcome():
    output = _run_and_capture("exercise10")
    assert output.strip() == "Welcome to Python programming!", (
        f"Expected 'Welcome to Python programming!' but got {output.strip()!r}"
    )


@pytest.mark.task(taskno=10)
def test_exercise10_has_spaces():
    output = _run_and_capture("exercise10")
    assert output.count(" ") >= MIN_SPACES, "Should have multiple spaces between words"


@pytest.mark.task(taskno=10)
def test_exercise10_ends_with_exclamation():
    output = _run_and_capture("exercise10")
    assert output.strip().endswith("!"), "Should end with an exclamation mark"


# Smoke test: all cells execute without errors
@pytest.mark.parametrize(
    "tag",
    [
        "exercise1",
        "exercise2",
        "exercise3",
        "exercise4",
        "exercise5",
        "exercise6",
        "exercise7",
        "exercise8",
        "exercise9",
        "exercise10",
    ],
)
@pytest.mark.task(taskno=0)
def test_exercise_cells_execute(tag: str) -> None:
    """Verify each tagged cell executes without error."""
    output = _run_and_capture(tag)
    assert output is not None, f"{tag} should produce output"
