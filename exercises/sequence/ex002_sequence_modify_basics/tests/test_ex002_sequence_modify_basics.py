"""Tests for ex002 sequence modify basics."""

from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex002_sequence_modify_basics"
framework_support = load_exercise_test_module(_EXERCISE_KEY, "framework_support")
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _task_mark(exercise_no: int, title: str) -> pytest.MarkDecorator:
    return pytest.mark.task(name=f"Exercise {exercise_no}: {title}", taskno=exercise_no)


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_code(exercise_no: int) -> str:
    return extract_tagged_code(
        _EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _assert_clean(issues: list[str]) -> None:
    assert not issues, "\n".join(issues)


@_task_mark(1, "Logic")
def test_exercise1_logic() -> None:
    _assert_clean(framework_support.logic_issues(1, _exercise_output(1)))


@_task_mark(1, "Formatting")
def test_exercise1_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(1, _exercise_output(1), _exercise_code(1))
    )


@_task_mark(1, "Construct")
def test_exercise1_construct() -> None:
    _assert_clean(framework_support.construct_issues(1, _exercise_code(1)))


@_task_mark(2, "Logic")
def test_exercise2_logic() -> None:
    _assert_clean(framework_support.logic_issues(2, _exercise_output(2)))


@_task_mark(2, "Formatting")
def test_exercise2_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(2, _exercise_output(2), _exercise_code(2))
    )


@_task_mark(2, "Construct")
def test_exercise2_construct() -> None:
    _assert_clean(framework_support.construct_issues(2, _exercise_code(2)))


@_task_mark(3, "Logic")
def test_exercise3_logic() -> None:
    _assert_clean(framework_support.logic_issues(3, _exercise_output(3)))


@_task_mark(3, "Formatting")
def test_exercise3_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(3, _exercise_output(3), _exercise_code(3))
    )


@_task_mark(3, "Construct")
def test_exercise3_construct() -> None:
    _assert_clean(framework_support.construct_issues(3, _exercise_code(3)))


@_task_mark(4, "Logic")
def test_exercise4_logic() -> None:
    _assert_clean(framework_support.logic_issues(4, _exercise_output(4)))


@_task_mark(4, "Formatting")
def test_exercise4_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(4, _exercise_output(4), _exercise_code(4))
    )


@_task_mark(4, "Construct")
def test_exercise4_construct() -> None:
    _assert_clean(framework_support.construct_issues(4, _exercise_code(4)))


@_task_mark(5, "Logic")
def test_exercise5_logic() -> None:
    _assert_clean(framework_support.logic_issues(5, _exercise_output(5)))


@_task_mark(5, "Formatting")
def test_exercise5_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(5, _exercise_output(5), _exercise_code(5))
    )


@_task_mark(5, "Construct")
def test_exercise5_construct() -> None:
    _assert_clean(framework_support.construct_issues(5, _exercise_code(5)))


@_task_mark(6, "Logic")
def test_exercise6_logic() -> None:
    _assert_clean(framework_support.logic_issues(6, _exercise_output(6)))


@_task_mark(6, "Formatting")
def test_exercise6_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(6, _exercise_output(6), _exercise_code(6))
    )


@_task_mark(6, "Construct")
def test_exercise6_construct() -> None:
    _assert_clean(framework_support.construct_issues(6, _exercise_code(6)))


@_task_mark(7, "Logic")
def test_exercise7_logic() -> None:
    _assert_clean(framework_support.logic_issues(7, _exercise_output(7)))


@_task_mark(7, "Formatting")
def test_exercise7_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(7, _exercise_output(7), _exercise_code(7))
    )


@_task_mark(7, "Construct")
def test_exercise7_construct() -> None:
    _assert_clean(framework_support.construct_issues(7, _exercise_code(7)))


@_task_mark(8, "Logic")
def test_exercise8_logic() -> None:
    _assert_clean(framework_support.logic_issues(8, _exercise_output(8)))


@_task_mark(8, "Formatting")
def test_exercise8_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(8, _exercise_output(8), _exercise_code(8))
    )


@_task_mark(8, "Construct")
def test_exercise8_construct() -> None:
    _assert_clean(framework_support.construct_issues(8, _exercise_code(8)))


@_task_mark(9, "Logic")
def test_exercise9_logic() -> None:
    _assert_clean(framework_support.logic_issues(9, _exercise_output(9)))


@_task_mark(9, "Formatting")
def test_exercise9_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(9, _exercise_output(9), _exercise_code(9))
    )


@_task_mark(9, "Construct")
def test_exercise9_construct() -> None:
    _assert_clean(framework_support.construct_issues(9, _exercise_code(9)))


@_task_mark(10, "Logic")
def test_exercise10_logic() -> None:
    _assert_clean(framework_support.logic_issues(10, _exercise_output(10)))


@_task_mark(10, "Formatting")
def test_exercise10_formatting() -> None:
    _assert_clean(
        framework_support.formatting_issues(10, _exercise_output(10), _exercise_code(10))
    )


@_task_mark(10, "Construct")
def test_exercise10_construct() -> None:
    _assert_clean(framework_support.construct_issues(10, _exercise_code(10)))
