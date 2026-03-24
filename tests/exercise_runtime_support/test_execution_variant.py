from __future__ import annotations

import pytest

from exercise_runtime_support.execution_variant import get_active_variant


def test_get_active_variant_defaults_to_solution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)

    assert get_active_variant() == "solution"


def test_get_active_variant_preserves_environment_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "student")

    assert get_active_variant() == "student"
