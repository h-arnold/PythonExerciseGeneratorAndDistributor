"""Expectations for ex007 data types debug casting."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex007InputCase(TypedDict):
    inputs: list[str]
    prompts: list[str]
    last_line: str

EX007_NOTEBOOK_PATH: Final[str] = "notebooks/ex007_data_types_debug_casting.ipynb"
EX007_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX007_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "run the code first",
    "explain what happened",
    "describe what happened",
    "todo",
    "...",
)

EX007_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "You have 3 pens\n",
    2: "Total price: £7.5\n",
    4: "Average per day: 3.5 km\n",
}

EX007_INPUT_CASES: Final[dict[int, Ex007InputCase]] = {
    3: {
        "inputs": ["14"],
        "prompts": ["Enter your age: "],
        "last_line": "Next year you will be 15",
    },
    5: {
        "inputs": ["hi", "3"],
        "prompts": ["Word to repeat: ", "How many times? "],
        "last_line": "hihihi",
    },
    6: {
        "inputs": ["20"],
        "prompts": ["Enter temperature in Celsius: "],
        "last_line": "Temperature in Fahrenheit: 68.0",
    },
    7: {
        "inputs": ["2.5", "4"],
        "prompts": ["Enter price per item (£): ", "Enter quantity: "],
        "last_line": "Total cost: £10.0",
    },
    8: {
        "inputs": ["50", "60", "70"],
        "prompts": ["Enter score 1: ", "Enter score 2: ", "Enter score 3: "],
        "last_line": "Average score: 60.0",
    },
    9: {
        "inputs": ["4", "50"],
        "prompts": ["Pounds: ", "Pence: "],
        "last_line": "Total pence: 450",
    },
    10: {
        "inputs": ["120", "4"],
        "prompts": ["Total bill (£): ", "Number of people: "],
        "last_line": "Each person pays: £33.0",
    },
}
