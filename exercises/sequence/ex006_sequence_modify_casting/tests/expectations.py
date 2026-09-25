"""Canonical expectations for ex006 sequence modify casting."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex006InputCase(TypedDict):
    """One deterministic input/output transcript for an interactive task."""

    inputs: list[str]
    expected_output: str


# Exercises 1-5, 8, and 9 are static-output tasks.
EX006_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "15",
    2: "6.0",
    3: "28",
    4: "Your score is 500",
    5: "25",
    8: "Area: 50",
    9: "The Burger costs \u00a35.5",
}

# Exercises 6, 7, and 10 are interactive; each part has two complete cases.
EX006_INPUT_CASES: Final[dict[int, tuple[Ex006InputCase, ...]]] = {
    6: (
        {
            "inputs": ["6"],
            "expected_output": "Enter number:\n12",
        },
        {
            "inputs": ["9"],
            "expected_output": "Enter number:\n18",
        },
    ),
    7: (
        {
            "inputs": ["1.5"],
            "expected_output": "Enter price:\nTwo items cost: 3.0",
        },
        {
            "inputs": ["2.25"],
            "expected_output": "Enter price:\nTwo items cost: 4.5",
        },
    ),
    10: (
        {
            "inputs": ["10", "20"],
            "expected_output": "Enter item 1:\nEnter item 2:\nTotal: 30.0",
        },
        {
            "inputs": ["2.5", "4.5"],
            "expected_output": "Enter item 1:\nEnter item 2:\nTotal: 7.0",
        },
    ),
}

# Derived all-part catalog for repository tooling. It is intentionally separate
# from the static and interactive classifications above and is not consumed by
# the exercise tests or self-checker.
EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    **EX006_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"] for exercise_no, cases in EX006_INPUT_CASES.items()
    },
}
