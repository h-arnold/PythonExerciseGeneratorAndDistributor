"""Canonical expectations for ex010 sequence debug f-strings.

Static and interactive outputs are kept in separate maps.  The derived map at
the end is only a catalogue for tooling; it is not a second declaration of
interactive outputs.
"""

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

# Only non-interactive parts belong in the static output map.
EX010_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome, Sam!",
    2: "My pet is a rabbit!",
    3: "Mia enjoys drawing after school.",
    4: "Our best lesson is computing.",
    7: "You scored 4 goals today.",
    8: "Tickets sold altogether: 7",
    9: "Pages read in two days: 20",
    10: "Total cost for 6 pencils: £3.0",
}

# Each interactive part has two deterministic cases.  The complete transcript
# includes each prompt and the final response, so a hard-coded first answer
# cannot satisfy the exercise.
EX010_INPUT_CASES: Final[dict[int, tuple[Ex010InputCase, ...]]] = {
    5: (
        {
            "inputs": ["popcorn"],
            "expected_output": (
                "Type your favourite snack: You chose popcorn for break time."
            ),
        },
        {
            "inputs": ["carrot"],
            "expected_output": (
                "Type your favourite snack: You chose carrot for break time."
            ),
        },
    ),
    6: (
        {
            "inputs": ["Aisha", "Leeds"],
            "expected_output": (
                "Enter your first name: Enter your town: Hello Aisha from Leeds."
            ),
        },
        {
            "inputs": ["Jordan", "Oxford"],
            "expected_output": (
                "Enter your first name: Enter your town: Hello Jordan from Oxford."
            ),
        },
    ),
}

# The quality verifier scans for an output catalogue covering all parts.  Keep
# it derived from the canonical maps above so interactive cases are not
# duplicated into (or misclassified as) the static map.
EX010_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX010_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX010_INPUT_CASES.items()
    },
}
