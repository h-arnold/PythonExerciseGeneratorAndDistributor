"""Expectations for ex002 sequence modify basics."""

from __future__ import annotations

from typing import Final

EX002_NOTEBOOK_PATH: Final[str] = "notebooks/ex002_sequence_modify_basics.ipynb"
EX002_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "Hello Python!",
    2: "I go to Bassaleg School",
    3: "15",
    4: "Good Morning Everyone",
    5: "5.0",
    7: "The result is 100",
    8: "24",
    10: "Welcome to Python programming!",
}
EX002_EXPECTED_MULTI_LINE: Final[dict[int, list[str]]] = {
    6: ["Learning", "to", "code rocks"],
    9: ["10 minus 3 equals", "7"],
}
EX002_EXPECTED_NUMERIC: Final[dict[int, int | float]] = {
    3: int(EX002_EXPECTED_SINGLE_LINE[3]),
    5: float(EX002_EXPECTED_SINGLE_LINE[5]),
    8: int(EX002_EXPECTED_SINGLE_LINE[8]),
    9: int(EX002_EXPECTED_MULTI_LINE[9][1]),
}
EX002_EXPECTED_PRINT_CALLS: Final[dict[int, int]] = {
    4: 1,
    6: 3,
    9: 2,
}

EX002_MODIFY_STARTER_BASELINES: Final[dict[str, str]] = {
    "exercise1": (
        "# Exercise 1 — YOUR CODE\n"
        "# Modify the print statement below\n"
        "print(\"Hello World!\")\n"
    ),
    "exercise2": (
        "# Exercise 2 — YOUR CODE\n"
        "# Modify the print statement below\n"
        "print(\"I go to Greenfield School\")\n"
    ),
    "exercise3": (
        "# Exercise 3 — YOUR CODE\n"
        "# Modify the arithmetic below\n"
        "print(5 + 3)\n"
    ),
    "exercise4": (
        "# Exercise 4 — YOUR CODE\n"
        "# Modify the concatenation below\n"
        "print(\"Hello\" + \" \" + \"World\")\n"
    ),
    "exercise5": (
        "# Exercise 5 — YOUR CODE\n"
        "# Modify the calculation below\n"
        "print(10 - 4)\n"
    ),
    "exercise6": (
        "# Exercise 6 — YOUR CODE\n"
        "# Add two more print() statements so the output is:\n"
        "# Learning\n"
        "# to\n"
        "# code rocks\n"
        "print(\"Learning\")\n\n"
        "# TODO: add the two missing print statements below"
    ),
    "exercise7": (
        "# Exercise 7 — YOUR CODE\n"
        "# Complete the print statement below so it produces:\n"
        "# The result is 100\n"
        "print(\"The result is \")\n\n"
        "# TODO: add the rest of the print (concatenate \"100\" as text)"
    ),
    "exercise8": (
        "# Exercise 8 — YOUR CODE\n"
        "# Modify the calculation below\n"
        "print(2 + 3 + 4)\n"
    ),
    "exercise9": (
        "# Exercise 9 — YOUR CODE\n"
        "# Modify the statements below\n"
        "print(\"10 minus 3 equals\")\n"
        "# The calculation must be performed inside the print() call; do not just print \"7\"\n"
        "# TODO: add the print(...) with 10 - 3\n"
    ),
    "exercise10": (
        "# Exercise 10 — YOUR CODE\n"
        "# Add the rest of the concatenation so it prints:\n"
        "# Welcome to Python programming!\n"
        "print(\"Welcome\")\n\n"
        "# TODO: complete the concatenation on the line below"
    ),
}
