"""Tests for ex011 sequence gaps consolidation."""

from __future__ import annotations

import ast
from typing import Any, cast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex011_sequence_gaps_consolidation"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


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


def _input_cases(exercise_no: int) -> tuple[dict[str, Any], ...]:
    cases = cast(tuple[dict[str, Any], ...], _ex.EX011_INPUT_CASES[exercise_no])
    assert len(cases) >= _ex.EX011_MIN_INPUT_CASES, (
        f"Exercise {exercise_no} needs at least {_ex.EX011_MIN_INPUT_CASES} input cases."
    )
    return cases


def _assert_exact_output(exercise_no: int, output: str, expected: str) -> None:
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact output {expected!r}, got {output!r}."
    )


def _assert_input_case(exercise_no: int, case: dict[str, Any]) -> None:
    inputs = list(case["inputs"])
    output = _exercise_output_with_inputs(exercise_no, inputs)
    prompts = list(_ex.EX011_EXPECTED_PROMPTS[exercise_no])
    assert output.splitlines()[: len(prompts)] == prompts, (
        f"Exercise {exercise_no}: prompt flow must be exact."
    )
    _assert_exact_output(exercise_no, output, case["expected_output"])


def _assert_semantics(exercise_no: int) -> None:
    issues = _construct_checks.required_flow_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


@pytest.mark.task(taskno=1)
def test_exercise1_exact_output() -> None:
    output = _exercise_output(1)
    _assert_exact_output(1, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[1])


@pytest.mark.task(taskno=1)
def test_exercise1_semantic_sensitivity() -> None:
    _assert_semantics(1)


@pytest.mark.task(taskno=2)
def test_exercise2_exact_output() -> None:
    output = _exercise_output(2)
    _assert_exact_output(2, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[2])


@pytest.mark.task(taskno=2)
def test_exercise2_semantic_sensitivity() -> None:
    _assert_semantics(2)


@pytest.mark.task(taskno=3)
def test_exercise3_case_1() -> None:
    _assert_input_case(3, _input_cases(3)[0])


@pytest.mark.task(taskno=3)
def test_exercise3_case_2() -> None:
    _assert_input_case(3, _input_cases(3)[1])


@pytest.mark.task(taskno=3)
def test_exercise3_case_3() -> None:
    _assert_input_case(3, _input_cases(3)[2])


@pytest.mark.task(taskno=3)
def test_exercise3_semantic_sensitivity() -> None:
    _assert_semantics(3)


@pytest.mark.task(taskno=4)
def test_exercise4_exact_output() -> None:
    output = _exercise_output(4)
    _assert_exact_output(4, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[4])


@pytest.mark.task(taskno=4)
def test_exercise4_semantic_sensitivity() -> None:
    _assert_semantics(4)


@pytest.mark.task(taskno=5)
def test_exercise5_exact_output() -> None:
    output = _exercise_output(5)
    _assert_exact_output(5, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[5])


@pytest.mark.task(taskno=5)
def test_exercise5_semantic_sensitivity() -> None:
    _assert_semantics(5)


@pytest.mark.task(taskno=6)
def test_exercise6_exact_output() -> None:
    output = _exercise_output(6)
    _assert_exact_output(6, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[6])


@pytest.mark.task(taskno=6)
def test_exercise6_semantic_sensitivity() -> None:
    _assert_semantics(6)


@pytest.mark.task(taskno=7)
def test_exercise7_exact_output() -> None:
    output = _exercise_output(7)
    _assert_exact_output(7, output, _ex.EX011_EXPECTED_STATIC_OUTPUTS[7])


@pytest.mark.task(taskno=7)
def test_exercise7_fstring_and_semantic_sensitivity() -> None:
    _assert_semantics(7)


@pytest.mark.task(taskno=8)
def test_exercise8_case_1() -> None:
    _assert_input_case(8, _input_cases(8)[0])


@pytest.mark.task(taskno=8)
def test_exercise8_case_2() -> None:
    _assert_input_case(8, _input_cases(8)[1])


@pytest.mark.task(taskno=8)
def test_exercise8_case_3() -> None:
    _assert_input_case(8, _input_cases(8)[2])


@pytest.mark.task(taskno=8)
def test_exercise8_semantic_sensitivity() -> None:
    _assert_semantics(8)


@pytest.mark.task(taskno=9)
def test_exercise9_case_1() -> None:
    _assert_input_case(9, _input_cases(9)[0])


@pytest.mark.task(taskno=9)
def test_exercise9_case_2() -> None:
    _assert_input_case(9, _input_cases(9)[1])


@pytest.mark.task(taskno=9)
def test_exercise9_case_3() -> None:
    _assert_input_case(9, _input_cases(9)[2])


@pytest.mark.task(taskno=9)
def test_exercise9_semantic_sensitivity() -> None:
    _assert_semantics(9)


@pytest.mark.task(taskno=10)
def test_exercise10_case_1() -> None:
    _assert_input_case(10, _input_cases(10)[0])


@pytest.mark.task(taskno=10)
def test_exercise10_case_2() -> None:
    _assert_input_case(10, _input_cases(10)[1])


@pytest.mark.task(taskno=10)
def test_exercise10_case_3() -> None:
    _assert_input_case(10, _input_cases(10)[2])


@pytest.mark.task(taskno=10)
def test_exercise10_semantic_sensitivity() -> None:
    _assert_semantics(10)
