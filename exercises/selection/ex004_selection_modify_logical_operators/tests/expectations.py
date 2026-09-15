"""Exercise-local expectations for ex004_selection_modify_logical_operators."""
from __future__ import annotations

from typing import Final, TypedDict


class Ex004InputCase(TypedDict):
    """Input case for an exercise that uses input()."""

    inputs: list[str]
    expected_output: str


# ---------------------------------------------------------------------------
# Primary input cases — used by both the pytest suite and the student checker.
# Every exercise in ex004 is interactive and its starter diverges from the
# solution on the primary input (the key operator/message change), so each
# output check fails on the unedited student notebook.
# ---------------------------------------------------------------------------

EX004_INPUT_CASES: Final[dict[int, Ex004InputCase]] = {
    1: {
        "inputs": ["20"],
        "expected_output": "Enter your age: Out of range: age 20 does not fit",
    },
    2: {
        "inputs": ["Sunday"],
        "expected_output": "Enter the day: Weekend! Sunday is a lie-in day",
    },
    3: {
        "inputs": ["55", "60"],
        "expected_output": (
            "Enter your score: Enter your attendance: "
            "Well done! Score 55, attendance 60% is a pass"
        ),
    },
    4: {
        "inputs": ["30"],
        "expected_output": "Enter your score: Not a pass yet: score 30",
    },
    5: {
        "inputs": ["30"],
        "expected_output": "Enter temperature: Uncomfortable: 30°C is not ideal",
    },
    6: {
        "inputs": ["67"],
        "expected_output": "Enter your age: Free museum entry for age 67",
    },
    7: {
        "inputs": ["70", "60"],
        "expected_output": (
            "Enter first number: Enter second number: "
            "Outside the gold band: total 130"
        ),
    },
    8: {
        "inputs": ["12", "yes"],
        "expected_output": (
            "Enter your age: Are you scared of the dark? (yes/no): "
            "Maybe later. Age 12, scared yes"
        ),
    },
    9: {
        # membership alone is no longer enough — starter greets a member who
        # qualifies for neither extra, so the primary case diverges.
        "inputs": ["yes", "10", "20"],
        "expected_output": (
            "Are you a member? (yes/no): Enter your spend: Enter your age: "
            "Full price. Spend £10, age 20"
        ),
    },
    10: {
        # films 6 → points 30, a tenth off (3) → £27, whereas the starter
        # prints the undiscounted £30.
        "inputs": ["6", "20"],
        "expected_output": (
            "How many films this month? Enter your age: Gold member: £27 for age 20"
        ),
    },
}


# ---------------------------------------------------------------------------
# Primary expected outputs — keyed by exercise number, used by the quality
# verifier (Gate G) and as a quick reference. The full input cases live in
# EX004_INPUT_CASES above; every exercise in ex004 is interactive.
#
# Named EX004_DERIVED_OUTPUTS rather than EX004_EXPECTED_OUTPUTS because it is
# derived directly from EX004_INPUT_CASES (nothing is listed twice): the
# Gate G scan still accepts any EX<N>…_OUTPUTS dict, and the gate that checks
# static/interactive classification skips dicts whose names contain DERIVED.
# ---------------------------------------------------------------------------

EX004_DERIVED_OUTPUTS: Final[dict[int, str]] = {
    exercise_no: case["expected_output"]
    for exercise_no, case in EX004_INPUT_CASES.items()
}


# ---------------------------------------------------------------------------
# Edge-case input cases — probe the new operators at their boundaries
# ---------------------------------------------------------------------------

EX004_EDGE_CASES: Final[dict[int, list[Ex004InputCase]]] = {
    # Ex 1: both ends of the 11–16 range matter, not just the lower bound.
    1: [
        {"inputs": ["11"], "expected_output": "Enter your age: In range: age 11 fits the club"},
        {"inputs": ["16"], "expected_output": "Enter your age: In range: age 16 fits the club"},
        {"inputs": ["10"], "expected_output": "Enter your age: Out of range: age 10 does not fit"},
        {"inputs": ["17"], "expected_output": "Enter your age: Out of range: age 17 does not fit"},
    ],
    2: [
        {"inputs": ["Saturday"], "expected_output": "Enter the day: Weekend! Saturday is a lie-in day"},
        {"inputs": ["Monday"], "expected_output": "Enter the day: School day. Monday needs an early start"},
    ],
    # Ex 3: either check alone is now enough — probe each side on its own.
    3: [
        {
            "inputs": ["40", "90"],
            "expected_output": (
                "Enter your score: Enter your attendance: "
                "Well done! Score 40, attendance 90% is a pass"
            ),
        },
        {
            "inputs": ["40", "60"],
            "expected_output": (
                "Enter your score: Enter your attendance: "
                "Keep trying! Score 40, attendance 60% is not a pass yet"
            ),
        },
        {
            "inputs": ["50", "0"],
            "expected_output": (
                "Enter your score: Enter your attendance: "
                "Well done! Score 50, attendance 0% is a pass"
            ),
        },
        {
            "inputs": ["0", "80"],
            "expected_output": (
                "Enter your score: Enter your attendance: "
                "Well done! Score 0, attendance 80% is a pass"
            ),
        },
    ],
    # Ex 4: `not (score >= 50)` keeps the 50 boundary team-blind either way.
    4: [
        {"inputs": ["50"], "expected_output": "Enter your score: A pass! Score 50"},
        {"inputs": ["49"], "expected_output": "Enter your score: Not a pass yet: score 49"},
    ],
    # Ex 5: comfortable band is 15–25 inclusive.
    5: [
        {"inputs": ["20"], "expected_output": "Enter temperature: Comfortable: 20°C is just right"},
        {"inputs": ["15"], "expected_output": "Enter temperature: Comfortable: 15°C is just right"},
        {"inputs": ["25"], "expected_output": "Enter temperature: Comfortable: 25°C is just right"},
        {"inputs": ["26"], "expected_output": "Enter temperature: Uncomfortable: 26°C is not ideal"},
        {"inputs": ["14"], "expected_output": "Enter temperature: Uncomfortable: 14°C is not ideal"},
    ],
    # Ex 6: under-5s and over-65s are free (age < 5 or age >= 65); 5–64 pay.
    6: [
        {"inputs": ["5"], "expected_output": "Enter your age: Please pay for age 5"},
        {"inputs": ["4"], "expected_output": "Enter your age: Free museum entry for age 4"},
        {"inputs": ["65"], "expected_output": "Enter your age: Free museum entry for age 65"},
        {"inputs": ["64"], "expected_output": "Enter your age: Please pay for age 64"},
    ],
    # Ex 7: gold band is 60–120 inclusive.
    7: [
        {
            "inputs": ["30", "30"],
            "expected_output": "Enter first number: Enter second number: In the gold band: total 60",
        },
        {
            "inputs": ["60", "60"],
            "expected_output": "Enter first number: Enter second number: In the gold band: total 120",
        },
        {
            "inputs": ["30", "29"],
            "expected_output": "Enter first number: Enter second number: Outside the gold band: total 59",
        },
        {
            "inputs": ["50", "71"],
            "expected_output": "Enter first number: Enter second number: Outside the gold band: total 121",
        },
    ],
    8: [
        {
            "inputs": ["12", "no"],
            "expected_output": (
                "Enter your age: Are you scared of the dark? (yes/no): "
                "Come in! Age 12, scared no"
            ),
        },
        {
            "inputs": ["10", "no"],
            "expected_output": (
                "Enter your age: Are you scared of the dark? (yes/no): "
                "Come in! Age 10, scared no"
            ),
        },
        {
            "inputs": ["9", "no"],
            "expected_output": (
                "Enter your age: Are you scared of the dark? (yes/no): "
                "Maybe later. Age 9, scared no"
            ),
        },
    ],
    # Ex 9: members need spend ≥ 40 or age ≥ 60; non-members always pay.
    9: [
        {
            "inputs": ["yes", "50", "20"],
            "expected_output": (
                "Are you a member? (yes/no): Enter your spend: Enter your age: "
                "Discount for you! Spend £50, age 20"
            ),
        },
        {
            "inputs": ["yes", "40", "20"],
            "expected_output": (
                "Are you a member? (yes/no): Enter your spend: Enter your age: "
                "Discount for you! Spend £40, age 20"
            ),
        },
        {
            "inputs": ["yes", "10", "60"],
            "expected_output": (
                "Are you a member? (yes/no): Enter your spend: Enter your age: "
                "Discount for you! Spend £10, age 60"
            ),
        },
        {
            "inputs": ["no", "50", "70"],
            "expected_output": (
                "Are you a member? (yes/no): Enter your spend: Enter your age: "
                "Full price. Spend £50, age 70"
            ),
        },
        {
            "inputs": ["yes", "39", "19"],
            "expected_output": (
                "Are you a member? (yes/no): Enter your spend: Enter your age: "
                "Full price. Spend £39, age 19"
            ),
        },
    ],
    # Ex 10: points are films × 5 with a tenth taken off (floored).
    # 6 films → 30 − 3 = 27 gold; 10 films → 50 − 5 = 45 gold;
    # 5 films → 25 − 2 = 23 silver (age 13) but bronze when under 5;
    # 4 films → 20 − 2 = 18 bronze; 2 films → 10 − 1 = 9 bronze.
    10: [
        {
            "inputs": ["10", "8"],
            "expected_output": "How many films this month? Enter your age: Gold member: £45 for age 8",
        },
        {
            "inputs": ["5", "13"],
            "expected_output": "How many films this month? Enter your age: Silver member: £23 for age 13",
        },
        {
            "inputs": ["5", "4"],
            "expected_output": "How many films this month? Enter your age: Bronze member: £23 for age 4",
        },
        {
            "inputs": ["4", "20"],
            "expected_output": "How many films this month? Enter your age: Bronze member: £18 for age 20",
        },
        {
            "inputs": ["2", "3"],
            "expected_output": "How many films this month? Enter your age: Bronze member: £9 for age 3",
        },
    ],
}
