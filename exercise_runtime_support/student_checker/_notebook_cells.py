"""Shared source type guard for saved notebook cells."""

from __future__ import annotations

from typing import TypeGuard, cast


def is_source(value: object) -> TypeGuard[str | list[str]]:
    """Return whether a notebook cell source is a string or list of strings."""
    return isinstance(value, str) or _is_string_list(value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(part, str) for part in cast(list[object], value)
    )
