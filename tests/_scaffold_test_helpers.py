"""Shared test helpers for exercise scaffolder tests."""

from __future__ import annotations

from typing import Any


def source_text(cell: dict[str, Any]) -> str:
    """Join a notebook cell's source lines into a single string."""
    return "".join(cell["source"])
