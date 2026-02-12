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

EX006_MODIFY_STARTER_BASELINES: Final[dict[str, str]] = {
    "exercise1": (
        "# Exercise 1 — YOUR CODE\n"
        "# Cast a and b to ints so the print shows 15\n"
        "a = \"5\"\n"
        "b = \"10\"\n"
        "print(a + b)\n"
    ),
    "exercise2": (
        "# Exercise 2 — YOUR CODE\n"
        "price_1 = \"2.5\"\n"
        "price_2 = \"3.5\"\n"
        "print(price_1 + price_2)\n"
    ),
    "exercise3": (
        "# Exercise 3 — YOUR CODE\n"
        "# Cast days to int so the multiplication gives 28\n"
        "days = \"7\"\n"
        "weeks = 4\n"
        "print(days * weeks)\n"
    ),
    "exercise4": (
        "# Exercise 4 — YOUR CODE\n"
        "score = 500\n"
        "print(\"Your score is\", score)\n"
    ),
    "exercise5": (
        "# Exercise 5 — YOUR CODE\n"
        "temperature = 25.9\n"
        "print(temperature)\n"
    ),
    "exercise6": (
        "# Exercise 6 — YOUR CODE\n"
        "# Print the prompt then read an answer with input()\n"
        "print(\"Enter number:\")\n"
        "num = input()\n"
        "print(num + num)\n"
    ),
    "exercise7": (
        "# Exercise 7 — YOUR CODE\n"
        "print(\"Enter price:\")\n"
        "price = input()\n"
        "print(\"Two items cost: \" + price + price)\n"
    ),
    "exercise8": (
        "# Exercise 8 — YOUR CODE\n"
        "width = \"10\"\n"
        "height = \"5\"\n"
        "print(\"Dimensions: \" + width + \" by \" + height)\n"
    ),
    "exercise9": (
        "# Exercise 9 — YOUR CODE\n"
        "item = \"Burger\"\n"
        "cost = 5.50\n"
        "print(\"The \" + item + \" costs £\" + cost)\n"
    ),
    "exercise10": (
        "# Exercise 10 — YOUR CODE\n"
        "print(\"Enter item 1:\")\n"
        "p1 = input()\n"
        "print(\"Enter item 2:\")\n"
        "p2 = input()\n"
        "print(\"Total: \" + p1 + p2)\n"
    ),
}
