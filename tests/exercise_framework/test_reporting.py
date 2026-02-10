from __future__ import annotations

import textwrap

from tests.exercise_framework.reporting import (
    ERROR_COLUMN_WIDTH,
    format_status,
    normalise_issue_lines,
    normalise_issue_text,
    render_grouped_table_with_errors,
    strip_exercise_prefix,
    wrap_text_to_width,
)

WRAP_WIDTH = 22
MIN_WRAPPED_LINES = 2
MINIMUM_EXPECTED_ROWS = 3
MINIMUM_CORNER_COUNT = 2


def test_strip_exercise_prefix_removes_leading_label() -> None:
    message = "Exercise 3: colour mismatch in the greeting."
    assert strip_exercise_prefix(message) == "colour mismatch in the greeting."


def test_strip_exercise_prefix_leaves_unmatched_text() -> None:
    message = "The greeting had the wrong colour."
    assert strip_exercise_prefix(message) == message


def test_wrap_text_to_width_splits_long_message() -> None:
    message = "This error message should wrap into tidy lines for learners."
    width = WRAP_WIDTH

    lines = wrap_text_to_width(message, width)

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

    table = render_grouped_table_with_errors(rows)

    assert format_status(True) in table
    assert format_status(False) in table
    assert "Exercise 2:" not in table

    lines = table.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].count("+") >= MINIMUM_CORNER_COUNT
    assert lines[-1].startswith("+")
    assert lines[-1].count("+") >= MINIMUM_CORNER_COUNT

    expected_error = (
        "The output did not match the expected wording for the sentence about the school location."
    )
    expected_lines = textwrap.wrap(
        expected_error,
        width=ERROR_COLUMN_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    )
    assert expected_lines

    assert "The output did not match the expected" in table
    assert "wording for the sentence about the" in table
    assert "school location." in table


def test_render_grouped_table_with_errors_wraps_long_words() -> None:
    long_word = "a" * (ERROR_COLUMN_WIDTH + 12)
    error_message = f"Exercise 1: {long_word}"
    rows = [
        ("Exercise 1", "Long word check", False, error_message),
    ]

    table = render_grouped_table_with_errors(rows)

    lines = table.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].count("+") >= MINIMUM_CORNER_COUNT
    assert lines[-1].startswith("+")
    assert lines[-1].count("+") >= MINIMUM_CORNER_COUNT

    expected_lines = textwrap.wrap(
        long_word,
        width=ERROR_COLUMN_WIDTH,
        break_long_words=True,
        break_on_hyphens=False,
    )
    assert expected_lines

    assert long_word not in table
    first_chunk = "a" * ERROR_COLUMN_WIDTH
    assert first_chunk in table


def test_render_grouped_table_with_errors_continuation_rows_blank_columns() -> None:
    long_error = (
        "Exercise 2: The output did not match the expected wording for the sentence "
        "about the school location and punctuation in this response."
    )

    table = render_grouped_table_with_errors(
        [("Exercise 2", "Logic", False, long_error)])

    row_lines = [line for line in table.splitlines() if line.startswith("| ")]

    assert len(row_lines) >= MINIMUM_EXPECTED_ROWS

    first_data_row = row_lines[1]
    continuation_row = row_lines[2]

    assert "Exercise 2" in first_data_row
    assert "Logic" in first_data_row
    assert "🔴 NO" in first_data_row

    assert "Exercise 2" not in continuation_row
    assert "Logic" not in continuation_row
    assert "🔴 NO" not in continuation_row


def test_normalise_issue_lines_strips_joins_and_wraps() -> None:
    issues = [
        "Exercise 1: expected a friendlier greeting for the learner.",
        "Exercise 1: expected punctuation to match the prompt wording.",
    ]

    joined = normalise_issue_text(issues)
    lines = normalise_issue_lines(issues, width=ERROR_COLUMN_WIDTH)

    assert "; " in joined
    assert "Exercise 1:" not in joined
    assert all(len(line) <= ERROR_COLUMN_WIDTH for line in lines)
    assert " ".join(lines) == joined
