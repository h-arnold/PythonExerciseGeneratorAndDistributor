from __future__ import annotations

from pathlib import Path

import pytest

from tests.exercise_framework import paths
from tests.notebook_grader import resolve_notebook_path as grader_resolve_notebook_path


def test_paths_resolver_matches_notebook_grader_for_existing_override_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    override_root = tmp_path / "override"
    candidate = override_root / "ex001_sanity.ipynb"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", str(override_root))

    from_framework = paths.resolve_notebook_path("notebooks/ex001_sanity.ipynb")
    from_grader = grader_resolve_notebook_path("notebooks/ex001_sanity.ipynb")

    assert from_framework == from_grader


def test_paths_resolver_matches_notebook_grader_for_missing_override_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    from_framework = paths.resolve_notebook_path("notebooks/does_not_exist.ipynb")
    from_grader = grader_resolve_notebook_path("notebooks/does_not_exist.ipynb")

    assert from_framework == from_grader


def test_paths_resolver_matches_notebook_grader_for_non_notebooks_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    override_root = tmp_path / "override"
    candidate = override_root / "lesson.ipynb"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", str(override_root))

    from_framework = paths.resolve_notebook_path("arbitrary/path/lesson.ipynb")
    from_grader = grader_resolve_notebook_path("arbitrary/path/lesson.ipynb")

    assert from_framework == from_grader
