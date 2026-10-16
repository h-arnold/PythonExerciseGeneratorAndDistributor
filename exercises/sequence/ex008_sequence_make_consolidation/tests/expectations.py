"""Exercise-local expectations for ex008 sequence make consolidation."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex008InteractiveCase(TypedDict):
    """Inputs and required result for an interactive exercise case."""

    inputs: list[str]
    expected_output: str


EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome to Oakwood Coding Club!",
    2: "Snack box: muffins\nTotal cost: 8 pounds",
}

EX008_INTERACTIVE_CASES: Final[dict[int, list[Ex008InteractiveCase]]] = {
    3: [
        {
            "inputs": ["Aisha", "drawing"],
            "expected_output": "Hello Aisha! Your hobby is drawing.",
        },
        {
            "inputs": ["Leo", "chess"],
            "expected_output": "Hello Leo! Your hobby is chess.",
        },
    ],
    4: [
        {
            "inputs": ["6", "3"],
            "expected_output": "Books read altogether: 18",
        },
        {
            "inputs": ["0", "4"],
            "expected_output": "Books read altogether: 0",
        },
        {
            "inputs": ["6", "4"],
            "expected_output": "Books read altogether: 24",
        },
    ],
    5: [
        {
            "inputs": ["2.5", "3"],
            "expected_output": "Total distance: 7.5 km",
        },
        {
            "inputs": ["1.2", "4"],
            "expected_output": "Total distance: 4.8 km",
        },
    ],
}
