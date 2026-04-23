"""Direct runtime contract tests for repository surfaces."""

from __future__ import annotations

from pathlib import Path


def test_scaffolder_runtime_import_contract() -> None:
    """The scaffolder must emit the direct runtime and explanation helper imports."""
    source = Path("scripts/new_exercise.py").read_text(encoding="utf-8")

    assert "from exercise_runtime_support.exercise_framework import (" in source
    assert "    RuntimeCache," in source
    assert "    resolve_exercise_notebook_path," in source
    assert "    run_cell_and_capture_output," in source
    assert "    get_explanation_cell," in source
    assert (
        "from exercise_runtime_support.exercise_framework.expectations_helpers import ("
        in source
    )
    assert "    is_valid_explanation," in source

    assert "runtime.run_cell_and_capture_output" not in source
    assert "runtime.get_explanation_cell" not in source
    assert "from tests.notebook_grader import run_cell_and_capture_output" not in source
    assert "from tests.notebook_grader import get_explanation_cell" not in source


def test_notebook_grader_wrapper_links_to_canonical_module() -> None:
    """The compatibility wrapper must point at the canonical notebook grader module."""
    source = Path("tests/notebook_grader.py").read_text(encoding="utf-8")

    assert (
        '"""Compatibility wrapper for '
        ':mod:`exercise_runtime_support.notebook_grader`."""'
        in source
    )
    assert "exercise_runtime_support.notebook_grader" in source
    assert '_import_module("exercise_runtime_support.notebook_grader")' in source


def test_workflow_variant_script_contract() -> None:
    """Workflow files must invoke the explicit variant-aware scripts."""
    tests_workflow = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")
    solutions_workflow = Path(".github/workflows/tests-solutions.yml").read_text(
        encoding="utf-8"
    )
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
    packager_source = Path("scripts/template_repo_cli/core/packager.py").read_text(
        encoding="utf-8"
    )

    assert "exercise_runtime_support.pytest_collection_guard" in collector_source
    assert "find_duplicate_exercise_test_sources" in collector_source
    assert "exercise_runtime_support" in packager_source
    assert 'workspace / "exercise_runtime_support"' in packager_source
    assert "REQUIRED_PACKAGE_DIRECTORIES" in packager_source


def test_contributor_docs_align_on_execution_model_contract() -> None:
    """Contributor-facing docs must reference the execution-model contract."""
    agents_source = Path("AGENTS.md").read_text(encoding="utf-8")
    execution_model_source = Path("docs/execution-model.md").read_text(encoding="utf-8")
    testing_framework_source = Path("docs/testing-framework.md").read_text(
        encoding="utf-8"
    )
    cli_source = Path("docs/exercise-generation-cli.md").read_text(encoding="utf-8")

    assert "docs/execution-model.md" in agents_source
    assert "scripts/run_pytest_variant.py --variant solution" in agents_source

    assert "docs/execution-model.md" in testing_framework_source
    assert "Source of truth:" in testing_framework_source
    assert "scripts/run_pytest_variant.py --variant solution" in testing_framework_source
    assert "scripts/build_autograde_payload.py --variant student" in testing_framework_source

    assert "docs/execution-model.md" in cli_source
    assert "Source of truth:" in cli_source
    assert "from exercise_runtime_support.exercise_framework" in cli_source
    assert "run_notebook_checks('<exercise_key>')" in cli_source

    assert "## 2) Shared runtime import model (`exercise_runtime_support`)" in execution_model_source
    assert "## 3) Variant selection contract (`PYTUTOR_ACTIVE_VARIANT` and `--variant`)" in execution_model_source
    assert "## 4) Source-to-export mapping contract" in execution_model_source


def test_contributor_docs_lock_metadata_only_packaged_contract() -> None:
    """Contributor docs must remove snapshot-era guidance and state the packaged contract."""
    required_fragments = {
        Path("docs/execution-model.md"): (
            "Packaged runtime contract",
            "Resolution and packaging failures must remain fail-fast",
        ),
        Path("docs/testing-framework.md"): (
            "metadata-backed runtime surfaces required by the packaged runtime contract",
        ),
        Path("docs/project-structure.md"): (
            "The packaged Classroom layout includes the metadata-backed runtime contract",
        ),
        Path("docs/development.md"): (
            "metadata-backed student contract rather than the source-repository authoring contract",
        ),
        Path("docs/setup.md"): (
            "metadata-backed student contract used in Classroom",
        ),
        Path("docs/exercise-generation.md"): (
            "flattened notebook/test mirrors are not part of the supported contract",
        ),
        Path("docs/exercise-generation-cli.md"): (
            "Flattened notebook/test mirrors are not part of the supported contract and must not be introduced in scaffold output",
        ),
        Path("docs/exercise-testing.md"): (
            "packaged repositories must satisfy the metadata-backed runtime contract",
        ),
        Path("docs/CLI_README.md"): (
            "Exported per-exercise metadata (`exercise.json`)",
        ),
    }

    forbidden_fragments = (
        "No exported per-exercise metadata",
        "metadata-free",
        "exercise_catalogue_snapshot.json",
        "snapshot",
    )

    for path, fragments in required_fragments.items():
        source = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in source, f"Expected '{fragment}' in {path}"
        for fragment in forbidden_fragments:
            assert fragment not in source, f"Unexpected '{fragment}' in {path}"


def test_framework_wrapper_surfaces_link_to_canonical_modules() -> None:
    """The framework wrapper surface files must point at the canonical modules."""
    expected_targets = {
        Path("tests/exercise_framework/runtime.py"): (
            'exercise_runtime_support.exercise_framework.runtime'
        ),
        Path("tests/exercise_framework/api.py"): "exercise_runtime_support.exercise_framework.api",
        Path("tests/exercise_framework/reporting.py"): (
            "exercise_runtime_support.exercise_framework.reporting"
        ),
        Path("tests/exercise_framework/assertions.py"): (
            "exercise_runtime_support.exercise_framework.assertions"
        ),
        Path("tests/exercise_framework/constructs.py"): (
            "exercise_runtime_support.exercise_framework.constructs"
        ),
        Path("tests/exercise_framework/expectations_helpers.py"): (
            "exercise_runtime_support.exercise_framework.expectations_helpers"
        ),
        Path("tests/exercise_framework/fixtures.py"): (
            "exercise_runtime_support.exercise_framework.fixtures"
        ),
        Path("tests/exercise_framework/paths.py"): (
            "from exercise_runtime_support.exercise_framework.paths import ("
        ),
    }

    for path, target in expected_targets.items():
        source = path.read_text(encoding="utf-8")
        assert target in source
