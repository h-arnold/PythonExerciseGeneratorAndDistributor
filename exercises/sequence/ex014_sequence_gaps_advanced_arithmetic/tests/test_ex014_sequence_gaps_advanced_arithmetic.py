from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex014_sequence_gaps_advanced_arithmetic"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_ast(tag: str) -> ast.AST:
    """Parse the tagged cell source into an AST."""
    return ast.parse(extract_tagged_code(_NOTEBOOK_PATH, tag=tag, cache=_CACHE))


def _has_pow_operator(tree: ast.AST) -> bool:
    """Return True if the AST tree contains a ``**`` (Pow) operation."""
    return any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow) for node in ast.walk(tree))


# ---------------------------------------------------------------------------
# Task 1 — Static output exercises (ex1, ex2: no input required)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("exercise1", _ex.EX014_EXPECTED_STATIC_OUTPUTS[1]),
        ("exercise2", _ex.EX014_EXPECTED_STATIC_OUTPUTS[2]),
    ],
)
def test_static_output(tag: str, expected: str) -> None:
    """Exercises 1-2 produce the correct output without any input."""
    output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)
    assert output.strip() == expected


@pytest.mark.task(taskno=1)
@pytest.mark.parametrize("tag", ["exercise1", "exercise2"])
def test_static_construct(tag: str) -> None:
    """Exercises 1-2 must use the ** operator (ast.Pow)."""
    tree = _as_ast(tag)
    assert _has_pow_operator(tree), f"{tag} must use the ** operator"


# ---------------------------------------------------------------------------
# Task 2 — Input-based output exercises (ex3–ex10)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=2)
@pytest.mark.parametrize(
    ("tag", "inputs", "expected"),
    [
        (
            f"exercise{n}",
            _ex.EX014_INPUT_CASES[n]["inputs"],
            _ex.EX014_INPUT_CASES[n]["expected_output"],
        )
        for n in sorted(_ex.EX014_INPUT_CASES)
    ],
)
def test_input_output(tag: str, inputs: list[str], expected: str) -> None:
    """Exercises 3-10 produce the correct output with the default inputs."""
    output = run_cell_with_input(
        _NOTEBOOK_PATH, tag=tag, inputs=inputs, cache=_CACHE)
    assert output.strip() == expected


@pytest.mark.task(taskno=2)
@pytest.mark.parametrize(
    ("tag", "inputs", "expected"),
    [
        (
            f"exercise{n}",
            case["inputs"],
            case["expected_output"],
        )
        for n in sorted(_ex.EX014_EDGE_CASES)
        for case in _ex.EX014_EDGE_CASES[n]
    ],
)
def test_input_edge_cases(tag: str, inputs: list[str], expected: str) -> None:
    """Exercises 3-10 produce correct output for varied inputs (not just defaults)."""
    output = run_cell_with_input(
        _NOTEBOOK_PATH, tag=tag, inputs=inputs, cache=_CACHE)
    assert output.strip() == expected


# ---------------------------------------------------------------------------
# Task 3 — Construct enforcement: ** operator in relevant exercises
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize(
    "tag",
    [f"exercise{n}" for n in range(1, 11) if n != 6],
)
def test_construct_uses_pow(tag: str) -> None:
    """Exercises 1-5, 7-10 must use the ** operator (the core learning
    objective). Exercise 6 (rectangle area) is excepted because it
    practises multiplication (width × length) rather than exponentiation."""
    tree = _as_ast(tag)
    assert _has_pow_operator(tree), (
        f"{tag} must use the ** operator (ast.Pow) — "
        f"this exercise teaches the power operator"
    )
