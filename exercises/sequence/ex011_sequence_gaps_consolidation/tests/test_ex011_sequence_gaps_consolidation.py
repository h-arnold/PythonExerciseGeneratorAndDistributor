from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)

EXERCISE_KEY = "ex011_sequence_gaps_consolidation"
NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
CACHE = RuntimeCache()

NO_INPUT_CASES = [
    ("exercise1", "Sequence is fun"),
    ("exercise2", "Hello Amina"),
    ("exercise4", "The total is 10"),
    ("exercise5", "Total cost: 7.5"),
    ("exercise6", "Average distance: 3.5 km"),
    ("exercise7", "Aisha enjoys drawing after school."),
]

INPUT_CASES = [
    (
        "exercise3",
        ["word with space"],
        "What is your favourite word?\nYou chose word with space",
    ),
    (
        "exercise8",
        ["Aisha", "St Asaph"],
        "Enter your first name:\nEnter your town:\nHello Aisha from St Asaph.",
    ),
    (
        "exercise9",
        ["blue", "fox"],
        "Enter your favourite colour:\nEnter your favourite animal:\nMy favourite colour is blue and my favourite animal is fox.",
    ),
    (
        "exercise10",
        ["Amina"],
        "Enter your name:\nWelcome to Sequence Supplies, Amina. Your total is £14.0.",
    ),
]


@pytest.mark.parametrize(("tag", "expected"), NO_INPUT_CASES)
def test_no_input_cells(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag, cache=CACHE)
    assert output.strip() == expected


@pytest.mark.parametrize(("tag", "inputs", "expected"), INPUT_CASES)
def test_input_cells(tag: str, inputs: list[str], expected: str) -> None:
    output = run_cell_with_input(
        NOTEBOOK_PATH, tag=tag, inputs=inputs, cache=CACHE)
    assert output.strip() == expected


def test_exercise7_uses_an_f_string() -> None:
    code = extract_tagged_code(NOTEBOOK_PATH, tag="exercise7", cache=CACHE)
    tree = ast.parse(code)
    has_f_string = any(isinstance(node, ast.JoinedStr)
                       for node in ast.walk(tree))
    assert has_f_string, "exercise7 must use an f-string"
