"""Exercise-local expectations for ex007 sequence debug casting."""

from __future__ import annotations

import ast
from typing import Final, TypedDict


class Ex007InputCase(TypedDict):
    inputs: list[str]
    expected_output: str


class Ex007InteractiveConstructs(TypedDict, total=False):
    required_calls: tuple[str, ...]
    required_ops: tuple[type[ast.operator], ...]
    forbidden_ops: tuple[type[ast.operator], ...]


EX007_MIN_EXPLANATION_LENGTH: Final[int] = 50
EX007_PLACEHOLDER_PHRASES: Final[tuple[str, ...]] = (
    "run the code first",
    "explain what happened",
    "describe what happened",
    "after running the buggy code",
    "describe the fault and how you fixed it",
    "todo",
    "...",
)
EX007_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "You have 3 pens",
    2: "Total price: \u00a37.5",
    4: "Average per day: 3.5 km",
}
EX007_INTERACTIVE_CONSTRUCTS: Final[dict[int, Ex007InteractiveConstructs]] = {
    3: {"required_calls": ("int", "str")},
    5: {"required_calls": ("int",), "required_ops": (ast.Mult,)},
    6: {"required_calls": ("float", "str"), "required_ops": (ast.Mult, ast.Div)},
    7: {"required_calls": ("float", "int", "str"), "required_ops": (ast.Mult,)},
    8: {
        "required_calls": ("int", "str"),
        "required_ops": (ast.Add, ast.Div),
        "forbidden_ops": (ast.FloorDiv,),
    },
    9: {"required_calls": ("int", "str"), "required_ops": (ast.Mult, ast.Add)},
    10: {
        "required_calls": ("float", "int", "str"),
        "required_ops": (ast.Add, ast.Mult, ast.Div),
        "forbidden_ops": (ast.FloorDiv,),
    },
}
EX007_INPUT_CASES: Final[dict[int, tuple[Ex007InputCase, ...]]] = {
    3: (
        {"inputs": [
            "14"], "expected_output": "Enter your age: Next year you will be 15"},
        {"inputs": [
            "9"], "expected_output": "Enter your age: Next year you will be 10"},
        {"inputs": [
            "0"], "expected_output": "Enter your age: Next year you will be 1"},
        {"inputs": [
            "41"], "expected_output": "Enter your age: Next year you will be 42"},
    ),
    5: (
        {"inputs": ["hi", "3"],
            "expected_output": "Word to repeat: How many times? hihihi"},
        {"inputs": ["go", "2"],
            "expected_output": "Word to repeat: How many times? gogo"},
        {"inputs": ["z", "5"],
            "expected_output": "Word to repeat: How many times? zzzzz"},
        {"inputs": ["wow", "1"],
            "expected_output": "Word to repeat: How many times? wow"},
    ),
    6: (
        {
            "inputs": ["20"],
            "expected_output": "Enter temperature in Celsius: Temperature in Fahrenheit: 68.0",
        },
        {
            "inputs": ["0"],
            "expected_output": "Enter temperature in Celsius: Temperature in Fahrenheit: 32.0",
        },
        {
            "inputs": ["-40"],
            "expected_output": "Enter temperature in Celsius: Temperature in Fahrenheit: -40.0",
        },
        {
            "inputs": ["37.5"],
            "expected_output": "Enter temperature in Celsius: Temperature in Fahrenheit: 99.5",
        },
    ),
    7: (
        {
            "inputs": ["1.5", "4"],
            "expected_output": "Enter price per item (\u00a3): Enter quantity: Total cost: \u00a36.0",
        },
        {
            "inputs": ["2.5", "4"],
            "expected_output": "Enter price per item (\u00a3): Enter quantity: Total cost: \u00a310.0",
        },
        {
            "inputs": ["3.2", "5"],
            "expected_output": "Enter price per item (\u00a3): Enter quantity: Total cost: \u00a316.0",
        },
        {
            "inputs": ["0.5", "7"],
            "expected_output": "Enter price per item (\u00a3): Enter quantity: Total cost: \u00a33.5",
        },
    ),
    8: (
        {
            "inputs": ["12", "15", "9"],
            "expected_output": "Enter score 1: Enter score 2: Enter score 3: Average score: 12.0",
        },
        {
            "inputs": ["50", "60", "70"],
            "expected_output": "Enter score 1: Enter score 2: Enter score 3: Average score: 60.0",
        },
        {
            "inputs": ["2", "4", "6"],
            "expected_output": "Enter score 1: Enter score 2: Enter score 3: Average score: 4.0",
        },
        {
            "inputs": ["7", "8", "9"],
            "expected_output": "Enter score 1: Enter score 2: Enter score 3: Average score: 8.0",
        },
    ),
    9: (
        {"inputs": ["3", "45"],
            "expected_output": "Pounds: Pence: Total pence: 345"},
        {"inputs": ["4", "50"],
            "expected_output": "Pounds: Pence: Total pence: 450"},
        {"inputs": ["0", "99"],
            "expected_output": "Pounds: Pence: Total pence: 99"},
        {"inputs": ["12", "0"],
            "expected_output": "Pounds: Pence: Total pence: 1200"},
    ),
    10: (
        {
            "inputs": ["20", "4"],
            "expected_output": "Total bill (\u00a3): Number of people: Each person pays: \u00a35.5",
        },
        {
            "inputs": ["120", "4"],
            "expected_output": "Total bill (\u00a3): Number of people: Each person pays: \u00a333.0",
        },
        {
            "inputs": ["30", "2"],
            "expected_output": "Total bill (\u00a3): Number of people: Each person pays: \u00a316.5",
        },
        {
            "inputs": ["10", "4"],
            "expected_output": "Total bill (\u00a3): Number of people: Each person pays: \u00a32.75",
        },
    ),
}
