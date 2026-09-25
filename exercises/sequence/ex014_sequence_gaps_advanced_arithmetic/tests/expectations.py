"""Canonical expectations for ex014 sequence gaps advanced arithmetic."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex014InputCase(TypedDict):
    """One deterministic input and exact transcript for an interactive exercise."""

    id: str
    inputs: list[str]
    expected_output: str


EX014_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "The square of 8 is 64",
    2: "The cube of 6 is 216",
}

# This is the single source of truth for pytest and the student self-check. The
# first case matches the notebook example; later cases prevent canned transcripts.
EX014_INPUT_CASES: Final[dict[int, tuple[Ex014InputCase, ...]]] = {
    3: (
        {
            "id": "shown-example-144",
            "inputs": ["144"],
            "expected_output": "Enter a number: The square root of 144 is 12.0",
        },
        {
            "id": "zero",
            "inputs": ["0"],
            "expected_output": "Enter a number: The square root of 0 is 0.0",
        },
        {
            "id": "one",
            "inputs": ["1"],
            "expected_output": "Enter a number: The square root of 1 is 1.0",
        },
        {
            "id": "twenty-five",
            "inputs": ["25"],
            "expected_output": "Enter a number: The square root of 25 is 5.0",
        },
    ),
    4: (
        {
            "id": "shown-example-two-ten",
            "inputs": ["2", "10"],
            "expected_output": "Enter the base: Enter the exponent: 2 to the power of 10 is 1024",
        },
        {
            "id": "three-four",
            "inputs": ["3", "4"],
            "expected_output": "Enter the base: Enter the exponent: 3 to the power of 4 is 81",
        },
        {
            "id": "five-two",
            "inputs": ["5", "2"],
            "expected_output": "Enter the base: Enter the exponent: 5 to the power of 2 is 25",
        },
        {
            "id": "five-zero",
            "inputs": ["5", "0"],
            "expected_output": "Enter the base: Enter the exponent: 5 to the power of 0 is 1",
        },
    ),
    5: (
        {
            "id": "shown-example-nine",
            "inputs": ["9"],
            "expected_output": "Enter the side length: A square with side 9 has area 81.0",
        },
        {
            "id": "three",
            "inputs": ["3"],
            "expected_output": "Enter the side length: A square with side 3 has area 9.0",
        },
        {
            "id": "decimal-two-point-five",
            "inputs": ["2.5"],
            "expected_output": "Enter the side length: A square with side 2.5 has area 6.25",
        },
    ),
    6: (
        {
            "id": "shown-example-five-three",
            "inputs": ["5", "3"],
            "expected_output": "Enter the width: Enter the length: The area of the rectangle is 15.0",
        },
        {
            "id": "seven-two",
            "inputs": ["7", "2"],
            "expected_output": "Enter the width: Enter the length: The area of the rectangle is 14.0",
        },
        {
            "id": "decimal-one-point-five-four",
            "inputs": ["1.5", "4"],
            "expected_output": "Enter the width: Enter the length: The area of the rectangle is 6.0",
        },
    ),
    7: (
        {
            "id": "shown-example-four",
            "inputs": ["4"],
            "expected_output": "Enter the side length: The volume of the cube is 64.0",
        },
        {
            "id": "two",
            "inputs": ["2"],
            "expected_output": "Enter the side length: The volume of the cube is 8.0",
        },
        {
            "id": "ten",
            "inputs": ["10"],
            "expected_output": "Enter the side length: The volume of the cube is 1000.0",
        },
    ),
    8: (
        {
            "id": "shown-example-144",
            "inputs": ["144"],
            "expected_output": "Enter a whole number: The square root of 144 is 12.0",
        },
        {
            "id": "zero",
            "inputs": ["0"],
            "expected_output": "Enter a whole number: The square root of 0 is 0.0",
        },
        {
            "id": "one",
            "inputs": ["1"],
            "expected_output": "Enter a whole number: The square root of 1 is 1.0",
        },
        {
            "id": "one-hundred",
            "inputs": ["100"],
            "expected_output": "Enter a whole number: The square root of 100 is 10.0",
        },
    ),
    9: (
        {
            "id": "shown-example-five",
            "inputs": ["5"],
            "expected_output": "Enter the radius: The area of the circle is 78.53975",
        },
        {
            "id": "one",
            "inputs": ["1"],
            "expected_output": "Enter the radius: The area of the circle is 3.14159",
        },
        {
            "id": "ten",
            "inputs": ["10"],
            "expected_output": "Enter the radius: The area of the circle is 314.159",
        },
        {
            "id": "zero",
            "inputs": ["0"],
            "expected_output": "Enter the radius: The area of the circle is 0.0",
        },
    ),
    10: (
        {
            "id": "shown-example-two-ten",
            "inputs": ["2", "10"],
            "expected_output": "Enter the base: Enter the exponent: 2 to the power of 10 is 1024",
        },
        {
            "id": "one-one",
            "inputs": ["1", "1"],
            "expected_output": "Enter the base: Enter the exponent: 1 to the power of 1 is 1",
        },
        {
            "id": "seven-three",
            "inputs": ["7", "3"],
            "expected_output": "Enter the base: Enter the exponent: 7 to the power of 3 is 343",
        },
        {
            "id": "three-zero",
            "inputs": ["3", "0"],
            "expected_output": "Enter the base: Enter the exponent: 3 to the power of 0 is 1",
        },
    ),
}

# Gate G requires a complete output catalog. Interactive values remain classified
# only in INPUT_CASES and are copied here from each primary deterministic case.
EX014_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX014_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX014_INPUT_CASES.items()
    },
}
