"""Tests for ``exercise_runtime_support.exercise_test_support``."""

from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support import exercise_test_support
from exercise_runtime_support.exercise_catalogue import ExerciseCatalogueEntry


def _catalogue_entry_for(exercise_key: str) -> ExerciseCatalogueEntry | None:
    """Return a typed catalogue entry for the synthetic exercise keys used here."""

    if not exercise_key.startswith("ex999_sequence_modify_"):
        return None

    return ExerciseCatalogueEntry(
        exercise_key=exercise_key,
        exercise_id=999,
        slug=exercise_key.removeprefix("ex999_sequence_modify_"),
        title="Synthetic exercise",
        display_label="Synthetic exercise",
        construct="sequence",
        exercise_type="modify",
        parts=1,
        layout="single",
    )


def test_resolve_exercise_tests_dir_prefers_canonical_exercise_local_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Canonical exercise-local tests directories resolve when present."""
    exercise_key = "ex999_sequence_modify_canonical_only"
    canonical_dir = tmp_path / "exercises" / "sequence" / exercise_key / "tests"
    packaged_dir = tmp_path / "tests" / "sequence" / exercise_key
    canonical_dir.mkdir(parents=True)
    packaged_dir.mkdir(parents=True)

    monkeypatch.setattr(exercise_test_support, "get_catalogue_entry", _catalogue_entry_for)
    monkeypatch.setattr(exercise_test_support, "_REPO_ROOT", tmp_path)

    assert exercise_test_support.resolve_exercise_tests_dir(exercise_key) == canonical_dir


def test_resolve_exercise_tests_dir_rejects_packaged_fallback_when_canonical_dir_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The resolver fails fast when the canonical tests directory is missing."""
    exercise_key = "ex999_sequence_modify_packaged_only"
    packaged_dir = tmp_path / "tests" / "sequence" / exercise_key
    packaged_dir.mkdir(parents=True)

    monkeypatch.setattr(exercise_test_support, "get_catalogue_entry", _catalogue_entry_for)
    monkeypatch.setattr(exercise_test_support, "_REPO_ROOT", tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=rf"Canonical exercise-local tests directory not found for {exercise_key!r}:",
    ):
        exercise_test_support.resolve_exercise_tests_dir(exercise_key)


def test_load_exercise_test_module_rejects_packaged_fallback_when_canonical_dir_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Exercise test modules must not load without a canonical tests directory."""
    exercise_key = "ex999_sequence_modify_packaged_module_only"
    fallback_dir = tmp_path / "tests" / "sequence" / exercise_key
    fallback_dir.mkdir(parents=True)
    (fallback_dir / "student_checker_support.py").write_text(
        "answer = 'legacy fallback'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(exercise_test_support, "get_catalogue_entry", _catalogue_entry_for)
    monkeypatch.setattr(exercise_test_support, "_REPO_ROOT", tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=rf"Canonical exercise-local tests directory not found for {exercise_key!r}:",
    ):
        exercise_test_support.load_exercise_test_module(
            exercise_key,
            "student_checker_support",
        )


def test_load_exercise_test_module_prefers_canonical_module_when_packaged_copy_exists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Canonical exercise-local modules should win over packaged copies when both exist."""
    exercise_key = "ex999_sequence_modify_canonical_over_packaged"
    canonical_dir = tmp_path / "exercises" / "sequence" / exercise_key / "tests"
    packaged_dir = tmp_path / "tests" / "sequence" / exercise_key
    canonical_dir.mkdir(parents=True)
    packaged_dir.mkdir(parents=True)
    (canonical_dir / "student_checker_support.py").write_text(
        "answer = 'canonical'\n",
        encoding="utf-8",
    )
    (packaged_dir / "student_checker_support.py").write_text(
        "answer = 'packaged'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(exercise_test_support, "get_catalogue_entry", _catalogue_entry_for)
    monkeypatch.setattr(exercise_test_support, "_REPO_ROOT", tmp_path)

    module = exercise_test_support.load_exercise_test_module(
        exercise_key,
        "student_checker_support",
    )

    assert module.answer == "canonical"
