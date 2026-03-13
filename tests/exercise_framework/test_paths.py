from __future__ import annotations

from pathlib import Path

import pytest

from tests.exercise_framework import paths
from tests.notebook_grader import resolve_notebook_path as grader_resolve_notebook_path


def test_paths_resolver_matches_notebook_grader_for_solution_variant() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    original = repo_root / "notebooks/ex002_sequence_modify_basics.ipynb"

    from_framework = paths.resolve_notebook_path(original, variant="solution")
    from_grader = grader_resolve_notebook_path(original, variant="solution")

    assert from_framework == from_grader


def test_paths_resolver_matches_notebook_grader_for_missing_solution_variant() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    original = repo_root / "notebooks/does_not_exist.ipynb"

    from_framework = paths.resolve_notebook_path(original, variant="solution")
    from_grader = grader_resolve_notebook_path(original, variant="solution")

    assert from_framework == from_grader
    assert from_framework == repo_root / "notebooks/solutions/does_not_exist.ipynb"


def test_paths_resolver_matches_notebook_grader_for_non_notebooks_path(
    tmp_path: Path,
) -> None:
    notebook_path = tmp_path / "arbitrary" / "path" / "lesson.ipynb"
    expected = notebook_path.resolve()

    from_framework = paths.resolve_notebook_path(
        notebook_path, variant="solution")
    from_grader = grader_resolve_notebook_path(
        notebook_path, variant="solution")

    assert from_framework == expected
    assert from_grader == notebook_path


def test_paths_resolver_anchors_relative_notebook_paths_to_repo_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root / "notebooks")

    resolved = paths.resolve_notebook_path(
        "notebooks/ex002_sequence_modify_basics.ipynb",
        variant="student",
    )
    expected = repo_root / "notebooks/ex002_sequence_modify_basics.ipynb"

    assert resolved == expected
    assert resolved.exists()


def test_paths_resolver_uses_solution_variant_when_cwd_is_notebooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root / "notebooks")

    resolved = paths.resolve_notebook_path(
        "notebooks/ex002_sequence_modify_basics.ipynb",
        variant="solution",
    )

    assert resolved == repo_root / \
        "notebooks/solutions/ex002_sequence_modify_basics.ipynb"
