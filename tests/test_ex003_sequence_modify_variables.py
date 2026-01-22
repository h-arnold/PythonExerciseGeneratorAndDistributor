from __future__ import annotations

import pytest

from tests.helpers import run_tagged_cell_output

NOTEBOOK_PATH = "notebooks/ex003_sequence_modify_variables.ipynb"


def _run_and_capture(tag: str, *, inputs: list[str] | None = None) -> str:
    """Execute the tagged cell while capturing stdout and optional inputs."""
    return run_tagged_cell_output(NOTEBOOK_PATH, tag=tag, inputs=inputs)


def test_exercise1_prints_hi_there() -> None:
    output = _run_and_capture("exercise1")
    assert output.strip() == "Hi there!", f"Unexpected output: {output!r}"


def test_exercise2_prints_coding_message() -> None:
    output = _run_and_capture("exercise2")
    assert output.strip(
    ) == "I enjoy coding lessons.", f"Unexpected output: {output!r}"


def test_exercise3_prints_favourite_food() -> None:
    output = _run_and_capture("exercise3")
    assert output.strip(
    ) == "My favourite food is sushi", f"Unexpected output: {output!r}"


def test_exercise4_prompt_and_fruit_message() -> None:
    output = _run_and_capture("exercise4", inputs=["mango"])
    lines = output.strip().splitlines()
    assert lines == [
        "Type the name of your favourite fruit:",
        "I like mango",
    ], f"Unexpected lines: {lines!r}"


def test_exercise5_prompt_and_town_message() -> None:
    output = _run_and_capture("exercise5", inputs=["Cardiff"])
    lines = output.strip().splitlines()
    assert lines == [
        "Which town do you like the most?",
        "I would visit Cardiff",
    ], f"Unexpected lines: {lines!r}"


def test_exercise6_prompt_and_name_message() -> None:
    output = _run_and_capture("exercise6", inputs=["Alex"])
    lines = output.strip().splitlines()
    assert lines == [
        "Please enter your name:",
        "Welcome, Alex!",
    ], f"Unexpected lines: {lines!r}"


def test_exercise7_prints_variables_matter() -> None:
    output = _run_and_capture("exercise7")
    assert output.strip(
    ) == "Variables matter", f"Unexpected output: {output!r}"


def test_exercise8_prints_keep_experimenting() -> None:
    output = _run_and_capture("exercise8")
    assert output.strip(
    ) == "Keep experimenting", f"Unexpected output: {output!r}"


def test_exercise9_prints_good_evening_message() -> None:
    output = _run_and_capture("exercise9")
    assert output.strip(
    ) == "Good evening everyone!", f"Unexpected output: {output!r}"


def test_exercise10_prints_combined_message() -> None:
    output = _run_and_capture("exercise10")
    assert output.strip() == "Variables and strings make a message!", (
        f"Unexpected output: {output!r}"
    )


# Additional tests to increase coverage: positive cases, edge cases and invalid-input reasoning


@pytest.mark.parametrize("fruit", ["mango", "banana", "kiwi"])
def test_exercise4_various_fruits(fruit: str) -> None:
    """Positive cases: typical fruit names are echoed correctly."""
    output = _run_and_capture("exercise4", inputs=[fruit])
    lines = output.strip().splitlines()
    assert lines == [
        "Type the name of your favourite fruit:",
        f"I like {fruit}",
    ], f"Unexpected lines for {fruit!r}: {lines!r}"


def test_exercise4_empty_input() -> None:
    """Edge case: empty input should still produce the prompt and the message with empty value."""
    output = _run_and_capture("exercise4", inputs=[""])
    lines = output.splitlines()
    # Do not strip here; we expect the second line to include the trailing space after the phrase
    assert lines == [
        "Type the name of your favourite fruit:",
        "I like ",
    ], f"Unexpected lines for empty input: {lines!r}"


def test_exercise4_whitespace_input() -> None:
    """Edge case: whitespace-only input is preserved in the concatenation."""
    output = _run_and_capture("exercise4", inputs=["   "])
    lines = output.splitlines()
    assert lines == [
        "Type the name of your favourite fruit:",
        "I like    ",
    ], f"Unexpected lines for whitespace input: {lines!r}"


def test_exercise6_long_name() -> None:
    """Invalid/robustness case: very long input should be handled (no crash) and echoed correctly."""
    long_name = "A" * 5000
    output = _run_and_capture("exercise6", inputs=[long_name])
    lines = output.strip().splitlines()
    assert lines[0] == "Please enter your name:", "Missing prompt"
    assert lines[1] == f"Welcome, {long_name}!"


def test_input_non_string_not_applicable() -> None:
    """Explains why non-string inputs are not applicable: input() returns str; test with numeric-like string instead."""
    output = _run_and_capture("exercise6", inputs=["12345"])
    lines = output.strip().splitlines()
    assert lines == ["Please enter your name:", "Welcome, 12345!"], (
        f"Unexpected behaviour for numeric-like input: {lines!r}"
    )
