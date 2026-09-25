"""Canonical expectations for ex009 sequence modify f-strings."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex009InputCase(TypedDict):
    """One deterministic input/output transcript for an interactive task."""

    inputs: list[str]
    expected_output: str


# Exercises 1-4, 7, and 8 do not call input().
EX009_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome, Sam!",
    2: "My pet is a rabbit!",
    3: "Mia enjoys drawing after school.",
    4: "Our best lesson is computing.",
    7: "You scored 4 goals today.",
    8: "Tickets sold altogether: 7",
}

# Exercises 5, 6, 9, and 10 each have two complete deterministic cases.
EX009_INPUT_CASES: Final[dict[int, tuple[Ex009InputCase, ...]]] = {
    5: (
        {
            "inputs": ["popcorn"],
            "expected_output": (
                "Type your favourite snack:\nYou chose popcorn for break time."
            ),
        },
        {
            "inputs": ["almonds"],
            "expected_output": (
                "Type your favourite snack:\nYou chose almonds for break time."
            ),
        },
    ),
    6: (
        {
            "inputs": ["Aisha", "Leeds"],
            "expected_output": (
                "Enter your first name:\nEnter your town:\nHello Aisha from Leeds."
            ),
        },
        {
            "inputs": ["Noah", "York"],
            "expected_output": (
                "Enter your first name:\nEnter your town:\nHello Noah from York."
            ),
        },
    ),
    9: (
        {
            "inputs": ["12"],
            "expected_output": (
                "How many pages did you read today?\nPages read in two days: 20"
            ),
        },
        {
            "inputs": ["7"],
            "expected_output": (
                "How many pages did you read today?\nPages read in two days: 15"
            ),
        },
    ),
    10: (
        {
            "inputs": ["0.5", "6"],
            "expected_output": (
                "Enter the price of one pencil:\n"
                "Enter how many pencils you bought:\n"
                "Total cost for 6 pencils: £3.0"
            ),
        },
        {
            "inputs": ["1.25", "4"],
            "expected_output": (
                "Enter the price of one pencil:\n"
                "Enter how many pencils you bought:\n"
                "Total cost for 4 pencils: £5.0"
            ),
        },
    ),
}

EX009_MIN_INPUT_CASES: Final[int] = 2

# Derived tooling catalog for the quality verifier; interactive outputs remain
# sourced only from EX009_INPUT_CASES.
EX009_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX009_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX009_INPUT_CASES.items()
    },
}


__all__ = [
    "EX009_DERIVED_OUTPUTS",
    "EX009_EXPECTED_STATIC_OUTPUTS",
    "EX009_INPUT_CASES",
    "EX009_MIN_INPUT_CASES",
    "Ex009InputCase",
]
