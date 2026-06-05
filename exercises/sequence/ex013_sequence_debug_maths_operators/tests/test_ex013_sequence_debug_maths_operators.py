from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex013_sequence_debug_maths_operators"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _exercise_source(exercise_no: int) -> str:
    return extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _has_f_string(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _call_count(tree: ast.AST, func_name: str) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == func_name
    )


def _has_binop(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


def _print_uses_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id == name:
                    return True
    return False


# ---------------------------------------------------------------------------
# Exercise 1 — Full groups only  (taskno=1)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _exercise_output(1) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _has_f_string(tree), "Exercise 1 must use an f-string"
    assert _has_binop(
        tree, ast.FloorDiv), "Exercise 1 must use // (floor division)"
    source = _exercise_source(1)
    assert "+ str(" not in source and "+str(" not in source, "Exercise 1 must not use + concatenation"


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(1))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 2 — Find the leftover  (taskno=2)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _exercise_output(2) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _has_f_string(tree), "Exercise 2 must use an f-string"
    assert _has_binop(tree, ast.Mod), "Exercise 2 must use % (modulus)"
    source = _exercise_source(2)
    assert "+ str(" not in source and "+str(" not in source, "Exercise 2 must not use + concatenation"


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(2))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 3 — Round an average  (taskno=3)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _exercise_output(3) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    assert _has_call(tree, "round"), "Exercise 3 must use round()"


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(3))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 4 — Teams from input  (taskno=4)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    case = _ex.EX013_INPUT_CASES[4]
    assert _exercise_output_with_inputs(
        4, list(case["inputs"])) == case["expected_output"]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    assert _has_call(tree, "int"), "Exercise 4 must cast input with int()"
    assert _has_call(tree, "input"), "Exercise 4 must use input()"
    assert _has_binop(tree, ast.FloorDiv), "Exercise 4 must use //"


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(4))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 5 — Round money to 2 decimal places  (taskno=5)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    assert _exercise_output(5) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    assert _has_call(tree, "round"), "Exercise 5 must use round()"
    assert _print_uses_name(tree, "total"), (
        "Exercise 5 must print the 'total' variable, not 'price'"
    )


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(5))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 6 — Split minutes  (taskno=6)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    assert _exercise_output(6) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    assert _has_binop(
        tree, ast.FloorDiv), "Exercise 6 must use // (floor division)"
    assert _has_binop(tree, ast.Mod), "Exercise 6 must use % (modulus)"


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(6))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 7 — Pence to pounds  (taskno=7)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    case = _ex.EX013_INPUT_CASES[7]
    assert _exercise_output_with_inputs(
        7, list(case["inputs"])) == case["expected_output"]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _has_call(tree, "int"), "Exercise 7 must cast input with int()"
    assert _has_call(tree, "input"), "Exercise 7 must use input()"
    assert _has_binop(tree, ast.Mod), "Exercise 7 must use % (modulus)"


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(7))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 8 — Area of a square  (taskno=8)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    assert _exercise_output(8) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _has_call(tree, "round"), "Exercise 8 must use round()"
    assert _print_uses_name(tree, "rounded"), (
        "Exercise 8 must print the 'rounded' variable, not 'area'"
    )


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(8))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 9 — Apples into bags  (taskno=9)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _exercise_output(9) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _has_f_string(tree), "Exercise 9 must use an f-string"
    assert _has_binop(
        tree, ast.FloorDiv), "Exercise 9 must use // (floor division)"


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(9))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 10 — Mixed challenge  (taskno=10)
# ---------------------------------------------------------------------------

@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    case = _ex.EX013_INPUT_CASES[10]
    assert _exercise_output_with_inputs(
        10, list(case["inputs"])) == case["expected_output"]


_EX10_MIN_INT_CASTS = 2


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    int_calls = _call_count(tree, "int")
    assert int_calls >= _EX10_MIN_INT_CASTS, (
        f"Exercise 10 must cast at least two inputs with int(); found {int_calls}"
    )
    assert _has_call(tree, "input"), "Exercise 10 must use input()"
    assert _has_binop(
        tree, ast.FloorDiv), "Exercise 10 must use // (floor division)"
    assert _has_binop(tree, ast.Mod), "Exercise 10 must use % (modulus)"


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH, tag=_explanation_tag(10))
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Shared guard: no TODO placeholders in any exercise cell
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exercise_no", list(range(1, 11)))
def test_exercise_cells_no_todo(exercise_no: int) -> None:
    source = _exercise_source(exercise_no)
    assert "TODO" not in source, (
        f"exercise{exercise_no} still contains a TODO placeholder"
    )
