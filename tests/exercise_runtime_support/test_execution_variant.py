from __future__ import annotations

import os
from pathlib import Path

import pytest

from exercise_runtime_support.execution_variant import (
    Variant,
    active_variant_context,
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
    ("environment_value", "default", "expected"),
    [(None, "student", "student"), ("solution", "student", "solution")],
)
def test_active_variant_context_restores_environment_after_normal_exit(
    environment_value: str | None,
    default: Variant,
    expected: Variant,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if environment_value is None:
        monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    else:
        monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", environment_value)

    with active_variant_context(default=default) as variant:
        assert variant == expected
        assert os.environ["PYTUTOR_ACTIVE_VARIANT"] == expected

    assert os.environ.get("PYTUTOR_ACTIVE_VARIANT") == environment_value


def test_active_variant_context_restores_environment_after_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    with pytest.raises(ValueError, match="failure"), active_variant_context():
        raise ValueError("failure")

    assert os.environ["PYTUTOR_ACTIVE_VARIANT"] == "solution"


def test_active_variant_context_rejects_invalid_variant_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "invalid")

    with (
        pytest.raises(RuntimeError, match="must be 'student' or 'solution'"),
        active_variant_context(),
    ):
        pytest.fail("invalid variant must be rejected before entering the context")

    assert os.environ["PYTUTOR_ACTIVE_VARIANT"] == "invalid"


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
            Path("notebooks") / "solutions" / "ex002_sequence_modify_basics.ipynb",
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
