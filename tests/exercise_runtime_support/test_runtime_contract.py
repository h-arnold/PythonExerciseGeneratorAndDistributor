"""Direct runtime contract tests for repository surfaces."""

from __future__ import annotations

from pathlib import Path


def test_scaffolder_runtime_import_contract() -> None:
    """The scaffolder must emit the direct runtime and explanation helper imports."""
    base_source = Path("scripts/exercise_scaffolder/base.py").read_text(encoding="utf-8")

    assert "from exercise_runtime_support.exercise_framework import (" in base_source
    assert "    RuntimeCache," in base_source
    assert "    resolve_exercise_notebook_path," in base_source
    assert "    run_cell_and_capture_output," in base_source

    assert "    get_explanation_cell," in base_source
    # Explanation helpers are in the debug subclass only
    assert (
        "from exercise_runtime_support.exercise_framework.expectations_helpers import ("
        in base_source
    )
    assert "    is_valid_explanation," in base_source

    # Old import paths must not appear in the scaffolder
    new_exe_source = Path("scripts/new_exercise.py").read_text(encoding="utf-8")
    assert "runtime.run_cell_and_capture_output" not in new_exe_source
    assert "runtime.get_explanation_cell" not in new_exe_source
    assert "from tests.notebook_grader import run_cell_and_capture_output" not in new_exe_source
    assert "from tests.notebook_grader import get_explanation_cell" not in new_exe_source


def test_workflow_variant_script_contract() -> None:
    """Workflow files must invoke the explicit variant-aware scripts."""
    tests_workflow = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")
    solutions_workflow = Path(".github/workflows/tests-solutions.yml").read_text(encoding="utf-8")
    classroom_workflow = Path("template_repo_files/.github/workflows/classroom.yml").read_text(
        encoding="utf-8"
    )

    assert "scripts/run_pytest_variant.py --variant solution" in tests_workflow
    assert '"scripts/run_pytest_variant.py"' in solutions_workflow
    assert '"--variant"' in solutions_workflow
    assert '"solution"' in solutions_workflow
    assert "scripts/build_autograde_payload.py" in classroom_workflow
    assert "--variant student" in classroom_workflow


def test_template_cli_consumers_link_to_shared_runtime_support() -> None:
    """Template CLI consumers must use the shared runtime support package."""
    collector_source = Path("scripts/template_repo_cli/core/collector.py").read_text(
        encoding="utf-8"
    )
    packager_source = Path("scripts/template_repo_cli/core/packager.py").read_text(encoding="utf-8")

    assert "exercise_runtime_support.pytest_collection_guard" in collector_source
    assert "find_duplicate_exercise_test_sources" in collector_source
    assert "exercise_runtime_support" in packager_source
    assert '"exercise_runtime_support",' in packager_source
    assert "REQUIRED_PACKAGE_DIRECTORIES" in packager_source
