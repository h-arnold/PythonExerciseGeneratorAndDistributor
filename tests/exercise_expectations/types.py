"""Shared type definitions for exercise expectations."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class Ex006InputExpectation(TypedDict):
    """Expectations for exercises that prompt for input in ex006."""

    inputs: list[str]
    prompt_contains: str
    output_contains: NotRequired[str]
    last_line: NotRequired[str]


__all__ = ["Ex006InputExpectation"]
