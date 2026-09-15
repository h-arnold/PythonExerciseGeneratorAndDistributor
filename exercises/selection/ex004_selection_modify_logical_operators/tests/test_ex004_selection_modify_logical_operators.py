"""Tests for ex004 selection modify logical operators."""
from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex004_selection_modify_logical_operators"
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
ex004 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
has_boolop = construct_checks.has_boolop
has_unary_not = construct_checks.has_unary_not
has_floordiv = construct_checks.has_floordiv
and_groups_or = construct_checks.and_groups_or
assignment_value = construct_checks.assignment_value
code_contains = construct_checks.code_contains
comparison_uses_name = construct_checks.comparison_uses_name
prints_use_fstrings = construct_checks.prints_use_fstrings
_MESSAGES = construct_checks.MESSAGES
_CACHE = RuntimeCache()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _tag(n: int) -> str:
    """Return the cell tag for exercise *n*."""
    return f"exercise{n}"


def _run_with_inputs(n: int, inputs: list[str]) -> str:
    """Execute the tagged cell with predetermined inputs."""
    return run_cell_with_input(_EXERCISE_KEY, tag=_tag(n), inputs=inputs, cache=_CACHE)


def _ast(n: int) -> ast.Module:
    """Parse the tagged cell's source into an AST."""
    return ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE))


def _code(n: int) -> str:
    """Return the raw source code of the tagged cell."""
    return extract_tagged_code(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE)


# ── Per-exercise construct checks ──────────────────────────────────────────
# These must FAIL on the unedited student notebook (which still holds the
# single-check starters and old messages) and PASS on the solution notebook.
# Every logic, messages and edge test below calls the matching construct check
# so that no test can pass on the starter code.


def _assert_ex1_construct() -> None:
    """Exercise 1 must combine two comparisons with ``and``."""
    assert has_boolop(_ast(1), ast.And), (
        "Must require both checks at once — use and"
    )
    assert prints_use_fstrings(_ast(1)), "Must print the messages with f-strings"


def _assert_ex2_construct() -> None:
    """Exercise 2 must accept either weekend day with ``or``."""
    assert has_boolop(_ast(2), ast.Or), "Must accept either day — use or"
    assert prints_use_fstrings(_ast(2)), "Must print the messages with f-strings"


def _assert_ex3_construct() -> None:
    """Exercise 3 must swap ``and`` for ``or``."""
    assert has_boolop(_ast(3), ast.Or), (
        "Only one check needs to pass now — use or"
    )
    assert prints_use_fstrings(_ast(3)), "Must print the messages with f-strings"


def _assert_ex4_construct() -> None:
    """Exercise 4 must reverse the check with ``not``."""
    assert has_unary_not(_ast(4)), "Must reverse the check — use not"
    assert prints_use_fstrings(_ast(4)), "Must print the messages with f-strings"


def _assert_ex5_construct() -> None:
    """Exercise 5 must use ``and`` with both range constants kept."""
    tree = _ast(5)
    assert has_boolop(tree, ast.And), (
        "Must require two checks at once — use and"
    )
    assert assignment_value(tree, "LOW") == 15, "LOW must stay at 15"
    assert assignment_value(tree, "HIGH") == 25, "HIGH must stay at 25"
    assert comparison_uses_name(tree, "LOW"), "Must compare against LOW, not type 15"
    assert comparison_uses_name(tree, "HIGH"), "Must compare against HIGH, not type 25"
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


def _assert_ex6_construct() -> None:
    """Exercise 6 must use ``or`` with both free-group constants kept."""
    tree = _ast(6)
    assert has_boolop(tree, ast.Or), "Must accept either free group — use or"
    assert assignment_value(tree, "CHILD_MAX") == 5, "CHILD_MAX must stay at 5"
    assert assignment_value(tree, "SENIOR_MIN") == 65, "SENIOR_MIN must stay at 65"
    assert comparison_uses_name(tree, "CHILD_MAX"), "Must compare against CHILD_MAX, not type 5"
    assert comparison_uses_name(tree, "SENIOR_MIN"), "Must compare against SENIOR_MIN, not type 65"
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


def _assert_ex7_construct() -> None:
    """Exercise 7 must use ``and`` to trap the total inside the band."""
    tree = _ast(7)
    assert has_boolop(tree, ast.And), (
        "The total must satisfy both checks — use and"
    )
    assert assignment_value(tree, "LOW_TOTAL") == 60, "LOW_TOTAL must stay at 60"
    assert assignment_value(tree, "HIGH_TOTAL") == 120, "HIGH_TOTAL must stay at 120"
    assert comparison_uses_name(tree, "LOW_TOTAL"), "Must compare against LOW_TOTAL, not type 60"
    assert comparison_uses_name(tree, "HIGH_TOTAL"), "Must compare against HIGH_TOTAL, not type 120"
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


def _assert_ex8_construct() -> None:
    """Exercise 8 must combine ``and`` with ``not`` for the scared check."""
    tree = _ast(8)
    assert has_boolop(tree, ast.And), "Must need two things together — use and"
    assert has_unary_not(tree), "Must flip the scared check — use not"
    assert assignment_value(tree, "AGE_LIMIT") == 10, "AGE_LIMIT must stay at 10"
    assert comparison_uses_name(tree, "AGE_LIMIT"), "Must compare against AGE_LIMIT, not type 10"
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


def _assert_ex9_construct() -> None:
    """Exercise 9 must bracket the either-or part inside an ``and``."""
    tree = _ast(9)
    assert has_boolop(tree, ast.And), "Membership and one extra are needed — use and"
    assert has_boolop(tree, ast.Or), "Either extra is enough — use or"
    assert and_groups_or(tree), (
        "The either-or check must be bracketed inside the and check"
    )
    assert assignment_value(tree, "SPEND_LIMIT") == 40, "SPEND_LIMIT must stay at 40"
    assert assignment_value(tree, "SENIOR_AGE") == 60, "SENIOR_AGE must stay at 60"
    assert comparison_uses_name(tree, "SPEND_LIMIT"), "Must compare against SPEND_LIMIT, not type 40"
    assert comparison_uses_name(tree, "SENIOR_AGE"), "Must compare against SENIOR_AGE, not type 60"
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


def _assert_ex10_construct() -> None:
    """Exercise 10 must add the discount maths and operator rules per tier."""
    tree = _ast(10)
    code = _code(10)
    # Discount calculation straight after the points total
    assert has_floordiv(tree), "Must find a tenth of the total with //"
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "discount" for t in node.targets)
        for node in ast.walk(tree)
    ), "Must add a discount variable for the tenth of the total"
    assert code_contains(code, "total = total - discount") or code_contains(
        code, "total -= discount"
    ), "Must take the discount off the total"
    # Gold tier: high total plus either rule, bracketed
    assert has_boolop(tree, ast.And), "Gold needs a high total and an extra rule — use and"
    assert has_boolop(tree, ast.Or), "Either gold extra is enough — use or"
    assert and_groups_or(tree), "The either-or rule must be bracketed inside the and"
    # Silver tier: still uses the not style for the age rule
    assert has_unary_not(tree), "Silver must reverse the age check — use not"
    # Constants kept exactly and actually used in the tier checks
    for name, expected in (
        ("BIG_SPEND", 18),
        ("STANDARD_SPEND", 14),
        ("GOLD_AGE", 12),
        ("GOLD_FILMS", 5),
    ):
        assert assignment_value(tree, name) == expected, f"{name} must stay at {expected}"
        assert comparison_uses_name(tree, name), (
            f"Must compare against {name}, not type {expected}"
        )
    assert prints_use_fstrings(tree), "Must print the messages with f-strings"


# ── Exercise 1: `and` for both ends of the age range ─────────────────────────


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    """Exercise 1 must use `and` and print the out-of-range message for age 20."""
    _assert_ex1_construct()
    output = _run_with_inputs(1, list(ex004.EX004_INPUT_CASES[1]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[1]["expected_output"]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    """Exercise 1 must combine the two comparisons with ``and``."""
    _assert_ex1_construct()


@pytest.mark.task(taskno=1)
def test_exercise1_messages() -> None:
    """Exercise 1 must use the new fits-the-club messages."""
    _assert_ex1_construct()
    code = _code(1)
    for fragment in _MESSAGES[1]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[1]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[1],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=1)
def test_exercise1_edge_cases(case: dict[str, object]) -> None:
    """Exercise 1 boundaries: 11 and 16 are in range, 10 and 17 are not."""
    _assert_ex1_construct()
    output = _run_with_inputs(1, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 1 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 2: `or` for the whole weekend ───────────────────────────────────


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    """Exercise 2 must use `or` and count Sunday as a lie-in day."""
    _assert_ex2_construct()
    output = _run_with_inputs(2, list(ex004.EX004_INPUT_CASES[2]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[2]["expected_output"]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    """Exercise 2 must accept either weekend day with ``or``."""
    _assert_ex2_construct()


@pytest.mark.task(taskno=2)
def test_exercise2_messages() -> None:
    """Exercise 2 must use the lie-in and school-day messages."""
    _assert_ex2_construct()
    code = _code(2)
    for fragment in _MESSAGES[2]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[2]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[2],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=2)
def test_exercise2_edge_cases(case: dict[str, object]) -> None:
    """Exercise 2 edges: Saturday is a lie-in too, Monday is a school day."""
    _assert_ex2_construct()
    output = _run_with_inputs(2, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 2 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 3: swap `and` for `or` ──────────────────────────────────────────


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    """Exercise 3 must use `or` and pass on the score alone (55/60)."""
    _assert_ex3_construct()
    output = _run_with_inputs(3, list(ex004.EX004_INPUT_CASES[3]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[3]["expected_output"]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    """Exercise 3 must accept either check with ``or``."""
    _assert_ex3_construct()


@pytest.mark.task(taskno=3)
def test_exercise3_messages() -> None:
    """Exercise 3 must use the well-done and keep-trying messages."""
    _assert_ex3_construct()
    code = _code(3)
    for fragment in _MESSAGES[3]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[3]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[3],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=3)
def test_exercise3_edge_cases(case: dict[str, object]) -> None:
    """Exercise 3 edges: either pass target alone is enough, neither fails."""
    _assert_ex3_construct()
    output = _run_with_inputs(3, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 3 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 4: flip the check with `not` ────────────────────────────────────


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    """Exercise 4 must use `not` and print the not-a-pass-yet message for 30."""
    _assert_ex4_construct()
    output = _run_with_inputs(4, list(ex004.EX004_INPUT_CASES[4]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[4]["expected_output"]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    """Exercise 4 must reverse the check with ``not``."""
    _assert_ex4_construct()


@pytest.mark.task(taskno=4)
def test_exercise4_messages() -> None:
    """Exercise 4 must use the rewritten pass/fail messages."""
    _assert_ex4_construct()
    code = _code(4)
    for fragment in _MESSAGES[4]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[4]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[4],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=4)
def test_exercise4_edge_cases(case: dict[str, object]) -> None:
    """Exercise 4 edges: the 50 boundary must behave exactly as before."""
    _assert_ex4_construct()
    output = _run_with_inputs(4, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 4 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 5: `and` for the comfortable band ───────────────────────────────


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    """Exercise 5 must use `and` and reject a temperature above HIGH."""
    _assert_ex5_construct()
    output = _run_with_inputs(5, list(ex004.EX004_INPUT_CASES[5]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[5]["expected_output"]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    """Exercise 5 must use ``and`` and keep LOW=15, HIGH=25."""
    _assert_ex5_construct()


@pytest.mark.task(taskno=5)
def test_exercise5_messages() -> None:
    """Exercise 5 must use the comfortable/uncomfortable messages."""
    _assert_ex5_construct()
    code = _code(5)
    for fragment in _MESSAGES[5]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[5]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[5],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=5)
def test_exercise5_edge_cases(case: dict[str, object]) -> None:
    """Exercise 5 edges: 15–25 inclusive is comfortable, outside is not."""
    _assert_ex5_construct()
    output = _run_with_inputs(5, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 5 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 6: `or` for the second free group ───────────────────────────────


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    """Exercise 6 must use `or` and let a 67-year-old in for free."""
    _assert_ex6_construct()
    output = _run_with_inputs(6, list(ex004.EX004_INPUT_CASES[6]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[6]["expected_output"]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    """Exercise 6 must use ``or`` and keep CHILD_MAX=5, SENIOR_MIN=65."""
    _assert_ex6_construct()


@pytest.mark.task(taskno=6)
def test_exercise6_messages() -> None:
    """Exercise 6 must use the free-entry message and keep the pay message."""
    _assert_ex6_construct()
    code = _code(6)
    for fragment in _MESSAGES[6]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[6]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[6],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=6)
def test_exercise6_edge_cases(case: dict[str, object]) -> None:
    """Exercise 6 edges: under 5 or 65+ is free, ages 5–64 pay."""
    _assert_ex6_construct()
    output = _run_with_inputs(6, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 6 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 7: `and` for the gold band ──────────────────────────────────────


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    """Exercise 7 must use `and` and reject a total above HIGH_TOTAL."""
    _assert_ex7_construct()
    output = _run_with_inputs(7, list(ex004.EX004_INPUT_CASES[7]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[7]["expected_output"]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    """Exercise 7 must use ``and`` and keep LOW_TOTAL=60, HIGH_TOTAL=120."""
    _assert_ex7_construct()


@pytest.mark.task(taskno=7)
def test_exercise7_messages() -> None:
    """Exercise 7 must use the in-band/outside-band messages."""
    _assert_ex7_construct()
    code = _code(7)
    for fragment in _MESSAGES[7]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[7]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[7],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=7)
def test_exercise7_edge_cases(case: dict[str, object]) -> None:
    """Exercise 7 edges: 60–120 inclusive is in the gold band."""
    _assert_ex7_construct()
    output = _run_with_inputs(7, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 7 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 8: age `and` not scared ─────────────────────────────────────────


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    """Exercise 8 must use `and`/`not` and delay a scared 12-year-old."""
    _assert_ex8_construct()
    output = _run_with_inputs(8, list(ex004.EX004_INPUT_CASES[8]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[8]["expected_output"]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    """Exercise 8 must use ``and`` with ``not`` and keep AGE_LIMIT=10."""
    _assert_ex8_construct()


@pytest.mark.task(taskno=8)
def test_exercise8_messages() -> None:
    """Exercise 8 must use the come-in/maybe-later messages."""
    _assert_ex8_construct()
    code = _code(8)
    for fragment in _MESSAGES[8]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[8]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[8],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=8)
def test_exercise8_edge_cases(case: dict[str, object]) -> None:
    """Exercise 8 edges: brave 12-year-olds come in, 9-year-olds wait."""
    _assert_ex8_construct()
    output = _run_with_inputs(8, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 8 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 9: member `and` (spend `or` age) ────────────────────────────────


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    """Exercise 9 must bracket the `or` inside an `and` and charge a plain member."""
    _assert_ex9_construct()
    output = _run_with_inputs(9, list(ex004.EX004_INPUT_CASES[9]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[9]["expected_output"]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    """Exercise 9 must use and with a bracketed or and keep the constants."""
    _assert_ex9_construct()


@pytest.mark.task(taskno=9)
def test_exercise9_messages() -> None:
    """Exercise 9 must use the discount message and keep the full-price one."""
    _assert_ex9_construct()
    code = _code(9)
    for fragment in _MESSAGES[9]["present"]:
        assert code_contains(code, fragment), (
            f"Must print the message: {fragment!r}"
        )
    for fragment in _MESSAGES[9]["absent"]:
        assert not code_contains(code, fragment), (
            f"Old message fragment must be removed: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[9],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=9)
def test_exercise9_edge_cases(case: dict[str, object]) -> None:
    """Exercise 9 edges: both extras at boundaries, non-members always pay."""
    _assert_ex9_construct()
    output = _run_with_inputs(9, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 9 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )


# ── Exercise 10: film points tiers with the discount ─────────────────────────


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    """Exercise 10 must add the discount and print £27 for 6 films at age 20."""
    _assert_ex10_construct()
    output = _run_with_inputs(10, list(ex004.EX004_INPUT_CASES[10]["inputs"]))
    assert output == ex004.EX004_INPUT_CASES[10]["expected_output"]
    # The starter prints the undiscounted price (£30 for 6 films); the
    # discounted solution gives £27, so £30 must no longer be printed.
    assert "£30" not in output, (
        "The starter's undiscounted price £30 must be gone — 6 films at "
        "age 20 should cost £27 after the tenth-off discount"
    )


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    """Exercise 10 must add the discount maths and the tier operator rules."""
    _assert_ex10_construct()


@pytest.mark.task(taskno=10)
def test_exercise10_messages() -> None:
    """Exercise 10 must keep all three tier messages."""
    _assert_ex10_construct()
    code = _code(10)
    for fragment in _MESSAGES[10]["present"]:
        assert code_contains(code, fragment), (
            f"Must keep the message: {fragment!r}"
        )


@pytest.mark.parametrize(
    "case",
    ex004.EX004_EDGE_CASES[10],
    ids=lambda case: ",".join(case["inputs"]),
)
@pytest.mark.task(taskno=10)
def test_exercise10_edge_cases(case: dict[str, object]) -> None:
    """Exercise 10 edges: gold, silver (blocked under 5) and bronze tiers."""
    _assert_ex10_construct()
    output = _run_with_inputs(10, list(case["inputs"]))  # type: ignore[arg-type]
    assert output == case["expected_output"], (
        f"Exercise 10 with inputs {case['inputs']}: "
        f"expected {case['expected_output']!r} but got {output!r}"
    )
