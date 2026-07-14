"""Exercise-local expectations for ex003_selection_modify_elif_boundaries."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex003InputCase(TypedDict):
    """Input case for an exercise that uses input()."""

    inputs: list[str]
    expected_output: str


# ---------------------------------------------------------------------------
# Primary input cases — used by both the pytest suite and the student checker
# ---------------------------------------------------------------------------

EX003_INPUT_CASES: Final[dict[int, Ex003InputCase]] = {
    # Ex 1–3: pure refactors — output must stay the same.
    1: {
        "inputs": ["25"],
        "expected_output": "Enter your total spend: Standard delivery for £25 order",
    },
    2: {
        "inputs": ["1"],
        "expected_output": "How many passengers? Small van for 1 passengers",
    },
    3: {
        "inputs": ["60", "40"],
        "expected_output": "Enter first number: Enter second number: The total 100 is large",
    },
    # Ex 4–10: constant / operator / message changes.
    4: {
        "inputs": ["35"],
        "expected_output": "Enter your score: Try again! Score 35 is a fail",
    },
    5: {
        "inputs": ["150"],
        "expected_output": "Enter minutes studied: Amazing! You studied 2 hours",
    },
    6: {
        "inputs": ["26"],
        "expected_output": "Enter temperature: It is a heatwave! 26°C",
    },
    7: {
        "inputs": ["36"],
        "expected_output": "Enter number of items: Medium order: 3 boxes, 6 leftover",
    },
    8: {
        "inputs": ["130"],
        "expected_output": "Enter spend: You saved £13 with 10% off",
    },
    9: {
        # Average 73.0: Grade B under the new GRADE_B=70 threshold, but Grade C
        # under the old GRADE_B=75 threshold — so this input distinguishes the
        # edited solution from the unedited starter.
        "inputs": ["73", "73", "73"],
        "expected_output": "Score 1: Score 2: Score 3: Grade B: 73.0",
    },
    10: {
        "inputs": ["30", "4"],
        "expected_output": "Enter base price: Enter quantity: Bulk order, cost £132",
    },
}


# ---------------------------------------------------------------------------
# Primary expected outputs — keyed by exercise number, used by the quality
# verifier (Gate G) and as a quick reference. The full input cases live in
# EX003_INPUT_CASES above; every exercise in ex003 is interactive.
# ---------------------------------------------------------------------------

EX003_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    exercise_no: case["expected_output"]
    for exercise_no, case in EX003_INPUT_CASES.items()
}


# ---------------------------------------------------------------------------
# Edge-case input cases — used by the pytest suite for broader coverage
# ---------------------------------------------------------------------------

EX003_EDGE_CASES: Final[dict[int, list[Ex003InputCase]]] = {
    # Ex 1–3 edge cases deliberately probe the new boundary operators (>= / <=)
    # at their exact threshold values as well as just outside them.
    1: [
        {
            "inputs": ["55"],
            "expected_output": "Enter your total spend: Free delivery! Your total is £55",
        },
        {
            "inputs": ["50"],
            "expected_output": "Enter your total spend: Free delivery! Your total is £50",
        },
        {
            "inputs": ["20"],
            "expected_output": "Enter your total spend: Standard delivery for £20 order",
        },
        {
            "inputs": ["10"],
            "expected_output": "Enter your total spend: Small order: £10",
        },
    ],
    2: [
        {
            "inputs": ["4"],
            "expected_output": "How many passengers? Small van for 4 passengers",
        },
        {
            "inputs": ["8"],
            "expected_output": "How many passengers? Minibus for 8 passengers",
        },
        {
            "inputs": ["9"],
            "expected_output": "How many passengers? Coach for 9 passengers",
        },
    ],
    3: [
        {
            "inputs": ["100", "0"],
            "expected_output": "Enter first number: Enter second number: The total 100 is large",
        },
        {
            "inputs": ["50", "0"],
            "expected_output": "Enter first number: Enter second number: The total 50 is medium",
        },
        {
            "inputs": ["49", "0"],
            "expected_output": "Enter first number: Enter second number: The total 49 is small",
        },
    ],
    4: [
        {
            "inputs": ["40"],
            "expected_output": "Enter your score: Well done! Score 40 is a pass",
        },
        {
            "inputs": ["39"],
            "expected_output": "Enter your score: Try again! Score 39 is a fail",
        },
        {
            "inputs": ["45"],
            "expected_output": "Enter your score: Well done! Score 45 is a pass",
        },
    ],
    5: [
        {
            "inputs": ["120"],
            "expected_output": "Enter minutes studied: Amazing! You studied 2 hours",
        },
        {
            "inputs": ["60"],
            "expected_output": "Enter minutes studied: Keep going — you studied 1 hours",
        },
    ],
    6: [
        {"inputs": ["25"], "expected_output": "Enter temperature: It is a heatwave! 25°C"},
        {"inputs": ["15"], "expected_output": "Enter temperature: Mild. 15°C"},
        {"inputs": ["10"], "expected_output": "Enter temperature: Cold. 10°C"},
    ],
    7: [
        {
            "inputs": ["12"],
            "expected_output": "Enter number of items: Small order: 1 box(es), 2 leftover",
        },
        {
            "inputs": ["37"],
            "expected_output": "Enter number of items: Large order: 3 boxes",
        },
    ],
    8: [
        {
            "inputs": ["80"],
            "expected_output": "Enter spend: You saved £4 with 5% off",
        },
        {"inputs": ["25"], "expected_output": "Enter spend: Free gift at £25"},
        {"inputs": ["10"], "expected_output": "Enter spend: No offer at £10"},
    ],
    9: [
        {
            "inputs": ["85", "85", "85"],
            "expected_output": "Score 1: Score 2: Score 3: Grade A: 85.0",
        },
        {
            "inputs": ["70", "70", "70"],
            "expected_output": "Score 1: Score 2: Score 3: Grade B: 70.0",
        },
        {
            "inputs": ["90", "88", "82"],
            "expected_output": "Score 1: Score 2: Score 3: Grade A: 86.7",
        },
        {
            "inputs": ["65", "72", "58"],
            "expected_output": "Score 1: Score 2: Score 3: Grade C: 65.0",
        },
    ],
    10: [
        {
            "inputs": ["2", "10"],
            "expected_output": "Enter base price: Enter quantity: Medium order, cost £22",
        },
        {
            "inputs": ["5", "10"],
            "expected_output": "Enter base price: Enter quantity: Large order, cost £55",
        },
        {
            "inputs": ["11", "10"],
            "expected_output": "Enter base price: Enter quantity: Bulk order, cost £121",
        },
        {
            "inputs": ["20", "10"],
            "expected_output": "Enter base price: Enter quantity: Bulk order, cost £220",
        },
        {
            "inputs": ["50", "6"],
            "expected_output": "Enter base price: Enter quantity: Wholesale order, cost £330",
        },
    ],
}
