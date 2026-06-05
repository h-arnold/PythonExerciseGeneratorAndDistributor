"""Exercise-local expectations for ex013 sequence debug maths operators."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex013InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX013_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX013_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what error",
    "describe what happened",
    "describe the problem you saw",
    "describe the error you saw",
    "describe the bug",
    "describe the fault",
    "explain how you fixed it",
    "explain what you changed",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "include any error messages",
)

EX013_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Full groups: 6\n",
    2: "Leftover: 1\n",
    3: "Average: 6.7\n",
    5: "Total: \u00a33.77\n",
    6: "200 minutes is 3 hours and 20 minutes\n",
    8: "Area of square: 5.5\n",
    9: "Full bags: 9, Left over: 2\n",
}

EX013_INPUT_CASES: Final[dict[int, Ex013InputCase]] = {
    4: {
        "inputs": ["23"],
        "expected_output": "How many players? Full teams: 4\n",
    },
    7: {
        "inputs": ["389"],
        "expected_output": "Enter pence: 389p is \u00a33 and 89p\n",
    },
    10: {
        "inputs": ["29", "6", "10.99"],
        "expected_output": (
            "How many items? How many per box? Total cost? \u00a3"
            "Full boxes: 4\n"
            "Leftover items: 5\n"
            "Cost per box: \u00a32.75\n"
        ),
    },
}
