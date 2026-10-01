"""Exercise-local expectations for ex001_selection_modify_basics."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex001InputExpectation(TypedDict):
    """Expectations for exercises that prompt for input in ex001."""

    inputs: list[str]
    prompt_contains: str
    output_contains: str


# Exercise 1 prints fixed text; exercises 2-10 all call input() and are
# declared only in EX001_INPUT_CASES.
EX001_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "No it isn't.",
}

EX001_INPUT_CASES: Final[dict[int, Ex001InputExpectation]] = {
    2: {
        "inputs": ["26"],
        "prompt_contains": "temperature",
        "output_contains": "It's hot today!",
    },
    3: {
        "inputs": ["5"],
        "prompt_contains": "number",
        "output_contains": "That's not ten!",
    },
    4: {
        "inputs": ["10"],
        "prompt_contains": "age",
        "output_contains": "You are a child",
    },
    5: {
        "inputs": ["7"],
        "prompt_contains": "3 + 5",
        "output_contains": "Wrong answer!",
    },
    6: {
        "inputs": ["90"],
        "prompt_contains": "score",
        "output_contains": "Distinction!",
    },
    7: {
        "inputs": ["Bob"],
        "prompt_contains": "name",
        "output_contains": "Hello Bob!",
    },
    8: {
        "inputs": ["140"],
        "prompt_contains": "height",
        "output_contains": "You are tall enough to ride!",
    },
    9: {
        "inputs": ["coffee"],
        "prompt_contains": "drink",
        "output_contains": "Here is your coffee!",
    },
    10: {
        "inputs": ["opensesame"],
        "prompt_contains": "password",
        "output_contains": "Wrong password!",
    },
}
