"""Tests for ex013 sequence debug maths operators."""

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
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


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
    return ast.parse(
        extract_tagged_code(
            _NOTEBOOK_PATH,
            tag=_tag(exercise_no),
            cache=_CACHE,
        )
    )


def _assert_input_cases(exercise_no: int) -> None:
    cases = _ex.EX013_INPUT_CASES[exercise_no]
    assert len(cases) >= _ex.EX013_MIN_INPUT_CASES
    actual = [_exercise_output_with_inputs(exercise_no, list(case["inputs"])) for case in cases]
    expected = [case["expected_output"] for case in cases]
    assert actual == expected


def _assert_construct(exercise_no: int) -> None:
    issues = _construct_checks.construct_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {'; '.join(issues)}"


def _assert_explanation(exercise_no: int) -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH,
        tag=_explanation_tag(exercise_no),
    )
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX013_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX013_PLACEHOLDER_PHRASES,
    ), f"Exercise {exercise_no} needs a meaningful explanation"


@pytest.mark.task(taskno=1)
def test_exercise1_output() -> None:
    assert _exercise_output(1) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct_and_data_flow() -> None:
    _assert_construct(1)


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    _assert_explanation(1)


@pytest.mark.task(taskno=2)
def test_exercise2_output() -> None:
    assert _exercise_output(2) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct_and_data_flow() -> None:
    _assert_construct(2)


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    _assert_explanation(2)


@pytest.mark.task(taskno=3)
def test_exercise3_output() -> None:
    assert _exercise_output(3) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct_and_data_flow() -> None:
    _assert_construct(3)


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    _assert_explanation(3)


@pytest.mark.task(taskno=4)
def test_exercise4_input_cases() -> None:
    _assert_input_cases(4)


@pytest.mark.task(taskno=4)
def test_exercise4_construct_and_data_flow() -> None:
    _assert_construct(4)


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    _assert_explanation(4)


@pytest.mark.task(taskno=5)
def test_exercise5_output() -> None:
    assert _exercise_output(5) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct_and_data_flow() -> None:
    _assert_construct(5)


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    _assert_explanation(5)


@pytest.mark.task(taskno=6)
def test_exercise6_output() -> None:
    assert _exercise_output(6) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_construct_and_data_flow() -> None:
    _assert_construct(6)


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    _assert_explanation(6)


@pytest.mark.task(taskno=7)
def test_exercise7_input_cases() -> None:
    _assert_input_cases(7)


@pytest.mark.task(taskno=7)
def test_exercise7_construct_and_data_flow() -> None:
    _assert_construct(7)


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    _assert_explanation(7)


@pytest.mark.task(taskno=8)
def test_exercise8_output() -> None:
    assert _exercise_output(8) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct_and_data_flow() -> None:
    _assert_construct(8)


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    _assert_explanation(8)


@pytest.mark.task(taskno=9)
def test_exercise9_output() -> None:
    assert _exercise_output(9) == _ex.EX013_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct_and_data_flow() -> None:
    _assert_construct(9)


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    _assert_explanation(9)


@pytest.mark.task(taskno=10)
def test_exercise10_input_cases() -> None:
    _assert_input_cases(10)


@pytest.mark.task(taskno=10)
def test_exercise10_construct_and_data_flow() -> None:
    _assert_construct(10)


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    _assert_explanation(10)
