"""Shared runtime support matrix for framework check wiring.

This module is the single source of truth for which exercise IDs are wired into
framework smoke checks and framework detailed checks. It intentionally stores
only runtime wiring flags, not exercise identity data (such as titles, slugs,
or construct/type labels), which come from metadata.
"""

from __future__ import annotations

from collections.abc import Iterator
from enum import StrEnum
from typing import Final


class SupportRole(StrEnum):
    """Runtime wiring role for an exercise."""

    FRAMEWORK_DETAILED = "framework_detailed"
    FRAMEWORK_SMOKE = "framework_smoke"


_SUPPORT_MATRIX: Final[dict[int, frozenset[SupportRole]]] = {
    2: frozenset({SupportRole.FRAMEWORK_DETAILED}),
    3: frozenset({SupportRole.FRAMEWORK_SMOKE}),
    4: frozenset({SupportRole.FRAMEWORK_SMOKE}),
    5: frozenset({SupportRole.FRAMEWORK_SMOKE}),
    6: frozenset({SupportRole.FRAMEWORK_SMOKE}),
}


def has_support_role(exercise_id: int, role: SupportRole) -> bool:
    """Return whether an exercise ID supports the given runtime role."""
    return role in _SUPPORT_MATRIX.get(exercise_id, frozenset())


def iter_exercise_ids_for_role(role: SupportRole) -> Iterator[int]:
    """Yield exercise IDs that support the given runtime role in sorted order."""
    for exercise_id, roles in sorted(_SUPPORT_MATRIX.items()):
        if role in roles:
            yield exercise_id
