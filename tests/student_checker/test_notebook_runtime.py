from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from tests.notebook_grader import NotebookGradingError
from tests.student_checker import notebook_runtime


def test_run_notebook_checks_uses_static_runner_when_no_input_calls(
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

    results = notebook_runtime._run_notebook_checks(Path("dummy.ipynb"), ["exercise1"])

    assert calls == {"static": 1, "interactive": 0}
    assert len(results) == 1
    assert results[0].passed is True


def test_run_notebook_checks_uses_mocked_inputs_for_interactive_cells(
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

    results = notebook_runtime._run_notebook_checks(Path("dummy.ipynb"), ["exercise1"])

    assert calls == {"static": 0, "interactive": 1}
    assert len(results) == 1
    assert results[0].passed is True


def test_count_input_calls_detects_name_and_builtins_calls(monkeypatch: MonkeyPatch) -> None:
    expected_count = 2
    source = (
        "first = input('A: ')\n"
        "second = builtins.input('B: ')\n"
        "print(first, second)\n"
    )
    monkeypatch.setattr(notebook_runtime, "extract_tagged_code", lambda *_args, **_kwargs: source)

    count = notebook_runtime._count_input_calls("dummy.ipynb", tag="exercise1")

    assert count == expected_count


def test_run_notebook_checks_marks_failure_when_execution_raises(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 0

    def fake_run_static(notebook_path: str, *, tag: str) -> str:
        raise NotebookGradingError("Execution failed")

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)

    results = notebook_runtime._run_notebook_checks(Path("dummy.ipynb"), ["exercise1"])

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].message == "Execution failed"
