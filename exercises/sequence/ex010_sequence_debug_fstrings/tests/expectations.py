"""Exercise-local expectations for ex010 sequence debug f-strings."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex010InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX010_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX010_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe the problem you saw",
    "describe the bug",
    "describe the fault",
    "explain how you fixed it",
    "todo",
    "...",
)

EX010_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome, Sam!\n",
    2: "My pet is a rabbit!\n",
    3: "Mia enjoys drawing after school.\n",
    4: "Our best lesson is computing.\n",
    7: "You scored 4 goals today.\n",
    8: "Tickets sold altogether: 7\n",
    9: "Pages read in two days: 20\n",
    10: "Total cost for 6 pencils: £3.0\n",
}

EX010_INPUT_CASES: Final[dict[int, Ex010InputCase]] = {
    5: {
        "inputs": ["popcorn"],
        "expected_output": "Type your favourite snack: You chose popcorn for break time.\n",
    },
    6: {
        "inputs": ["Aisha", "Leeds"],
        "expected_output": "Enter your first name: Enter your town: Hello Aisha from Leeds.\n",
    },
}
