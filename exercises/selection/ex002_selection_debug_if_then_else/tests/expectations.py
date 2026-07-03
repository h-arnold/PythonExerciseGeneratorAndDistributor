"""Exercise-local expectations for ex002_selection_debug_if_then_else."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex002InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX002_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX002_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "describe what",
    "describe briefly",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
    "include any error",
)


# Expected output for every exercise (including prompt text from input()).
# All 20 exercises use input(), so expected_output includes the prompt
# followed immediately by the program's printed message.
EX002_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "Enter a number: Odd number!",
    2: "Enter the radius: Area exceeds 100!",
    3: "Enter a number: Divisible by 3!",
    4: "Enter a number: Square is greater than 1000!",
    5: "What is your favourite colour? Nice choice!",
    6: "Enter your PIN: Wrong PIN!",
    7: "What is 3 + 5? Correct answer!",
    8: "Enter your height in cm: You can ride!",
    9: "Enter your score: You passed!",
    10: "Enter your name: Hello Bob!",
    11: "Enter your score: Distinction",
    12: "Enter your age: Child",
    13: "Enter a number: Positive",
    14: "Enter the password: Correct password!",
    15: "Enter the temperature: It's hot!",
    16: "Enter a number: Odd number",
    17: "Enter your age: Invalid age",
    18: "Enter your score: Excellent score",
    19: "Enter a number: Number is 10 or greater",
    20: "Enter your score: You passed!",
}

# Input cases for every exercise (all exercises use input()).
EX002_INPUT_CASES: Final[dict[int, Ex002InputCase]] = {
    1: {
        "inputs": ["7"],
        "expected_output": "Enter a number: Odd number!",
    },
    2: {
        "inputs": ["6"],
        "expected_output": "Enter the radius: Area exceeds 100!",
    },
    3: {
        "inputs": ["9"],
        "expected_output": "Enter a number: Divisible by 3!",
    },
    4: {
        "inputs": ["35"],
        "expected_output": "Enter a number: Square is greater than 1000!",
    },
    5: {
        "inputs": ["blue"],
        "expected_output": "What is your favourite colour? Nice choice!",
    },
    6: {
        "inputs": ["5678"],
        "expected_output": "Enter your PIN: Wrong PIN!",
    },
    7: {
        "inputs": ["8"],
        "expected_output": "What is 3 + 5? Correct answer!",
    },
    8: {
        "inputs": ["140"],
        "expected_output": "Enter your height in cm: You can ride!",
    },
    9: {
        "inputs": ["60"],
        "expected_output": "Enter your score: You passed!",
    },
    10: {
        "inputs": ["Bob"],
        "expected_output": "Enter your name: Hello Bob!",
    },
    11: {
        "inputs": ["90"],
        "expected_output": "Enter your score: Distinction",
    },
    12: {
        "inputs": ["12"],
        "expected_output": "Enter your age: Child",
    },
    13: {
        "inputs": ["5"],
        "expected_output": "Enter a number: Positive",
    },
    14: {
        "inputs": ["python"],
        "expected_output": "Enter the password: Correct password!",
    },
    15: {
        "inputs": ["35"],
        "expected_output": "Enter the temperature: It's hot!",
    },
    16: {
        "inputs": ["7"],
        "expected_output": "Enter a number: Odd number",
    },
    17: {
        "inputs": ["-5"],
        "expected_output": "Enter your age: Invalid age",
    },
    18: {
        "inputs": ["95"],
        "expected_output": "Enter your score: Excellent score",
    },
    19: {
        "inputs": ["10"],
        "expected_output": "Enter a number: Number is 10 or greater",
    },
    20: {
        "inputs": ["75"],
        "expected_output": "Enter your score: You passed!",
    },
}
