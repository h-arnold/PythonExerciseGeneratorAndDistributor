from __future__ import annotations

from pathlib import Path

from tests.notebook_grader import resolve_notebook_path


def test_resolve_notebook_path_uses_solution_variant_when_candidate_exists() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    original = repo_root / "notebooks/ex002_sequence_modify_basics.ipynb"

    resolved = resolve_notebook_path(original, variant="solution")

    assert resolved == repo_root / \
        "notebooks/solutions/ex002_sequence_modify_basics.ipynb"


def test_resolve_notebook_path_returns_requested_missing_variant_target() -> None:
    original = Path("notebooks/does_not_exist.ipynb")
    resolved = resolve_notebook_path(original, variant="solution")

    assert resolved == Path("notebooks/solutions/does_not_exist.ipynb")


def test_resolve_notebook_path_leaves_non_notebook_paths_unchanged(tmp_path: Path) -> None:
    original = tmp_path / "arbitrary" / "path" / "lesson.ipynb"
    resolved = resolve_notebook_path(original, variant="solution")

    assert resolved == original
