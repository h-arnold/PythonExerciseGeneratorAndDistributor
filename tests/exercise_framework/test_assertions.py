"""Tests for assertion helper messages."""

from __future__ import annotations

from tests.exercise_framework import assertions


def test_assert_has_print_statement_failure_message() -> None:
    assert assertions.assert_has_print_statement(exercise_no=2, has_print=False) == [
        "Exercise 2: expected a print statement."
    ]


def test_assert_has_print_statement_success_message() -> None:
    assert assertions.assert_has_print_statement(exercise_no=2, has_print=True) == []


def test_assert_uses_operator_failure_message() -> None:
    assert assertions.assert_uses_operator(exercise_no=3, operator="*", used=False) == [
        "Exercise 3: expected to use '*' in the calculation."
    ]


def test_assert_uses_operator_success_message() -> None:
    assert assertions.assert_uses_operator(exercise_no=3, operator="*", used=True) == []
