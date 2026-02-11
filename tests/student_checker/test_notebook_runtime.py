from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from pytest import MonkeyPatch

from tests.notebook_grader import NotebookGradingError
from tests.student_checker import notebook_runtime as _notebook_runtime

notebook_runtime = cast(Any, _notebook_runtime)


def test_run_tagged_cell_uses_static_runner_when_no_input_calls(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = {"static": 0, "interactive": 0}

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        assert notebook_path == "dummy.ipynb"
        assert tag == "exercise1"
        return 0

    def fake_run_static(notebook_path: str, *, tag: str) -> str:
        calls["static"] += 1
        assert notebook_path == "dummy.ipynb"
        assert tag == "exercise1"
        return "ok\n"

    def fake_run_with_input(notebook_path: str, *, tag: str, inputs: list[str]) -> str:
        calls["interactive"] += 1
        return ""

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy.ipynb", "exercise1")

    assert calls == {"static": 1, "interactive": 0}


def test_run_tagged_cell_uses_mocked_inputs_for_interactive_cells(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = {"static": 0, "interactive": 0}

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        assert notebook_path == "dummy.ipynb"
        assert tag == "exercise1"
        return 2

    def fake_run_static(notebook_path: str, *, tag: str) -> str:
        calls["static"] += 1
        return ""

    def fake_run_with_input(notebook_path: str, *, tag: str, inputs: list[str]) -> str:
        calls["interactive"] += 1
        assert notebook_path == "dummy.ipynb"
        assert tag == "exercise1"
        assert inputs == ["2", "2"]
        return "ok\n"

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy.ipynb", "exercise1")

    assert calls == {"static": 0, "interactive": 1}


def test_count_input_calls_detects_name_and_builtins_calls(monkeypatch: MonkeyPatch) -> None:
    expected_count = 2
    source = "first = input('A: ')\nsecond = builtins.input('B: ')\nprint(first, second)\n"

    def fake_extract_tagged_code(*_args: object, **_kwargs: object) -> str:
        return source

    monkeypatch.setattr(notebook_runtime, "extract_tagged_code", fake_extract_tagged_code)

    count = notebook_runtime._count_input_calls("dummy.ipynb", tag="exercise1")

    assert count == expected_count


def test_run_notebook_checks_marks_failure_when_execution_raises(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_run_tagged_cell(notebook_path: str, tag: str) -> None:
        raise NotebookGradingError("Execution failed")

    monkeypatch.setattr(notebook_runtime, "_run_tagged_cell", fake_run_tagged_cell)

    results = notebook_runtime._run_notebook_checks(Path("dummy.ipynb"), ["exercise1"])

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].message == "Execution failed"


def test_run_tagged_cell_retries_when_missing_inputs(monkeypatch: MonkeyPatch) -> None:
    attempt_lengths: list[int] = []

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(notebook_path: str, *, tag: str, inputs: list[str]) -> str:
        attempt_lengths.append(len(inputs))
        if len(attempt_lengths) == 1:
            _raise_missing_input_error()
        return "ok\n"

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy.ipynb", "exercise1")

    assert attempt_lengths == [1, 2]


def test_run_tagged_cell_propagates_real_errors(monkeypatch: MonkeyPatch) -> None:
    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(notebook_path: str, *, tag: str, inputs: list[str]) -> str:
        raise NotebookGradingError("Execution failed")

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    with pytest.raises(NotebookGradingError, match="Execution failed"):
        notebook_runtime._run_tagged_cell("dummy.ipynb", "exercise1")


def test_run_tagged_cell_stops_after_max_attempts(monkeypatch: MonkeyPatch) -> None:
    attempts = 0
    limit = 2

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(notebook_path: str, *, tag: str, inputs: list[str]) -> str:
        nonlocal attempts
        attempts += 1
        _raise_missing_input_error()
        return ""

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)
    monkeypatch.setattr(notebook_runtime, "_MAX_AUTOMATED_INPUTS", limit)

    with pytest.raises(NotebookGradingError):
        notebook_runtime._run_tagged_cell("dummy.ipynb", "exercise1")

    assert attempts == limit


def _raise_missing_input_error() -> None:
    try:
        raise RuntimeError("Test expected more input values")
    except RuntimeError as exc:
        raise NotebookGradingError("Execution failed for missing input") from exc
