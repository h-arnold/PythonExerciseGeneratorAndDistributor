from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex006_sequence_modify_casting"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_checks = load_exercise_test_module(EXERCISE_KEY, "checks")


def _source(number: int) -> str:
    return extract_tagged_code(EXERCISE_KEY, tag=f"exercise{number}")


def _static_output(number: int) -> str:
    return run_cell_and_capture_output(EXERCISE_KEY, tag=f"exercise{number}")


def _input_output(number: int, inputs: list[str]) -> str:
    return run_cell_with_input(EXERCISE_KEY, tag=f"exercise{number}", inputs=inputs)


def _check_static(number: int) -> None:
    assert _checks.matches_segments(_static_output(number), [_ex.EX006_EXPECTED_OUTPUTS[number]])
    assert _checks.complete(number, _source(number))


def _check_interactive(number: int) -> None:
    case = _ex.EX006_INPUT_EXPECTATIONS[number]
    for inputs, segments in (
        (case["inputs"], case["expected_segments"]),
        (case["alternate_inputs"], case["alternate_segments"]),
    ):
        assert _checks.matches_segments(_input_output(number, inputs), segments)
    assert _checks.complete(number, _source(number))


@pytest.mark.task(taskno=1)
def test_exercise1_both_strings_are_converted_before_addition() -> None:
    _check_static(1)


@pytest.mark.task(taskno=2)
def test_exercise2_both_prices_are_converted_before_addition() -> None:
    _check_static(2)


@pytest.mark.task(taskno=3)
def test_exercise3_cast_days_are_multiplied() -> None:
    _check_static(3)


@pytest.mark.task(taskno=4)
def test_exercise4_string_cast_and_concatenation_reach_output() -> None:
    _check_static(4)


@pytest.mark.task(taskno=5)
def test_exercise5_integer_cast_reaches_output_without_later_overwrite() -> None:
    _check_static(5)


@pytest.mark.task(taskno=6)
def test_exercise6_input_is_cast_and_doubled() -> None:
    _check_interactive(6)


@pytest.mark.task(taskno=7)
def test_exercise7_input_price_is_cast_and_added() -> None:
    _check_interactive(7)


@pytest.mark.task(taskno=8)
def test_exercise8_cast_dimensions_are_multiplied() -> None:
    _check_static(8)


@pytest.mark.task(taskno=9)
def test_exercise9_cost_cast_reaches_output() -> None:
    _check_static(9)


@pytest.mark.task(taskno=10)
def test_exercise10_ordered_prompts_and_converted_sum() -> None:
    _check_interactive(10)
