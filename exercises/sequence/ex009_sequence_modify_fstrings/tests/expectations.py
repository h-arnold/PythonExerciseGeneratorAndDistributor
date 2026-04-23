"""Exercise-local expectations for ex009 sequence modify f-strings."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex009InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX009_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome, Sam!\n",
    2: "My pet is a rabbit!\n",
    3: "Mia enjoys drawing after school.\n",
    4: "Our best lesson is computing.\n",
    7: "You scored 4 goals today.\n",
    8: "Tickets sold altogether: 7\n",
}

EX009_INPUT_CASES: Final[dict[int, Ex009InputCase]] = {
    5: {
        "inputs": ["popcorn"],
        "expected_output": "Type your favourite snack:\nYou chose popcorn for break time.\n",
    },
    6: {
        "inputs": ["Aisha", "Leeds"],
        "expected_output": "Enter your first name:\nEnter your town:\nHello Aisha from Leeds.\n",
    },
    9: {
        "inputs": ["12"],
        "expected_output": "How many pages did you read today?\nPages read in two days: 20\n",
    },
    10: {
        "inputs": ["0.5", "6"],
        "expected_output": "Enter the price of one pencil:\nEnter how many pencils you bought:\nTotal cost for 6 pencils: £3.0\n",
    },
}
