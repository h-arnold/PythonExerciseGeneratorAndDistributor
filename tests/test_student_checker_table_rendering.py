from __future__ import annotations

import textwrap

from tests.student_checker import (
    ERROR_COLUMN_WIDTH,
    FAIL_STATUS_LABEL,
    PASS_STATUS_LABEL,
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

    assert PASS_STATUS_LABEL in table
    assert FAIL_STATUS_LABEL in table
    assert "Exercise 2:" not in table

    lines = table.splitlines()
    assert lines[0].startswith("\u250c")
    assert lines[0].count("\u252c") == EXPECTED_SEPARATOR_COUNT
    assert lines[-1].startswith("\u2514")
    assert lines[-1].count("\u2534") == EXPECTED_SEPARATOR_COUNT

    expected_error = (
        "The output did not match the expected wording for the sentence about the school location."
    )
    expected_lines = textwrap.wrap(
        expected_error,
        width=ERROR_COLUMN_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    )

    row_lines = [line for line in lines if "\u2502" in line]
    error_rows: list[tuple[list[str], str]] = []
    for row in row_lines:
        columns = _split_table_row(row)
        error_cell = columns[3].strip()
        if error_cell:
            error_rows.append((columns, error_cell))

    assert len(error_rows) >= MIN_ERROR_ROWS
    assert [cell for _, cell in error_rows] == expected_lines

    first_columns = error_rows[0][0]
    assert first_columns[0].strip() == "Exercise 2"
    assert first_columns[1].strip() == "School name"
    assert first_columns[2].strip() == FAIL_STATUS_LABEL

    for columns, error_cell in error_rows[1:]:
        assert columns[0].strip() == ""
        assert columns[1].strip() == ""
        assert columns[2].strip() == ""
        assert len(error_cell) <= ERROR_COLUMN_WIDTH
        assert len(columns[3]) == ERROR_COLUMN_WIDTH + TABLE_CELL_PADDING
