"""Exercise-local expectations for ex015_sequence_make_consolidation_v2."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex015InputCase(TypedDict):
    """Expected transcript for an interactive exercise case."""

    inputs: list[str]
    expected_output: str


# Exercises 1 and 2 use fixed values (no input) — static output only.
# Exercises 3–10 use input() — they only appear in EX015_INPUT_CASES.
EX015_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "You can make 7 full bags with 1 sweets left over.",
    2: (
        "Wall area: 15 square metres\n"
        "You need 2 cans; 9 square metres of paint will be unused."
    ),
    3: "",
    4: "",
    5: "",
    6: "",
    7: "",
    8: "",
    9: "",
    10: "",
}

EX015_INPUT_CASES: Final[dict[int, Ex015InputCase]] = {
    3: {
        "inputs": ["4"],
        "expected_output": (
            "How old are you in human years?\n"
            "If you were a dog, you would be 28 years old."
        ),
    },
    4: {
        "inputs": ["3", "5"],
        "expected_output": (
            "Number of pizzas:\n"
            "Number of people:\n"
            "If you ordered 3 pizzas for 5 people:\n"
            "Each person gets 4 slices, with 4 slices left over."
        ),
    },
    5: {
        "inputs": ["50", "1.45"],
        "expected_output": (
            "Litres of fuel:\n"
            "Price per litre in pounds:\n"
            "50.0 litres at \u00a31.45 per litre costs \u00a372.5."
        ),
    },
    6: {
        "inputs": ["25"],
        "expected_output": (
            "Enter temperature in \u00b0C:\n"
            "25\u00b0C is 77.0\u00b0F"
        ),
    },
    7: {
        "inputs": ["350", "50"],
        "expected_output": (
            "What is your savings goal in pounds?\n"
            "How much can you save each week in pounds?\n"
            "Saving \u00a350 per week towards a \u00a3350 goal:\n"
            "It will take 7 full weeks, with \u00a30 left to save."
        ),
    },
    8: {
        "inputs": ["5"],
        "expected_output": (
            "Side length of the square garden in metres:\n"
            "A square garden with side 5m has area 25 square metres.\n"
            "A garden with double the area would have side 7.07m."
        ),
    },
    9: {
        "inputs": ["50", "10", "4"],
        "expected_output": (
            "Total bill amount in \u00a3:\n"
            "Tip percentage (e.g. 10 for 10%):\n"
            "Number of people sharing:\n"
            "Total bill: \u00a350.0\n"
            "Tip (10%): \u00a35.0\n"
            "Total with tip: \u00a355.0\n"
            "Each of 4 people pays: \u00a313.75"
        ),
    },
    10: {
        "inputs": ["30", "3", "2"],
        "expected_output": (
            "Number of students:\n"
            "Pencils needed per student:\n"
            "Erasers needed per student:\n"
            "For 30 students:\n"
            "Each student needs 3 pencils and 2 erasers.\n"
            "Order 4 packs of pencils (24 per pack) \u2014 6 pencils will be left over.\n"
            "Order 4 packs of erasers (15 per pack) \u2014 0 erasers will be left over."
        ),
    },
}
