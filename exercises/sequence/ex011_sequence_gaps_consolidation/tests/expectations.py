"""Exercise-local expectations for ex011_sequence_gaps_consolidation."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex011InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


# Exercises 1, 2, 4, 5, 6, and 7 print fixed text without reading input.
EX011_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Sequence is fun",
    2: "Hello Amina",
    4: "The total is 10",
    5: "Total cost: 7.5",
    6: "Average distance: 3.5 km",
    7: "Aisha enjoys drawing after school.",
}

# Exercises 3, 8, 9, and 10 call input(); each expected_output is the full
# transcript, so the prompt text is part of the expectation.
EX011_INPUT_CASES: Final[dict[int, Ex011InputCase]] = {
    3: {
        "inputs": ["word with space"],
        "expected_output": "What is your favourite word?\nYou chose word with space",
    },
    8: {
        "inputs": ["Aisha", "St Asaph"],
        "expected_output": (
            "Enter your first name:\nEnter your town:\nHello Aisha from St Asaph."
        ),
    },
    9: {
        "inputs": ["blue", "fox"],
        "expected_output": (
            "Enter your favourite colour:\nEnter your favourite animal:\n"
            "My favourite colour is blue and my favourite animal is fox."
        ),
    },
    10: {
        "inputs": ["Amina"],
        "expected_output": (
            "Enter your name:\nWelcome to Sequence Supplies, Amina. Your total is £14.0."
        ),
    },
}
