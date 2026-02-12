"""Expectations for ex003 sequence modify variables."""

from __future__ import annotations

from typing import Final

EX003_NOTEBOOK_PATH: Final[str] = "notebooks/ex003_sequence_modify_variables.ipynb"
EX003_EXPECTED_STATIC_OUTPUT: Final[dict[int, str]] = {
    1: "Hi there!",
    2: "I enjoy coding lessons.",
    3: "My favourite food is sushi",
    7: "Variables matter",
    8: "Keep experimenting",
    9: "Good evening everyone!",
    10: "Variables and strings make a message!",
}
EX003_EXPECTED_PROMPTS: Final[dict[int, list[str]]] = {
    4: ["Type the name of your favourite fruit:", "Type one word to describe it:"],
    5: ["Which town do you like the most?", "Which country is it in?"],
    6: ["Please enter your first name:", "Please enter your last name:"],
}
EX003_EXPECTED_INPUT_MESSAGES: Final[dict[int, str]] = {
    4: "I like {value1} because it is {value2}",
    5: "I would visit {town} in {country}",
    6: "Welcome, {first} {last}!",
}
EX003_ORIGINAL_PROMPTS: Final[dict[int, str]] = {
    4: "What is your favourite fruit?",
    5: "Tell me your favourite place:",
    6: "Enter your name:",
}

EX003_EXPECTED_ASSIGNMENTS: Final[dict[int, dict[str, str]]] = {
    1: {"greeting": "Hi there!"},
    2: {"subject": "coding"},
    3: {"food": "sushi"},
    7: {"first_word": "Variables", "second_word": "matter"},
    8: {"part1": "Keep", "part2": "experimenting"},
    9: {
        "greeting": "Good",
        "time_of_day": "evening",
        "audience": "everyone!",
    },
}

EX003_EXPECTED_INPUT_VARIABLES: Final[dict[int, tuple[str, str]]] = {
    4: ("fav_fruit", "descriptor"),
    5: ("town", "country"),
    6: ("first_name", "last_name"),
}

EX003_EXERCISE10_REQUIRED_PHRASES: Final[dict[str, str]] = {
    "part_one": "Variables",
    "part_two": "strings",
    "part_three": "message",
}

EX003_MODIFY_STARTER_BASELINES: Final[dict[str, str]] = {
    "exercise1": (
        "# Exercise 1 — YOUR CODE\n"
        "# Modify the greeting assignment below\n"
        "greeting = \"Hello from Python!\"\n"
        "print(greeting)\n"
    ),
    "exercise2": (
        "# Exercise 2 — YOUR CODE\n"
        "# Change the subject variable to a different string\n"
        "subject = \"math\"\n"
        "print(\"I enjoy \" + subject + \" lessons.\")\n"
    ),
    "exercise3": (
        "# Exercise 3 — YOUR CODE\n"
        "# Use a new favourite food below\n"
        "food = \"pasta\"\n"
        "print(\"My favourite food is \" + food)\n"
    ),
    "exercise4": (
        "# Exercise 4 — YOUR CODE\n"
        "# Update the prompt to the new wording and the final message\n"
        "print(\"What is your favourite fruit?\")\n"
        "fruit = input()\n"
        "print(\"My favourite fruit is \" + fruit)"
    ),
    "exercise5": (
        "# Exercise 5 — YOUR CODE\n"
        "# Update the prompt and final message\n"
        "print(\"Tell me your favourite place:\")\n"
        "place = input()\n"
        "print(\"I love visiting \" + place)\n"
    ),
    "exercise6": (
        "# Exercise 6 — YOUR CODE\n"
        "# Update the prompt and the final message\n"
        "print(\"Enter your name:\")\n"
        "name = input()\n"
        "print(\"Hello there, \" + name)\n"
    ),
    "exercise7": (
        "# Exercise 7 — YOUR CODE\n"
        "# Replace the literal strings with input() calls for `first_word` and `second_word`.\n"
        "first_word = \"Learning\"\n"
        "second_word = \"Python\"\n"
        "# e.g., first_word = input(\"Enter first word:\")\n"
        "print(first_word + \" \" + second_word)\n"
    ),
    "exercise8": (
        "# Exercise 8 — YOUR CODE\n"
        "# Use two input() calls to collect an action and an object, then print them.\n"
        "part1 = \"Keep\"\n"
        "part2 = \"coding\"\n"
        "# e.g., part1 = input(\"Enter an action:\")\n"
        "print(part1 + \" \" + part2)\n"
    ),
    "exercise9": (
        "# Exercise 9 — YOUR CODE\n"
        "# Use input() to collect `greeting`, `time_of_day`, and `audience`, then print them together.\n"
        "greeting = \"Good\"\n"
        "time_of_day = \"morning\"\n"
        "audience = \"students\"\n"
        "# e.g., greeting = input(\"Enter a greeting:\")\n"
        "print(greeting + \" \" + time_of_day + \" \" + audience)\n"
    ),
    "exercise10": (
        "# Exercise 10 — YOUR CODE\n"
        "# Collect three parts using input() and then print them joined into a sentence.\n"
        "part_one = \"Python\"\n"
        "part_two = \"strings\"\n"
        "part_three = \"matter\"\n"
        "# e.g., part_one = input(\"Enter part one:\")\n"
        "print(part_one + \" \" + part_two + \" \" + part_three)\n"
    ),
}
