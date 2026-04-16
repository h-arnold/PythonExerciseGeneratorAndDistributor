"""Tests for ``exercise_runtime_support.student_checker.notebook_runtime``."""

from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.notebook_grader import NotebookGradingError
from exercise_runtime_support.student_checker import notebook_runtime


def test_run_tagged_cell_uses_static_runner_when_no_input_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"static": 0, "interactive": 0}

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        assert notebook_path == "dummy_exercise"
        assert tag == "exercise1"
        return 0

    def fake_run_static(notebook_path: str, *, tag: str, variant: str) -> str:
        calls["static"] += 1
        assert notebook_path == "dummy_exercise"
        assert tag == "exercise1"
        assert variant == "student"
        return "ok\n"

    def fake_run_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
        variant: str,
    ) -> str:
        calls["interactive"] += 1
        assert variant == "student"
        return ""

    monkeypatch.setattr(
        notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert calls == {"static": 1, "interactive": 0}


def test_run_tagged_cell_uses_mocked_inputs_for_interactive_cells(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"static": 0, "interactive": 0}

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        assert notebook_path == "dummy_exercise"
        assert tag == "exercise1"
        return 2

    def fake_run_static(notebook_path: str, *, tag: str, variant: str) -> str:
        calls["static"] += 1
        assert variant == "student"
        return ""

    def fake_run_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
        variant: str,
    ) -> str:
        calls["interactive"] += 1
        assert notebook_path == "dummy_exercise"
        assert tag == "exercise1"
        assert inputs == ["2", "2"]
        assert variant == "student"
        return "ok\n"

    monkeypatch.setattr(
        notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert calls == {"static": 0, "interactive": 1}


def test_count_input_calls_detects_name_and_builtins_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_count = 2
    source = "first = input('A: ')\nsecond = builtins.input('B: ')\nprint(first, second)\n"

    def fake_extract_tagged_code(*_args: object, **kwargs: object) -> str:
        assert kwargs["variant"] == "student"
        return source

    monkeypatch.setattr(
        notebook_runtime, "extract_tagged_code", fake_extract_tagged_code)

    count = notebook_runtime._count_input_calls(
        "dummy_exercise", tag="exercise1")

    assert count == expected_count


def test_run_notebook_checks_marks_failure_when_execution_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_tagged_cell(notebook_path: str, tag: str) -> None:
        raise NotebookGradingError("Execution failed")

    monkeypatch.setattr(
        notebook_runtime, "_run_tagged_cell", fake_run_tagged_cell)

    results = notebook_runtime._run_notebook_checks(
        Path("dummy_exercise"), ["exercise1"])

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].message == "Execution failed"


def test_run_notebook_checks_passes_path_object_to_tagged_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[Path] = []

    def fake_run_tagged_cell(notebook_path: str | Path, tag: str) -> None:
        assert tag == "exercise1"
        assert isinstance(notebook_path, Path)
        received.append(notebook_path)

    notebook_path = Path("dummy_exercise.ipynb")
    monkeypatch.setattr(
        notebook_runtime, "_run_tagged_cell", fake_run_tagged_cell)

    results = notebook_runtime._run_notebook_checks(
        notebook_path, ["exercise1"])

    assert [result.passed for result in results] == [True]
    assert received == [notebook_path]


def test_run_notebook_checks_uses_exercise_local_student_checker_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_results: list[object] = []
    sentinel_results = [object()]

    def fake_has_exercise_checks(exercise_key: str) -> bool:
        assert exercise_key == "ex002_sequence_modify_basics"
        return True

    def fake_run_exercise_checks(exercise_key: str) -> list[object]:
        assert exercise_key == "ex002_sequence_modify_basics"
        return sentinel_results

    def fake_print_exercise_results(results: list[object]) -> None:
        captured_results.extend(results)

    def fail_resolve_notebook_path(*_args: object, **_kwargs: object) -> Path:
        raise AssertionError("generic notebook fallback should not run")

    monkeypatch.setattr(
        notebook_runtime,
        "has_exercise_checks",
        fake_has_exercise_checks,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "run_exercise_checks",
        fake_run_exercise_checks,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "print_exercise_results",
        fake_print_exercise_results,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "resolve_notebook_path",
        fail_resolve_notebook_path,
    )

    notebook_runtime.run_notebook_checks("ex002_sequence_modify_basics")

    assert captured_results == sentinel_results


def test_run_notebook_checks_falls_back_to_tagged_execution_when_support_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook_path = Path("dummy_exercise.ipynb")
    seen: dict[str, object] = {}
    sentinel_results = [object()]

    def fake_has_exercise_checks(_exercise_key: str) -> bool:
        return False

    def fake_resolve_notebook_path(
        exercise_key: str,
        *,
        variant: str,
    ) -> Path:
        seen["exercise_key"] = exercise_key
        seen["variant"] = variant
        return notebook_path

    def fake_collect_exercise_tags(path: Path) -> list[str]:
        assert path == notebook_path
        return ["exercise1"]

    def fake_run_notebook_checks(
        path: Path,
        tags: list[str],
    ) -> list[object]:
        assert path == notebook_path
        assert tags == ["exercise1"]
        return sentinel_results

    def fake_print_notebook_check_results(results: list[object]) -> None:
        seen["results"] = results

    monkeypatch.setattr(
        notebook_runtime,
        "has_exercise_checks",
        fake_has_exercise_checks,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "resolve_notebook_path",
        fake_resolve_notebook_path,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "_collect_exercise_tags",
        fake_collect_exercise_tags,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "_run_notebook_checks",
        fake_run_notebook_checks,
    )
    monkeypatch.setattr(
        notebook_runtime,
        "_print_notebook_check_results",
        fake_print_notebook_check_results,
    )

    notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    assert seen == {
        "exercise_key": "ex003_sequence_modify_variables",
        "variant": "student",
        "results": sentinel_results,
    }


def test_run_notebook_checks_reports_failures_for_unsolved_ex002(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)

    notebook_runtime.run_notebook_checks("ex002_sequence_modify_basics")

    output = capsys.readouterr().out

    assert "Exercise 1" in output
    assert "Logic" in output
    assert "Hello Python!" in output
    assert "Great work! Everything that can be checked here looks good." not in output
    assert "Great work! All exercise cells ran without errors." not in output


def test_run_tagged_cell_retries_when_missing_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    attempt_lengths: list[int] = []

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
        variant: str,
    ) -> str:
        attempt_lengths.append(len(inputs))
        assert variant == "student"
        if len(attempt_lengths) == 1:
            _raise_missing_input_error()
        return "ok\n"

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(
        notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_with_input", fake_run_with_input)

    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert attempt_lengths == [1, 2]


def test_run_tagged_cell_propagates_real_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
        variant: str,
    ) -> str:
        assert variant == "student"
        raise NotebookGradingError("Execution failed")

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(
        notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_with_input", fake_run_with_input)

    with pytest.raises(NotebookGradingError, match="Execution failed"):
        notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")


def test_run_tagged_cell_stops_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0
    limit = 2

    def fake_count_input_calls(notebook_path: str, *, tag: str) -> int:
        return 1

    def fake_run_with_input(
        notebook_path: str,
        *,
        tag: str,
        inputs: list[str],
        variant: str,
    ) -> str:
        nonlocal attempts
        attempts += 1
        assert variant == "student"
        _raise_missing_input_error()
        return ""

    def fake_run_static(*_args: object, **_kwargs: object) -> str:
        return ""

    monkeypatch.setattr(
        notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(
        notebook_runtime, "run_cell_with_input", fake_run_with_input)
    monkeypatch.setattr(notebook_runtime, "_MAX_AUTOMATED_INPUTS", limit)

    with pytest.raises(NotebookGradingError):
        notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert attempts == limit


def _raise_missing_input_error() -> None:
    try:
        raise RuntimeError("Test expected more input values")
    except RuntimeError as exc:
        raise NotebookGradingError(
            "Execution failed for missing input") from exc
