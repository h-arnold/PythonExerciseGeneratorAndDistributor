"""Canonical expectations for ex008 sequence make consolidation."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex008InputCase(TypedDict):
    """One deterministic input and exact transcript for an interactive task."""

    id: str
    inputs: list[str]
    expected_output: str


# Exercises 1 and 2 use fixed values (no input) — static output only.
EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome to Oakwood Coding Club!",
    2: "Snack box: muffins\nTotal cost: 8 pounds",
}

# Exercises 3-5 use input().  The cases below are shared by pytest and the
# specialised self-check.  Each part has more than one non-fixture transcript
# so a hard-coded worked example cannot satisfy the interactive tests.
EX008_INPUT_CASES: Final[dict[int, tuple[Ex008InputCase, ...]]] = {
    3: (
        {
            "id": "aisha-drawing",
            "inputs": ["Aisha", "drawing"],
            "expected_output": (
                "Enter your name:\nEnter your favourite hobby:\nHello Aisha! Your hobby is drawing."
            ),
        },
        {
            "id": "leo-chess",
            "inputs": ["Leo", "chess"],
            "expected_output": (
                "Enter your name:\nEnter your favourite hobby:\nHello Leo! Your hobby is chess."
            ),
        },
        {
            "id": "mina-pottery",
            "inputs": ["Mina", "pottery"],
            "expected_output": (
                "Enter your name:\nEnter your favourite hobby:\nHello Mina! Your hobby is pottery."
            ),
        },
    ),
    4: (
        {
            "id": "six-three",
            "inputs": ["6", "3"],
            "expected_output": (
                "Books read in one week:\nNumber of weeks:\nBooks read altogether: 18"
            ),
        },
        {
            "id": "zero-four",
            "inputs": ["0", "4"],
            "expected_output": (
                "Books read in one week:\nNumber of weeks:\nBooks read altogether: 0"
            ),
        },
    ),
    5: (
        {
            "id": "two-point-five-three",
            "inputs": ["2.5", "3"],
            "expected_output": (
                "Distance for one walk in km:\nNumber of walks:\nTotal distance: 7.5 km"
            ),
        },
        {
            "id": "one-point-two-four",
            "inputs": ["1.2", "4"],
            "expected_output": (
                "Distance for one walk in km:\nNumber of walks:\nTotal distance: 4.8 km"
            ),
        },
    ),
}

# Tooling requires a complete derived catalog, but interactive parts remain
# classified in EX008_INPUT_CASES rather than being copied into static outputs.
EX008_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX008_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"] for exercise_no, cases in EX008_INPUT_CASES.items()
    },
}
