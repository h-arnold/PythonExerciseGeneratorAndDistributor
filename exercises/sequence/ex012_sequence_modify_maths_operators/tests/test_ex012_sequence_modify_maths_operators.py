from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
)

_EXERCISE_KEY = "ex012_sequence_modify_maths_operators"
ex012 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


# ── AST helpers ──────────────────────────────────────────────────────────────


def _has_floor_div(tree: ast.AST) -> bool:
    """Return True when the AST contains at least one floor-division (//) operator."""
    return any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv) for node in ast.walk(tree))


def _has_mod(tree: ast.AST) -> bool:
    """Return True when the AST contains at least one modulus (%) operator."""
    return any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) for node in ast.walk(tree))


def _has_div(tree: ast.AST) -> bool:
    """Return True when the AST contains at least one plain division (/) operator."""
    return any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) for node in ast.walk(tree))


def _has_call(tree: ast.AST, func_name: str) -> bool:
    """Return True when the AST contains a call to *func_name*."""
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _assert_strict_output(exercise_no: int, output: str, expected: str) -> None:
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact output {expected!r} but got {output!r}."
    )


# ── Exercise 1 — Floor division: full groups ─────────────────────────────────


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _run(1)
    _assert_strict_output(1, output, ex012.EX012_EXPECTED_OUTPUTS[1])


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _ast(1)
    assert _has_floor_div(tree), "Exercise 1 must use floor division //"
    assert not _has_div(tree), "Exercise 1 must not use plain / division"


# ── Exercise 2 — Modulus: leftover cupcakes ──────────────────────────────────


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _run(2)
    _assert_strict_output(2, output, ex012.EX012_EXPECTED_OUTPUTS[2])


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _ast(2)
    assert _has_mod(tree), "Exercise 2 must use modulus %"


# ── Exercise 3 — Floor division: complete teams ──────────────────────────────


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _run(3)
    _assert_strict_output(3, output, ex012.EX012_EXPECTED_OUTPUTS[3])


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _ast(3)
    assert _has_floor_div(tree), "Exercise 3 must use floor division //"
    assert not _has_div(tree), "Exercise 3 must not use plain / division"


# ── Exercise 4 — Modulus: leftover stickers ──────────────────────────────────


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _run(4)
    _assert_strict_output(4, output, ex012.EX012_EXPECTED_OUTPUTS[4])


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _ast(4)
    assert _has_mod(tree), "Exercise 4 must use modulus %"


# ── Exercise 5 — Round to 1 decimal place ────────────────────────────────────


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _run(5)
    _assert_strict_output(5, output, ex012.EX012_EXPECTED_OUTPUTS[5])


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _ast(5)
    assert _has_call(tree, "round"), "Exercise 5 must use round()"


# ── Exercise 6 — Round money to 2 decimal places ─────────────────────────────


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _run(6)
    _assert_strict_output(6, output, ex012.EX012_EXPECTED_OUTPUTS[6])


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _ast(6)
    assert _has_call(tree, "round"), "Exercise 6 must use round()"


# ── Exercise 7 — Split minutes: // and % together ────────────────────────────


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _run(7)
    _assert_strict_output(7, output, ex012.EX012_EXPECTED_OUTPUTS[7])


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _ast(7)
    assert _has_floor_div(
        tree), "Exercise 7 must use floor division // for hours"
    assert _has_mod(tree), "Exercise 7 must use modulus % for leftover minutes"
    assert not _has_div(tree), "Exercise 7 must not use plain / division"


# ── Exercise 8 — Convert pence: // and % together ────────────────────────────


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _run(8)
    _assert_strict_output(8, output, ex012.EX012_EXPECTED_OUTPUTS[8])


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _ast(8)
    assert _has_floor_div(
        tree), "Exercise 8 must use floor division // for pounds"
    assert _has_mod(tree), "Exercise 8 must use modulus % for leftover pence"
    assert not _has_div(tree), "Exercise 8 must not use plain / division"


# ── Exercise 9 — Round average speed to 1 decimal place ──────────────────────


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _run(9)
    _assert_strict_output(9, output, ex012.EX012_EXPECTED_OUTPUTS[9])


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _ast(9)
    assert _has_call(tree, "round"), "Exercise 9 must use round()"


# ── Exercise 10 — Mixed challenge: //, %, and round() ────────────────────────


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _run(10)
    _assert_strict_output(10, output, ex012.EX012_EXPECTED_OUTPUTS[10])


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _ast(10)
    assert _has_floor_div(
        tree), "Exercise 10 must use floor division // for full boxes"
    assert _has_mod(
        tree), "Exercise 10 must use modulus % for leftover crayons"
    assert _has_call(
        tree, "round"), "Exercise 10 must use round() for price per box"
