"""Shared expectations for notebook exercises."""

from __future__ import annotations

from typing import Final, NotRequired, TypedDict

EX001_NOTEBOOK_PATH: Final[str] = "notebooks/ex001_sanity.ipynb"
EX001_TAG: Final[str] = "exercise1"
EX001_FUNCTION_NAME: Final[str] = "example"

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

EX004_NOTEBOOK_PATH: Final[str] = "notebooks/ex004_sequence_debug_syntax.ipynb"
EX004_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX004_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what",
    "describe briefly",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
    "test it by",
    "verifying it works",
    "include any error",
)
EX004_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "Hello World!",
    2: "I like Python",
    3: "Learning Python",
    4: "50",
    5: "Hello Alice",
    6: "Welcome to school",
    9: "It's amazing",
}
EX004_PROMPT_STRINGS: Final[dict[int, str]] = {
    7: "How many apples?",
    8: "Enter your name:",
    10: "What is your favourite colour?",
}
EX004_FORMAT_VALIDATION: Final[dict[int, str]] = {
    7: "You have 10 apples in total",
    8: "Hello Alice",
    10: "My favourite colour is Blue",
}

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

EX006_NOTEBOOK_PATH: Final[str] = "notebooks/ex006_sequence_modify_casting.ipynb"
EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "15\n",
    2: "6.0\n",
    3: "28\n",
    4: "Your score is 500\n",
    5: "25\n",
    8: "Area: 50\n",
    9: "The Burger costs £5.5\n",
}


class Ex006InputExpectation(TypedDict):
    """Expectations for exercises that prompt for input in ex006."""

    inputs: list[str]
    prompt_contains: str
    output_contains: NotRequired[str]
    last_line: NotRequired[str]


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


def is_valid_explanation(
    text: str,
    *,
    min_length: int,
    placeholder_phrases: tuple[str, ...],
) -> bool:
    """Return True when an explanation is long enough and not a placeholder."""
    stripped = text.strip().lower()
    if len(stripped) < min_length:
        return False
    return not any(phrase in stripped for phrase in placeholder_phrases)
