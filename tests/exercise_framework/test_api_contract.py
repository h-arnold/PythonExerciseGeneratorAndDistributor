from __future__ import annotations

import pytest

from tests.exercise_framework.api import (
    EX002_SLUG,
    ExerciseCheckResult,
    NotebookCheckResult,
    run_all_checks,
    run_detailed_ex002_check,
    run_notebook_check,
)

EXPECTED_NOTEBOOK_CHECK_COUNT = 6
EXPECTED_EX002_DETAILED_CHECK_COUNT = 30
EXPECTED_EX002_CHECK_TITLES = {"Logic", "Formatting", "Construct"}


def test_run_all_checks_returns_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    results = run_all_checks()

    assert len(results) == EXPECTED_NOTEBOOK_CHECK_COUNT
    assert all(isinstance(result, NotebookCheckResult) for result in results)
    assert all(result.passed for result in results)


def test_run_notebook_check_returns_single_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    results = run_notebook_check("ex001_sanity")

    assert len(results) == 1
    assert isinstance(results[0], NotebookCheckResult)
    assert results[0].label == "ex001 Sanity"
    assert results[0].passed is True


def test_run_notebook_check_unknown_slug_is_explicit() -> None:
    with pytest.raises(ValueError, match="Unknown notebook 'unknown_notebook'\\. Available:"):
        run_notebook_check("unknown_notebook")


def test_run_detailed_ex002_check_returns_detailed_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    results = run_detailed_ex002_check()

    assert len(results) == EXPECTED_EX002_DETAILED_CHECK_COUNT
    assert all(isinstance(result, ExerciseCheckResult) for result in results)
    assert {result.title for result in results} == EXPECTED_EX002_CHECK_TITLES
    assert all(result.passed for result in results)


def test_run_notebook_check_supports_ex002_summary_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    results = run_notebook_check(EX002_SLUG)

    assert len(results) == 1
    assert results[0].label == "ex002 Sequence Modify Basics"
    assert results[0].passed is True
