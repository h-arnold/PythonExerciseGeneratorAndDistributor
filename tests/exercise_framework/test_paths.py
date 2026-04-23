from __future__ import annotations

from pathlib import Path

import pytest

import exercise_metadata.resolver as metadata_resolver
from exercise_runtime_support.execution_variant import Variant
from tests.exercise_framework import paths

EX003_EXERCISE_KEY = "ex003_sequence_modify_variables"
EX004_EXERCISE_KEY = "ex004_sequence_debug_syntax"


def test_paths_resolver_uses_canonical_exercise_key_for_solution_variant() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    expected = (
        repo_root
        / "exercises"
        / "sequence"
        / EX004_EXERCISE_KEY
        / "notebooks"
        / "solution.ipynb"
    )

    resolved = paths.resolve_notebook_path(
        EX004_EXERCISE_KEY, variant="solution")

    assert resolved == expected


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

    assert str(framework_exc.value) == expected_message


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

    assert str(framework_exc.value) == expected_message


def test_paths_resolver_rejects_relative_legacy_source_path_objects() -> None:
    notebook_path = Path("notebooks") / "ex002_sequence_modify_basics.ipynb"
    expected_message = (
        "Source-repository notebook resolution requires an exercise_key, not a "
        f"legacy notebooks/ path: {notebook_path!r}. Pass an exercise_key "
        "string instead."
    )

    with pytest.raises(LookupError) as framework_exc:
        paths.resolve_notebook_path(notebook_path, variant="solution")

    assert str(framework_exc.value) == expected_message


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

    resolved = paths.resolve_notebook_path(
        student_notebook, variant="solution")

    assert resolved == expected


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

    resolved = paths.resolve_notebook_path(
        student_notebook, variant="solution")

    assert resolved == expected


def test_paths_resolver_leaves_explicit_external_paths_unchanged(tmp_path: Path) -> None:
    notebook_path = tmp_path / "arbitrary" / "path" / "lesson.ipynb"
    expected = notebook_path

    resolved = paths.resolve_notebook_path(notebook_path, variant="solution")

    assert resolved == expected


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


@pytest.mark.parametrize(
    ("requested_variant", "expected_filename"),
    [
        ("student", "student.ipynb"),
        ("solution", "solution.ipynb"),
    ],
)
def test_resolve_exercise_notebook_path_uses_metadata_resolver_for_all_variants(
    monkeypatch: pytest.MonkeyPatch,
    requested_variant: Variant,
    expected_filename: str,
) -> None:
    called_with: list[tuple[str, Variant | None]] = []

    def fake_metadata_resolver(
        exercise_key: str,
        variant: Variant | None = None,
    ) -> Path:
        called_with.append((exercise_key, variant))
        return Path(f"/tmp/{expected_filename}")

    monkeypatch.setattr(
        metadata_resolver,
        "resolve_notebook_path",
        fake_metadata_resolver,
    )

    resolved = paths.resolve_exercise_notebook_path(
        "ex004_sequence_debug_syntax",
        variant=requested_variant,
    )

    assert resolved == Path(f"/tmp/{expected_filename}")
    assert called_with == [("ex004_sequence_debug_syntax", requested_variant)]
