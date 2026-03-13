"""Tests for ``exercise_runtime_support.student_checker.api``."""

from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_catalogue import get_catalogue_entry, get_exercise_catalogue
from exercise_runtime_support.student_checker import api as student_api


def test_check_exercises_uses_catalogue_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Summary checks follow the shared catalogue order."""
    seen_labels: list[str] = []

    def fake_run_checks(checks):
        seen_labels.extend(check.label for check in checks)
        return []

    monkeypatch.setattr(student_api, "run_checks", fake_run_checks)
    monkeypatch.setattr(student_api, "print_results", lambda _results: None)

    student_api.check_exercises()

    assert seen_labels == [entry.display_label for entry in get_exercise_catalogue()]


def test_check_notebook_uses_catalogue_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """Single-notebook checks use the shared catalogue display label."""
    captured_labels: list[str] = []

    def fake_run_check(check) -> None:
        captured_labels.append(check.label)

    monkeypatch.setattr(student_api, "run_check", fake_run_check)

    student_api.check_notebook("ex004_sequence_debug_syntax")

    assert captured_labels == [get_catalogue_entry("ex004_sequence_debug_syntax").display_label]


def test_check_notebook_unknown_slug_is_explicit() -> None:
    """Unknown notebook keys still fail with a clear message."""
    with pytest.raises(ValueError, match="Unknown notebook 'unknown_notebook'\\. Available:"):
        student_api.check_notebook("unknown_notebook")
