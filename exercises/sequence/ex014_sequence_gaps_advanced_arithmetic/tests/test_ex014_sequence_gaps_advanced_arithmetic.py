"""Notebook-facing output and semantic tests for ex014 advanced arithmetic."""

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
_construct_checks = load_exercise_test_module(EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    """Return the tagged-cell name for an exercise part."""
    return f"exercise{exercise_no}"


def _run_static(exercise_no: int) -> str:
    """Validate and execute a non-interactive exercise cell."""
    _assert_required_flow(exercise_no)
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    """Validate and execute an interactive exercise cell with deterministic inputs."""
    _assert_required_flow(exercise_no)
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _assert_all_input_cases(exercise_no: int) -> None:
    """Require exact output for every canonical case in one exercise part."""
    for case in _ex.EX014_INPUT_CASES[exercise_no]:
        inputs = list(case["inputs"])
        expected = case["expected_output"]
        output = _run_with_inputs(exercise_no, inputs)
        assert output == expected, (
            f"Exercise {exercise_no}, case {case['id']!r}: "
            f"expected {expected!r}, got {output!r}."
        )


def _required_flow_issues(exercise_no: int) -> list[str]:
    """Return semantic issues for the active notebook cell."""
    source = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return _construct_checks.required_flow_issues(ast.parse(source), exercise_no)


def _assert_required_flow(exercise_no: int) -> None:
    """Require the active notebook cell to satisfy the conservative semantic grammar."""
    issues = _required_flow_issues(exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


@pytest.mark.task(taskno=1)
def test_exercise1_exact_output() -> None:
    assert _run_static(1) == _ex.EX014_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_required_number_square_flow() -> None:
    _assert_required_flow(1)


@pytest.mark.task(taskno=2)
def test_exercise2_exact_output() -> None:
    assert _run_static(2) == _ex.EX014_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_required_number_cube_flow() -> None:
    _assert_required_flow(2)


@pytest.mark.task(taskno=3)
def test_exercise3_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(3)


@pytest.mark.task(taskno=3)
def test_exercise3_required_input_int_sqrt_flow() -> None:
    _assert_required_flow(3)


@pytest.mark.task(taskno=4)
def test_exercise4_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(4)


@pytest.mark.task(taskno=4)
def test_exercise4_required_base_int_exponent_int_power_flow() -> None:
    _assert_required_flow(4)


@pytest.mark.task(taskno=5)
def test_exercise5_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(5)


@pytest.mark.task(taskno=5)
def test_exercise5_required_input_float_square_flow() -> None:
    _assert_required_flow(5)


@pytest.mark.task(taskno=6)
def test_exercise6_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(6)


@pytest.mark.task(taskno=6)
def test_exercise6_required_float_inputs_multiplication_flow() -> None:
    _assert_required_flow(6)


@pytest.mark.task(taskno=7)
def test_exercise7_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(7)


@pytest.mark.task(taskno=7)
def test_exercise7_required_input_float_cube_flow() -> None:
    _assert_required_flow(7)


@pytest.mark.task(taskno=8)
def test_exercise8_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(8)


@pytest.mark.task(taskno=8)
def test_exercise8_required_input_int_sqrt_flow() -> None:
    _assert_required_flow(8)


@pytest.mark.task(taskno=9)
def test_exercise9_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(9)


@pytest.mark.task(taskno=9)
def test_exercise9_required_pi_radius_square_flow() -> None:
    _assert_required_flow(9)


@pytest.mark.task(taskno=10)
def test_exercise10_exact_output_for_all_cases() -> None:
    _assert_all_input_cases(10)


@pytest.mark.task(taskno=10)
def test_exercise10_required_base_int_exponent_int_power_flow() -> None:
    _assert_required_flow(10)
