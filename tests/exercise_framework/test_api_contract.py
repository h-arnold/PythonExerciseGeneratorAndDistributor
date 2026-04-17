from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import exercise_runtime_support.exercise_framework as framework_package
import exercise_runtime_support.exercise_framework.api as framework_api
import exercise_runtime_support.exercise_framework.expectations as framework_expectations
import exercise_runtime_support.exercise_framework.paths as framework_paths
import exercise_runtime_support.exercise_framework.runtime as framework_runtime
from exercise_runtime_support.exercise_catalogue import (
    get_catalogue_key_for_exercise_id,
    get_exercise_catalogue,
)
from exercise_runtime_support.support_matrix import SupportRole, has_support_role
from tests.exercise_framework.api import (
    ExerciseCheckResult,
    NotebookCheckResult,
    run_all_checks,
    run_detailed_ex002_check,
    run_notebook_check,
)

EXPECTED_EX002_DETAILED_CHECK_COUNT = 30
EXPECTED_EX002_CHECK_TITLES = {"Logic", "Formatting", "Construct"}


def test_run_all_checks_returns_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    results = run_all_checks()
    expected_labels = [
        entry.display_label
        for entry in get_exercise_catalogue()
        if has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_DETAILED)
        or has_support_role(entry.exercise_id, SupportRole.FRAMEWORK_SMOKE)
    ]

    assert len(results) == len(expected_labels)
    assert all(isinstance(result, NotebookCheckResult) for result in results)
    assert all(result.passed for result in results)
    assert [result.label for result in results] == expected_labels


def test_run_notebook_check_returns_single_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    results = run_notebook_check("ex004_sequence_debug_syntax")

    assert len(results) == 1
    assert isinstance(results[0], NotebookCheckResult)
    assert results[0].label == "ex004 Debug Syntax Errors"
    assert results[0].passed is True


def test_run_notebook_check_unknown_slug_is_explicit() -> None:
    with pytest.raises(ValueError, match="Unknown exercise key 'unknown_notebook'\\. Available:"):
        run_notebook_check("unknown_notebook")


def test_run_detailed_ex002_check_returns_detailed_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    results = run_detailed_ex002_check()

    assert len(results) == EXPECTED_EX002_DETAILED_CHECK_COUNT
    assert all(isinstance(result, ExerciseCheckResult) for result in results)
    assert {result.title for result in results} == EXPECTED_EX002_CHECK_TITLES
    assert all(result.passed for result in results)


def test_run_notebook_check_supports_ex002_summary_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    results = run_notebook_check(get_catalogue_key_for_exercise_id(2))

    assert len(results) == 1
    assert results[0].label == "ex002 Sequence Modify Basics"
    assert results[0].passed is True


def test_run_notebook_check_passes_exercise_key_to_runtime_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_arguments: list[tuple[object, str]] = []

    def fake_run_cell_and_capture_output(
        notebook_path: object,
        *,
        tag: str,
    ) -> str:
        captured_arguments.append((notebook_path, tag))
        assert notebook_path == "ex004_sequence_debug_syntax"
        assert isinstance(notebook_path, str)
        assert not isinstance(notebook_path, Path)
        assert not notebook_path.startswith("notebooks/")
        return ""

    monkeypatch.setattr(
        framework_api.runtime,
        "run_cell_and_capture_output",
        fake_run_cell_and_capture_output,
    )

    results = run_notebook_check("ex004_sequence_debug_syntax")

    assert captured_arguments == [("ex004_sequence_debug_syntax", "exercise1")]
    assert results == [NotebookCheckResult(
        "ex004 Debug Syntax Errors", True, [])]


def test_package_surface_re_exports_expectations_symbols() -> None:
    expected_sources = {
        "resolve_exercise_notebook_path": framework_paths,
        "resolve_notebook_path": framework_paths,
        "RuntimeCache": framework_runtime,
        "exec_tagged_code": framework_runtime,
        "extract_tagged_code": framework_runtime,
        "get_explanation_cell": framework_runtime,
        "run_cell_and_capture_output": framework_runtime,
        "run_cell_with_input": framework_runtime,
        "expected_output_lines": framework_expectations,
        "expected_output_text": framework_expectations,
        "expected_print_call_count": framework_expectations,
        "ExerciseCheckResult": framework_api,
        "NotebookCheckResult": framework_api,
        "run_all_checks": framework_api,
        "run_detailed_ex002_check": framework_api,
        "run_notebook_check": framework_api,
    }

    for name, module in expected_sources.items():
        assert getattr(framework_package, name) is getattr(module, name)

    assert framework_package.__all__ == [
        "EX002_CHECKS",
        "Ex002CheckDefinition",
        "ExerciseCheckResult",
        "NotebookCheckResult",
        "RuntimeCache",
        "exec_tagged_code",
        "expected_output_lines",
        "expected_output_text",
        "expected_print_call_count",
        "extract_tagged_code",
        "get_explanation_cell",
        "resolve_exercise_notebook_path",
        "resolve_notebook_path",
        "run_all_checks",
        "run_cell_and_capture_output",
        "run_cell_with_input",
        "run_detailed_ex002_check",
        "run_notebook_check",
    ]


def test_package_surface_lazy_loads_ex002_support_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(framework_expectations, "_ex002_support_module", None)
    monkeypatch.delitem(vars(framework_expectations),
                        "EX002_CHECKS", raising=False)
    monkeypatch.delitem(vars(framework_expectations),
                        "Ex002CheckDefinition", raising=False)
    monkeypatch.delitem(vars(framework_package), "EX002_CHECKS", raising=False)
    monkeypatch.delitem(vars(framework_package),
                        "Ex002CheckDefinition", raising=False)

    reloaded_package = importlib.reload(framework_package)

    assert "EX002_CHECKS" not in vars(reloaded_package)
    assert "Ex002CheckDefinition" not in vars(reloaded_package)
    assert "EX002_CHECKS" not in vars(framework_expectations)
    assert "Ex002CheckDefinition" not in vars(framework_expectations)

    assert reloaded_package.EX002_CHECKS is framework_expectations.EX002_CHECKS
    assert (
        reloaded_package.Ex002CheckDefinition
        is framework_expectations.Ex002CheckDefinition
    )
