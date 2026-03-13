from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import exercise_runtime_support.exercise_framework.paths as paths_impl
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


def test_resolve_exercise_notebook_path_uses_source_canonical_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    resolved = paths.resolve_exercise_notebook_path(
        "ex004_sequence_debug_syntax",
        variant="solution",
    )

    assert resolved == (
        repo_root
        / "exercises"
        / "sequence"
        / "ex004_sequence_debug_syntax"
        / "notebooks"
        / "solution.ipynb"
    )


def test_resolve_exercise_notebook_path_uses_variant_selected_legacy_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    resolved = paths.resolve_exercise_notebook_path(
        "ex003_sequence_modify_variables",
        variant="solution",
    )

    assert resolved == repo_root / \
        "notebooks/solutions/ex003_sequence_modify_variables.ipynb"


def test_resolve_exercise_notebook_path_uses_solution_mirror_in_metadata_free_exports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    solution_mirror = (
        tmp_path / "notebooks" / "solutions" / "ex004_sequence_debug_syntax.ipynb"
    )
    solution_mirror.parent.mkdir(parents=True)
    solution_mirror.write_text("{}", encoding="utf-8")

    def fake_repo_root() -> Path:
        return tmp_path

    def fake_catalogue_entry(exercise_key: str) -> SimpleNamespace:
        del exercise_key
        return SimpleNamespace(layout="canonical")

    def fake_has_local_metadata_package(repo_root: Path) -> bool:
        del repo_root
        return False

    monkeypatch.setattr(paths_impl, "_framework_repo_root", fake_repo_root)
    monkeypatch.setattr(
        paths_impl,
        "get_catalogue_entry",
        fake_catalogue_entry,
    )
    monkeypatch.setattr(
        paths_impl,
        "_has_local_metadata_package",
        fake_has_local_metadata_package,
    )

    def fail_if_called(
        exercise_key: str,
        *,
        variant: str | None = None,
    ) -> Path:
        raise AssertionError(
            "canonical metadata resolver should not be used in metadata-free exports"
        )

    monkeypatch.setattr(
        paths_impl, "_resolve_source_canonical_notebook_path", fail_if_called)

    resolved = paths.resolve_exercise_notebook_path(
        "ex004_sequence_debug_syntax",
        variant="solution",
    )

    assert resolved == solution_mirror


def test_resolve_exercise_notebook_path_uses_flattened_export_only_for_student_variant(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    exported_notebook = tmp_path / "notebooks" / "ex004_sequence_debug_syntax.ipynb"
    exported_notebook.parent.mkdir(parents=True)
    exported_notebook.write_text("{}", encoding="utf-8")

    def fake_repo_root() -> Path:
        return tmp_path

    def fake_catalogue_entry(exercise_key: str) -> SimpleNamespace:
        del exercise_key
        return SimpleNamespace(layout="canonical")

    def fake_has_local_metadata_package(repo_root: Path) -> bool:
        del repo_root
        return False

    monkeypatch.setattr(paths_impl, "_framework_repo_root", fake_repo_root)
    monkeypatch.setattr(
        paths_impl,
        "get_catalogue_entry",
        fake_catalogue_entry,
    )
    monkeypatch.setattr(
        paths_impl,
        "_has_local_metadata_package",
        fake_has_local_metadata_package,
    )

    def fail_if_called(
        exercise_key: str,
        *,
        variant: str | None = None,
    ) -> Path:
        raise AssertionError(
            "canonical metadata resolver should not be used in metadata-free exports"
        )

    monkeypatch.setattr(
        paths_impl, "_resolve_source_canonical_notebook_path", fail_if_called)

    student_resolved = paths.resolve_exercise_notebook_path(
        "ex004_sequence_debug_syntax",
        variant="student",
    )
    expected_solution_mirror = (
        tmp_path / "notebooks" / "solutions" / "ex004_sequence_debug_syntax.ipynb"
    )

    assert student_resolved == exported_notebook
    with pytest.raises(FileNotFoundError) as exc_info:
        paths.resolve_exercise_notebook_path(
            "ex004_sequence_debug_syntax",
            variant="solution",
        )

    message = str(exc_info.value)
    assert "Metadata-free packaged repositories do not include solution notebooks" in message
    assert "ex004_sequence_debug_syntax" in message
    assert str(expected_solution_mirror) in message
