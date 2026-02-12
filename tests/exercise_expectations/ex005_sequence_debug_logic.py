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

EX005_MODIFY_STARTER_BASELINES: Final[dict[str, str]] = {
    "exercise1": "price = 10\nquantity = 5\ntotal = price + quantity\nprint(total)",
    "exercise2": 'name = "Alice"\nusername = "Bob"\nprint(username)',
    "exercise3": "width = 6\nheight = 4\narea = width / height\nprint(area)",
    "exercise4": 'word1 = "Hello"\nword2 = "World"\nmessage = word1 + word2\nprint(message)',
    "exercise5": (
        'first_name = input("Enter first name: ")\n'
        'last_name = input("Enter last name: ")\n'
        'full_name = first_name + last_name\n'
        'print(full_name)'
    ),
    "exercise6": "paid = 20\ncost = 15\nchange = cost - paid\nprint(paid)",
    "exercise7": "score1 = 20\nscore2 = 30\ntotal = score1 * score2\naverage = total + 2\nprint(average)",
    "exercise8": (
        'word1 = "I"\n'
        'word2 = "love"\n'
        'word3 = "learning"\n'
        'word4 = "Python"\n'
        'sentence = word1 + word2 + word3 + word4\n'
        'print(sentence)'
    ),
    "exercise9": "length = 10\nwidth = 5\nperimeter = length + length + width\nprint(length)",
    "exercise10": (
        'age = input("Enter your age: ")\n'
        'city = input("Enter your city: ")\n'
        'message = "You are " + age + " years old and live in" + city\n'
        'print(message)'
    ),
}
