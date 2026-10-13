"""Tests for the shared test-only readability output reader."""

import pytest

from tests.readability_table import assert_no_footer, table_rows


def test_table_rows_reads_grid_cells_without_losing_feedback() -> None:
    output = "| Exercise 1 | Readability | 🟢 OK | All clear |\n"

    assert table_rows(output) == [("Exercise 1", "Readability", "🟢 OK", "All clear")]


def test_table_rows_ignores_output_without_table_rows() -> None:
    assert table_rows("Self-check: example\n") == []


def test_assert_no_footer_accepts_table_only_output() -> None:
    assert_no_footer("Self-check: example\n| Check | Status |\n")


@pytest.mark.parametrize(
    "footer",
    [
        "Functional summary:",
        "Readability summary:",
        "Overall self-check:",
        "Save your notebook",
        "fixing-readability-issues.md",
        "teacher-side marks",
    ],
)
def test_assert_no_footer_rejects_each_forbidden_footer_marker(footer: str) -> None:
    with pytest.raises(AssertionError):
        assert_no_footer(f"Self-check: example\n| Check | Status |\n{footer}\n")
