"""Tests for ex009 sequence modify f-strings."""

from __future__ import annotations

import ast
from typing import Final

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex009_sequence_modify_fstrings"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
_CACHE = RuntimeCache()
_EXPECTED_PAGES_TOMORROW: Final[int] = 8
_OLD_PAGES_TOMORROW: Final[int] = 3


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _assert_construct(exercise_no: int) -> None:
    issues = _construct_checks.construct_issues(_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {'; '.join(issues)}"


def _assert_strict_output(exercise_no: int, output: str, expected: str) -> None:
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact output {expected!r} but got {output!r}."
    )


def _assert_all_input_cases(exercise_no: int) -> None:
    cases = _ex.EX009_INPUT_CASES[exercise_no]
    assert len(cases) >= _ex.EX009_MIN_INPUT_CASES, (
        f"Exercise {exercise_no} needs at least {_ex.EX009_MIN_INPUT_CASES} input cases."
    )
    for case in cases:
        inputs = list(case["inputs"])
        output = _run_with_inputs(exercise_no, inputs)
        _assert_strict_output(exercise_no, output, case["expected_output"])


def _has_operator(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and type(node.op) is operator_type
        for node in ast.walk(tree)
    )


# ---------------------------------------------------------------------------
# Static-output exercises
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    _assert_strict_output(1, _run(1), _ex.EX009_EXPECTED_STATIC_OUTPUTS[1])


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_construct(1)


@pytest.mark.task(taskno=1)
def test_exercise1_no_old_concatenation() -> None:
    assert not _construct_checks.has_addition_in_print(_ast(1))


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    _assert_strict_output(2, _run(2), _ex.EX009_EXPECTED_STATIC_OUTPUTS[2])


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_construct(2)


@pytest.mark.task(taskno=2)
def test_exercise2_replaces_cat_assignment() -> None:
    tree = _ast(2)
    values = _construct_checks.assignment_literal_values(tree, "pet")
    literals = _construct_checks.string_literal_values(tree)
    assert "rabbit" in values
    assert "cat" not in literals
    assert not _construct_checks.has_addition_in_print(tree)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    _assert_strict_output(3, _run(3), _ex.EX009_EXPECTED_STATIC_OUTPUTS[3])


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_construct(3)


@pytest.mark.task(taskno=3)
def test_exercise3_no_old_concatenation() -> None:
    assert not _construct_checks.has_addition_in_print(_ast(3))


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    _assert_strict_output(4, _run(4), _ex.EX009_EXPECTED_STATIC_OUTPUTS[4])


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _assert_construct(4)


@pytest.mark.task(taskno=4)
def test_exercise4_replaces_science_assignment() -> None:
    tree = _ast(4)
    values = _construct_checks.assignment_literal_values(tree, "subject")
    literals = _construct_checks.string_literal_values(tree)
    assert "computing" in values
    assert "science" not in literals
    assert not _construct_checks.has_addition_in_print(tree)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    _assert_strict_output(7, _run(7), _ex.EX009_EXPECTED_STATIC_OUTPUTS[7])


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    _assert_construct(7)


@pytest.mark.task(taskno=7)
def test_exercise7_replaces_str_and_concatenation() -> None:
    tree = _ast(7)
    assert not _construct_checks.has_call(tree, "str")
    assert not _construct_checks.has_addition_in_print(tree)


# ---------------------------------------------------------------------------
# Input/output exercises
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    _assert_all_input_cases(5)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_construct(5)


@pytest.mark.task(taskno=5)
def test_exercise5_no_old_concatenation() -> None:
    assert not _construct_checks.has_addition_in_print(_ast(5))


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    _assert_all_input_cases(6)


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    _assert_construct(6)


@pytest.mark.task(taskno=6)
def test_exercise6_no_old_concatenation() -> None:
    assert not _construct_checks.has_addition_in_print(_ast(6))


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    _assert_all_input_cases(9)


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    _assert_construct(9)


@pytest.mark.task(taskno=9)
def test_exercise9_replaces_tomorrow_value() -> None:
    values = _construct_checks.assignment_literal_values(_ast(9), "pages_tomorrow")
    assert _EXPECTED_PAGES_TOMORROW in values
    assert _OLD_PAGES_TOMORROW not in values


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    _assert_all_input_cases(10)


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    _assert_construct(10)


@pytest.mark.task(taskno=10)
def test_exercise10_rejects_old_addition() -> None:
    assert not _has_operator(_ast(10), ast.Add)


# ---------------------------------------------------------------------------
# Arithmetic/output exercise
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    _assert_strict_output(8, _run(8), _ex.EX009_EXPECTED_STATIC_OUTPUTS[8])


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    _assert_construct(8)


@pytest.mark.task(taskno=8)
def test_exercise8_rejects_old_subtraction() -> None:
    assert not _has_operator(_ast(8), ast.Sub)


@pytest.mark.task(taskno=8)
def test_exercise8_uses_calculated_total_in_final_fstring() -> None:
    tree = _ast(8)
    assert _construct_checks.required_placeholder_names(tree)
    _assert_construct(8)
