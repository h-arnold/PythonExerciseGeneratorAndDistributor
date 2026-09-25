"""Repository-only analyzer regressions for ex009 sequence modify f-strings."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex009_sequence_modify_fstrings"
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _issues(code: str, exercise_no: int) -> list[str]:
    return _construct_checks.construct_issues(ast.parse(code), exercise_no)


def test_rejects_zero_width_f_string_format_spec() -> None:
    issues = _issues(
        """
name = "Sam"
print(f"Welcome, {name:}")
""",
        1,
    )

    assert any("format specifier" in issue for issue in issues)


def test_rejects_unsafe_f_string_conversion() -> None:
    issues = _issues(
        """
name = "Sam"
print(f"Welcome, {name!r}!")
""",
        1,
    )

    assert any("safe !s conversion" in issue for issue in issues)


def test_rejects_boolop_compare_lookup_branches() -> None:
    issues = _issues(
        """
snack = input()
message = "You chose popcorn for break time." if snack == "popcorn" else "No."
print(f"{message}")
""",
        5,
    )

    assert any("Conditional expressions" in issue for issue in issues)
    assert any("Comparisons" in issue for issue in issues)


def test_rejects_boolop_lookup_branch() -> None:
    issues = _issues(
        """
name = "Sam"
message = "Welcome, Sam!" and name
print(f"{message}")
""",
        1,
    )

    assert any("Boolean expressions" in issue for issue in issues)


def test_rejects_finite_case_mapping_and_subscript() -> None:
    issues = _issues(
        """
lookup = {"popcorn": "You chose popcorn for break time."}
snack = input()
print(f"{lookup[snack]}")
""",
        5,
    )

    assert any("Finite-case mappings" in issue for issue in issues)
    assert any("Subscript" in issue for issue in issues)


def test_rejects_arithmetic_hidden_in_an_output_label() -> None:
    issues = _issues(
        """
tickets_sold = 5
extra_tickets = 2
total_tickets = tickets_sold + extra_tickets
label = total_tickets + 0
print(f"Tickets sold altogether: {label}")
""",
        8,
    )

    assert any("one live arithmetic operation" in issue for issue in issues)


def test_accepts_simple_variable_alias() -> None:
    issues = _issues(
        """
name = "Sam"
display_name = name
print(f"Welcome, {display_name}!")
""",
        1,
    )

    assert issues == []


def test_accepts_named_arithmetic_alias() -> None:
    issues = _issues(
        """
tickets_sold = 5
extra_tickets = 2
total_tickets = tickets_sold + extra_tickets
answer = total_tickets
print(f"Tickets sold altogether: {answer}")
""",
        8,
    )

    assert issues == []


def test_accepts_named_constant_and_input_aliases() -> None:
    issues = _issues(
        """
pages_today = int(input())
pages_tomorrow = 8
tomorrow_pages = pages_tomorrow
total_pages = pages_today + tomorrow_pages
answer = total_pages
print(f"Pages read in two days: {answer}")
""",
        9,
    )

    assert issues == []
