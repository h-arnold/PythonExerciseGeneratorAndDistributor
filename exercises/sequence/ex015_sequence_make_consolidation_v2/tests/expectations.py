"""Canonical expectations for ex015 sequence make consolidation."""

from __future__ import annotations

from typing import Final, TypedDict


class Ex015InputCase(TypedDict):
    """One concise deterministic input case and its exact transcript."""

    id: str
    inputs: list[str]
    expected_output: str


EX015_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {
    1: "You can make 7 full bags with 1 sweets left over.",
    2: (
        "Wall area: 15 square metres\n"
        "You need 2 cans; 9 square metres of paint will be unused."
    ),
}

# The same catalog drives every pytest case and the student self-check.
# Static parts 1-2 and interactive parts 3-10 never overlap.
EX015_INPUT_CASES: Final[dict[int, tuple[Ex015InputCase, ...]]] = {
    3: (
        {
            "id": "dog-4",
            "inputs": ["4"],
            "expected_output": (
                "How old are you in human years?\n"
                "If you were a dog, you would be 28 years old."
            ),
        },
        {
            "id": "dog-0",
            "inputs": ["0"],
            "expected_output": (
                "How old are you in human years?\n"
                "If you were a dog, you would be 0 years old."
            ),
        },
        {
            "id": "dog-12",
            "inputs": ["12"],
            "expected_output": (
                "How old are you in human years?\n"
                "If you were a dog, you would be 84 years old."
            ),
        },
    ),
    4: (
        {
            "id": "pizza-3-5",
            "inputs": ["3", "5"],
            "expected_output": (
                "Number of pizzas:\n"
                "Number of people:\n"
                "If you ordered 3 pizzas for 5 people:\n"
                "Each person gets 4 slices, with 4 slices left over."
            ),
        },
        {
            "id": "pizza-2-8",
            "inputs": ["2", "8"],
            "expected_output": (
                "Number of pizzas:\n"
                "Number of people:\n"
                "If you ordered 2 pizzas for 8 people:\n"
                "Each person gets 2 slices, with 0 slices left over."
            ),
        },
        {
            "id": "pizza-1-1",
            "inputs": ["1", "1"],
            "expected_output": (
                "Number of pizzas:\n"
                "Number of people:\n"
                "If you ordered 1 pizzas for 1 people:\n"
                "Each person gets 8 slices, with 0 slices left over."
            ),
        },
    ),
    5: (
        {
            "id": "fuel-50-1.45",
            "inputs": ["50", "1.45"],
            "expected_output": (
                "Litres of fuel:\n"
                "Price per litre in pounds:\n"
                "50.0 litres at £1.45 per litre costs £72.5."
            ),
        },
        {
            "id": "fuel-0-1.45",
            "inputs": ["0", "1.45"],
            "expected_output": (
                "Litres of fuel:\n"
                "Price per litre in pounds:\n"
                "0.0 litres at £1.45 per litre costs £0.0."
            ),
        },
    ),
    6: (
        {
            "id": "temp-25",
            "inputs": ["25"],
            "expected_output": "Enter temperature in °C:\n25°C is 77.0°F",
        },
        {
            "id": "temp-0",
            "inputs": ["0"],
            "expected_output": "Enter temperature in °C:\n0°C is 32.0°F",
        },
        {
            "id": "temp-negative-10",
            "inputs": ["-10"],
            "expected_output": "Enter temperature in °C:\n-10°C is 14.0°F",
        },
    ),
    7: (
        {
            "id": "save-350-50",
            "inputs": ["350", "50"],
            "expected_output": (
                "What is your savings goal in pounds?\n"
                "How much can you save each week in pounds?\n"
                "Saving £50 per week towards a £350 goal:\n"
                "It will take 7 full weeks, with £0 left to save."
            ),
        },
        {
            "id": "save-100-30",
            "inputs": ["100", "30"],
            "expected_output": (
                "What is your savings goal in pounds?\n"
                "How much can you save each week in pounds?\n"
                "Saving £30 per week towards a £100 goal:\n"
                "It will take 3 full weeks, with £10 left to save."
            ),
        },
        {
            "id": "save-200-40",
            "inputs": ["200", "40"],
            "expected_output": (
                "What is your savings goal in pounds?\n"
                "How much can you save each week in pounds?\n"
                "Saving £40 per week towards a £200 goal:\n"
                "It will take 5 full weeks, with £0 left to save."
            ),
        },
    ),
    8: (
        {
            "id": "garden-5",
            "inputs": ["5"],
            "expected_output": (
                "Side length of the square garden in metres:\n"
                "A square garden with side 5m has area 25 square metres.\n"
                "A garden with double the area would have side 7.07m."
            ),
        },
        {
            "id": "garden-10",
            "inputs": ["10"],
            "expected_output": (
                "Side length of the square garden in metres:\n"
                "A square garden with side 10m has area 100 square metres.\n"
                "A garden with double the area would have side 14.14m."
            ),
        },
        {
            "id": "garden-1",
            "inputs": ["1"],
            "expected_output": (
                "Side length of the square garden in metres:\n"
                "A square garden with side 1m has area 1 square metres.\n"
                "A garden with double the area would have side 1.41m."
            ),
        },
    ),
    9: (
        {
            "id": "bill-50-10-4",
            "inputs": ["50", "10", "4"],
            "expected_output": (
                "Total bill amount in £:\n"
                "Tip percentage (e.g. 10 for 10%):\n"
                "Number of people sharing:\n"
                "Total bill: £50.0\n"
                "Tip (10%): £5.0\n"
                "Total with tip: £55.0\n"
                "Each of 4 people pays: £13.75"
            ),
        },
        {
            "id": "bill-20-15-2",
            "inputs": ["20", "15", "2"],
            "expected_output": (
                "Total bill amount in £:\n"
                "Tip percentage (e.g. 10 for 10%):\n"
                "Number of people sharing:\n"
                "Total bill: £20.0\n"
                "Tip (15%): £3.0\n"
                "Total with tip: £23.0\n"
                "Each of 2 people pays: £11.5"
            ),
        },
        {
            "id": "bill-100-0-1",
            "inputs": ["100", "0", "1"],
            "expected_output": (
                "Total bill amount in £:\n"
                "Tip percentage (e.g. 10 for 10%):\n"
                "Number of people sharing:\n"
                "Total bill: £100.0\n"
                "Tip (0%): £0.0\n"
                "Total with tip: £100.0\n"
                "Each of 1 people pays: £100.0"
            ),
        },
    ),
    10: (
        {
            "id": "supplies-30-3-2",
            "inputs": ["30", "3", "2"],
            "expected_output": (
                "Number of students:\n"
                "Pencils needed per student:\n"
                "Erasers needed per student:\n"
                "For 30 students:\n"
                "Each student needs 3 pencils and 2 erasers.\n"
                "Order 4 packs of pencils (24 per pack) — 6 pencils will be left over.\n"
                "Order 4 packs of erasers (15 per pack) — 0 erasers will be left over."
            ),
        },
        {
            "id": "supplies-15-2-1",
            "inputs": ["15", "2", "1"],
            "expected_output": (
                "Number of students:\n"
                "Pencils needed per student:\n"
                "Erasers needed per student:\n"
                "For 15 students:\n"
                "Each student needs 2 pencils and 1 erasers.\n"
                "Order 2 packs of pencils (24 per pack) — 18 pencils will be left over.\n"
                "Order 1 packs of erasers (15 per pack) — 0 erasers will be left over."
            ),
        },
        {
            "id": "supplies-1-1-1",
            "inputs": ["1", "1", "1"],
            "expected_output": (
                "Number of students:\n"
                "Pencils needed per student:\n"
                "Erasers needed per student:\n"
                "For 1 students:\n"
                "Each student needs 1 pencils and 1 erasers.\n"
                "Order 1 packs of pencils (24 per pack) — 23 pencils will be left over.\n"
                "Order 1 packs of erasers (15 per pack) — 14 erasers will be left over."
            ),
        },
    ),
}

# Gate G requires a complete catalog. Interactive values remain classified only
# in EX015_INPUT_CASES; this derived view is not a second static declaration.
EX015_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    **EX015_EXPECTED_STATIC_OUTPUTS,
    **{
        exercise_no: cases[0]["expected_output"]
        for exercise_no, cases in EX015_INPUT_CASES.items()
    },
}
