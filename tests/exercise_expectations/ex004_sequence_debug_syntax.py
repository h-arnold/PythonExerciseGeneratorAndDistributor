"""Expectations for ex004 debug syntax."""

from __future__ import annotations

from typing import Final

EX004_NOTEBOOK_PATH: Final[str] = "notebooks/ex004_sequence_debug_syntax.ipynb"
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
EX004_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "Hello World!",
    2: "I like Python",
    3: "Learning Python",
    4: "50",
    5: "Hello Alice",
    6: "Welcome to school",
    9: "It's amazing",
}
EX004_PROMPT_STRINGS: Final[dict[int, str]] = {
    7: "How many apples?",
    8: "Enter your name:",
    10: "What is your favourite colour?",
}
EX004_FORMAT_VALIDATION: Final[dict[int, str]] = {
    7: "You have 10 apples in total",
    8: "Hello Alice",
    10: "My favourite colour is Blue",
}
