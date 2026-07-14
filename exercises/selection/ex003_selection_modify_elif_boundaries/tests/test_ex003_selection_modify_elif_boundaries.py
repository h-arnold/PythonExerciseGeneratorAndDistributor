"""Tests for ex003 selection modify elif boundaries."""
from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)


_EXERCISE_KEY = "ex003_selection_modify_elif_boundaries"
ex003 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_CACHE = RuntimeCache()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _tag(n: int) -> str:
    """Return the cell tag for exercise *n*."""
    return f"exercise{n}"


def _run(n: int) -> str:
    """Execute the tagged cell and capture output (no input)."""
    return run_cell_and_capture_output(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE)


def _run_with_inputs(n: int, inputs: list[str]) -> str:
    """Execute the tagged cell with predetermined inputs."""
    return run_cell_with_input(_EXERCISE_KEY, tag=_tag(n), inputs=inputs, cache=_CACHE)


def _ast(n: int) -> ast.Module:
    """Parse the tagged cell's source into an AST."""
    return ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE))


def _code(n: int) -> str:
    """Return the raw source code of the tagged cell."""
    return extract_tagged_code(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE)


def _has_if(tree: ast.AST) -> bool:
    """Return True when the AST contains an ``if`` statement."""
    return any(isinstance(node, ast.If) for node in ast.walk(tree))


def _string_constants(tree: ast.AST) -> set[str]:
    """Return all string literal values found in the AST."""
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _has_upper_case_assignment(tree: ast.AST, name: str) -> bool:
    """Return True when the AST contains an assignment to *name*."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return True
    return False


def _assignment_value(tree: ast.AST, name: str) -> int | None:
    """Return the integer value assigned to *name*, or None if not found."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, int
                    ):
                        return node.value.value
    return None


def _comparison_uses_name(tree: ast.AST, name: str) -> bool:
    """Return True when a comparison uses a Name node with *name* as a comparator."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Name) and comp.id == name:
                    return True
    return False


def _literal_in_comparison(tree: ast.AST, value: int) -> bool:
    """Return True when an integer literal appears as a comparator."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and comp.value == value:
                    return True
    return False


def _has_comparison_op(tree: ast.AST, op_type: type[ast.cmpop]) -> bool:
    """Return True when a comparison uses the given operator type."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if isinstance(op, op_type):
                    return True
    return False


def _code_contains(code: str, fragment: str) -> bool:
    """Return True when *fragment* appears in the raw source code."""
    return fragment in code


def _has_call(tree: ast.AST, name: str) -> bool:
    """Return True when the AST contains a call to a specific function name."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == name:
                return True
    return False


def _has_floor_div(tree: ast.AST) -> bool:
    """Return True when the AST contains a floor-division (//) operator."""
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv)
        for node in ast.walk(tree)
    )


def _has_delivery_assignment(tree: ast.AST) -> bool:
    """Return True when the AST assigns to a ``delivery`` variable."""
    return any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "delivery" for t in node.targets)
        for node in ast.walk(tree)
    )


# ── Per-exercise construct checks ──────────────────────────────────────────
# These must FAIL on the unedited student notebook (which still holds the old
# constants / messages / operators) and PASS on the solution notebook. Every
# logic and edge test below calls the matching construct check so that no test
# can pass on the starter code.


def _assert_refactor(n: int, constants: list[str], literals: list[int]) -> None:
    """Assert a pure-refactor exercise defines & uses UPPER_CASE constants."""
    tree = _ast(n)
    code = _code(n)
    for name in constants:
        assert _has_upper_case_assignment(tree, name), (
            f"Must define the {name} constant"
        )
        assert _comparison_uses_name(tree, name), (
            f"Must use {name} in a comparison instead of the bare number"
        )
    for lit in literals:
        assert not _literal_in_comparison(tree, lit), (
            f"Bare literal {lit} must not appear in a comparison — use the constant"
        )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


def _assert_ex4_construct() -> None:
    tree = _ast(4)
    code = _code(4)
    assert _assignment_value(tree, "PASS_MARK") == 40, (
        "PASS_MARK must be changed from 60 to 40"
    )
    assert _has_comparison_op(tree, ast.GtE), "Must use >= comparison"
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


def _assert_ex5_construct() -> None:
    tree = _ast(5)
    code = _code(5)
    assert _assignment_value(tree, "BIG_STUDY") == 2, (
        "BIG_STUDY must be changed from 1 to 2"
    )
    assert _has_comparison_op(tree, ast.GtE), "Must use >= comparison"
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op in node.ops:
                assert not isinstance(op, ast.LtE), (
                    "Must not use <= in comparisons — operator should be >="
                )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


def _assert_ex6_construct() -> None:
    tree = _ast(6)
    code = _code(6)
    assert _assignment_value(tree, "HOT") == 25, "HOT must be changed from 30 to 25"
    assert _code_contains(code, "It is a heatwave! {temp}°C"), (
        "Must print the new heatwave message"
    )
    assert not _code_contains(code, "Hot!"), "Old message 'Hot!' must be removed"


def _assert_ex7_construct() -> None:
    tree = _ast(7)
    code = _code(7)
    assert _assignment_value(tree, "SMALL") == 12, "SMALL must be changed from 10 to 12"
    assert _assignment_value(tree, "MEDIUM") == 36, (
        "MEDIUM must be changed from 30 to 36"
    )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


def _assert_ex8_construct() -> None:
    tree = _ast(8)
    code = _code(8)
    assert _assignment_value(tree, "BIG_SPEND") == 120, (
        "BIG_SPEND must be changed from 100 to 120"
    )
    assert _assignment_value(tree, "MID_SPEND") == 75, (
        "MID_SPEND must be changed from 50 to 75"
    )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


def _assert_ex9_construct() -> None:
    tree = _ast(9)
    code = _code(9)
    assert _assignment_value(tree, "GRADE_A") == 85, (
        "GRADE_A must be changed from 90 to 85"
    )
    assert _assignment_value(tree, "GRADE_B") == 70, (
        "GRADE_B must be changed from 75 to 70"
    )
    assert _has_call(tree, "round"), "Must use round() for the average calculation"


def _assert_ex10_construct() -> None:
    tree = _ast(10)
    code = _code(10)
    assert _assignment_value(tree, "BULK_ORDER") == 250, (
        "BULK_ORDER must be changed from 200 to 250"
    )
    assert _has_delivery_assignment(tree), (
        "Must add a 'delivery' variable assignment (delivery = cost // 10)"
    )
    assert _has_floor_div(tree), "Must use // (floor division) in the delivery formula"
    assert "cost = cost + delivery" in code or "cost += delivery" in code, (
        "Must add 'cost = cost + delivery' or 'cost += delivery'"
    )


# ── Exercise 1: Refactor — delivery thresholds ───────────────────────────────


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    """Exercise 1 must refactor to constants AND print the standard message."""
    _assert_refactor(1, ["FREE_DELIVERY_THRESHOLD", "STANDARD_DELIVERY_THRESHOLD"], [50, 20])
    output = _run_with_inputs(1, list(ex003.EX003_INPUT_CASES[1]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[1]["expected_output"]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    """Exercise 1 must define UPPER_CASE constants and use them in comparisons."""
    tree = _ast(1)
    code = _code(1)
    assert _has_upper_case_assignment(tree, "FREE_DELIVERY_THRESHOLD"), (
        "Must define FREE_DELIVERY_THRESHOLD constant"
    )
    assert _has_upper_case_assignment(tree, "STANDARD_DELIVERY_THRESHOLD"), (
        "Must define STANDARD_DELIVERY_THRESHOLD constant"
    )
    assert _comparison_uses_name(tree, "FREE_DELIVERY_THRESHOLD"), (
        "FREE_DELIVERY_THRESHOLD must be used in a comparison"
    )
    assert _comparison_uses_name(tree, "STANDARD_DELIVERY_THRESHOLD"), (
        "STANDARD_DELIVERY_THRESHOLD must be used in a comparison"
    )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


@pytest.mark.task(taskno=1)
def test_exercise1_no_bare_literals() -> None:
    """Exercise 1 must not use bare literals 50 or 20 in comparisons."""
    tree = _ast(1)
    assert not _literal_in_comparison(tree, 50), (
        "Bare literal 50 must not appear in a comparison — use FREE_DELIVERY_THRESHOLD"
    )
    assert not _literal_in_comparison(tree, 20), (
        "Bare literal 20 must not appear in a comparison — use STANDARD_DELIVERY_THRESHOLD"
    )


# ── Exercise 2: Refactor — passenger limits ──────────────────────────────────


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    """Exercise 2 must refactor to constants AND print the small van message."""
    _assert_refactor(2, ["SMALL_VAN_LIMIT", "MINIBUS_LIMIT"], [4, 8])
    output = _run_with_inputs(2, list(ex003.EX003_INPUT_CASES[2]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[2]["expected_output"]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    """Exercise 2 must define UPPER_CASE constants and use them in comparisons."""
    tree = _ast(2)
    code = _code(2)
    assert _has_upper_case_assignment(tree, "SMALL_VAN_LIMIT"), (
        "Must define SMALL_VAN_LIMIT constant"
    )
    assert _has_upper_case_assignment(tree, "MINIBUS_LIMIT"), (
        "Must define MINIBUS_LIMIT constant"
    )
    assert _comparison_uses_name(tree, "SMALL_VAN_LIMIT"), (
        "SMALL_VAN_LIMIT must be used in a comparison"
    )
    assert _comparison_uses_name(tree, "MINIBUS_LIMIT"), (
        "MINIBUS_LIMIT must be used in a comparison"
    )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


@pytest.mark.task(taskno=2)
def test_exercise2_no_bare_literals() -> None:
    """Exercise 2 must not use bare literals 4 or 8 in comparisons."""
    tree = _ast(2)
    assert not _literal_in_comparison(tree, 4), (
        "Bare literal 4 must not appear in a comparison — use SMALL_VAN_LIMIT"
    )
    assert not _literal_in_comparison(tree, 8), (
        "Bare literal 8 must not appear in a comparison — use MINIBUS_LIMIT"
    )


# ── Exercise 3: Refactor — total bands ───────────────────────────────────────


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    """Exercise 3 must refactor to constants AND print 'The total 100 is large'."""
    _assert_refactor(3, ["LARGE_TOTAL", "MEDIUM_TOTAL"], [100, 50])
    output = _run_with_inputs(3, list(ex003.EX003_INPUT_CASES[3]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[3]["expected_output"]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    """Exercise 3 must define UPPER_CASE constants and use them in comparisons."""
    tree = _ast(3)
    code = _code(3)
    assert _has_upper_case_assignment(tree, "LARGE_TOTAL"), (
        "Must define LARGE_TOTAL constant"
    )
    assert _has_upper_case_assignment(tree, "MEDIUM_TOTAL"), (
        "Must define MEDIUM_TOTAL constant"
    )
    assert _comparison_uses_name(tree, "LARGE_TOTAL"), (
        "LARGE_TOTAL must be used in a comparison"
    )
    assert _comparison_uses_name(tree, "MEDIUM_TOTAL"), (
        "MEDIUM_TOTAL must be used in a comparison"
    )
    assert _code_contains(code, 'f"') or _code_contains(code, "f'"), (
        "Must use f-strings for printed messages"
    )


@pytest.mark.task(taskno=3)
def test_exercise3_no_bare_literals() -> None:
    """Exercise 3 must not use bare literals 100 or 50 in comparisons."""
    tree = _ast(3)
    assert not _literal_in_comparison(tree, 100), (
        "Bare literal 100 must not appear in a comparison — use LARGE_TOTAL"
    )
    assert not _literal_in_comparison(tree, 50), (
        "Bare literal 50 must not appear in a comparison — use MEDIUM_TOTAL"
    )


# ── Exercise 4: Change pass mark + messages ──────────────────────────────────


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    """Exercise 4 must set PASS_MARK=40 and print the 'Try again!' message."""
    _assert_ex4_construct()
    output = _run_with_inputs(4, list(ex003.EX003_INPUT_CASES[4]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[4]["expected_output"]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    """Exercise 4 must set PASS_MARK to 40 (not 60) and use >=."""
    _assert_ex4_construct()


@pytest.mark.task(taskno=4)
def test_exercise4_messages() -> None:
    """Exercise 4 must use the new pass/fail messages."""
    _assert_ex4_construct()
    code = _code(4)
    assert _code_contains(code, "Well done! Score {score} is a pass"), (
        "Pass message must be 'Well done! Score {score} is a pass'"
    )
    assert _code_contains(code, "Try again! Score {score} is a fail"), (
        "Fail message must be 'Try again! Score {score} is a fail'"
    )
    assert not _code_contains(code, "you passed"), "Old message 'you passed' must be removed"
    assert not _code_contains(code, "you failed"), "Old message 'you failed' must be removed"


# ── Exercise 5: Swap operator + change constant + messages ───────────────────


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    """Exercise 5 must set BIG_STUDY=2 and print 'Amazing!' when hours >= 2."""
    _assert_ex5_construct()
    output = _run_with_inputs(5, list(ex003.EX003_INPUT_CASES[5]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[5]["expected_output"]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    """Exercise 5 must set BIG_STUDY to 2 and use >= operator."""
    _assert_ex5_construct()


@pytest.mark.task(taskno=5)
def test_exercise5_messages() -> None:
    """Exercise 5 must use the new study messages."""
    _assert_ex5_construct()
    code = _code(5)
    assert _code_contains(code, "Amazing! You studied {hours} hours"), (
        "Must print 'Amazing! You studied {hours} hours'"
    )
    assert _code_contains(code, "Keep going — you studied {hours} hours"), (
        "Must print 'Keep going — you studied {hours} hours'"
    )
    assert not _code_contains(code, "keep going!"), "Old message 'keep going!' must be removed"
    assert not _code_contains(code, "Great! You studied"), (
        "Old message 'Great! You studied' must be removed"
    )


# ── Exercise 6: Change HOT constant + message ────────────────────────────────


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    """Exercise 6 must set HOT=25 and print the heatwave message for 26."""
    _assert_ex6_construct()
    output = _run_with_inputs(6, list(ex003.EX003_INPUT_CASES[6]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[6]["expected_output"]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    """Exercise 6 must set HOT to 25 (not 30)."""
    _assert_ex6_construct()


@pytest.mark.task(taskno=6)
def test_exercise6_messages() -> None:
    """Exercise 6 must use the new heatwave message and keep mild/cold messages."""
    _assert_ex6_construct()
    code = _code(6)
    assert _code_contains(code, "Mild. {temp}°C"), "Mild message must be kept"
    assert _code_contains(code, "Cold. {temp}°C"), "Cold message must be kept"


# ── Exercise 7: Change SMALL, MEDIUM + messages ──────────────────────────────


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    """Exercise 7 must set SMALL=12, MEDIUM=36 and print 'Medium order'."""
    _assert_ex7_construct()
    output = _run_with_inputs(7, list(ex003.EX003_INPUT_CASES[7]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[7]["expected_output"]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    """Exercise 7 must set SMALL to 12 and MEDIUM to 36."""
    _assert_ex7_construct()


@pytest.mark.task(taskno=7)
def test_exercise7_messages() -> None:
    """Exercise 7 must use the updated parcel-box messages."""
    _assert_ex7_construct()
    code = _code(7)
    assert _code_contains(code, "Small order: {boxes} box(es), {leftover} leftover"), (
        "Small-order message must use 'Small order:' prefix"
    )
    assert _code_contains(code, "Medium order: {boxes} boxes, {leftover} leftover"), (
        "Medium-order message must use 'Medium order:' prefix"
    )
    assert _code_contains(code, "Large order: {boxes} boxes"), (
        "Large-order message must use 'Large order:' prefix"
    )
    assert not _code_contains(code, "One box,"), "Old message 'One box,' must be removed"
    assert not _code_contains(code, "Too many:"), "Old message 'Too many:' must be removed"


# ── Exercise 8: Change BIG_SPEND, MID_SPEND + messages ───────────────────────


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    """Exercise 8 must set BIG_SPEND=120, MID_SPEND=75 and print 10% off."""
    _assert_ex8_construct()
    output = _run_with_inputs(8, list(ex003.EX003_INPUT_CASES[8]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[8]["expected_output"]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    """Exercise 8 must set BIG_SPEND to 120 and MID_SPEND to 75."""
    _assert_ex8_construct()


@pytest.mark.task(taskno=8)
def test_exercise8_messages() -> None:
    """Exercise 8 must use the updated discount messages."""
    _assert_ex8_construct()
    code = _code(8)
    assert _code_contains(code, "You saved £{discount} with 10% off"), (
        "10% off message must be 'You saved £{discount} with 10% off'"
    )
    assert _code_contains(code, "You saved £{discount} with 5% off"), (
        "5% off message must be 'You saved £{discount} with 5% off'"
    )
    assert not _code_contains(code, "10% off: £{discount} saved"), (
        "Old 10% off message must be removed"
    )
    assert not _code_contains(code, "5% off: £{discount} saved"), (
        "Old 5% off message must be removed"
    )
    assert _code_contains(code, "Free gift at £{spend}"), "Free gift message must be kept"
    assert _code_contains(code, "No offer at £{spend}"), "No-offer message must be kept"


# ── Exercise 9: Change GRADE_A, GRADE_B ──────────────────────────────────────


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    """Exercise 9 must set GRADE_A=85, GRADE_B=70 (avg 73 → Grade B not C)."""
    _assert_ex9_construct()
    output = _run_with_inputs(9, list(ex003.EX003_INPUT_CASES[9]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[9]["expected_output"]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    """Exercise 9 must set GRADE_A to 85 and GRADE_B to 70."""
    _assert_ex9_construct()


# ── Exercise 10: Add delivery formula + change BULK_ORDER ────────────────────


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    """Exercise 10 must set BULK_ORDER=250 and add the delivery formula."""
    _assert_ex10_construct()
    output = _run_with_inputs(10, list(ex003.EX003_INPUT_CASES[10]["inputs"]))
    assert output == ex003.EX003_INPUT_CASES[10]["expected_output"]


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    """Exercise 10 must set BULK_ORDER to 250 and add a delivery formula."""
    _assert_ex10_construct()


# ── Edge-case logic tests (probe the new boundary operators) ──────────────────


def _assert_edge_output(exercise_no: int, case: dict[str, object]) -> None:
    """Run an edge-case input set and assert the exact expected output."""
    inputs = list(case["inputs"])  # type: ignore[arg-type]
    expected = case["expected_output"]  # type: ignore[assignment]
    output = _run_with_inputs(exercise_no, inputs)
    assert output == expected, (
        f"Exercise {exercise_no} with inputs {inputs}: "
        f"expected {expected!r} but got {output!r}"
    )


_ID = lambda case: ",".join(case["inputs"])  # type: ignore[attr-defined]


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[1], ids=_ID)
@pytest.mark.task(taskno=1)
def test_exercise1_edge_cases(case: dict[str, object]) -> None:
    _assert_refactor(1, ["FREE_DELIVERY_THRESHOLD", "STANDARD_DELIVERY_THRESHOLD"], [50, 20])
    _assert_edge_output(1, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[2], ids=_ID)
@pytest.mark.task(taskno=2)
def test_exercise2_edge_cases(case: dict[str, object]) -> None:
    _assert_refactor(2, ["SMALL_VAN_LIMIT", "MINIBUS_LIMIT"], [4, 8])
    _assert_edge_output(2, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[3], ids=_ID)
@pytest.mark.task(taskno=3)
def test_exercise3_edge_cases(case: dict[str, object]) -> None:
    _assert_refactor(3, ["LARGE_TOTAL", "MEDIUM_TOTAL"], [100, 50])
    _assert_edge_output(3, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[4], ids=_ID)
@pytest.mark.task(taskno=4)
def test_exercise4_edge_cases(case: dict[str, object]) -> None:
    _assert_ex4_construct()
    _assert_edge_output(4, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[5], ids=_ID)
@pytest.mark.task(taskno=5)
def test_exercise5_edge_cases(case: dict[str, object]) -> None:
    _assert_ex5_construct()
    _assert_edge_output(5, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[6], ids=_ID)
@pytest.mark.task(taskno=6)
def test_exercise6_edge_cases(case: dict[str, object]) -> None:
    _assert_ex6_construct()
    _assert_edge_output(6, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[7], ids=_ID)
@pytest.mark.task(taskno=7)
def test_exercise7_edge_cases(case: dict[str, object]) -> None:
    _assert_ex7_construct()
    _assert_edge_output(7, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[8], ids=_ID)
@pytest.mark.task(taskno=8)
def test_exercise8_edge_cases(case: dict[str, object]) -> None:
    _assert_ex8_construct()
    _assert_edge_output(8, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[9], ids=_ID)
@pytest.mark.task(taskno=9)
def test_exercise9_edge_cases(case: dict[str, object]) -> None:
    _assert_ex9_construct()
    _assert_edge_output(9, case)


@pytest.mark.parametrize("case", ex003.EX003_EDGE_CASES[10], ids=_ID)
@pytest.mark.task(taskno=10)
def test_exercise10_edge_cases(case: dict[str, object]) -> None:
    _assert_ex10_construct()
    _assert_edge_output(10, case)
