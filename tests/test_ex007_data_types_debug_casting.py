from __future__ import annotations

import ast

import pytest

from tests.exercise_expectations import ex007_data_types_debug_casting as ex007
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from tests.exercise_framework.expectations_helpers import is_valid_explanation

_NOTEBOOK_PATH = resolve_notebook_path(ex007.EX007_NOTEBOOK_PATH)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _run_static(exercise_no: int) -> str:
    return run_cell_and_capture_output(_NOTEBOOK_PATH, tag=_tag(exercise_no), cache=_CACHE)


def _run_with_inputs(exercise_no: int) -> str:
    case = ex007.EX007_INPUT_CASES[exercise_no]
    inputs = list(case["inputs"])
    return run_cell_with_input(_NOTEBOOK_PATH, tag=_tag(exercise_no), inputs=inputs, cache=_CACHE)


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(_NOTEBOOK_PATH, tag=_tag(exercise_no), cache=_CACHE)
    return ast.parse(code)


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _assert_interactive_output(exercise_no: int) -> None:
    case = ex007.EX007_INPUT_CASES[exercise_no]
    output = _run_with_inputs(exercise_no)
    prompts = case["prompts"]
    assert isinstance(prompts, list)
    for prompt in prompts:
        assert isinstance(prompt, str)
        assert prompt in output
    last_line = output.strip().splitlines()[-1]
    expected_last_line = case["last_line"]
    assert isinstance(expected_last_line, str)
    assert last_line.endswith(expected_last_line)


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _run_static(1) == ex007.EX007_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(1))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _run_static(2) == ex007.EX007_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(2))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    _assert_interactive_output(3)


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    assert _has_call(tree, "int")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(3))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _run_static(4) == ex007.EX007_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(4))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    _assert_interactive_output(5)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    assert _has_call(tree, "int")


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(5))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    _assert_interactive_output(6)


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    assert _has_call(tree, "float")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(6))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    _assert_interactive_output(7)


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _has_call(tree, "float")
    assert _has_call(tree, "int")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(7))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    _assert_interactive_output(8)


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _has_call(tree, "int")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(8))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    _assert_interactive_output(9)


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _has_call(tree, "int")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(9))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    _assert_interactive_output(10)


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    assert _has_call(tree, "float")
    assert _has_call(tree, "int")
    assert _has_call(tree, "str")


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(10))
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )
