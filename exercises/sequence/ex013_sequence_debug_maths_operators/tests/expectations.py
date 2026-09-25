"""Canonical expectations for ex013 sequence debug maths operators."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex013InputCase(TypedDict):
    """One deterministic input/output transcript for an interactive part."""

    inputs: tuple[str, ...]
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

# Static and interactive expectations remain separate. Interactive values are
# not duplicated in a static map because doing so would misclassify input cells.
EX013_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Full groups: 6",
    2: "Leftover: 1",
    3: "Average: 6.7",
    5: "Total: £3.77",
    6: "200 minutes is 3 hours and 20 minutes",
    8: "Area of square: 5.5",
    9: "Full bags: 9, Left over: 2",
}

# Exercises 4, 7, and 10 are interactive. Every case is run by pytest and by
# the specialised student checker.
EX013_INPUT_CASES: Final[dict[int, tuple[Ex013InputCase, ...]]] = {
    4: (
        {
            "inputs": ("23",),
            "expected_output": "How many players? Full teams: 4",
        },
        {
            "inputs": ("0",),
            "expected_output": "How many players? Full teams: 0",
        },
        {
            "inputs": ("17",),
            "expected_output": "How many players? Full teams: 3",
        },
        {
            "inputs": ("10",),
            "expected_output": "How many players? Full teams: 2",
        },
    ),
    7: (
        {
            "inputs": ("389",),
            "expected_output": "Enter pence: 389p is £3 and 89p",
        },
        {
            "inputs": ("250",),
            "expected_output": "Enter pence: 250p is £2 and 50p",
        },
        {
            "inputs": ("99",),
            "expected_output": "Enter pence: 99p is £0 and 99p",
        },
        {
            "inputs": ("100",),
            "expected_output": "Enter pence: 100p is £1 and 0p",
        },
    ),
    10: (
        {
            "inputs": ("29", "6", "10.99"),
            "expected_output": (
                "How many items? How many per box? Total cost? £"
                "Full boxes: 4\n"
                "Leftover items: 5\n"
                "Cost per box: £2.75"
            ),
        },
        {
            "inputs": ("30", "6", "12.00"),
            "expected_output": (
                "How many items? How many per box? Total cost? £"
                "Full boxes: 5\n"
                "Leftover items: 0\n"
                "Cost per box: £2.4"
            ),
        },
        {
            "inputs": ("7", "2", "5.55"),
            "expected_output": (
                "How many items? How many per box? Total cost? £"
                "Full boxes: 3\n"
                "Leftover items: 1\n"
                "Cost per box: £1.85"
            ),
        },
        {
            "inputs": ("8", "4", "10"),
            "expected_output": (
                "How many items? How many per box? Total cost? £"
                "Full boxes: 2\n"
                "Leftover items: 0\n"
                "Cost per box: £5.0"
            ),
        },
    ),
}
EX013_MIN_INPUT_CASES: Final[int] = 2

# The quality verifier requires a complete output catalog. This is a tooling
# view only; interactive parts remain classified in EX013_INPUT_CASES.
EX013_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX013_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"] for exercise_no, cases in EX013_INPUT_CASES.items()
    },
}


__all__ = [
    "EX013_DERIVED_OUTPUTS",
    "EX013_EXPECTED_STATIC_OUTPUTS",
    "EX013_INPUT_CASES",
    "EX013_MIN_EXPLANATION_LENGTH",
    "EX013_MIN_INPUT_CASES",
    "EX013_PLACEHOLDER_PHRASES",
    "Ex013InputCase",
]
