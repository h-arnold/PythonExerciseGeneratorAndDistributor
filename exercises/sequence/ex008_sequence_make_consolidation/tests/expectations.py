"""Exercise-local expectations for ex008 sequence make consolidation."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex008InteractiveCase(TypedDict):
    """Expected transcript for an interactive exercise case."""

    inputs: list[str]
    expected_output: str


EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Welcome to Oakwood Coding Club!\n",
    2: "Snack box: muffins\nTotal cost: 8 pounds\n",
}

EX008_INTERACTIVE_CASES: Final[dict[int, list[Ex008InteractiveCase]]] = {
    3: [
        {
            "inputs": ["Aisha", "drawing"],
            "expected_output": (
                "Enter your name:\n"
                "Enter your favourite hobby:\n"
                "Hello Aisha! Your hobby is drawing.\n"
            ),
        },
        {
            "inputs": ["Leo", "chess"],
            "expected_output": (
                "Enter your name:\n"
                "Enter your favourite hobby:\n"
                "Hello Leo! Your hobby is chess.\n"
            ),
        },
    ],
    4: [
        {
            "inputs": ["6", "3"],
            "expected_output": (
                "Books read in one week:\n"
                "Number of weeks:\n"
                "Books read altogether: 18\n"
            ),
        },
        {
            "inputs": ["0", "4"],
            "expected_output": (
                "Books read in one week:\n"
                "Number of weeks:\n"
                "Books read altogether: 0\n"
            ),
        },
    ],
    5: [
        {
            "inputs": ["2.5", "3"],
            "expected_output": (
                "Distance for one walk in km:\n"
                "Number of walks:\n"
                "Total distance: 7.5 km\n"
            ),
        },
        {
            "inputs": ["1.2", "4"],
            "expected_output": (
                "Distance for one walk in km:\n"
                "Number of walks:\n"
                "Total distance: 4.8 km\n"
            ),
        },
    ],
}
