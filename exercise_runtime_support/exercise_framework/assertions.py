"""Assertion helpers for exercise check messaging."""

from __future__ import annotations


def assert_has_print_statement(*, exercise_no: int, has_print: bool) -> list[str]:
    """Return an error message when a print statement is missing."""
    if has_print:
        return []
    return [f"Exercise {exercise_no}: expected a print statement."]


def assert_uses_operator(*, exercise_no: int, operator: str, used: bool) -> list[str]:
    """Return an error message when the required operator is missing."""
    if used:
        return []
    return [f"Exercise {exercise_no}: expected to use '{operator}' in the calculation."]
