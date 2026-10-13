"""Small output readers shared by notebook readability regressions."""

from __future__ import annotations


def table_rows(output: str) -> list[tuple[str, ...]]:
    """Return parsed grid-table rows, excluding borders and header separators."""
    return [
        tuple(column.strip() for column in line.strip().strip("|").split("|"))
        for line in output.splitlines()
        if line.startswith("|")
    ]


def assert_no_footer(output: str) -> None:
    """Assert that checker output contains only its header and table."""
    for text in (
        "Functional summary:",
        "Readability summary:",
        "Overall self-check:",
        "Save your notebook",
        "fixing-readability-issues.md",
        "teacher-side marks",
    ):
        assert text not in output
