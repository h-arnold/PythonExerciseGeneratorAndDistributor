"""Exercise-local student checker definitions for ex003_selection_modify_elif_boundaries."""
from __future__ import annotations

import ast
from collections.abc import Callable

from exercise_runtime_support.exercise_framework import extract_tagged_code
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import run_cell_with_input
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex003_selection_modify_elif_boundaries"
ex003 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


# ── AST / source helpers (student-checker local copies) ───────────────────────


def _parse(n: int) -> ast.Module:
    """Parse the tagged cell's source for exercise *n* into an AST."""
    return ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(n)))


def _source(n: int) -> str:
    """Return the raw source of the tagged cell for exercise *n*."""
    return extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(n))


def _has_upper_assignment(tree: ast.Module, name: str) -> bool:
    """Return True when an assignment to UPPER_CASE *name* exists."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return True
    return False


def _comparison_uses_name(tree: ast.Module, name: str) -> bool:
    """Return True when a comparison compares against the Name *name*."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Name) and comp.id == name:
                    return True
    return False


def _literal_in_comparison(tree: ast.Module, value: int) -> bool:
    """Return True when the integer literal *value* appears in a comparison."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and comp.value == value:
                    return True
    return False


def _assignment_value(tree: ast.Module, name: str) -> int | None:
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


def _has_comparison_op(tree: ast.Module, op_type: type[ast.cmpop]) -> bool:
    """Return True when a comparison uses operator *op_type*."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if isinstance(op, op_type):
                    return True
    return False


def _code_contains(code: str, fragment: str) -> bool:
    """Return True when *fragment* appears verbatim in *code*."""
    return fragment in code


# ── Output checks (one per exercise, primary input case) ──────────────────────


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the correct output."""
    case = ex003.EX003_INPUT_CASES[exercise_no]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=case["inputs"],
        )
    except Exception as exc:  # noqa: BLE001 — report any runtime failure to the student
        return [str(exc)]
    expected = case["expected_output"]
    if output != expected:
        return [
            f"Expected: {expected!r}\n"
            f"     Got: {output!r}"
        ]
    return []


# ── Construct checks (the "why", not just the output) ─────────────────────────


def _check_refactor(n: int, constants: list[tuple[str, int]]) -> list[str]:
    """Check a pure-refactor exercise: constants defined, used, no bare literals."""
    tree = _parse(n)
    issues: list[str] = []
    for name, value in constants:
        if not _has_upper_assignment(tree, name):
            issues.append(f"Define the {name} constant (UPPER_CASE).")
        elif not _comparison_uses_name(tree, name):
            issues.append(f"Use {name} in the comparison instead of the bare number.")
        if _literal_in_comparison(tree, value):
            issues.append(
                f"Do not use the bare literal {value} in a comparison — use {name}."
            )
    return issues


def _check_value_messages(
    n: int,
    values: dict[str, int],
    *,
    msg_present: list[str],
    msg_absent: list[str],
) -> list[str]:
    """Check a value/message exercise: new constant values and messages."""
    tree = _parse(n)
    code = _source(n)
    issues: list[str] = []
    for name, expected in values.items():
        actual = _assignment_value(tree, name)
        if actual != expected:
            issues.append(f"Set {name} to {expected} (currently {actual}).")
    for present in msg_present:
        if not _code_contains(code, present):
            issues.append(f"Use the message: {present!r}")
    for absent in msg_absent:
        if _code_contains(code, absent):
            issues.append(f"Remove the old message fragment: {absent!r}")
    return issues


def _check_value_op_messages(
    n: int,
    values: dict[str, int],
    op: type[ast.cmpop],
    *,
    no_op: type[ast.cmpop] | None = None,
    msg_present: list[str],
    msg_absent: list[str],
) -> list[str]:
    """Check a value/message exercise that also requires a specific operator."""
    tree = _parse(n)
    code = _source(n)
    issues: list[str] = []
    for name, expected in values.items():
        actual = _assignment_value(tree, name)
        if actual != expected:
            issues.append(f"Set {name} to {expected} (currently {actual}).")
    if not _has_comparison_op(tree, op):
        issues.append(f"Use the {op.__name__} operator in a comparison.")
    if no_op is not None and _has_comparison_op(tree, no_op):
        issues.append(f"Do not use the {no_op.__name__} operator — swap it.")
    for present in msg_present:
        if not _code_contains(code, present):
            issues.append(f"Use the message: {present!r}")
    for absent in msg_absent:
        if _code_contains(code, absent):
            issues.append(f"Remove the old message fragment: {absent!r}")
    return issues


def _check_ex10() -> list[str]:
    """Exercise 10: new BULK_ORDER value plus the added delivery formula."""
    tree = _parse(10)
    code = _source(10)
    issues: list[str] = []
    if _assignment_value(tree, "BULK_ORDER") != 250:
        issues.append("Set BULK_ORDER to 250.")
    if "delivery = cost // 10" not in code:
        issues.append("Add the line: delivery = cost // 10")
    if "cost = cost + delivery" not in code and "cost += delivery" not in code:
        issues.append("Add: cost = cost + delivery (or cost += delivery)")
    return issues


_CONSTRUCT_CHECKS: dict[int, Callable[[], list[str]]] = {
    1: lambda: _check_refactor(
        1, [("FREE_DELIVERY_THRESHOLD", 50), ("STANDARD_DELIVERY_THRESHOLD", 20)]
    ),
    2: lambda: _check_refactor(
        2, [("SMALL_VAN_LIMIT", 4), ("MINIBUS_LIMIT", 8)]
    ),
    3: lambda: _check_refactor(
        3, [("LARGE_TOTAL", 100), ("MEDIUM_TOTAL", 50)]
    ),
    4: lambda: _check_value_messages(
        4,
        {"PASS_MARK": 40},
        msg_present=[
            "Well done! Score {score} is a pass",
            "Try again! Score {score} is a fail",
        ],
        msg_absent=["you passed", "you failed"],
    ),
    5: lambda: _check_value_op_messages(
        5,
        {"BIG_STUDY": 2},
        ast.GtE,
        no_op=ast.LtE,
        msg_present=[
            "Amazing! You studied {hours} hours",
            "Keep going — you studied {hours} hours",
        ],
        msg_absent=["keep going!", "Great! You studied"],
    ),
    6: lambda: _check_value_messages(
        6,
        {"HOT": 25},
        msg_present=["It is a heatwave! {temp}°C"],
        msg_absent=["Hot!"],
    ),
    7: lambda: _check_value_messages(
        7,
        {"SMALL": 12, "MEDIUM": 36},
        msg_present=[
            "Small order: {boxes} box(es), {leftover} leftover",
            "Medium order: {boxes} boxes, {leftover} leftover",
            "Large order: {boxes} boxes",
        ],
        msg_absent=["One box,", "Too many:"],
    ),
    8: lambda: _check_value_messages(
        8,
        {"BIG_SPEND": 120, "MID_SPEND": 75},
        msg_present=[
            "You saved £{discount} with 10% off",
            "You saved £{discount} with 5% off",
        ],
        msg_absent=["10% off: £{discount} saved", "5% off: £{discount} saved"],
    ),
    9: lambda: _check_value_messages(
        9,
        {"GRADE_A": 85, "GRADE_B": 70},
        msg_present=[],
        msg_absent=[],
    ),
    10: _check_ex10,
}


def _make_construct_check(exercise_no: int) -> Callable[[int], list[str]]:
    """Return a construct-check callable bound to *exercise_no*."""
    check = _CONSTRUCT_CHECKS[exercise_no]

    def _run(_n: int) -> list[str]:
        return check()

    return _run


# ── Build the interleaved CHECKS list ─────────────────────────────────────────


def _check_refactor_output(exercise_no: int) -> list[str]:
    """Exercises 1–3: output is correct ONLY once the refactor is done.

    The starter and solution produce identical output, so a pure output check
    would show green on the unedited student notebook and wrongly suggest the
    refactor is complete. We therefore require both the correct output AND the
    UPPER_CASE constants to be defined/used.
    """
    issues = _check_refactor(
        exercise_no,
        _REFACTOR_CONSTANTS[exercise_no],
    )
    issues += _check_input_output(exercise_no)
    return issues


_REFACTOR_CONSTANTS: dict[int, list[tuple[str, int]]] = {
    1: [("FREE_DELIVERY_THRESHOLD", 50), ("STANDARD_DELIVERY_THRESHOLD", 20)],
    2: [("SMALL_VAN_LIMIT", 4), ("MINIBUS_LIMIT", 8)],
    3: [("LARGE_TOTAL", 100), ("MEDIUM_TOTAL", 50)],
}


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in sorted(ex003.EX003_INPUT_CASES):
        if exercise_no <= 3:
            # Pure refactors: the output row is green only if the constants are
            # also introduced, otherwise the student sees a red row.
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Correct output (and uses constants)",
                    _check_refactor_output,
                )
            )
        else:
            # Interleave: output check first, then the construct check, so both
            # appear under the same "Exercise N" heading in the self-check table.
            checks.append(
                build_exercise_check(exercise_no, "Correct output", _check_input_output)
            )
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Uses the required construct",
                    _make_construct_check(exercise_no),
                )
            )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
