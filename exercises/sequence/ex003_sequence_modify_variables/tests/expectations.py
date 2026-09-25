"""Canonical expectations for ex003 sequence modify variables."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex003InputCase(TypedDict):
    """Deterministic input and exact output for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX003_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "Hi there!",
    2: "I enjoy coding lessons.",
    3: "My favourite food is sushi",
    7: "Variables matter",
    8: "Keep experimenting",
    9: "Good evening everyone!",
    10: "Variables and strings make a message!",
}

# These cases are the single source of truth for Exercises 4-6.  The pytest
# suite and the specialised student checker both execute these exact inputs and
# compare the complete captured transcript, including prompts and punctuation.
EX003_INPUT_CASES: Final[dict[int, Ex003InputCase]] = {
    4: {
        "inputs": ["mango", "tropical"],
        "expected_output": (
            "Type the name of your favourite fruit:\n"
            "Type one word to describe it:\n"
            "I like mango because it is tropical"
        ),
    },
    5: {
        "inputs": ["Cardiff", "Wales"],
        "expected_output": (
            "Which town do you like the most?\n"
            "Which country is it in?\n"
            "I would visit Cardiff in Wales"
        ),
    },
    6: {
        "inputs": ["Alex", "Morgan"],
        "expected_output": (
            "Please enter your first name:\n"
            "Please enter your last name:\n"
            "Welcome, Alex Morgan!"
        ),
    },
}

# A second deterministic case per interactive exercise makes the tests exercise
# the data flow rather than merely check one hard-coded transcript.
EX003_INPUT_EDGE_CASES: Final[dict[int, Ex003InputCase]] = {
    4: {
        "inputs": ["dragonfruit", "sweet"],
        "expected_output": (
            "Type the name of your favourite fruit:\n"
            "Type one word to describe it:\n"
            "I like dragonfruit because it is sweet"
        ),
    },
    5: {
        "inputs": ["Newport", "Wales"],
        "expected_output": (
            "Which town do you like the most?\n"
            "Which country is it in?\n"
            "I would visit Newport in Wales"
        ),
    },
    6: {
        "inputs": ["Jess", "Jones"],
        "expected_output": (
            "Please enter your first name:\n"
            "Please enter your last name:\n"
            "Welcome, Jess Jones!"
        ),
    },
}

# A third case uses values that do not appear in the documented transcripts.
# It catches output that only works for the two example fixtures.
EX003_INPUT_SEMANTIC_CASES: Final[dict[int, Ex003InputCase]] = {
    4: {
        "inputs": ["pomelo", "zesty"],
        "expected_output": (
            "Type the name of your favourite fruit:\n"
            "Type one word to describe it:\n"
            "I like pomelo because it is zesty"
        ),
    },
    5: {
        "inputs": ["Bristol", "England"],
        "expected_output": (
            "Which town do you like the most?\n"
            "Which country is it in?\n"
            "I would visit Bristol in England"
        ),
    },
    6: {
        "inputs": ["Amina", "Khan"],
        "expected_output": (
            "Please enter your first name:\n"
            "Please enter your last name:\n"
            "Welcome, Amina Khan!"
        ),
    },
}

# Complete output catalog for tooling.  It is derived from the two source-of-truth
# maps above; interactive cases are not classified as static outputs.
EX003_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX003_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: case["expected_output"]
        for exercise_no, case in EX003_INPUT_CASES.items()
    },
}

EX003_EXPECTED_PROMPTS: Final[dict[int, list[str]]] = {
    4: [
        "Type the name of your favourite fruit:",
        "Type one word to describe it:",
    ],
    5: [
        "Which town do you like the most?",
        "Which country is it in?",
    ],
    6: [
        "Please enter your first name:",
        "Please enter your last name:",
    ],
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

EX003_ORIGINAL_MESSAGES: Final[dict[int, str]] = {
    4: "My favourite fruit is ",
    5: "I love visiting ",
    6: "Hello there, ",
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

EX003_EXERCISE10_REQUIRED_PHRASES: Final[dict[str, str]] = {
    "part_one": "Variables",
    "part_two": "strings",
    "part_three": "message",
}
