"""Exercise-local student checker definitions for ex004_selection_modify_logical_operators."""
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

_EXERCISE_KEY = "ex004_selection_modify_logical_operators"
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
ex004 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
has_boolop = construct_checks.has_boolop
has_unary_not = construct_checks.has_unary_not
has_floordiv = construct_checks.has_floordiv
and_groups_or = construct_checks.and_groups_or
assignment_value = construct_checks.assignment_value
code_contains = construct_checks.code_contains
_MESSAGES = construct_checks.MESSAGES


# ── Source helpers ────────────────────────────────────────────────────────────


def _parse(n: int) -> ast.Module:
    """Parse the tagged cell's source for exercise *n* into an AST."""
    return ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(n)))


def _source(n: int) -> str:
    """Return the raw source of the tagged cell for exercise *n*."""
    return extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(n))


def _messages_tuples(n: int) -> list[tuple[str, bool]]:
    """Derive (fragment, should_exist) tuples from the shared MESSAGES table."""
    return (
        [(fragment, True) for fragment in _MESSAGES[n]["present"]]
        + [(fragment, False) for fragment in _MESSAGES[n]["absent"]]
    )


# ── Output checks (one per exercise, primary input case) ──────────────────────


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the correct output."""
    case = ex004.EX004_INPUT_CASES[exercise_no]
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


def _check_operator(n: int, wanted: list[str]) -> list[str]:
    """Check which logical operators (*and*/*or*/*not*) appear in exercise *n*."""
    tree = _parse(n)
    issues: list[str] = []
    if "and" in wanted and not has_boolop(tree, ast.And):
        issues.append("Use and so both checks must pass together.")
    if "or" in wanted and not has_boolop(tree, ast.Or):
        issues.append("Use or so either check is enough.")
    if "not" in wanted and not has_unary_not(tree):
        issues.append("Use not to reverse the check.")
    if "grouping" in wanted and not and_groups_or(tree):
        issues.append("Bracket the either-or part inside the and check, e.g. "
                      "(spend >= SPEND_LIMIT or age >= SENIOR_AGE).")
    return issues


def _check_constants(
    n: int,
    constants: list[tuple[str, int]],
) -> list[str]:
    """Check that UP_CASE constants in exercise *n* keep their values."""
    tree = _parse(n)
    return [
        f"Keep {name} at {expected} (currently {assignment_value(tree, name)})."
        for name, expected in constants
        if assignment_value(tree, name) != expected
    ]


def _check_messages(n: int, messages: list[tuple[str, bool]]) -> list[str]:
    """Check messages present (True) or absent (False) in exercise *n*."""
    code = _source(n)
    issues: list[str] = []
    for fragment, should_exist in messages:
        if should_exist and not code_contains(code, fragment):
            issues.append(f"Use the message: {fragment!r}")
        if not should_exist and code_contains(code, fragment):
            issues.append(f"Remove the old message fragment: {fragment!r}")
    return issues


def _check_ex10() -> list[str]:
    """Exercise 10: discount maths plus per-tier operator rules."""
    tree = _parse(10)
    code = _source(10)
    issues: list[str] = []
    if not has_floordiv(tree):
        issues.append("Add the discount: find a tenth of the total with //.")
    if not any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "discount" for t in node.targets)
        for node in ast.walk(tree)
    ):
        issues.append("Add a discount variable for the tenth of the total.")
    if "total = total - discount" not in code and "total -= discount" not in code:
        issues.append("Take the discount off the total: total = total - discount")
    issues += _check_operator(10, ["and", "or", "grouping", "not"])
    issues += _check_constants(
        10,
        [("BIG_SPEND", 25), ("STANDARD_SPEND", 20), ("GOLD_AGE", 12), ("GOLD_FILMS", 5)],
    )
    issues += _check_messages(10, _messages_tuples(10))
    return issues


_CONSTRUCT_CHECKS: dict[int, Callable[[], list[str]]] = {
    1: lambda: _check_operator(1, ["and"])
    + _check_messages(1, _messages_tuples(1)),
    2: lambda: _check_operator(2, ["or"])
    + _check_messages(2, _messages_tuples(2)),
    3: lambda: _check_operator(3, ["or"])
    + _check_messages(3, _messages_tuples(3)),
    4: lambda: _check_operator(4, ["not"])
    + _check_messages(4, _messages_tuples(4)),
    5: lambda: _check_operator(5, ["and"])
    + _check_constants(5, [("LOW", 15), ("HIGH", 25)])
    + _check_messages(5, _messages_tuples(5)),
    6: lambda: _check_operator(6, ["or"])
    + _check_constants(6, [("CHILD_MAX", 5), ("SENIOR_MIN", 65)])
    + _check_messages(6, _messages_tuples(6)),
    7: lambda: _check_operator(7, ["and"])
    + _check_constants(7, [("LOW_TOTAL", 60), ("HIGH_TOTAL", 120)])
    + _check_messages(7, _messages_tuples(7)),
    8: lambda: _check_operator(8, ["and", "not"])
    + _check_constants(8, [("AGE_LIMIT", 10)])
    + _check_messages(8, _messages_tuples(8)),
    9: lambda: _check_operator(9, ["and", "or", "grouping"])
    + _check_constants(9, [("SPEND_LIMIT", 40), ("SENIOR_AGE", 60)])
    + _check_messages(9, _messages_tuples(9)),
    10: _check_ex10,
}


def _make_construct_check(exercise_no: int) -> Callable[[int], list[str]]:
    """Return a construct-check callable bound to *exercise_no*."""
    check = _CONSTRUCT_CHECKS[exercise_no]

    def _run(_n: int) -> list[str]:
        return check()

    return _run


# ── Build the interleaved CHECKS list ─────────────────────────────────────────


def _build_checks() -> list[ExerciseCheckDefinition]:
    """Output and construct rows appear together per exercise."""
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in sorted(ex004.EX004_INPUT_CASES):
        checks.append(
            build_exercise_check(exercise_no, "Correct output", _check_input_output)
        )
        checks.append(
            build_exercise_check(
                exercise_no,
                "Uses the required operators",
                _make_construct_check(exercise_no),
            )
        )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
