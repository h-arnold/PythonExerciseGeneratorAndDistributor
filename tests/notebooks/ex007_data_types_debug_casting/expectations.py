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

EX007_MODIFY_STARTER_BASELINES: Final[dict[str, str]] = {
    "exercise1": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "count = 3\n"
        "message = \"You have \" + count + \" pens\"\n"
        "print(message)\n"
    ),
    "exercise2": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "price_pounds = 7.5\n"
        "label = \"Total price: £\"\n"
        "print(label + int(price_pounds))\n"
    ),
    "exercise3": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "age_text = input(\"Enter your age: \")\n"
        "next_age = age_text + 1\n"
        "print(\"Next year you will be \" + str(next_age))\n"
    ),
    "exercise4": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "total_distance = 7\n"
        "days = 2\n"
        "average = total_distance // days\n"
        "print(\"Average per day: \" + str(average) + \" km\")\n"
    ),
    "exercise5": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "word = input(\"Word to repeat: \")\n"
        "repeat_text = input(\"How many times? \")\n"
        "print(word * repeat_text)\n"
    ),
    "exercise6": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "temp_celsius = input(\"Enter temperature in Celsius: \")\n"
        "fahrenheit = temp_celsius * 9 / 5 + \"32\"\n"
        "print(\"Temperature in Fahrenheit: \" + str(fahrenheit))\n"
    ),
    "exercise7": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "price_text = input(\"Enter price per item (£): \")\n"
        "quantity_text = input(\"Enter quantity: \")\n"
        "total_cost = price_text * quantity_text\n"
        "print(\"Total cost: £\" + total_cost)\n"
    ),
    "exercise8": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "score1 = input(\"Enter score 1: \")\n"
        "score2 = input(\"Enter score 2: \")\n"
        "score3 = input(\"Enter score 3: \")\n"
        "total_score = score1 + score2 + score3\n"
        "average_score = total_score // 3\n"
        "print(\"Average score: \" + str(average_score))\n"
    ),
    "exercise9": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "pounds_text = input(\"Pounds: \")\n"
        "pence_text = input(\"Pence: \")\n"
        "total_pence = pounds_text * 100 + pence_text\n"
        "print(\"Total pence: \" + total_pence)\n"
    ),
    "exercise10": (
        "# BUGGY CODE (students edit this tagged cell)\n"
        "# Fix the code below and run the cell.\n\n"
        "total_bill_text = input(\"Total bill (£): \")\n"
        "people_text = input(\"Number of people: \")\n"
        "tip_rate = 0.1\n"
        "total_with_tip = total_bill_text + total_bill_text * tip_rate\n"
        "per_person = total_with_tip // people_text\n"
        "print(\"Each person pays: £\" + str(per_person))\n"
    ),
}
