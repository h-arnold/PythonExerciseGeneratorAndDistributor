"""Tests for the shared test-only readability output reader."""

from tests.readability_table import assert_no_footer, table_rows


def test_table_rows_reads_grid_cells_without_losing_feedback() -> None:
    output = "| Exercise 1 | Readability | 🟢 OK | All clear |\n"

    assert table_rows(output) == [("Exercise 1", "Readability", "🟢 OK", "All clear")]


def test_table_rows_ignores_output_without_table_rows() -> None:
    assert table_rows("Self-check: example\n") == []


def test_assert_no_footer_accepts_table_only_output() -> None:
    assert_no_footer("Self-check: example\n| Check | Status |\n")
