from __future__ import annotations

from pathlib import Path

import pytest

from tests.notebook_grader import resolve_notebook_path


def test_resolve_notebook_path_uses_override_when_candidate_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override_root = tmp_path / "override"
    candidate = override_root / "ex001_sanity.ipynb"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", str(override_root))

    resolved = resolve_notebook_path("notebooks/ex001_sanity.ipynb")

    assert resolved == candidate


def test_resolve_notebook_path_falls_back_when_override_candidate_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    original = Path("notebooks/does_not_exist.ipynb")
    resolved = resolve_notebook_path(original)

    assert resolved == original


def test_resolve_notebook_path_uses_filename_when_not_under_notebooks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override_root = tmp_path / "override"
    candidate = override_root / "lesson.ipynb"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", str(override_root))

    resolved = resolve_notebook_path("arbitrary/path/lesson.ipynb")

    assert resolved == candidate
