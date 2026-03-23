"""Tests for ``exercise_runtime_support.student_checker.api``."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from exercise_runtime_support.exercise_catalogue import get_catalogue_entry, get_exercise_catalogue
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.student_checker import api as student_api
from exercise_runtime_support.student_checker.models import ExerciseCheckResult, NotebookCheckSpec
from exercise_runtime_support.student_checker.reporting import CheckResult

ex003 = load_exercise_test_module(
    "ex003_sequence_modify_variables", "expectations")
ex003_checks = load_exercise_test_module(
    "ex003_sequence_modify_variables",
    "student_checker_support",
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

_EX002_CHECK_RESULT_COUNT = 30


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


def test_check_exercise_uses_catalogue_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """Single-exercise checks use the shared catalogue display label."""
    captured_labels: list[str] = []

    def fake_run_check(check: NotebookCheckSpec) -> None:
        captured_labels.append(check.label)

    monkeypatch.setattr(student_api, "run_check", fake_run_check)

    student_api.check_exercise("ex004_sequence_debug_syntax")

    assert captured_labels == [get_catalogue_entry("ex004_sequence_debug_syntax").display_label]


def test_check_exercise_unknown_key_is_explicit() -> None:
    """Unknown exercise keys still fail with a clear message."""
    with pytest.raises(ValueError, match=r"Unknown exercise key 'unknown_notebook'\. Available:"):
        student_api.check_exercise("unknown_notebook")


def test_check_exercise_passes_exercise_key_to_student_checker_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_paths: list[str] = []

    def assert_exercise_key(exercise_reference: str) -> None:
        captured_paths.append(exercise_reference)
        assert exercise_reference == "ex003_sequence_modify_variables"
        assert not isinstance(exercise_reference, Path)
        assert not exercise_reference.startswith("notebooks/")

    def fake_run_cell_and_capture_output(exercise_reference: str, *, tag: str) -> str:
        assert_exercise_key(exercise_reference)
        exercise_no = int(tag.removeprefix("exercise"))
        return f"{ex003.EX003_EXPECTED_STATIC_OUTPUT[exercise_no]}\n"

    def fake_run_cell_with_input(
        exercise_reference: str,
        *,
        tag: str,
        inputs: list[str],
    ) -> str:
        assert_exercise_key(exercise_reference)
        exercise_no = int(tag.removeprefix("exercise"))
        assert inputs == _EX003_PROMPT_FLOW_INPUTS[exercise_no]
        values = dict(
            zip(_EX003_PROMPT_FLOW_PLACEHOLDERS[exercise_no], inputs, strict=True)
        )
        prompts = ex003.EX003_EXPECTED_PROMPTS[exercise_no]
        message = ex003.EX003_EXPECTED_INPUT_MESSAGES[exercise_no].format(**values)
        return "".join(f"{line}\n" for line in (*prompts, message))

    def fake_print_exercise_results(_results: Sequence[ExerciseCheckResult]) -> None:
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
    monkeypatch.setattr(student_api, "print_exercise_results", fake_print_exercise_results)

    student_api.check_exercise("ex003_sequence_modify_variables")

    assert captured_paths


def test_check_exercise_supports_generic_ex002_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_results: list[Sequence[ExerciseCheckResult]] = []

    def fake_print_exercise_results(results: Sequence[ExerciseCheckResult]) -> None:
        captured_results.append(results)

    monkeypatch.setattr(student_api, "print_exercise_results", fake_print_exercise_results)

    student_api.check_exercise("ex002_sequence_modify_basics")

    assert len(captured_results) == 1
    results = list(captured_results[0])
    assert len(results) == _EX002_CHECK_RESULT_COUNT
    assert {result.title for result in results} == {"Construct", "Formatting", "Logic"}
    assert {result.exercise_no for result in results} == set(range(1, 11))
