from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EX008_EXERCISE_KEY = "ex008_sequence_make_consolidation"
ex008 = load_exercise_test_module(_EX008_EXERCISE_KEY, "expectations")
checks = load_exercise_test_module(_EX008_EXERCISE_KEY, "checks")
construct_errors = checks.construct_errors
output_errors = checks.output_errors
capture_interactive_events = checks.capture_interactive_events
interactive_event_errors = checks.interactive_event_errors
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run_static(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EX008_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EX008_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _check_construct(exercise_no: int) -> None:
    assert not construct_errors(exercise_no, _exercise_ast(exercise_no))


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert not output_errors(1, _run_static(1))


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _check_construct(1)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert not output_errors(2, _run_static(2))


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _check_construct(2)


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[3])
def test_exercise3_logic(case: dict[str, object]) -> None:
    inputs = case["inputs"]
    events = capture_interactive_events(_EX008_EXERCISE_KEY, 3, inputs)
    assert not interactive_event_errors(3, events, inputs)


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _check_construct(3)


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[4])
def test_exercise4_logic(case: dict[str, object]) -> None:
    inputs = case["inputs"]
    events = capture_interactive_events(_EX008_EXERCISE_KEY, 4, inputs)
    assert not interactive_event_errors(4, events, inputs)


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _check_construct(4)


@pytest.mark.task(taskno=5)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[5])
def test_exercise5_logic(case: dict[str, object]) -> None:
    inputs = case["inputs"]
    events = capture_interactive_events(_EX008_EXERCISE_KEY, 5, inputs)
    assert not interactive_event_errors(5, events, inputs)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _check_construct(5)
