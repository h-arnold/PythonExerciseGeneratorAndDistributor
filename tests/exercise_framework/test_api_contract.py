from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_catalogue import (
    get_catalogue_key_for_exercise_id,
    get_exercise_catalogue,
)
from tests.exercise_framework.api import (
    ExerciseCheckResult,
    NotebookCheckResult,
    run_all_checks,
    run_detailed_ex002_check,
    run_notebook_check,
)

EXPECTED_NOTEBOOK_CHECK_COUNT = 5
EXPECTED_EX002_DETAILED_CHECK_COUNT = 30
EXPECTED_EX002_CHECK_TITLES = {"Logic", "Formatting", "Construct"}


def test_run_all_checks_returns_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    results = run_all_checks()

    assert len(results) == EXPECTED_NOTEBOOK_CHECK_COUNT
    assert all(isinstance(result, NotebookCheckResult) for result in results)
    assert all(result.passed for result in results)
    assert [result.label for result in results] == [
        entry.display_label
        for entry in get_exercise_catalogue()
        if entry.exercise_key != "ex007_sequence_debug_casting"
    ]


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
    with pytest.raises(ValueError, match="Unknown notebook 'unknown_notebook'\\. Available:"):
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
