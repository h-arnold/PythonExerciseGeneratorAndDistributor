"""Tests for expectation helper behaviour."""

from __future__ import annotations

import exercise_runtime_support.exercise_framework.expectations as framework_expectations
from exercise_runtime_support.exercise_framework.expectations import (
    expected_output_lines,
    expected_output_text,
    expected_print_call_count,
)

_SINGLE_LINE = {1: "Hello Python!", 4: "One line"}
_MULTI_LINE = {6: ["Learning", "to", "code rocks"], 9: ["10 minus 3 equals", "7"]}
_PRINT_CALLS = {4: 1, 6: 3, 9: 2}


def test_expected_output_lines_normalises_single_line() -> None:
    lines = expected_output_lines(
        1,
        single_line=_SINGLE_LINE,
        multi_line=_MULTI_LINE,
    )
    assert lines == [_SINGLE_LINE[1]]


def test_expected_output_lines_normalises_multi_line() -> None:
    lines = expected_output_lines(
        6,
        single_line=_SINGLE_LINE,
        multi_line=_MULTI_LINE,
    )
    assert lines == _MULTI_LINE[6]


def test_expected_output_text_uses_trailing_newline() -> None:
    expected = "\n".join(_MULTI_LINE[9]) + "\n"
    assert (
        expected_output_text(
            9,
            single_line=_SINGLE_LINE,
            multi_line=_MULTI_LINE,
        )
        == expected
    )


def test_expected_print_call_count_returns_value_or_none() -> None:
    assert (
        expected_print_call_count(
            4,
            expectations=_PRINT_CALLS,
        )
        == 1
    )
    assert (
        expected_print_call_count(
            1,
            expectations=_PRINT_CALLS,
        )
        is None
    )


def test_expected_helpers_return_none_for_unknown_exercise() -> None:
    exercise_no = 999
    assert (
        expected_output_lines(
            exercise_no,
            single_line=_SINGLE_LINE,
            multi_line=_MULTI_LINE,
        )
        is None
    )
    assert (
        expected_output_text(
            exercise_no,
            single_line=_SINGLE_LINE,
            multi_line=_MULTI_LINE,
        )
        is None
    )
    assert (
        expected_print_call_count(
            exercise_no,
            expectations=_PRINT_CALLS,
        )
        is None
    )


def test_framework_expectation_helpers_do_not_export_notebook_paths() -> None:
    notebook_path_names = [
        f"EX{exercise_no:03d}_NOTEBOOK_PATH"
        for exercise_no in range(2, 8)
    ]

    for notebook_path_name in notebook_path_names:
        assert notebook_path_name not in framework_expectations.__all__
        assert not hasattr(framework_expectations, notebook_path_name)
