"""Tests for expectation helper behaviour."""

from __future__ import annotations

from tests import exercise_expectations
from tests.exercise_expectations import (
    EX002_EXPECTED_MULTI_LINE,
    EX002_EXPECTED_PRINT_CALLS,
    EX002_EXPECTED_SINGLE_LINE,
    EX002_NOTEBOOK_PATH,
)
from tests.exercise_framework.expectations import (
    EX002_NOTEBOOK_PATH as FRAMEWORK_EX002_NOTEBOOK_PATH,
)
from tests.exercise_framework.expectations import (
    expected_output_lines,
    expected_output_text,
    expected_print_call_count,
)


def test_expected_output_lines_normalises_single_line() -> None:
    lines = expected_output_lines(
        1,
        single_line=EX002_EXPECTED_SINGLE_LINE,
        multi_line=EX002_EXPECTED_MULTI_LINE,
    )
    assert lines == [EX002_EXPECTED_SINGLE_LINE[1]]


def test_expected_output_lines_normalises_multi_line() -> None:
    lines = expected_output_lines(
        6,
        single_line=EX002_EXPECTED_SINGLE_LINE,
        multi_line=EX002_EXPECTED_MULTI_LINE,
    )
    assert lines == EX002_EXPECTED_MULTI_LINE[6]


def test_expected_output_text_uses_trailing_newline() -> None:
    expected = "\n".join(EX002_EXPECTED_MULTI_LINE[9]) + "\n"
    assert (
        expected_output_text(
            9,
            single_line=EX002_EXPECTED_SINGLE_LINE,
            multi_line=EX002_EXPECTED_MULTI_LINE,
        )
        == expected
    )


def test_expected_print_call_count_returns_value_or_none() -> None:
    assert (
        expected_print_call_count(
            4,
            expectations=EX002_EXPECTED_PRINT_CALLS,
        )
        == 1
    )
    assert (
        expected_print_call_count(
            1,
            expectations=EX002_EXPECTED_PRINT_CALLS,
        )
        is None
    )


def test_expected_helpers_return_none_for_unknown_exercise() -> None:
    exercise_no = 999
    assert (
        expected_output_lines(
            exercise_no,
            single_line=EX002_EXPECTED_SINGLE_LINE,
            multi_line=EX002_EXPECTED_MULTI_LINE,
        )
        is None
    )
    assert (
        expected_output_text(
            exercise_no,
            single_line=EX002_EXPECTED_SINGLE_LINE,
            multi_line=EX002_EXPECTED_MULTI_LINE,
        )
        is None
    )
    assert (
        expected_print_call_count(
            exercise_no,
            expectations=EX002_EXPECTED_PRINT_CALLS,
        )
        is None
    )


def test_framework_expectations_use_package_exports() -> None:
    assert FRAMEWORK_EX002_NOTEBOOK_PATH == EX002_NOTEBOOK_PATH
    assert FRAMEWORK_EX002_NOTEBOOK_PATH is exercise_expectations.EX002_NOTEBOOK_PATH
