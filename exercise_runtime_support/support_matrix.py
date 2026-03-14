"""Shared runtime support matrix for exercise check wiring.

This module is the single source of truth for which exercise IDs are wired into
framework smoke checks, framework detailed checks, and student-checker checks.
It intentionally stores only runtime wiring flags, not exercise identity data
(such as titles, slugs, or construct/type labels), which come from metadata.
"""

from __future__ import annotations

from collections.abc import Iterator
from enum import StrEnum
from typing import Final


class SupportRole(StrEnum):
    """Runtime wiring role for an exercise."""

    FRAMEWORK_DETAILED = "framework_detailed"
    FRAMEWORK_SMOKE = "framework_smoke"
    STUDENT_CHECKER = "student_checker"


_SUPPORT_MATRIX: Final[dict[int, frozenset[SupportRole]]] = {
    2: frozenset({SupportRole.FRAMEWORK_DETAILED, SupportRole.STUDENT_CHECKER}),
    3: frozenset({SupportRole.FRAMEWORK_SMOKE, SupportRole.STUDENT_CHECKER}),
    4: frozenset({SupportRole.FRAMEWORK_SMOKE, SupportRole.STUDENT_CHECKER}),
    5: frozenset({SupportRole.FRAMEWORK_SMOKE, SupportRole.STUDENT_CHECKER}),
    6: frozenset({SupportRole.FRAMEWORK_SMOKE, SupportRole.STUDENT_CHECKER}),
    7: frozenset({SupportRole.STUDENT_CHECKER}),
}


def has_support_role(exercise_id: int, role: SupportRole) -> bool:
    """Return whether an exercise ID supports the given runtime role."""
    return role in _SUPPORT_MATRIX.get(exercise_id, frozenset())


def iter_exercise_ids_for_role(role: SupportRole) -> Iterator[int]:
    """Yield exercise IDs that support the given runtime role in sorted order."""
    for exercise_id in sorted(_SUPPORT_MATRIX):
        if has_support_role(exercise_id, role):
            yield exercise_id
