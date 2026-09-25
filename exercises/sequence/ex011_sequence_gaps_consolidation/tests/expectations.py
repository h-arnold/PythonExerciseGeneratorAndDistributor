"""Canonical expectations for ex011 sequence gaps consolidation."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex011InputCase(TypedDict):
    """Deterministic input and exact output for an interactive exercise case."""

    inputs: list[str]
    expected_output: str


EX011_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Sequence is fun",
    2: "Hello Amina",
    4: "The total is 10",
    5: "Total cost: 7.5",
    6: "Average distance: 3.5 km",
    7: "Aisha enjoys drawing after school.",
}

# The first case matches the worked examples in the notebook.  The remaining
# cases are deterministic alternate transcripts used to reject hard-coded input
# and output answers.
EX011_INPUT_CASES: Final[dict[int, tuple[Ex011InputCase, ...]]] = {
    3: (
        {
            "inputs": ["coding"],
            "expected_output": "What is your favourite word?\nYou chose coding",
        },
        {
            "inputs": ["word with space"],
            "expected_output": (
                "What is your favourite word?\nYou chose word with space"
            ),
        },
        {
            "inputs": ["third choice"],
            "expected_output": "What is your favourite word?\nYou chose third choice",
        },
    ),
    8: (
        {
            "inputs": ["Aisha", "Cardiff"],
            "expected_output": (
                "Enter your first name:\n"
                "Enter your town:\n"
                "Hello Aisha from Cardiff."
            ),
        },
        {
            "inputs": ["Mina", "Swansea"],
            "expected_output": (
                "Enter your first name:\n"
                "Enter your town:\n"
                "Hello Mina from Swansea."
            ),
        },
        {
            "inputs": ["Rowan", "Bristol"],
            "expected_output": (
                "Enter your first name:\n"
                "Enter your town:\n"
                "Hello Rowan from Bristol."
            ),
        },
    ),
    9: (
        {
            "inputs": ["blue", "fox"],
            "expected_output": (
                "Enter your favourite colour:\n"
                "Enter your favourite animal:\n"
                "My favourite colour is blue and my favourite animal is fox."
            ),
        },
        {
            "inputs": ["green", "badger"],
            "expected_output": (
                "Enter your favourite colour:\n"
                "Enter your favourite animal:\n"
                "My favourite colour is green and my favourite animal is badger."
            ),
        },
        {
            "inputs": ["purple", "otter"],
            "expected_output": (
                "Enter your favourite colour:\n"
                "Enter your favourite animal:\n"
                "My favourite colour is purple and my favourite animal is otter."
            ),
        },
    ),
    10: (
        {
            "inputs": ["Amina"],
            "expected_output": (
                "Enter your name:\n"
                "Welcome to Sequence Supplies, Amina. Your total is £14.0."
            ),
        },
        {
            "inputs": ["Kai"],
            "expected_output": (
                "Enter your name:\n"
                "Welcome to Sequence Supplies, Kai. Your total is £14.0."
            ),
        },
        {
            "inputs": ["Noor"],
            "expected_output": (
                "Enter your name:\n"
                "Welcome to Sequence Supplies, Noor. Your total is £14.0."
            ),
        },
    ),
}

# The quality verifier expects a complete output catalog.  Interactive values
# are derived from their first case rather than duplicated in a static map.
EX011_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX011_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX011_INPUT_CASES.items()
    },
}

EX011_EXPECTED_PROMPTS: Final[dict[int, tuple[str, ...]]] = {
    3: ("What is your favourite word?",),
    8: ("Enter your first name:", "Enter your town:"),
    9: ("Enter your favourite colour:", "Enter your favourite animal:"),
    10: ("Enter your name:",),
}

EX011_MIN_INPUT_CASES: Final[int] = 3
