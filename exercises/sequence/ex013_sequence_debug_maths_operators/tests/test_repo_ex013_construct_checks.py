"""Repository-only analyzer regressions for ex013."""

from __future__ import annotations

import ast
from textwrap import dedent

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex013_sequence_debug_maths_operators"
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _issues(code: str, exercise_no: int) -> list[str]:
    return _construct_checks.construct_issues(ast.parse(dedent(code).strip()), exercise_no)


def test_rejects_augassign_neutralization() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 4
        full_groups = 6
        full_groups += students // group_size - 6
        print(f"Full groups: {full_groups}")
        """,
        1,
    )

    assert any("AugAssign" in issue for issue in issues)


def test_rejects_reassignment_neutralization() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 4
        full_groups = 6
        full_groups = full_groups + students // group_size - 6
        print(f"Full groups: {full_groups}")
        """,
        1,
    )

    assert any("live 'full_groups' calculation" in issue for issue in issues)


def test_rejects_finite_input_truth_table() -> None:
    issues = _issues(
        """
        players = int(input(prompt="How many players? "))
        teams = 4 if players == 23 else 0
        print(f"Full teams: {teams}")
        """,
        4,
    )

    assert any("conditional" in issue.lower() or "comparison" in issue.lower() for issue in issues)


def test_rejects_print_and_input_shadowing() -> None:
    print_issues = _issues(
        """
        print = 1
        students = 25
        group_size = 4
        full_groups = students // group_size
        print(f"Full groups: {full_groups}")
        """,
        1,
    )
    input_issues = _issues(
        """
        input = 3
        players = int(input("How many players? "))
        teams = players // 5
        print(f"Full teams: {teams}")
        """,
        4,
    )

    assert any("protected name 'print'" in issue for issue in print_issues)
    assert any("protected name 'input'" in issue for issue in input_issues)


def test_rejects_alias_of_old_result_output() -> None:
    issues = _issues(
        """
        length = 2.345
        area = length * length
        rounded = round(area, 2)
        shown = area
        print(f"Area of square: {shown}")
        """,
        8,
    )

    assert any("old result variable" in issue and "area" in issue for issue in issues)


def test_rejects_formula_in_separate_print_argument() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 4
        print(f"Full groups:", students // group_size)
        """,
        1,
    )

    assert any("complete result in one f-string" in issue for issue in issues)


def test_rejects_fstring_plus_concatenation() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 4
        print("Full groups: " + f"{students // group_size}")
        """,
        1,
    )

    assert any("must not use + concatenation" in issue for issue in issues)


def test_accepts_nested_fstring_arithmetic() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 4
        print(f"Full groups: {students // group_size}")
        """,
        1,
    )

    assert issues == []


def test_accepts_keyword_input_prompt() -> None:
    issues = _issues(
        """
        players = int(input(prompt="How many players? "))
        teams = players // 5
        print(f"Full teams: {teams}")
        """,
        4,
    )

    assert issues == []


def test_rejects_inline_input_without_named_variable() -> None:
    issues = _issues(
        """
        teams = int(input(prompt="How many players? ")) // 5
        print(f"Full teams: {teams}")
        """,
        4,
    )

    assert any("variable used in the printed result" in issue for issue in issues)


def test_accepts_repeated_quotient_and_direct_cost_formula() -> None:
    issues = _issues(
        """
        items = int(input("How many items? "))
        box_size = int(input("How many per box? "))
        total_cost = float(input("Total cost? £"))
        boxes = items // box_size
        leftover = items % box_size
        cost_per_box = round(total_cost / (items // box_size), 2)
        print(f"Full boxes: {boxes}")
        print(f"Leftover items: {leftover}")
        print(f"Cost per box: £{cost_per_box}")
        """,
        10,
    )

    assert issues == []


def test_accepts_factored_named_constant() -> None:
    issues = _issues(
        """
        two = 2
        fifty = 50
        hundred = two * fifty
        pence = int(input(prompt="Enter pence: "))
        pounds = pence // hundred
        leftover = pence % hundred
        print(f"{pence}p is £{pounds} and {leftover}p")
        """,
        7,
    )

    assert issues == []


def test_accepts_power_form_for_square_area() -> None:
    issues = _issues(
        """
        length = 2.345
        rounded = round(length**2, 2)
        print(f"Area of square: {rounded}")
        """,
        8,
    )

    assert issues == []


def test_accepts_reversed_multiplication_order() -> None:
    issues = _issues(
        """
        price = 1.257
        qty = 3
        total = qty * price
        total = round(total, 2)
        print(f"Total: £{total}")
        """,
        5,
    )

    assert issues == []


def test_accepts_simple_aliases_and_named_constants() -> None:
    issues = _issues(
        """
        students = 25
        group_size = 2 * 2
        student_count = students
        size = group_size
        full_groups = student_count // size
        print(f"Full groups: {full_groups}")
        """,
        1,
    )

    assert issues == []
