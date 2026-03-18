from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import pytest

from exercise_runtime_support import notebook_grader
from exercise_runtime_support.execution_variant import Variant
from tests.exercise_framework import runtime

EX002_EXERCISE_KEY = "ex002_sequence_modify_basics"
EX007_EXERCISE_KEY = "ex007_sequence_debug_casting"
EXERCISE1_TAG = "exercise1"
EXPECTED_CALL_COUNT_FOR_DISTINCT_INPUTS = 2


class InputRunner(Protocol):
    def __call__(
        self,
        notebook_path: str | Path,
        *,
        tag: str,
        inputs: list[str],
        variant: Variant | None = None,
    ) -> str: ...


def _make_fake_input_runner() -> tuple[InputRunner, Callable[[], int]]:
    call_count = 0

    def fake_run_cell_with_input(
        notebook_path: str | Path,
        *,
        tag: str,
        inputs: list[str],
        variant: Variant | None = None,
    ) -> str:
        nonlocal call_count
        call_count += 1
        return f"{notebook_path}:{tag}:{'|'.join(inputs)}"

    def get_call_count() -> int:
        return call_count

    return fake_run_cell_with_input, get_call_count


def test_runtime_output_helper_matches_notebook_grader() -> None:
    from_runtime = runtime.run_cell_and_capture_output(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        variant="solution",
    )
    from_grader = notebook_grader.run_cell_and_capture_output(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        variant="solution",
    )

    assert from_runtime == from_grader


def test_runtime_extract_helper_matches_notebook_grader() -> None:
    from_runtime = runtime.extract_tagged_code(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        variant="solution",
    )
    from_grader = notebook_grader.extract_tagged_code(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        variant="solution",
    )

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


def test_runtime_rejects_path_like_string_inputs() -> None:
    notebook_path = "notebooks/ex002_sequence_modify_basics.ipynb"
    expected_message = (
        "resolver input must be an exercise_key, not a path-like string: "
        f"{notebook_path!r}. Path-like inputs are not supported."
    )

    with pytest.raises(LookupError) as runtime_exc:
        runtime.extract_tagged_code(
            notebook_path,
            tag=EXERCISE1_TAG,
            variant="solution",
        )

    with pytest.raises(LookupError) as grader_exc:
        notebook_grader.extract_tagged_code(
            notebook_path,
            tag=EXERCISE1_TAG,
            variant="solution",
        )

    assert str(runtime_exc.value) == expected_message
    assert str(grader_exc.value) == expected_message


def test_runtime_output_cache_reuses_result_for_same_path_and_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = runtime.RuntimeCache()
    call_count = 0

    def fake_run_cell_and_capture_output(
        notebook_path: str | Path,
        *,
        tag: str,
        variant: Variant | None = None,
    ) -> str:
        nonlocal call_count
        call_count += 1
        return f"{notebook_path}:{tag}"

    monkeypatch.setattr(
        notebook_grader, "run_cell_and_capture_output", fake_run_cell_and_capture_output
    )

    first = runtime.run_cell_and_capture_output(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        cache=cache,
        variant="solution",
    )
    second = runtime.run_cell_and_capture_output(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        cache=cache,
        variant="solution",
    )

    assert first == second
    assert call_count == 1


def test_runtime_input_cache_reuses_result_for_same_input_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = runtime.RuntimeCache()
    fake_runner, get_call_count = _make_fake_input_runner()

    monkeypatch.setattr(notebook_grader, "run_cell_with_input", fake_runner)

    first = runtime.run_cell_with_input(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
        variant="solution",
    )
    second = runtime.run_cell_with_input(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
        variant="solution",
    )

    assert first == second
    assert get_call_count() == 1


def test_runtime_input_cache_uses_separate_entry_for_different_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = runtime.RuntimeCache()
    fake_runner, get_call_count = _make_fake_input_runner()

    monkeypatch.setattr(notebook_grader, "run_cell_with_input", fake_runner)

    first = runtime.run_cell_with_input(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        inputs=["Alice"],
        cache=cache,
        variant="solution",
    )
    second = runtime.run_cell_with_input(
        EX002_EXERCISE_KEY,
        tag=EXERCISE1_TAG,
        inputs=["Bob"],
        cache=cache,
        variant="solution",
    )

    assert first != second
    assert get_call_count() == EXPECTED_CALL_COUNT_FOR_DISTINCT_INPUTS


def test_runtime_solution_variant_resolves_migrated_exercise_key() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    expected = (
        repo_root
        / "exercises"
        / "sequence"
        / EX007_EXERCISE_KEY
        / "notebooks"
        / "solution.ipynb"
    )

    from_runtime = runtime.resolve_notebook_path(
        EX007_EXERCISE_KEY, variant="solution")
    from_grader = notebook_grader.resolve_notebook_path(
        EX007_EXERCISE_KEY, variant="solution")

    assert from_runtime == from_grader == expected
    assert from_runtime.exists()
