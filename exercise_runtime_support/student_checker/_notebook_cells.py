"""Shared task-tag and source primitives for saved notebook cells."""

from __future__ import annotations

import re
from typing import TypeGuard, cast

EXERCISE_TAG_PATTERN = re.compile(r"exercise(\d+)")


def is_source(value: object) -> TypeGuard[str | list[str]]:
    """Return whether a notebook cell source is a string or list of strings."""
    return isinstance(value, str) or _is_string_list(value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(part, str) for part in cast(list[object], value)
    )


def source_text(source: str | list[str]) -> str:
    """Return saved cell source unchanged, joining list-valued source directly."""
    return source if isinstance(source, str) else "".join(source)


def is_exercise_tag(tag: str) -> bool:
    """Return whether a tag exactly matches the exerciseN task-tag form."""
    return EXERCISE_TAG_PATTERN.fullmatch(tag) is not None
