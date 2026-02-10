"""Helper utilities for exercise expectations."""

from __future__ import annotations


def is_valid_explanation(
    text: str,
    *,
    min_length: int,
    placeholder_phrases: tuple[str, ...],
) -> bool:
    """Return True when an explanation is long enough and not a placeholder."""
    stripped = text.strip().lower()
    if len(stripped) < min_length:
        return False
    return not any(phrase in stripped for phrase in placeholder_phrases)
