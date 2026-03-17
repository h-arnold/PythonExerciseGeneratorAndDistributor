from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework.ex007_construct_checks import (
    has_binop,
    has_call,
    interactive_construct_issues,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from tests.exercise_expectations import ex007_sequence_debug_casting as ex007
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

_EX007_EXERCISE_KEY = "ex007_sequence_debug_casting"
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _run_static(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EX007_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
        variant="solution",
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _EX007_EXERCISE_KEY,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
        variant="solution",
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EX007_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
        variant="solution",
    )
    return ast.parse(code)


def _exercise_explanation(exercise_no: int) -> str:
    return get_explanation_cell(
        _EX007_EXERCISE_KEY,
        tag=_explanation_tag(exercise_no),
        variant="solution",
    )


def _assert_interactive_constructs(exercise_no: int) -> None:
    tree = _exercise_ast(exercise_no)
    rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
    issues = interactive_construct_issues(
        tree,
        expected_input_count=len(ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
        required_calls=rules.get("required_calls", ()),
        required_ops=rules.get("required_ops", ()),
        forbidden_ops=rules.get("forbidden_ops", ()),
    )
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


def _assert_interactive_output(exercise_no: int) -> None:
    for case in ex007.EX007_INPUT_CASES[exercise_no]:
        output = _run_with_inputs(exercise_no, list(case["inputs"]))
        expected_output = case["expected_output"]
        assert output == expected_output, (
            f"Exercise {exercise_no}: expected exact output {expected_output!r} but got {output!r}."
        )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _run_static(1) == ex007.EX007_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert has_call(tree, "str")


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = _exercise_explanation(1)
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
    assert has_call(tree, "str")


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = _exercise_explanation(2)
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
    _assert_interactive_constructs(3)


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = _exercise_explanation(3)
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
    assert has_binop(tree, ast.Div)
    assert not has_binop(tree, ast.FloorDiv)


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = _exercise_explanation(4)
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
    _assert_interactive_constructs(5)


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = _exercise_explanation(5)
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
    _assert_interactive_constructs(6)


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = _exercise_explanation(6)
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
    _assert_interactive_constructs(7)


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = _exercise_explanation(7)
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
    _assert_interactive_constructs(8)


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = _exercise_explanation(8)
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
    _assert_interactive_constructs(9)


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = _exercise_explanation(9)
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
    _assert_interactive_constructs(10)


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = _exercise_explanation(10)
    assert is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    )
