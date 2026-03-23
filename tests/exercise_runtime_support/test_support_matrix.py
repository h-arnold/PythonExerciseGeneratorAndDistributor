"""Tests for ``exercise_runtime_support.support_matrix``."""

from __future__ import annotations

from exercise_runtime_support.support_matrix import (
    SupportRole,
    has_support_role,
    iter_exercise_ids_for_role,
)


def test_iter_exercise_ids_for_framework_detailed_role() -> None:
    """The support matrix exposes ex002 as the only detailed framework check."""
    assert list(iter_exercise_ids_for_role(
        SupportRole.FRAMEWORK_DETAILED)) == [2]


def test_iter_exercise_ids_for_framework_smoke_role() -> None:
    """The support matrix exposes the expected framework smoke-check IDs."""
    assert list(iter_exercise_ids_for_role(
        SupportRole.FRAMEWORK_SMOKE)) == [3, 4, 5, 6]


def test_has_support_role_returns_false_for_unknown_exercise() -> None:
    """Unknown exercise IDs return False for all runtime support roles."""
    assert not has_support_role(999, SupportRole.FRAMEWORK_SMOKE)
