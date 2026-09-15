"""Exercise-local AST helpers and message table for ex004 construct checks.

Shared by the pytest suite (``test_ex004_selection_modify_logical_operators.py``)
and the student checker (``student_checker_support.py``) so that operator,
constant and message assertions have a single source of truth.
"""
from __future__ import annotations

import ast
from typing import Final


def has_boolop(tree: ast.AST, op_type: type[ast.boolop]) -> bool:
    """Return True when a boolean operation uses the given operator type."""
    return any(
        isinstance(node, ast.BoolOp) and isinstance(node.op, op_type)
        for node in ast.walk(tree)
    )


def has_unary_not(tree: ast.AST) -> bool:
    """Return True when a unary ``not`` is used."""
    return any(
        isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not)
        for node in ast.walk(tree)
    )


def has_floordiv(tree: ast.AST) -> bool:
    """Return True when a floor-division (//) operator is used."""
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv)
        for node in ast.walk(tree)
    )


def and_groups_or(tree: ast.AST) -> bool:
    """Return True when an ``and`` expression brackets an ``or`` expression.

    This verifies the bracketed mixed-operator form, for example
    ``member == "yes" and (spend >= 40 or age >= 60)``.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            for value in node.values:
                if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.Or):
                    return True
    return False


def assignment_value(tree: ast.AST, name: str) -> int | None:
    """Return the integer value assigned to *name*, or None if not found."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == name
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, int)
                ):
                    return node.value.value
    return None


def code_contains(code: str, fragment: str) -> bool:
    """Return True when *fragment* appears verbatim in *code*."""
    return fragment in code


# ── Message table (new message present, old message gone) ─────────────────────

MESSAGES: Final[dict[int, dict[str, tuple[str, ...]]]] = {
    1: {
        "present": (
            "In range: age {age} fits the club",
            "Out of range: age {age} does not fit",
        ),
        "absent": ("can join", "cannot join"),
    },
    2: {
        "present": (
            "Weekend! {day_name} is a lie-in day",
            "School day. {day_name} needs an early start",
        ),
        "absent": ("rest day", "Weekday."),
    },
    3: {
        "present": (
            "Well done! Score {score}, attendance {attendance}% is a pass",
            "Keep trying! Score {score}, attendance {attendance}% is not a pass yet",
        ),
        "absent": ("Pass: score", "Not yet:"),
    },
    4: {
        "present": (
            "Not a pass yet: score {score}",
            "A pass! Score {score}",
        ),
        "absent": ("needs more work", "is good enough"),
    },
    5: {
        "present": (
            "Comfortable: {temp}°C is just right",
            "Uncomfortable: {temp}°C is not ideal",
        ),
        "absent": ("Warm enough", "Too cold"),
    },
    6: {
        "present": ("Free museum entry for age {age}", "Please pay for age {age}"),
        "absent": ("Free for little ones",),
    },
    7: {
        "present": (
            "In the gold band: total {total}",
            "Outside the gold band: total {total}",
        ),
        "absent": ("Big enough", "Too small"),
    },
    8: {
        "present": (
            "Come in! Age {age}, scared {scared}",
            "Maybe later. Age {age}, scared {scared}",
        ),
        "absent": ("Old enough!", "Too young."),
    },
    9: {
        "present": ("Discount for you! Spend £{spend}, age {age}",),
        "absent": ("Hello member!",),
    },
    10: {
        "present": (
            "Gold member: £{total} for age {age}",
            "Silver member: £{total} for age {age}",
            "Bronze member: £{total} for age {age}",
        ),
        "absent": (),
    },
}
