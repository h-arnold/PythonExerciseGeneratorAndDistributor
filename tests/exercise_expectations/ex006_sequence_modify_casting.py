"""Expectations for ex006 sequence modify casting."""

from __future__ import annotations

from typing import Final

from tests.exercise_expectations.types import Ex006InputExpectation

EX006_NOTEBOOK_PATH: Final[str] = "notebooks/ex006_sequence_modify_casting.ipynb"
EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "15\n",
    2: "6.0\n",
    3: "28\n",
    4: "Your score is 500\n",
    5: "25\n",
    8: "Area: 50\n",
    9: "The Burger costs \u00a35.5\n",
}


EX006_INPUT_EXPECTATIONS: Final[dict[int, Ex006InputExpectation]] = {
    6: {
        "inputs": ["6"],
        "prompt_contains": "Enter number",
        "last_line": "12",
    },
    7: {
        "inputs": ["1.5"],
        "prompt_contains": "Enter price",
        "output_contains": "Two items cost: 3.0",
    },
    10: {
        "inputs": ["10", "20"],
        "prompt_contains": "Enter item",
        "output_contains": "Total: 30.0",
    },
}
