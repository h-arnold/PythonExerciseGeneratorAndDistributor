"""Canonical expectations for ex005 sequence debug logic.

Static and interactive parts are declared separately.  ``EX005_DERIVED_OUTPUTS``
is the complete part-to-output view used by the quality verifier; interactive
expected text lives only in ``EX005_INPUT_CASES``.
"""

from __future__ import annotations

from typing import Final, TypedDict


class Ex005InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX005_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX005_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
)

# Only the eight non-interactive parts belong in the static output map.
EX005_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "50",
    2: "Alice",
    3: "24",
    4: "Hello World",
    6: "5",
    7: "25.0",
    8: "I love learning Python",
    9: "30",
}

# Values that belong to the original scenarios.  Debugging fixes the live
# operation, not the data supplied by the exercise.
EX005_SCAFFOLD_ASSIGNMENTS: Final[dict[int, dict[str, int | str]]] = {
    1: {"price": 10, "quantity": 5},
    2: {"name": "Alice"},
    3: {"width": 6, "height": 4},
    4: {"word1": "Hello", "word2": "World"},
    6: {"paid": 20, "cost": 15},
    7: {"score1": 20, "score2": 30},
    8: {"word1": "I", "word2": "love", "word3": "learning", "word4": "Python"},
    9: {"length": 10, "width": 5},
}

# Exact variable provenance required in the live concatenation expressions.
EX005_CONCATENATION_VARIABLES: Final[dict[int, tuple[str, ...]]] = {
    4: ("word1", "word2"),
    5: ("first_name", "last_name"),
    8: ("word1", "word2", "word3", "word4"),
    10: ("age", "city"),
}

EX005_INPUT_PROMPTS: Final[dict[int, tuple[str, str]]] = {
    5: ("Enter first name: ", "Enter last name: "),
    10: ("Enter your age: ", "Enter your city: "),
}

# Multiple cases prevent a solution that hard-codes one known answer.
EX005_INPUT_CASES: Final[dict[int, tuple[Ex005InputCase, ...]]] = {
    5: (
        {
            "inputs": ["Maria", "Jones"],
            "expected_output": "Enter first name: Enter last name: Maria Jones",
        },
        {
            "inputs": ["Ada", "Lovelace"],
            "expected_output": "Enter first name: Enter last name: Ada Lovelace",
        },
    ),
    10: (
        {
            "inputs": ["16", "Birmingham"],
            "expected_output": (
                "Enter your age: Enter your city: "
                "You are 16 years old and live in Birmingham"
            ),
        },
        {
            "inputs": ["15", "London"],
            "expected_output": (
                "Enter your age: Enter your city: "
                "You are 15 years old and live in London"
            ),
        },
    ),
}

# Both absolute-difference argument orders are documented equivalents.
EX005_EX6_ALLOWED_CHANGE_FORMS: Final[tuple[str, ...]] = (
    "paid - cost",
    "abs(cost - paid)",
    "abs(paid - cost)",
)

# The quality verifier requires all ten part keys, but interactive text is
# derived from the primary case rather than copied into a static map.
EX005_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX005_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX005_INPUT_CASES.items()
    },
}
