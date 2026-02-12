"""Reporting helpers for exercise checks."""

from __future__ import annotations

import re
import textwrap
from collections.abc import Sequence
from typing import Final

from tabulate import tabulate

PASS_STATUS_EMOJI: Final[str] = "🟢"
FAIL_STATUS_EMOJI: Final[str] = "🔴"
NOT_STARTED_STATUS_EMOJI: Final[str] = "🟡"
PASS_STATUS_TAG: Final[str] = "OK"
FAIL_STATUS_TAG: Final[str] = "NO"
NOT_STARTED_STATUS_TAG: Final[str] = "NOT STARTED"
ERROR_COLUMN_WIDTH: Final[int] = 40


def format_status(status: bool | str) -> str:
    """Format a status marker using emoji and a short tag."""
    if isinstance(status, bool):
        emoji = PASS_STATUS_EMOJI if status else FAIL_STATUS_EMOJI
        tag = PASS_STATUS_TAG if status else FAIL_STATUS_TAG
        return f"{emoji} {tag}"

    normalized = status.replace("_", " ").strip().upper()
    if normalized in {"PASSED", "PASS", "OK"}:
        return f"{PASS_STATUS_EMOJI} {PASS_STATUS_TAG}"
    if normalized == NOT_STARTED_STATUS_TAG:
        return f"{NOT_STARTED_STATUS_EMOJI} {NOT_STARTED_STATUS_TAG}"
    return f"{FAIL_STATUS_EMOJI} {FAIL_STATUS_TAG}"


def strip_exercise_prefix(message: str) -> str:
    """Remove a leading "Exercise N:" prefix when present."""
    match = re.match(r"^Exercise\s+\d+:\s*", message)
    if match:
        return message[match.end():]
    return message


def wrap_text_to_width(message: str, width: int) -> list[str]:
    """Wrap text without splitting words."""
    if message == "":
        return [""]
    return textwrap.wrap(
        message,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _wrap_error_text(message: str, width: int) -> list[str]:
    if message == "":
        return [""]
    uses_long_word_wrap = any(len(word) > width for word in message.split())
    if uses_long_word_wrap:
        return textwrap.wrap(
            message,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
        )
    return wrap_text_to_width(message, width)


def normalise_issue_text(issues: list[str]) -> str:
    """Normalise issue text by stripping prefixes and joining with '; '."""
    return "; ".join(strip_exercise_prefix(issue) for issue in issues)


def normalise_issue_lines(issues: list[str], width: int = ERROR_COLUMN_WIDTH) -> list[str]:
    """Normalise and wrap issue text for display."""
    return _wrap_error_text(normalise_issue_text(issues), width)


def render_table(rows: list[tuple[str, bool | str]]) -> str:
    """Render a simple 2-column table with check name and status."""
    data = [[label, format_status(passed)] for label, passed in rows]
    return tabulate(data, headers=["Check", "Status"], tablefmt="grid")


def render_grouped_table(rows: list[tuple[str, str, bool | str]]) -> str:
    """Render a 3-column table with exercise, check name, and status."""
    data = [[label, title, format_status(passed)]
            for label, title, passed in rows]
    return tabulate(data, headers=["Exercise", "Check", "Status"], tablefmt="grid")


def render_grouped_table_with_errors(
    rows: Sequence[tuple[str, str, bool | str, str]],
    error_width: int = ERROR_COLUMN_WIDTH,
) -> str:
    """Render a 4-column table with exercise, check, status, and error."""
    data: list[list[str]] = []
    for exercise_label, title, row_status, error in rows:
        status = format_status(row_status)
        trimmed_error = strip_exercise_prefix(error)

        if trimmed_error and len(trimmed_error) > error_width:
            wrapped_lines = _wrap_error_text(trimmed_error, error_width)
            # Keep wrapped feedback in one multi-line cell so continuation lines
            # do not create extra row separators in grid output.
            data.append([exercise_label, title, status,
                        "\n".join(wrapped_lines)])
        else:
            data.append([exercise_label, title, status, trimmed_error])

    return tabulate(
        data,
        headers=["Exercise", "Check", "Status", "Error"],
        tablefmt="grid",
    )
