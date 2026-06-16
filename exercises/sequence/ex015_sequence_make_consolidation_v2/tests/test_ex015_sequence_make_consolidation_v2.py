"""Tests for ex015_sequence_make_consolidation_v2 — Sequence Make Consolidation.

Exercise types:
  - Exercises 1-2: Static output (no input)
  - Exercises 3-10: Interactive output (use input())

Run with::
  uv run pytest -q exercises/sequence/ex015_sequence_make_consolidation_v2/tests/
  uv run python scripts/run_pytest_variant.py --variant solution \\
      exercises/sequence/ex015_sequence_make_consolidation_v2/tests/ -q
"""
from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex015_sequence_make_consolidation_v2"
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()

# Load canonical expectations
_ex015_expectations = load_exercise_test_module(_EXERCISE_KEY, "expectations")
EX015_EXPECTED_OUTPUTS: dict[int, str] = (
    _ex015_expectations.EX015_EXPECTED_OUTPUTS  # type: ignore[attr-defined]
)
EX015_INPUT_CASES: dict[int, dict[str, object]] = (
    _ex015_expectations.EX015_INPUT_CASES  # type: ignore[attr-defined]
)


# ---------------------------------------------------------------------------
# Static-output exercises (1-2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("tag", "exercise_no"),
    [
        ("exercise1", 1),
        ("exercise2", 2),
    ],
)
def test_static_output(tag: str, exercise_no: int) -> None:
    """Verify static-output exercises produce the exact expected text."""
    expected = EX015_EXPECTED_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)
    assert output == expected, (
        f"Exercise {exercise_no}: expected {expected!r}, got {output!r}"
    )


# ---------------------------------------------------------------------------
# Interactive exercise primary cases (from expectations.py)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("tag", "exercise_no"),
    [
        ("exercise3", 3),
        ("exercise4", 4),
        ("exercise5", 5),
        ("exercise6", 6),
        ("exercise7", 7),
        ("exercise8", 8),
        ("exercise9", 9),
        ("exercise10", 10),
    ],
)
def test_interactive_output(tag: str, exercise_no: int) -> None:
    """Verify interactive exercises produce the exact expected transcript."""
    case = EX015_INPUT_CASES[exercise_no]
    inputs = list(case["inputs"])  # type: ignore[arg-type]
    expected = str(case["expected_output"])
    output = run_cell_with_input(
        _NOTEBOOK_PATH, tag=tag, cache=_CACHE, inputs=inputs
    )
    assert output == expected, (
        f"Exercise {exercise_no} with inputs={inputs}: "
        f"expected {expected!r}, got {output!r}"
    )


# ---------------------------------------------------------------------------
# Edge-case test sets for interactive exercises (additional input combinations)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("tag", "inputs", "expected"),
    [
        # Exercise 3: age = 0 -> dog years = 0
        ("exercise3", ["0"], (
            "How old are you in human years?\n"
            "If you were a dog, you would be 0 years old."
        )),
        # Exercise 3: age = 12 -> dog years = 84
        ("exercise3", ["12"], (
            "How old are you in human years?\n"
            "If you were a dog, you would be 84 years old."
        )),
        # Exercise 4: even sharing (2 pizzas, 8 people)
        ("exercise4", ["2", "8"], (
            "Number of pizzas:\n"
            "Number of people:\n"
            "If you ordered 2 pizzas for 8 people:\n"
            "Each person gets 2 slices, with 0 slices left over."
        )),
        # Exercise 4: 1 pizza for 1 person
        ("exercise4", ["1", "1"], (
            "Number of pizzas:\n"
            "Number of people:\n"
            "If you ordered 1 pizzas for 1 people:\n"
            "Each person gets 8 slices, with 0 slices left over."
        )),
        # Exercise 5: 0 litres
        ("exercise5", ["0", "1.45"], (
            "Litres of fuel:\n"
            "Price per litre in pounds:\n"
            "0.0 litres at \u00a31.45 per litre costs \u00a30.00."
        )),
        # Exercise 6: 0\u00b0C -> 32.0\u00b0F
        ("exercise6", ["0"], (
            "Enter temperature in \u00b0C:\n"
            "0\u00b0C is 32.0\u00b0F"
        )),
        # Exercise 6: -10\u00b0C -> 14.0\u00b0F
        ("exercise6", ["-10"], (
            "Enter temperature in \u00b0C:\n"
            "-10\u00b0C is 14.0\u00b0F"
        )),
        # Exercise 7: goal=100, weekly=30 -> 3 weeks, 10 left
        ("exercise7", ["100", "30"], (
            "What is your savings goal in pounds?\n"
            "How much can you save each week in pounds?\n"
            "Saving \u00a330 per week towards a \u00a3100 goal:\n"
            "It will take 3 full weeks, with \u00a310 left to save."
        )),
        # Exercise 7: goal=200, weekly=40 -> 5 weeks, 0 left
        ("exercise7", ["200", "40"], (
            "What is your savings goal in pounds?\n"
            "How much can you save each week in pounds?\n"
            "Saving \u00a340 per week towards a \u00a3200 goal:\n"
            "It will take 5 full weeks, with \u00a30 left to save."
        )),
        # Exercise 8: side=10 -> area=100, double side \u2248 14.14
        ("exercise8", ["10"], (
            "Side length of the square garden in metres:\n"
            "A square garden with side 10m has area 100 square metres.\n"
            "A garden with double the area would have side 14.14m."
        )),
        # Exercise 8: side=1 -> area=1, double side \u2248 1.41
        ("exercise8", ["1"], (
            "Side length of the square garden in metres:\n"
            "A square garden with side 1m has area 1 square metres.\n"
            "A garden with double the area would have side 1.41m."
        )),
        # Exercise 9: \u00a320, 15%, 2 people
        ("exercise9", ["20", "15", "2"], (
            "Total bill amount in \u00a3:\n"
            "Tip percentage (e.g. 10 for 10%):\n"
            "Number of people sharing:\n"
            "Total bill: \u00a320.00\n"
            "Tip (15%): \u00a33.00\n"
            "Total with tip: \u00a323.00\n"
            "Each of 2 people pays: \u00a311.5"
        )),
        # Exercise 9: \u00a3100, 0%, 1 person
        ("exercise9", ["100", "0", "1"], (
            "Total bill amount in \u00a3:\n"
            "Tip percentage (e.g. 10 for 10%):\n"
            "Number of people sharing:\n"
            "Total bill: \u00a3100.00\n"
            "Tip (0%): \u00a30.00\n"
            "Total with tip: \u00a3100.00\n"
            "Each of 1 people pays: \u00a3100.0"
        )),
        # Exercise 10: 15 students, 2 pencils, 1 eraser
        ("exercise10", ["15", "2", "1"], (
            "Number of students:\n"
            "Pencils needed per student:\n"
            "Erasers needed per student:\n"
            "For 15 students:\n"
            "Each student needs 2 pencils and 1 erasers.\n"
            "Order 2 packs of pencils (24 per pack) \u2014 18 pencils will be left over.\n"
            "Order 1 packs of erasers (15 per pack) \u2014 0 erasers will be left over."
        )),
        # Exercise 10: 1 student, 1 pencil, 1 eraser
        ("exercise10", ["1", "1", "1"], (
            "Number of students:\n"
            "Pencils needed per student:\n"
            "Erasers needed per student:\n"
            "For 1 students:\n"
            "Each student needs 1 pencils and 1 erasers.\n"
            "Order 1 packs of pencils (24 per pack) \u2014 23 pencils will be left over.\n"
            "Order 1 packs of erasers (15 per pack) \u2014 14 erasers will be left over."
        )),
    ],
)
def test_interactive_edge_cases(tag: str, inputs: list[str], expected: str) -> None:
    """Verify interactive exercises with additional edge-case inputs."""
    output = run_cell_with_input(
        _NOTEBOOK_PATH, tag=tag, cache=_CACHE, inputs=inputs
    )
    assert output == expected, (
        f"{tag} with inputs={inputs}: expected {expected!r}, got {output!r}"
    )
