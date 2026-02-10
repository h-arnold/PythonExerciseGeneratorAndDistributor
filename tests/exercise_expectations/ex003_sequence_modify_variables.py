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
