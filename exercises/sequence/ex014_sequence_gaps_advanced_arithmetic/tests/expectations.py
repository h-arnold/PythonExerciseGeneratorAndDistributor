"""Exercise-local expectations for ex014_sequence_gaps_advanced_arithmetic."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex014InputCase(TypedDict):
    """Deterministic input/output case for an interactive exercise."""

    inputs: list[str]
    expected_output: str


EX014_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "The square of 8 is 64",
    2: "The cube of 6 is 216",
}

EX014_INPUT_CASES: Final[dict[int, Ex014InputCase]] = {
    3: {
        "inputs": ["144"],
        "expected_output": "Enter a number: The square root of 144 is 12.0",
    },
    4: {
        "inputs": ["2", "10"],
        "expected_output": "Enter the base: Enter the exponent: 2 to the power of 10 is 1024",
    },
    5: {
        "inputs": ["9"],
        "expected_output": "Enter the side length: A square with side 9 has area 81.0",
    },
    6: {
        "inputs": ["5", "3"],
        "expected_output": "Enter the width: Enter the length: The area of the rectangle is 15.0",
    },
    7: {
        "inputs": ["4"],
        "expected_output": "Enter the side length: The volume of the cube is 64.0",
    },
    8: {
        "inputs": ["144"],
        "expected_output": "Enter a whole number: The square root of 144 is 12.0",
    },
    9: {
        "inputs": ["5"],
        "expected_output": "Enter the radius: The area of the circle is 78.53975",
    },
    10: {
        "inputs": ["2", "10"],
        "expected_output": "Enter the base: Enter the exponent: 2 to the power of 10 is 1024",
    },
}

# Additional edge cases for exercises that accept varied inputs
EX014_EDGE_CASES: Final[dict[int, list[Ex014InputCase]]] = {
    3: [
        {"inputs": [
            "0"], "expected_output": "Enter a number: The square root of 0 is 0.0"},
        {"inputs": [
            "1"], "expected_output": "Enter a number: The square root of 1 is 1.0"},
        {"inputs": [
            "25"], "expected_output": "Enter a number: The square root of 25 is 5.0"},
    ],
    4: [
        {"inputs": [
            "3", "4"], "expected_output": "Enter the base: Enter the exponent: 3 to the power of 4 is 81"},
        {"inputs": [
            "5", "2"], "expected_output": "Enter the base: Enter the exponent: 5 to the power of 2 is 25"},
    ],
    5: [
        {"inputs": [
            "3"], "expected_output": "Enter the side length: A square with side 3 has area 9.0"},
        {"inputs": [
            "2.5"], "expected_output": "Enter the side length: A square with side 2.5 has area 6.25"},
    ],
    6: [
        {"inputs": [
            "7", "2"], "expected_output": "Enter the width: Enter the length: The area of the rectangle is 14.0"},
        {"inputs": ["1.5", "4"], "expected_output":
            "Enter the width: Enter the length: The area of the rectangle is 6.0"},
    ],
    7: [
        {"inputs": [
            "2"], "expected_output": "Enter the side length: The volume of the cube is 8.0"},
        {"inputs": [
            "10"], "expected_output": "Enter the side length: The volume of the cube is 1000.0"},
    ],
    8: [
        {"inputs": [
            "0"], "expected_output": "Enter a whole number: The square root of 0 is 0.0"},
        {"inputs": [
            "1"], "expected_output": "Enter a whole number: The square root of 1 is 1.0"},
        {"inputs": [
            "100"], "expected_output": "Enter a whole number: The square root of 100 is 10.0"},
    ],
    9: [
        {"inputs": [
            "1"], "expected_output": "Enter the radius: The area of the circle is 3.14159"},
        {"inputs": [
            "10"], "expected_output": "Enter the radius: The area of the circle is 314.159"},
    ],
    10: [
        {"inputs": [
            "1", "1"], "expected_output": "Enter the base: Enter the exponent: 1 to the power of 1 is 1"},
        {"inputs": [
            "7", "3"], "expected_output": "Enter the base: Enter the exponent: 7 to the power of 3 is 343"},
    ],
}
