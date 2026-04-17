from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import exercise_runtime_support.exercise_framework.paths as paths_impl
from tests.exercise_framework import paths
from tests.notebook_grader import resolve_notebook_path as grader_resolve_notebook_path

EX003_EXERCISE_KEY = "ex003_sequence_modify_variables"
EX004_EXERCISE_KEY = "ex004_sequence_debug_syntax"


def test_paths_resolver_matches_notebook_grader_for_canonical_exercise_key() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    expected = (
        repo_root
        / "exercises"
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "solution.ipynb"
    )

    from_framework = paths.resolve_notebook_path(
        EX004_EXERCISE_KEY, variant="solution")
    from_grader = grader_resolve_notebook_path(
        EX004_EXERCISE_KEY, variant="solution")

    assert from_framework == from_grader == expected


@pytest.mark.parametrize(
    "notebook_path",
    [
        "notebooks/ex002_sequence_modify_basics.ipynb",
        "ex002_sequence_modify_basics.ipynb",
    ],
)
def test_paths_resolver_rejects_path_like_string_inputs(notebook_path: str) -> None:
    expected_message = (
        "resolver input must be an exercise_key, not a path-like string: "
        f"{notebook_path!r}. Path-like inputs are not supported."
    )

    with pytest.raises(LookupError) as framework_exc:
        paths.resolve_notebook_path(notebook_path, variant="solution")
    with pytest.raises(LookupError) as grader_exc:
        grader_resolve_notebook_path(notebook_path, variant="solution")

    assert str(framework_exc.value) == expected_message
    assert str(grader_exc.value) == expected_message


def test_paths_resolver_rejects_legacy_source_path_objects() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    notebook_path = repo_root / "notebooks" / "ex002_sequence_modify_basics.ipynb"
    expected_message = (
        "Source-repository notebook resolution requires an exercise_key, not a "
        f"legacy notebooks/ path: {notebook_path!r}. Pass an exercise_key "
        "string instead."
    )

    with pytest.raises(LookupError) as framework_exc:
        paths.resolve_notebook_path(notebook_path, variant="solution")
    with pytest.raises(LookupError) as grader_exc:
        grader_resolve_notebook_path(notebook_path, variant="solution")

    assert str(framework_exc.value) == expected_message
    assert str(grader_exc.value) == expected_message


def test_paths_resolver_rejects_relative_legacy_source_path_objects() -> None:
    notebook_path = Path("notebooks") / "ex002_sequence_modify_basics.ipynb"
    expected_message = (
        "Source-repository notebook resolution requires an exercise_key, not a "
        f"legacy notebooks/ path: {notebook_path!r}. Pass an exercise_key "
        "string instead."
    )

    with pytest.raises(LookupError) as framework_exc:
        paths.resolve_notebook_path(notebook_path, variant="solution")
    with pytest.raises(LookupError) as grader_exc:
        grader_resolve_notebook_path(notebook_path, variant="solution")

    assert str(framework_exc.value) == expected_message
    assert str(grader_exc.value) == expected_message


def test_paths_resolver_preserves_variant_switching_for_canonical_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    student_notebook = (
        repo_root
        / "exercises"
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "student.ipynb"
    )
    expected = student_notebook.with_name("solution.ipynb")

    from_framework = paths.resolve_notebook_path(
        student_notebook, variant="solution")
    from_grader = grader_resolve_notebook_path(
        student_notebook, variant="solution")

    assert from_framework == from_grader == expected


def test_paths_resolver_anchors_relative_canonical_paths_to_repo_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(tmp_path)
    student_notebook = (
        Path("exercises")
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "student.ipynb"
    )
    expected = (repo_root / student_notebook).with_name("solution.ipynb")

    from_framework = paths.resolve_notebook_path(
        student_notebook, variant="solution")
    from_grader = grader_resolve_notebook_path(
        student_notebook, variant="solution")

    assert from_framework == from_grader == expected


def test_paths_resolver_leaves_explicit_external_paths_unchanged(tmp_path: Path) -> None:
    notebook_path = tmp_path / "arbitrary" / "path" / "lesson.ipynb"
    expected = notebook_path

    from_framework = paths.resolve_notebook_path(
        notebook_path, variant="solution")
    from_grader = grader_resolve_notebook_path(
        notebook_path, variant="solution")

    assert from_framework == expected
    assert from_grader == expected


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


def test_resolve_exercise_notebook_path_uses_canonical_path_for_migrated_exercise() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    resolved = paths.resolve_exercise_notebook_path(
        EX003_EXERCISE_KEY,
        variant="solution",
    )

    assert resolved == (
        repo_root
        / "exercises"
        / "sequence"
        / EX003_EXERCISE_KEY
        / "notebooks"
        / "solution.ipynb"
    )


def test_resolve_exercise_notebook_path_propagates_legacy_layout_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    def fake_repo_root() -> Path:
        return repo_root

    def fake_catalogue_entry(exercise_key: str) -> SimpleNamespace:
        del exercise_key
        return SimpleNamespace(layout="legacy", construct="sequence")

    def raise_legacy_not_supported(
        exercise_key: str,
        *,
        variant: str | None = None,
    ) -> Path:
        del exercise_key, variant
        raise LookupError("legacy not supported")

    monkeypatch.setattr(paths_impl, "_framework_repo_root", fake_repo_root)
    monkeypatch.setattr(
        paths_impl,
        "_has_local_metadata_package",
        lambda _repo_root: True,
    )
    monkeypatch.setattr(
        paths_impl,
        "get_catalogue_entry",
        fake_catalogue_entry,
    )
    monkeypatch.setattr(
        paths_impl,
        "_resolve_source_canonical_notebook_path",
        raise_legacy_not_supported,
    )

    with pytest.raises(LookupError, match="legacy not supported"):
        paths.resolve_exercise_notebook_path(
            "ex999_legacy_layout",
            variant="solution",
        )


def test_resolve_exercise_notebook_path_uses_solution_mirror_in_metadata_free_exports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    solution_mirror = (
        tmp_path
        / "exercises"
        / "sequence"
        / "ex004_sequence_debug_syntax"
        / "notebooks"
        / "solution.ipynb"
    )
    solution_mirror.parent.mkdir(parents=True)
    solution_mirror.write_text("{}", encoding="utf-8")

    def fake_repo_root() -> Path:
        return tmp_path

    def fake_catalogue_entry(exercise_key: str) -> SimpleNamespace:
        del exercise_key
        return SimpleNamespace(layout="canonical", construct="sequence")

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


def test_resolve_exercise_notebook_path_uses_exercise_local_export_for_student_variant(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    exported_notebook = (
        tmp_path
        / "exercises"
        / "sequence"
        / "ex004_sequence_debug_syntax"
        / "notebooks"
        / "student.ipynb"
    )
    exported_notebook.parent.mkdir(parents=True)
    exported_notebook.write_text("{}", encoding="utf-8")

    def fake_repo_root() -> Path:
        return tmp_path

    def fake_catalogue_entry(exercise_key: str) -> SimpleNamespace:
        del exercise_key
        return SimpleNamespace(layout="canonical", construct="sequence")

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
        tmp_path
        / "exercises"
        / "sequence"
        / "ex004_sequence_debug_syntax"
        / "notebooks"
        / "solution.ipynb"
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
