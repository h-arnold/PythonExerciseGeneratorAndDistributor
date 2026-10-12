"""Tests for ``exercise_runtime_support.student_checker.notebook_runtime``."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest

from exercise_runtime_support.notebook_grader import NotebookGradingError
from exercise_runtime_support.student_checker import checks, notebook_runtime, readability
from exercise_runtime_support.student_checker.models import ExerciseCheckResult

_FUNCTIONAL_CHECK_COUNT = 30


def _functional_result(passed: bool) -> list[ExerciseCheckResult]:
    return [
        ExerciseCheckResult(
            exercise_no=1,
            title="Functional logic",
            passed=passed,
            issues=[] if passed else ["functional assertion failed"],
        )
    ]


def _two_functional_results(passed: bool) -> list[ExerciseCheckResult]:
    return [
        ExerciseCheckResult(1, "Functional logic", passed, [] if passed else ["task one failed"]),
        ExerciseCheckResult(2, "Functional output", passed, [] if passed else ["task two failed"]),
    ]


def _readability_result(
    passed: bool,
) -> readability.NotebookAnalysis:
    diagnostics = (
        ()
        if passed
        else (
            readability.Finding("E225", 2, 6, "Missing whitespace around operator"),
            readability.Finding("W291", 2, 10, "Trailing whitespace"),
        )
    )
    return readability.NotebookAnalysis(
        cells=(
            readability.CellAnalysis(
                source="first = 1\nvalue=1  \n",
                cell_index=5,
                task_tag="exercise1",
                findings=diagnostics,
                syntax_blocked=False,
            ),
            readability.CellAnalysis(
                source="clean_value = 2\n",
                cell_index=7,
                task_tag="exercise2",
                findings=(),
                syntax_blocked=False,
            ),
        )
    )


def test_run_tagged_cell_uses_static_runner_when_no_input_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
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

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    # pyright: ignore[reportPrivateUsage]
    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert calls == {"static": 1, "interactive": 0}


def test_run_tagged_cell_uses_mocked_inputs_for_interactive_cells(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
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

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    # pyright: ignore[reportPrivateUsage]
    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert calls == {"static": 0, "interactive": 1}


def test_count_input_calls_detects_name_and_builtins_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    expected_count = 2
    source = "first = input('A: ')\nsecond = builtins.input('B: ')\nprint(first, second)\n"

    def fake_extract_tagged_code(*_args: object, **kwargs: object) -> str:
        assert kwargs["variant"] == "student"
        return source

    monkeypatch.setattr(notebook_runtime, "extract_tagged_code", fake_extract_tagged_code)

    count = notebook_runtime._count_input_calls(  # pyright: ignore[reportPrivateUsage]
        "dummy_exercise", tag="exercise1"
    )

    assert count == expected_count


def test_load_notebook_json_rejects_non_mapping_json(
    tmp_path: Path,
) -> None:
    path = tmp_path / "broken.ipynb"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(
        NotebookGradingError,
        match="Notebook JSON must be a JSON object",
    ):
        # pyright: ignore[reportPrivateUsage]
        notebook_runtime._load_notebook_json(path)


def test_load_notebook_json_rejects_non_string_object_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "broken.ipynb"
    path.write_text("{}", encoding="utf-8")

    def fake_loads(_raw_json: str) -> object:
        return {1: []}

    monkeypatch.setattr(notebook_runtime.json, "loads", fake_loads)

    with pytest.raises(
        NotebookGradingError,
        match="Notebook JSON must be a JSON object",
    ):
        # pyright: ignore[reportPrivateUsage]
        notebook_runtime._load_notebook_json(path)


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ('{"metadata": {}}', "Notebook JSON must contain a 'cells' list"),
        ('{"cells": {}}', "Notebook JSON must contain a 'cells' list"),
        (
            '{"cells": [{"metadata": {}}, "oops"]}',
            "Notebook JSON must contain a 'cells' list of notebook cell objects",
        ),
        (
            '{"cells": [{"cell_type": "code", "metadata": {"tags": ["exercise1"]}, "source": 1}]}',
            "Notebook JSON must contain a 'cells' list of notebook cell objects",
        ),
        (
            '{"cells": [{"source": [], "metadata": {}}]}',
            "Notebook JSON must contain a 'cells' list of notebook cell objects",
        ),
    ],
)
def test_load_notebook_json_rejects_missing_or_invalid_cells(
    tmp_path: Path,
    content: str,
    match: str,
) -> None:
    path = tmp_path / "broken.ipynb"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(NotebookGradingError, match=match):
        # pyright: ignore[reportPrivateUsage]
        notebook_runtime._load_notebook_json(path)


def test_run_notebook_checks_marks_failure_when_execution_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_tagged_cell(notebook_path: str, tag: str) -> None:
        raise NotebookGradingError("Execution failed")

    monkeypatch.setattr(notebook_runtime, "_run_tagged_cell", fake_run_tagged_cell)

    results = notebook_runtime._run_notebook_checks(  # pyright: ignore[reportPrivateUsage]
        Path("dummy_exercise"), ["exercise1"]
    )

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
    monkeypatch.setattr(notebook_runtime, "_run_tagged_cell", fake_run_tagged_cell)

    results = notebook_runtime._run_notebook_checks(  # pyright: ignore[reportPrivateUsage]
        notebook_path, ["exercise1"]
    )

    assert [result.passed for result in results] == [True]
    assert received == [notebook_path]


_OUTCOME_CASES = [
    (local, functional, readable)
    for local in (False, True)
    for functional in (False, True)
    for readable in (False, True)
]
_TASK_CELL_COUNT = 2
_SOLUTION_BACKLOG_FUNCTIONAL_COUNT = 10


def _has_local_checks(enabled: bool) -> Callable[[str], bool]:
    def has_checks(_exercise_key: str) -> bool:
        return enabled

    return has_checks


def _collect_one_tag(_path: Path) -> list[str]:
    return ["exercise1"]


def _collect_two_tags(_path: Path) -> list[str]:
    return ["exercise1", "exercise2"]


def _fallback_results(
    passed: bool,
) -> Callable[[Path, list[str]], list[notebook_runtime.NotebookTagCheckResult]]:
    def run(_path: Path, _tags: list[str]) -> list[notebook_runtime.NotebookTagCheckResult]:
        return [
            notebook_runtime.NotebookTagCheckResult(
                tag="exercise1", passed=passed, message="task one failed" if not passed else ""
            ),
            notebook_runtime.NotebookTagCheckResult(
                tag="exercise2", passed=passed, message="task two failed" if not passed else ""
            ),
        ]

    return run


def _local_results(passed: bool) -> Callable[[str], list[ExerciseCheckResult]]:
    def run(_exercise_key: str) -> list[ExerciseCheckResult]:
        return _two_functional_results(passed)

    return run


def _three_functional_results(_key: str) -> list[ExerciseCheckResult]:
    return [
        ExerciseCheckResult(1, title, True, [])
        for title in ("First functional check", "Second functional check", "Third functional check")
    ]


def _one_clean_cell_analysis(_path: Path) -> readability.NotebookAnalysis:
    return readability.NotebookAnalysis(
        cells=(
            readability.CellAnalysis(
                source="value = 1\n",
                cell_index=5,
                task_tag="exercise1",
                findings=(),
                syntax_blocked=False,
            ),
        )
    )


def _assert_task_rows(
    output: str,
    *,
    local_support: bool,
    functional_passed: bool,
    readability_passed: bool,
) -> None:
    rows = output.splitlines()
    assert "Exercise 1" in output and "Exercise 2" in output
    if local_support:
        assert "Functional logic" in output and "Functional output" in output
        functional_rows = [
            line for line in rows if "Functional logic" in line or "Functional output" in line
        ]
        first_task_check = "Functional logic"
        second_task_check = "Functional output"
    else:
        functional_rows = [line for line in rows if "exercise1" in line or "exercise2" in line]
        first_task_check = "exercise1"
        second_task_check = "exercise2"
    assert len(functional_rows) == _TASK_CELL_COUNT
    assert all(("🟢 OK" in line) is functional_passed for line in functional_rows)
    assert output.index(first_task_check) < output.index("cell 6")
    assert output.index("cell 6") < output.index(second_task_check) < output.index("cell 8")

    if readability_passed:
        readability_rows = [line for line in rows if "cell 6" in line or "cell 8" in line]
        assert len(readability_rows) == _TASK_CELL_COUNT
        assert all("🟢 OK" in line for line in readability_rows)
        assert all("No selected readability issues found" in line for line in readability_rows)
    else:
        cell_six_row = next(line for line in rows if "cell 6" in line)
        cell_eight_row = next(line for line in rows if "cell 8" in line)
        assert "🔴 NO" in cell_six_row
        assert "🟢 OK" in cell_eight_row
        assert "No selected readability issues found" in cell_eight_row


def _assert_readability_diagnostics(output: str, *, passed: bool) -> None:
    if not passed:
        assert "line 2" in output and "column 6" in output and "column 10" in output
        assert "E225" in output and "Missing whitespace around operator" in output
        assert "W291" in output and "Trailing whitespace" in output
        assert output.index("E225") < output.index("W291") < output.index("cell 8")


def _assert_no_footer(output: str) -> None:
    for text in (
        "Functional summary:",
        "Readability summary:",
        "Overall self-check:",
        "Save your notebook",
        "RUFF_GUIDE.md",
        "teacher-side marks",
    ):
        assert text not in output
    assert "Great work! All exercise cells ran without errors." not in output
    assert "Great work! Everything that can be checked here looks good." not in output


@pytest.mark.parametrize("case", _OUTCOME_CASES)
def test_both_dispatch_paths_render_required_combined_task_rows(
    case: tuple[bool, bool, bool],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    local_support, functional_passed, readability_passed = case
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(local_support))
    notebook_path = Path("exercise.ipynb")
    resolved: list[tuple[str, str]] = []
    analyzed: list[Path] = []

    def resolve(exercise_key: str, *, variant: str) -> Path:
        resolved.append((exercise_key, variant))
        return notebook_path

    def analyze(path: Path) -> readability.NotebookAnalysis:
        analyzed.append(path)
        return _readability_result(readability_passed)

    monkeypatch.setattr(
        notebook_runtime,
        "resolve_notebook_path",
        resolve,
    )
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", analyze, raising=False)
    monkeypatch.setattr(notebook_runtime, "_collect_exercise_tags", _collect_two_tags)
    monkeypatch.setattr(
        notebook_runtime, "_run_notebook_checks", _fallback_results(functional_passed)
    )
    monkeypatch.setattr(notebook_runtime, "run_exercise_checks", _local_results(functional_passed))

    result = notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    output = capsys.readouterr().out
    assert result is None
    assert resolved == [("ex003_sequence_modify_variables", "student")]
    assert analyzed == [notebook_path]
    _assert_task_rows(
        output,
        local_support=local_support,
        functional_passed=functional_passed,
        readability_passed=readability_passed,
    )
    _assert_readability_diagnostics(output, passed=readability_passed)
    _assert_no_footer(output)
    assert output.rstrip().splitlines()[-1].startswith("+")
    assert "Readability" in output
    assert "ex003_sequence_modify_variables" in output and "student" in output
    if functional_passed:
        assert "task one failed" not in output
        assert "task two failed" not in output
    else:
        assert "task one failed" in output
        assert "task two failed" in output
    assert "Great work! All exercise cells ran without errors." not in output
    assert "Great work! Everything that can be checked here looks good." not in output
    assert "PYTUTOR_ACTIVE_VARIANT" not in os.environ


def test_readability_row_is_emitted_once_when_task_has_multiple_functional_checks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(True))
    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", _resolve_test_notebook)
    monkeypatch.setattr(notebook_runtime, "run_exercise_checks", _three_functional_results)
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", _one_clean_cell_analysis)

    notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    output = capsys.readouterr().out
    assert output.count("Readability — cell 6") == 1
    for title in ("First functional check", "Second functional check", "Third functional check"):
        assert output.count(title) == 1
    _assert_no_footer(output)


@pytest.mark.parametrize("local_support", [False, True])
def test_readability_tool_error_is_distinct_and_follows_functional_rows(
    local_support: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(local_support))
    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", _resolve_test_notebook)
    monkeypatch.setattr(
        notebook_runtime, "analyze_notebook", _raise_readability_tool_error, raising=False
    )
    monkeypatch.setattr(notebook_runtime, "run_exercise_checks", _local_results(True))
    monkeypatch.setattr(notebook_runtime, "_collect_exercise_tags", _collect_two_tags)
    monkeypatch.setattr(notebook_runtime, "_run_notebook_checks", _successful_fallback_results)

    with pytest.raises(readability.ReadabilityToolError, match="Ruff unavailable in test"):
        notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    output = capsys.readouterr().out
    assert output.index("🟢 OK") < output.index("ERROR")
    assert "Readability tool error" in output or "Ruff" in output
    _assert_no_footer(output)
    assert "Overall self-check: PASS" not in output
    assert "Readability: FAIL" not in output
    assert "Great work! Everything that can be checked here looks good." not in output
    assert "Great work! All exercise cells ran without errors." not in output
    assert "PYTUTOR_ACTIVE_VARIANT" not in os.environ


def _raise_readability_tool_error(_path: Path) -> readability.NotebookAnalysis:
    raise readability.ReadabilityToolError("Ruff unavailable in test")


def _resolve_test_notebook(_key: str, *, variant: str) -> Path:
    assert variant in {"student", "solution"}
    return Path("exercise.ipynb")


@pytest.mark.parametrize("local_support", [False, True])
@pytest.mark.parametrize("variant", ["student", "solution"])
def test_active_variant_resolves_same_path_for_execution_and_analysis(
    local_support: bool,
    variant: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", variant)
    notebook_path = Path("exercise.ipynb")
    resolutions: list[str] = []
    analyzed: list[Path] = []
    executed: list[str] = []

    def resolve(_exercise_key: str, *, variant: str) -> Path:
        resolutions.append(variant)
        return notebook_path

    def analyze(path: Path) -> readability.NotebookAnalysis:
        analyzed.append(path)
        return _readability_result(True)

    def run_functional(_exercise_key: str) -> list[ExerciseCheckResult]:
        executed.append(os.environ["PYTUTOR_ACTIVE_VARIANT"])
        return _functional_result(True)

    def run_fallback(path: Path, _tags: list[str]) -> list[notebook_runtime.NotebookTagCheckResult]:
        assert path == notebook_path
        executed.append(os.environ["PYTUTOR_ACTIVE_VARIANT"])
        return [notebook_runtime.NotebookTagCheckResult("exercise1", True, "")]

    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(local_support))
    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", resolve)
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", analyze, raising=False)
    monkeypatch.setattr(notebook_runtime, "run_exercise_checks", run_functional)
    monkeypatch.setattr(notebook_runtime, "_collect_exercise_tags", _collect_one_tag)
    monkeypatch.setattr(notebook_runtime, "_run_notebook_checks", run_fallback)

    notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    assert resolutions == [variant]
    assert analyzed == [notebook_path]
    assert executed == [variant]
    assert os.environ["PYTUTOR_ACTIVE_VARIANT"] == variant


def test_fallback_rejects_invalid_variant_and_restores_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "invalid")
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(False))

    with pytest.raises(RuntimeError):
        notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    assert os.environ["PYTUTOR_ACTIVE_VARIANT"] == "invalid"


@pytest.mark.parametrize("input_calls", [0, 1])
def test_fallback_execution_and_source_inspection_receive_active_solution_variant(
    input_calls: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook_path = Path("exercise.ipynb")
    captured: list[tuple[str, Path, str]] = []
    analyzed_paths: list[Path] = []
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")

    def extract(path: str | Path, *, tag: str, variant: str) -> str:
        captured.append((f"extract:{variant}", Path(path), tag))
        return "input()\n" if input_calls else "print('done')\n"

    def run_static(path: str | Path, *, tag: str, variant: str) -> str:
        captured.append((f"static:{variant}", Path(path), tag))
        return "done"

    def run_interactive(path: str | Path, *, tag: str, inputs: list[str], variant: str) -> str:
        assert inputs == ["2"]
        captured.append((f"interactive:{variant}", Path(path), tag))
        return "done"

    def analyze(path: Path) -> readability.NotebookAnalysis:
        analyzed_paths.append(path)
        return _readability_result(True)

    monkeypatch.setattr(notebook_runtime, "extract_tagged_code", extract)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", run_interactive)
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(False))
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", analyze, raising=False)

    resolutions: list[tuple[str, str]] = []

    def resolve(exercise_key: str, *, variant: str) -> Path:
        resolutions.append((exercise_key, variant))
        return notebook_path

    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", resolve)
    monkeypatch.setattr(notebook_runtime, "_collect_exercise_tags", _collect_one_tag)

    notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    expected_execution = "interactive:solution" if input_calls else "static:solution"
    assert resolutions == [("ex003_sequence_modify_variables", "solution")]
    assert analyzed_paths == [notebook_path]
    assert all(path == notebook_path and tag == "exercise1" for _, path, tag in captured)
    assert ("extract:solution", notebook_path, "exercise1") in captured
    assert (expected_execution, notebook_path, "exercise1") in captured


def test_functional_only_run_exercise_checks_does_not_launch_ruff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbid_ruff(*_args: object, **_kwargs: object) -> None:
        calls.append("ruff")
        raise AssertionError("functional-only check launched Ruff")

    monkeypatch.setattr(readability.subprocess, "run", forbid_ruff)

    results = checks.run_exercise_checks("ex002_sequence_modify_basics")

    assert len(results) == _FUNCTIONAL_CHECK_COUNT
    assert calls == []


@pytest.mark.parametrize("local_support", [False, True])
def test_syntax_blocked_cell_is_not_checked_without_cascading_diagnostics(
    local_support: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    syntax_analysis = readability.NotebookAnalysis(
        cells=(
            readability.CellAnalysis(
                source="if True \n",
                cell_index=3,
                task_tag="exercise1",
                findings=(
                    readability.Finding("invalid-syntax", 1, 8, "Expected ':'"),
                    readability.Finding("W291", 1, 8, "Trailing whitespace in blocked cell"),
                ),
                syntax_blocked=True,
            ),
            readability.CellAnalysis(
                source="value=1\n",
                cell_index=6,
                task_tag="exercise2",
                findings=(readability.Finding("E225", 1, 6, "Missing whitespace"),),
                syntax_blocked=False,
            ),
        )
    )
    _set_fallback_dispatch(monkeypatch, analysis=syntax_analysis)
    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(local_support))
    monkeypatch.setattr(notebook_runtime, "run_exercise_checks", _local_results(False))
    monkeypatch.setattr(notebook_runtime, "_run_notebook_checks", _fallback_results(False))

    notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")

    output = capsys.readouterr().out
    assert "cell 4" in output and "cell 7" in output
    blocked_row = next(line for line in output.splitlines() if "cell 4" in line)
    assert "⚪ NOT CHECKED" in blocked_row
    assert "Not checked - make sure your code runs first" in blocked_row
    assert "🟢 OK" not in blocked_row and "🔴 NO" not in blocked_row
    assert "invalid-syntax" not in output and "Expected ':'" not in output
    assert "W291" not in output and "Trailing whitespace in blocked cell" not in output
    assert "E225" in output
    assert "task one failed" in output and "task two failed" in output
    _assert_no_footer(output)


def test_saved_notebook_edits_are_reanalysed_without_footer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
    notebook_path = tmp_path / "exercises/sequence/ex003/notebooks/student.ipynb"
    notebook_path.parent.mkdir(parents=True)
    notebook_path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {"tags": ["exercise1"]},
                        "source": "value=1\n",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    resolved_paths: list[Path] = []
    analyzed_paths: list[Path] = []

    def resolve(_exercise_key: str, *, variant: str) -> Path:
        assert variant == "student"
        resolved_paths.append(notebook_path)
        return notebook_path

    def analyze(path: Path) -> readability.NotebookAnalysis:
        analyzed_paths.append(path)
        return readability.analyze_notebook(path)

    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(False))
    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", resolve)
    monkeypatch.setattr(notebook_runtime, "_run_notebook_checks", _one_successful_fallback_result)
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", analyze, raising=False)
    monkeypatch.chdir(tmp_path)

    first_result = notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")
    first_output = capsys.readouterr().out
    notebook_path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {"tags": ["exercise1"]},
                        "source": "value = 1\n",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    second_result = notebook_runtime.run_notebook_checks("ex003_sequence_modify_variables")
    second_output = capsys.readouterr().out

    assert first_result is None and second_result is None
    assert resolved_paths == [notebook_path, notebook_path]
    assert analyzed_paths == [notebook_path, notebook_path]
    assert "E225" in first_output and "🔴 NO" in first_output
    assert "E225" not in second_output and "🔴 NO" not in second_output
    assert "No selected readability issues found" in second_output
    _assert_no_footer(first_output)
    _assert_no_footer(second_output)


def _set_fallback_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    *,
    analysis: readability.NotebookAnalysis,
) -> None:
    notebook_path = Path("exercise.ipynb")

    def resolve(_key: str, *, variant: str) -> Path:
        assert variant == os.environ.get("PYTUTOR_ACTIVE_VARIANT", "student")
        return notebook_path

    def analyze(_path: Path) -> readability.NotebookAnalysis:
        return analysis

    monkeypatch.setattr(notebook_runtime, "has_exercise_checks", _has_local_checks(False))
    monkeypatch.setattr(notebook_runtime, "resolve_notebook_path", resolve)
    monkeypatch.setattr(notebook_runtime, "_collect_exercise_tags", _collect_two_tags)
    monkeypatch.setattr(notebook_runtime, "_run_notebook_checks", _successful_fallback_results)
    monkeypatch.setattr(notebook_runtime, "analyze_notebook", analyze, raising=False)


def _successful_fallback_results(
    _path: Path, _tags: list[str]
) -> list[notebook_runtime.NotebookTagCheckResult]:
    return [
        notebook_runtime.NotebookTagCheckResult("exercise1", True, ""),
        notebook_runtime.NotebookTagCheckResult("exercise2", True, ""),
    ]


def _one_successful_fallback_result(
    _path: Path, _tags: list[str]
) -> list[notebook_runtime.NotebookTagCheckResult]:
    return [notebook_runtime.NotebookTagCheckResult("exercise1", True, "")]


@pytest.mark.parametrize(
    ("construct", "exercise_key"),
    [
        ("sequence", "ex002_sequence_modify_basics"),
        ("selection", "ex001_selection_modify_basics"),
    ],
)
@pytest.mark.parametrize("variant", ["student", "solution"])
def test_real_canonical_sequence_and_selection_self_checks_keep_functional_outcomes(
    construct: str,
    exercise_key: str,
    variant: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", variant)
    expected_check_count = 30 if exercise_key == "ex002_sequence_modify_basics" else 10
    functional_results = checks.run_exercise_checks(exercise_key)

    assert len(functional_results) == expected_check_count
    assert all(result.passed for result in functional_results) is (variant == "solution")

    notebook_runtime.run_notebook_checks(exercise_key)

    output = capsys.readouterr().out
    assert exercise_key in output
    assert variant in output
    assert "Readability" in output
    functional_rows = [
        line
        for line in output.splitlines()
        if line.startswith("| Exercise")
        and line.split("|")[1].strip() != "Exercise"
        and "Readability" not in line
    ]
    assert len(functional_rows) == expected_check_count
    assert all("🟢 OK" in line for line in functional_rows) is (variant == "solution")
    assert sum("🟢 OK" in line for line in functional_rows) == sum(
        result.passed for result in functional_results
    )
    _assert_no_footer(output)
    assert construct in exercise_key


def test_real_solution_readability_backlog_keeps_failed_readability_rows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")
    functional_results = checks.run_exercise_checks("ex015_sequence_make_consolidation_v2")

    assert len(functional_results) == _SOLUTION_BACKLOG_FUNCTIONAL_COUNT
    assert all(result.passed for result in functional_results)

    notebook_runtime.run_notebook_checks("ex015_sequence_make_consolidation_v2")

    output = capsys.readouterr().out
    assert "Readability" in output
    assert "🔴 NO" in output
    assert "E501" in output
    readability_rows = [line for line in output.splitlines() if "Readability — cell" in line]
    assert len(readability_rows) == _SOLUTION_BACKLOG_FUNCTIONAL_COUNT
    assert sum("🔴 NO" in line for line in readability_rows) == 1
    functional_rows = [
        line
        for line in output.splitlines()
        if line.startswith("| Exercise")
        and line.split("|")[1].strip() != "Exercise"
        and "Readability" not in line
    ]
    assert len(functional_rows) == _SOLUTION_BACKLOG_FUNCTIONAL_COUNT
    assert all("🟢 OK" in line for line in functional_rows)
    _assert_no_footer(output)


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
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
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

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    # pyright: ignore[reportPrivateUsage]
    notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert attempt_lengths == [1, 2]


def test_run_tagged_cell_propagates_real_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)

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

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)

    with pytest.raises(NotebookGradingError, match="Execution failed"):
        # pyright: ignore[reportPrivateUsage]
        notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")


def test_run_tagged_cell_stops_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTUTOR_ACTIVE_VARIANT", raising=False)
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

    monkeypatch.setattr(notebook_runtime, "_count_input_calls", fake_count_input_calls)
    monkeypatch.setattr(notebook_runtime, "run_cell_and_capture_output", fake_run_static)
    monkeypatch.setattr(notebook_runtime, "run_cell_with_input", fake_run_with_input)
    monkeypatch.setattr(notebook_runtime, "_MAX_AUTOMATED_INPUTS", limit)

    with pytest.raises(NotebookGradingError):
        # pyright: ignore[reportPrivateUsage]
        notebook_runtime._run_tagged_cell("dummy_exercise", "exercise1")

    assert attempts == limit


def _raise_missing_input_error() -> None:
    try:
        raise RuntimeError("Test expected more input values")
    except RuntimeError as exc:
        raise NotebookGradingError("Execution failed for missing input") from exc
