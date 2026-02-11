from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import pytest

from tests import notebook_grader
from tests.exercise_framework import runtime

EX002_NOTEBOOK_PATH = "notebooks/ex002_sequence_modify_basics.ipynb"
EXERCISE1_TAG = "exercise1"
EXPECTED_CALL_COUNT_FOR_DISTINCT_INPUTS = 2


class InputRunner(Protocol):
    def __call__(self, notebook_path: str | Path, *, tag: str, inputs: list[str]) -> str: ...


def _make_fake_input_runner() -> tuple[InputRunner, Callable[[], int]]:
    call_count = 0

    def fake_run_cell_with_input(notebook_path: str | Path, *, tag: str, inputs: list[str]) -> str:
        nonlocal call_count
        call_count += 1
        return f"{notebook_path}:{tag}:{'|'.join(inputs)}"

    def get_call_count() -> int:
        return call_count

    return fake_run_cell_with_input, get_call_count


def test_runtime_output_helper_matches_notebook_grader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    from_runtime = runtime.run_cell_and_capture_output(EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG)
    from_grader = notebook_grader.run_cell_and_capture_output(
        EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG
    )

    assert from_runtime == from_grader


def test_runtime_extract_helper_matches_notebook_grader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    from_runtime = runtime.extract_tagged_code(EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG)
    from_grader = notebook_grader.extract_tagged_code(EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG)

    assert from_runtime == from_grader


def test_runtime_reports_missing_tag_with_same_error_message(tmp_path: Path) -> None:
    notebook_path = tmp_path / "minimal.ipynb"
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {"tags": ["different_tag"]},
                "source": ["print('hello')"],
            }
        ]
    }
    notebook_path.write_text(json.dumps(notebook), encoding="utf-8")

    with pytest.raises(notebook_grader.NotebookGradingError) as runtime_exc:
        runtime.extract_tagged_code(notebook_path, tag="exercise1")

    with pytest.raises(notebook_grader.NotebookGradingError) as grader_exc:
        notebook_grader.extract_tagged_code(notebook_path, tag="exercise1")

    assert str(runtime_exc.value) == str(grader_exc.value)


def test_runtime_output_cache_reuses_result_for_same_path_and_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    cache = runtime.RuntimeCache()
    call_count = 0

    def fake_run_cell_and_capture_output(notebook_path: str | Path, *, tag: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"{notebook_path}:{tag}"

    monkeypatch.setattr(
        notebook_grader, "run_cell_and_capture_output", fake_run_cell_and_capture_output
    )

    first = runtime.run_cell_and_capture_output(EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG, cache=cache)
    second = runtime.run_cell_and_capture_output(
        EX002_NOTEBOOK_PATH, tag=EXERCISE1_TAG, cache=cache
    )

    assert first == second
    assert call_count == 1


def test_runtime_input_cache_reuses_result_for_same_input_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    cache = runtime.RuntimeCache()
    fake_runner, get_call_count = _make_fake_input_runner()

    monkeypatch.setattr(notebook_grader, "run_cell_with_input", fake_runner)

    first = runtime.run_cell_with_input(
        EX002_NOTEBOOK_PATH,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
    )
    second = runtime.run_cell_with_input(
        EX002_NOTEBOOK_PATH,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
    )

    assert first == second
    assert get_call_count() == 1


def test_runtime_input_cache_uses_separate_entry_for_different_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTUTOR_NOTEBOOKS_DIR", "notebooks/solutions")

    cache = runtime.RuntimeCache()
    fake_runner, get_call_count = _make_fake_input_runner()

    monkeypatch.setattr(notebook_grader, "run_cell_with_input", fake_runner)

    first = runtime.run_cell_with_input(
        EX002_NOTEBOOK_PATH,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
    )
    second = runtime.run_cell_with_input(
        EX002_NOTEBOOK_PATH,
        tag=EXERCISE1_TAG,
        inputs=["Bob"],
        cache=cache,
    )

    assert first != second
    assert get_call_count() == EXPECTED_CALL_COUNT_FOR_DISTINCT_INPUTS
