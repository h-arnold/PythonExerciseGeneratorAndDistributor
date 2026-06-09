"""Test helpers for GitHub operations."""

from __future__ import annotations

import subprocess
from typing import TypeGuard, cast


def is_command_sequence(obj: object) -> TypeGuard[list[str] | tuple[str, ...]]:
    """Return True if ``obj`` is a sequence of strings representing a command.

    This helper narrows the type to either a `list[str]` or `tuple[str, ...]`.
    We avoid generator expressions here so static analyzers have a concrete
    variable to type-check (prevents 'Type of "x" is unknown' diagnostics).
    """
    if isinstance(obj, list):
        return all(isinstance(element, str) for element in cast(list[object], obj))

    if isinstance(obj, tuple):
        return all(isinstance(element, str) for element in cast(tuple[object, ...], obj))

    return False


def check_authentication() -> bool:
    """Check gh authentication status.

    Returns:
        True if authenticated, False otherwise.
    """
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, check=False, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
