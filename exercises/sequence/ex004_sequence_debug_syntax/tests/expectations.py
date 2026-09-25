"""Exercise-local expectations for ex004 debug syntax."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex004InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX004_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX004_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what",
    "describe briefly",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
    "test it by",
    "verifying it works",
    "include any error",
)

EX004_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Hello World!",
    2: "I like Python",
    3: "Learning Python",
    4: "50",
    5: "Hello Alice",
    6: "Welcome to school",
    9: "It's amazing",
}

EX004_INPUT_CASES: Final[dict[int, tuple[Ex004InputCase, ...]]] = {
    7: (
        {
            "inputs": ["5"],
            "expected_output": "How many apples? You have 5 apples",
        },
        {
            "inputs": ["12"],
            "expected_output": "How many apples? You have 12 apples",
        },
    ),
    8: (
        {
            "inputs": ["Alice"],
            "expected_output": "Enter your name: Hello Alice",
        },
        {
            "inputs": ["Jordan"],
            "expected_output": "Enter your name: Hello Jordan",
        },
    ),
    10: (
        {
            "inputs": ["Blue"],
            "expected_output": (
                "What is your favourite colour? My favourite colour is Blue"
            ),
        },
        {
            "inputs": ["Green"],
            "expected_output": (
                "What is your favourite colour? My favourite colour is Green"
            ),
        },
    ),
}

# Gate G requires a complete output catalog. Interactive values are derived
# from the canonical primary case; the full cases remain in EX004_INPUT_CASES.
EX004_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    **EX004_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX004_INPUT_CASES.items()
    },
}
