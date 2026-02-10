"""Expectations for ex005 debug logic."""

from __future__ import annotations

from typing import Final

EX005_NOTEBOOK_PATH: Final[str] = "notebooks/ex005_sequence_debug_logic.ipynb"
EX005_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX005_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
)
EX005_FULL_NAME_EXERCISE: Final[int] = 5
EX005_PROFILE_EXERCISE: Final[int] = 10
EX005_AVERAGE_DIVISOR: Final[int] = 2
EX005_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "50",
    2: "Alice",
    3: "24",
    4: "Hello World",
    6: "5",
    7: "25.0",
    8: "I love learning Python",
    9: "30",
}
EX005_EXERCISE_INPUTS: Final[dict[int, list[str]]] = {
    EX005_FULL_NAME_EXERCISE: ["Maria", "Jones"],
    EX005_PROFILE_EXERCISE: ["16", "Birmingham"],
}
EX005_INPUT_PROMPTS: Final[dict[int, tuple[str, str]]] = {
    EX005_FULL_NAME_EXERCISE: ("Enter first name: ", "Enter last name: "),
    EX005_PROFILE_EXERCISE: ("Enter your age: ", "Enter your city: "),
}
