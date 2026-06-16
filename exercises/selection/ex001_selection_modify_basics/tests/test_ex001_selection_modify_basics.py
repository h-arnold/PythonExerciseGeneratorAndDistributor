"""Tests for ex001 selection modify basics."""
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


_EXERCISE_KEY = "ex001_selection_modify_basics"
ex001 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_CACHE = RuntimeCache()


def _tag(n: int) -> str:
    return f"exercise{n}"


def _run(n: int) -> str:
    return run_cell_and_capture_output(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE)


def _run_with_inputs(n: int, inputs: list[str]) -> str:
    return run_cell_with_input(_EXERCISE_KEY, tag=_tag(n), inputs=inputs, cache=_CACHE)


def _ast(n: int) -> ast.Module:
    code = extract_tagged_code(_EXERCISE_KEY, tag=_tag(n), cache=_CACHE)
    return ast.parse(code)


def _has_if(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.If) for node in ast.walk(tree))


def _has_comparison(tree: ast.AST, ops: set[type[ast.cmpop]]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if type(op) in ops:
                    return True
    return False


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


# ── Exercise 1: Static output ────────────────────────────────────────────────


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    """Exercise 1 should print 'No it isn't.' (output-only, no input)."""
    output = _run(1)
    expected = ex001.EX001_EXPECTED_OUTPUTS[1]
    assert output == expected, f"Expected '{expected}' but got '{output}'"


@pytest.mark.task(taskno=1)
def test_exercise1_no_old_strings() -> None:
    """Exercise 1 should not contain old strings 'Arial' or 'Great choice!'."""
    tree = _ast(1)
    strings = _string_constants(tree)
    assert "Arial" not in strings, "Old value 'Arial' should be replaced"
    assert "Great choice!" not in strings, "Old message should be replaced"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    """Exercise 1 must use an if statement."""
    tree = _ast(1)
    assert _has_if(tree), "Must use an if statement"


# ── Exercise 2: Temperature threshold ────────────────────────────────────────


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    """Exercise 2 should print 'It's hot today!' when temp is 26."""
    details = ex001.EX001_INPUT_CASES[2]
    output = _run_with_inputs(2, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=2)
def test_exercise2_old_threshold_removed() -> None:
    """Exercise 2 should not compare against 30."""
    tree = _ast(2)
    strings = _string_constants(tree)
    assert not any("30" in s for s in strings), "Old value '30' should be removed"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    """Exercise 2 must use if with > comparison."""
    tree = _ast(2)
    assert _has_if(tree), "Must use an if statement"
    assert _has_comparison(tree, {ast.Gt}), "Must use > comparison"


# ── Exercise 3: Not equal to ─────────────────────────────────────────────────


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    """Exercise 3 should print 'That's not ten!' when input is 5."""
    details = ex001.EX001_INPUT_CASES[3]
    output = _run_with_inputs(3, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=3)
def test_exercise3_uses_not_equal() -> None:
    """Exercise 3 must use != (NotEq) comparison."""
    tree = _ast(3)
    assert _has_comparison(tree, {ast.NotEq}), "Must use != comparison"


@pytest.mark.task(taskno=3)
def test_exercise3_old_operator_removed() -> None:
    """Exercise 3 should not use == (Eq) comparison."""
    tree = _ast(3)
    assert not _has_comparison(tree, {ast.Eq}), (
        "Should not use ==, use != instead"
    )


# ── Exercise 4: Age category ─────────────────────────────────────────────────


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    """Exercise 4 should print 'You are a child' when age is 10."""
    details = ex001.EX001_INPUT_CASES[4]
    output = _run_with_inputs(4, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=4)
def test_exercise4_old_values_removed() -> None:
    """Exercise 4 should not contain old values '18' or 'minor'."""
    tree = _ast(4)
    strings = _string_constants(tree)
    assert not any("18" in s for s in strings), "Old value '18' should be removed"
    assert "minor" not in strings, "Old message 'minor' should be removed"


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    """Exercise 4 must use if with < comparison."""
    tree = _ast(4)
    assert _has_if(tree), "Must use an if statement"
    assert _has_comparison(tree, {ast.Lt}), "Must use < comparison"


# ── Exercise 5: Quiz check ───────────────────────────────────────────────────


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    """Exercise 5 should print 'Wrong answer!' when input is 7."""
    details = ex001.EX001_INPUT_CASES[5]
    output = _run_with_inputs(5, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=5)
def test_exercise5_uses_not_equal() -> None:
    """Exercise 5 must use != (NotEq) comparison."""
    tree = _ast(5)
    assert _has_comparison(tree, {ast.NotEq}), "Must use != comparison"


@pytest.mark.task(taskno=5)
def test_exercise5_old_operator_removed() -> None:
    """Exercise 5 should not use == (Eq) comparison."""
    tree = _ast(5)
    assert not _has_comparison(tree, {ast.Eq}), (
        "Should not use ==, use != instead"
    )


# ── Exercise 6: Score threshold ──────────────────────────────────────────────


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    """Exercise 6 should print 'Distinction!' when score is 90."""
    details = ex001.EX001_INPUT_CASES[6]
    output = _run_with_inputs(6, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=6)
def test_exercise6_old_threshold_removed() -> None:
    """Exercise 6 should not compare against 70."""
    tree = _ast(6)
    strings = _string_constants(tree)
    assert not any("70" in s for s in strings), "Old value '70' should be removed"


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    """Exercise 6 must use if with > comparison."""
    tree = _ast(6)
    assert _has_if(tree), "Must use an if statement"
    assert _has_comparison(tree, {ast.Gt}), "Must use > comparison"


# ── Exercise 7: Name check ───────────────────────────────────────────────────


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    """Exercise 7 should print 'Access denied!' when name is not 'Admin'."""
    details = ex001.EX001_INPUT_CASES[7]
    output = _run_with_inputs(7, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=7)
def test_exercise7_uses_not_equal() -> None:
    """Exercise 7 must use != (NotEq) comparison."""
    tree = _ast(7)
    assert _has_comparison(tree, {ast.NotEq}), "Must use != comparison"


@pytest.mark.task(taskno=7)
def test_exercise7_old_values_removed() -> None:
    """Exercise 7 should not contain old strings 'Welcome' or 'Admin' in the output message."""
    tree = _ast(7)
    strings = _string_constants(tree)
    assert "Welcome" not in strings, "Old message 'Welcome' should be removed"


# ── Exercise 8: Height restriction ───────────────────────────────────────────


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    """Exercise 8 should print 'You are tall enough to ride!' when height is 140."""
    details = ex001.EX001_INPUT_CASES[8]
    output = _run_with_inputs(8, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=8)
def test_exercise8_old_values_removed() -> None:
    """Exercise 8 should not contain old values."""
    tree = _ast(8)
    strings = _string_constants(tree)
    assert "You can ride!" not in strings, "Old message should be removed"
    assert not any("150" in s for s in strings), "Old value '150' should be removed"


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    """Exercise 8 must use if with > comparison."""
    tree = _ast(8)
    assert _has_if(tree), "Must use an if statement"
    assert _has_comparison(tree, {ast.Gt}), "Must use > comparison"


# ── Exercise 9: Drink order ──────────────────────────────────────────────────


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    """Exercise 9 should print 'Here is your coffee!' when drink is 'coffee'."""
    details = ex001.EX001_INPUT_CASES[9]
    output = _run_with_inputs(9, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=9)
def test_exercise9_old_values_removed() -> None:
    """Exercise 9 should not contain old values."""
    tree = _ast(9)
    strings = _string_constants(tree)
    assert "tea" not in strings, "Old value 'tea' should be replaced"
    assert "Here is your tea!" not in strings, "Old message should be replaced"


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    """Exercise 9 must use if with == comparison."""
    tree = _ast(9)
    assert _has_if(tree), "Must use an if statement"
    assert _has_comparison(tree, {ast.Eq}), "Must use == comparison"


# ── Exercise 10: Password check (hardest) ────────────────────────────────────


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    """Exercise 10 should print 'Wrong password!' when password is not 'opensesame'."""
    details = ex001.EX001_INPUT_CASES[10]
    output = _run_with_inputs(10, list(details["inputs"]))
    assert details["output_contains"] in output, (
        f"Expected '{details['output_contains']}' in output"
    )


@pytest.mark.task(taskno=10)
def test_exercise10_uses_not_equal() -> None:
    """Exercise 10 must use != (NotEq) comparison."""
    tree = _ast(10)
    assert _has_comparison(tree, {ast.NotEq}), "Must use != comparison"


@pytest.mark.task(taskno=10)
def test_exercise10_old_values_removed() -> None:
    """Exercise 10 should not contain old values."""
    tree = _ast(10)
    strings = _string_constants(tree)
    assert "secret123" not in strings, "Old password should be replaced"
    assert "Welcome!" not in strings, "Old message should be replaced"
