"""Tests for ``exercise_runtime_support.consumer_matrix``."""

from __future__ import annotations

from pathlib import Path

from exercise_runtime_support.consumer_matrix import CONSUMER_MATRIX


def test_consumer_matrix_has_required_surfaces() -> None:
    """The matrix tracks every required runtime contract consumer surface."""
    surfaces = {entry.surface for entry in CONSUMER_MATRIX}
    assert {
        "runtime/grading wrapper",
        "framework and student-checker APIs",
        "packager and collector CLI",
        "exercise scaffolder",
        "repository workflows",
        "classroom template workflow",
        "contributor documentation",
    } == surfaces


def test_consumer_matrix_lists_existing_files() -> None:
    """Each matrix row references concrete files that exist in this repository."""
    for entry in CONSUMER_MATRIX:
        assert entry.files, f"Consumer matrix entry has no files: {entry.surface}"
        for path in entry.files:
            assert path.exists(), f"Missing consumer matrix file for {entry.surface}: {path}"


def test_execution_model_docs_include_consumer_matrix_rows() -> None:
    """Execution model documentation mirrors the code-level consumer matrix."""
    doc_text = Path("docs/execution-model.md").read_text(encoding="utf-8")
    for entry in CONSUMER_MATRIX:
        assert entry.surface in doc_text
        assert entry.current_entry_point in doc_text
        assert entry.target_entry_point in doc_text


def test_new_exercise_scaffolder_emits_canonical_runtime_imports() -> None:
    """The scaffolder must emit runtime imports from exercise_runtime_support."""
    source = Path("scripts/new_exercise.py").read_text(encoding="utf-8")
    assert "from exercise_runtime_support.exercise_framework import runtime" in source
    assert "runtime.run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)" in source
    assert "runtime.get_explanation_cell(NOTEBOOK_PATH, tag='explanation1')" in source
    assert "from tests.notebook_grader import run_cell_and_capture_output" not in source
    assert "from tests.notebook_grader import get_explanation_cell" not in source


def test_workflow_consumers_use_variant_driven_scripts() -> None:
    """Workflow consumer surfaces must invoke the shared variant-aware scripts."""
    tests_workflow = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")
    solutions_workflow = Path(".github/workflows/tests-solutions.yml").read_text(encoding="utf-8")
    classroom_workflow = Path("template_repo_files/.github/workflows/classroom.yml").read_text(
        encoding="utf-8"
    )

    assert "scripts/run_pytest_variant.py --variant solution" in tests_workflow
    assert "scripts/run_pytest_variant.py --variant solution" in solutions_workflow
    assert "scripts/build_autograde_payload.py" in classroom_workflow
    assert "--variant student" in classroom_workflow
