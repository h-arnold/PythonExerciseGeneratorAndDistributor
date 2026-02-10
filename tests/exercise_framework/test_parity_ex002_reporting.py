from __future__ import annotations

from tests.student_checker import (
    Ex002CheckResult,
    _render_grouped_table_with_errors,
    _strip_exercise_prefix,
)

MINIMUM_EXPECTED_ROWS = 3


def test_ex002_error_normalisation_pipeline_parity() -> None:
    results = [
        Ex002CheckResult(
            exercise_no=1,
            title="Logic",
            passed=False,
            issues=["Exercise 1: expected 'Hello Python!'.", "Exercise 1: expected 1 print calls."],
        )
    ]

    error_message = "; ".join(_strip_exercise_prefix(issue) for issue in results[0].issues)
    table = _render_grouped_table_with_errors(
        [("Exercise 1", results[0].title, results[0].passed, error_message)]
    )

    assert "Exercise 1: expected" not in table
    assert "expected 'Hello Python!'.;" in table
    assert "expected 1" in table
    assert "print calls." in table
    assert "| Exercise 1" in table
    assert "| Logic" in table
    assert "| 🔴 NO" in table


def test_ex002_error_wrapping_continuation_row_columns_are_blank() -> None:
    long_error = (
        "Exercise 2: The output did not match the expected wording for the sentence "
        "about the school location and punctuation in this response."
    )

    table = _render_grouped_table_with_errors(
        [("Exercise 2", "Logic", False, long_error)]
    )

    row_lines = [line for line in table.splitlines() if line.startswith("| ")]

    # Header + at least one data row + at least one wrapped continuation row.
    assert len(row_lines) >= MINIMUM_EXPECTED_ROWS

    first_data_row = row_lines[1]
    continuation_row = row_lines[2]

    assert "Exercise 2" in first_data_row
    assert "Logic" in first_data_row
    assert "🔴 NO" in first_data_row

    # Continuation rows must blank out Exercise/Check/Status columns.
    assert "Exercise 2" not in continuation_row
    assert "Logic" not in continuation_row
    assert "🔴 NO" not in continuation_row
