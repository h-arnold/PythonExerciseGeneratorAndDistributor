"""Canonical output and input expectations for ex006."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex006InputExpectation(TypedDict):
    inputs: list[str]
    expected_segments: list[str]
    alternate_inputs: list[str]
    alternate_segments: list[str]


EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "15",
    2: "6.0",
    3: "28",
    4: "Your score is 500",
    5: "25",
    8: "Area: 50",
    9: "The Burger costs £5.5",
}

EX006_INPUT_EXPECTATIONS: Final[dict[int, Ex006InputExpectation]] = {
    6: {
        "inputs": ["6"],
        "expected_segments": ["Enter number:", "12"],
        "alternate_inputs": ["9"],
        "alternate_segments": ["Enter number:", "18"],
    },
    7: {
        "inputs": ["1.5"],
        "expected_segments": ["Enter price:", "Two items cost: 3.0"],
        "alternate_inputs": ["2.25"],
        "alternate_segments": ["Enter price:", "Two items cost: 4.5"],
    },
    10: {
        "inputs": ["10", "20"],
        "expected_segments": ["Enter item 1:", "Enter item 2:", "Total: 30.0"],
        "alternate_inputs": ["4.25", "1.75"],
        "alternate_segments": ["Enter item 1:", "Enter item 2:", "Total: 6.0"],
    },
}
