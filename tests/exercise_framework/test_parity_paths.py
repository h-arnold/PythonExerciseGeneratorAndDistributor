from __future__ import annotations

from pathlib import Path

import pytest

from tests.exercise_framework import paths

EX004_EXERCISE_KEY = "ex004_sequence_debug_syntax"


def test_resolve_notebook_path_uses_canonical_exercise_key_resolution() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    expected = (
        repo_root
        / "exercises"
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "solution.ipynb"
    )

    resolved = paths.resolve_notebook_path(EX004_EXERCISE_KEY, variant="solution")

    assert resolved == expected


def test_resolve_notebook_path_rejects_legacy_path_string_input() -> None:
    with pytest.raises(LookupError, match="resolver input must be an exercise_key"):
        paths.resolve_notebook_path(
            "notebooks/ex002_sequence_modify_basics.ipynb", variant="solution")


def test_resolve_notebook_path_switches_variant_for_canonical_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    original = (
        repo_root
        / "exercises"
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "student.ipynb"
    )
    resolved = paths.resolve_notebook_path(original, variant="solution")

    assert resolved == original.with_name("solution.ipynb")
