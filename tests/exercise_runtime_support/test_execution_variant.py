from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.execution_variant import (
    Variant,
    get_active_variant,
    resolve_variant_notebook_path,
)


def test_get_active_variant_defaults_to_solution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)

    assert get_active_variant() == "solution"


def test_get_active_variant_preserves_environment_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "student")

    assert get_active_variant() == "student"


@pytest.mark.parametrize(
    ("notebook_path", "variant", "expected_name"),
    [
        (Path("student.ipynb"), "solution", "solution.ipynb"),
        (Path("solution.ipynb"), "student", "student.ipynb"),
    ],
)
def test_resolve_variant_notebook_path_switches_canonical_filename(
    notebook_path: Path,
    variant: Variant,
    expected_name: str,
) -> None:
    resolved = resolve_variant_notebook_path(notebook_path, variant=variant)

    assert resolved == notebook_path.with_name(expected_name)


def test_resolve_variant_notebook_path_anchors_relative_canonical_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    notebook_path = (
        Path("exercises")
        / "sequence"
        / "ex004_sequence_debug_syntax"
        / "notebooks"
        / "student.ipynb"
    )

    resolved = resolve_variant_notebook_path(
        notebook_path,
        variant="solution",
        repo_root=repo_root,
        anchor_to_repo_root=True,
    )

    assert resolved == (repo_root / notebook_path).resolve().with_name("solution.ipynb")


@pytest.mark.parametrize(
    ("notebook_path", "variant"),
    [
        (Path("notebooks") / "ex002_sequence_modify_basics.ipynb", "solution"),
        (
            Path("notebooks")
            / "solutions"
            / "ex002_sequence_modify_basics.ipynb",
            "student",
        ),
    ],
)
def test_resolve_variant_notebook_path_leaves_legacy_notebooks_paths_unchanged(
    notebook_path: Path,
    variant: Variant,
) -> None:
    resolved = resolve_variant_notebook_path(notebook_path, variant=variant)

    assert resolved == notebook_path


def test_resolve_variant_notebook_path_leaves_non_canonical_filenames_unchanged() -> None:
    notebook_path = Path("lesson_notes.ipynb")

    resolved = resolve_variant_notebook_path(notebook_path, variant="solution")

    assert resolved == notebook_path
