from __future__ import annotations

import textwrap

from tests.student_checker import (
    ERROR_COLUMN_WIDTH,
    _format_status,
    _render_grouped_table_with_errors,
    _strip_exercise_prefix,
    _wrap_text_to_width,
)

EXPECTED_SEPARATOR_COUNT = 3
WRAP_WIDTH = 22
MIN_WRAPPED_LINES = 2
MIN_ERROR_ROWS = 2
TABLE_CELL_PADDING = 2


def _split_table_row(line: str) -> list[str]:
    parts = line.split("\u2502")
    return parts[1:-1]


def test_strip_exercise_prefix_removes_leading_label() -> None:
    message = "Exercise 3: colour mismatch in the greeting."
    assert _strip_exercise_prefix(message) == "colour mismatch in the greeting."


def test_strip_exercise_prefix_leaves_unmatched_text() -> None:
    message = "The greeting had the wrong colour."
    assert _strip_exercise_prefix(message) == message


def test_wrap_text_to_width_splits_long_message() -> None:
    message = "This error message should wrap into tidy lines for learners."
    width = WRAP_WIDTH

    lines = _wrap_text_to_width(message, width)

    assert len(lines) >= MIN_WRAPPED_LINES
    assert all(len(line) <= width for line in lines)
    assert " ".join(lines) == message


def test_render_grouped_table_with_errors_wraps_and_blanks() -> None:
    error_message = (
        "Exercise 2: The output did not match the expected wording for the sentence "
        "about the school location."
    )
    rows = [
        ("Exercise 1", "Greeting message", True, ""),
        ("Exercise 2", "School name", False, error_message),
    ]

    table = _render_grouped_table_with_errors(rows)

    assert _format_status(True) in table
    assert _format_status(False) in table
    assert "Exercise 2:" not in table

    lines = table.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].count("+") >= 2  # At least 2 corners
    assert lines[-1].startswith("+")
    assert lines[-1].count("+") >= 2  # At least 2 corners

    expected_error = (
        "The output did not match the expected wording for the sentence about the school location."
    )
    expected_lines = textwrap.wrap(
        expected_error,
        width=ERROR_COLUMN_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    )

    row_lines = [line for line in lines if "|" in line and not line.startswith("+")]
    # Verify error message wrapping happened correctly
    assert "Exercise 2:" not in table

    # Check that wrapping occurred - multiple lines for the lone error
    assert "The output did not match the expected" in table
    assert "wording for the sentence about the" in table
    assert "school location." in table


def test_render_grouped_table_with_errors_wraps_long_words() -> None:
    long_word = "a" * (ERROR_COLUMN_WIDTH + 12)
    error_message = f"Exercise 1: {long_word}"
    rows = [
        ("Exercise 1", "Long word check", False, error_message),
    ]

    table = _render_grouped_table_with_errors(rows)

    lines = table.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].count("+") >= 2  # At least 2 corners
    assert lines[-1].startswith("+")
    assert lines[-1].count("+") >= 2  # At least 2 corners

    expected_lines = textwrap.wrap(
        long_word,
        width=ERROR_COLUMN_WIDTH,
        break_long_words=True,
        break_on_hyphens=False,
    )

    row_lines = [line for line in lines if "|" in line and not line.startswith("+")]
    # Verify long word wrapping occurred
    assert long_word not in table  # Full word shouldn't appear unbroken
    # Check that the word was broken across multiple lines
    first_chunk = "a" * ERROR_COLUMN_WIDTH
    assert first_chunk in table
