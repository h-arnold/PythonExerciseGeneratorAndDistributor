"""Tests for ``exercise_runtime_support.student_checker.api``."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from exercise_runtime_support.exercise_catalogue import get_catalogue_entry, get_exercise_catalogue
from exercise_runtime_support.student_checker import api as student_api
from exercise_runtime_support.student_checker.checks import ex003 as ex003_checks
from exercise_runtime_support.student_checker.models import ExerciseCheckResult, NotebookCheckSpec
from exercise_runtime_support.student_checker.reporting import CheckResult
from tests.exercise_expectations import (
    EX003_EXPECTED_INPUT_MESSAGES,
    EX003_EXPECTED_PROMPTS,
    EX003_EXPECTED_STATIC_OUTPUT,
)

_EX003_PROMPT_FLOW_INPUTS = {
    4: ["mango", "tropical"],
    5: ["Cardiff", "Wales"],
    6: ["Alex", "Morgan"],
}

_EX003_PROMPT_FLOW_PLACEHOLDERS = {
    4: ("value1", "value2"),
    5: ("town", "country"),
    6: ("first", "last"),
}


def test_check_exercises_uses_catalogue_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Summary checks follow the shared catalogue order."""
    seen_labels: list[str] = []

    def fake_run_checks(check_specs: list[NotebookCheckSpec]) -> list[CheckResult]:
        seen_labels.extend(check.label for check in check_specs)
        return []

    def fake_print_results(_results: list[CheckResult]) -> None:
        return None

    monkeypatch.setattr(student_api, "run_checks", fake_run_checks)
    monkeypatch.setattr(student_api, "print_results", fake_print_results)

    student_api.check_exercises()

    assert seen_labels == [entry.display_label for entry in get_exercise_catalogue()]


def test_check_notebook_uses_catalogue_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """Single-notebook checks use the shared catalogue display label."""
    captured_labels: list[str] = []

    def fake_run_check(check: NotebookCheckSpec) -> None:
        captured_labels.append(check.label)

    monkeypatch.setattr(student_api, "run_check", fake_run_check)

    student_api.check_notebook("ex004_sequence_debug_syntax")

    assert captured_labels == [get_catalogue_entry("ex004_sequence_debug_syntax").display_label]


def test_check_notebook_unknown_slug_is_explicit() -> None:
    """Unknown notebook keys still fail with a clear message."""
    with pytest.raises(ValueError, match=r"Unknown notebook 'unknown_notebook'\. Available:"):
        student_api.check_notebook("unknown_notebook")


def test_check_notebook_passes_exercise_key_to_student_checker_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_paths: list[str] = []

    def assert_exercise_key(notebook_path: str) -> None:
        captured_paths.append(notebook_path)
        assert notebook_path == "ex003_sequence_modify_variables"
        assert not isinstance(notebook_path, Path)
        assert not notebook_path.startswith("notebooks/")

    def fake_run_cell_and_capture_output(notebook_path: str, *, tag: str) -> str:
        assert_exercise_key(notebook_path)
        exercise_no = int(tag.removeprefix("exercise"))
        return f"{EX003_EXPECTED_STATIC_OUTPUT[exercise_no]}\n"

    def fake_run_cell_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
    ) -> str:
        assert_exercise_key(notebook_path)
        exercise_no = int(tag.removeprefix("exercise"))
        assert inputs == _EX003_PROMPT_FLOW_INPUTS[exercise_no]
        values = dict(zip(_EX003_PROMPT_FLOW_PLACEHOLDERS[exercise_no], inputs, strict=True))
        prompts = EX003_EXPECTED_PROMPTS[exercise_no]
        message = EX003_EXPECTED_INPUT_MESSAGES[exercise_no].format(**values)
        return "".join(f"{line}\n" for line in (*prompts, message))

    def fake_print_ex003_results(_results: Sequence[ExerciseCheckResult]) -> None:
        return None

    monkeypatch.setattr(
        ex003_checks,
        "run_cell_and_capture_output",
        fake_run_cell_and_capture_output,
    )
    monkeypatch.setattr(
        ex003_checks,
        "run_cell_with_input",
        fake_run_cell_with_input,
    )
    monkeypatch.setattr(student_api, "print_ex003_results", fake_print_ex003_results)

    student_api.check_notebook("ex003_sequence_modify_variables")

    assert captured_paths
