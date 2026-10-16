from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_KEY = "ex005_sequence_debug_logic"
_ex = load_exercise_test_module(_KEY, "expectations")
_checks = load_exercise_test_module(_KEY, "task_checks")
_CACHE = RuntimeCache()


def _run(n: int, inputs: list[str] | None = None) -> str:
    if inputs is None:
        inputs = _ex.EX005_EXERCISE_INPUTS.get(n)
    if inputs is not None:
        return run_cell_with_input(_KEY, tag=f"exercise{n}", inputs=inputs, cache=_CACHE)
    return run_cell_and_capture_output(_KEY, tag=f"exercise{n}", cache=_CACHE)


@pytest.mark.parametrize(
    "n",
    [pytest.param(n, id=f"exercise{n}", marks=pytest.mark.task(taskno=n)) for n in range(1, 11)],
)
def test_task_completion(n: int) -> None:
    code = extract_tagged_code(_KEY, tag=f"exercise{n}", cache=_CACHE)

    def output(inputs: list[str] | None) -> str:
        return _run(n, inputs)

    errors = _checks.validate_task(n, code, output)
    assert not errors, "; ".join(errors)


@pytest.mark.parametrize(
    "n",
    [pytest.param(n, id=f"exercise{n}", marks=pytest.mark.task(taskno=n)) for n in range(1, 11)],
)
def test_explanation_has_content(n: int) -> None:
    assert is_valid_explanation(
        get_explanation_cell(_KEY, tag=f"explanation{n}"),
        min_length=_ex.EX005_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX005_PLACEHOLDER_PHRASES,
    )
