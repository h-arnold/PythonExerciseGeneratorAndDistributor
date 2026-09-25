from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import is_valid_explanation
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex010_sequence_debug_fstrings"
ex010 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _assert_input_cases(exercise_no: int) -> None:
    cases = ex010.EX010_INPUT_CASES[exercise_no]
    actual = [
        _exercise_output_with_inputs(exercise_no, list(case["inputs"]))
        for case in cases
    ]
    expected = [case["expected_output"] for case in cases]
    assert actual == expected, (
        f"Exercise {exercise_no}: expected exact transcripts {expected!r}, "
        f"got {actual!r}."
    )


def _assert_construct(exercise_no: int) -> None:
    issues = _construct_checks.construct_issues(
        _exercise_ast(exercise_no),
        exercise_no,
    )
    assert not issues, f"Exercise {exercise_no}: {'; '.join(issues)}"


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _exercise_output(1) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_construct(1)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _exercise_output(2) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_construct(2)


@pytest.mark.task(taskno=2)
def test_exercise2_rejects_old_variable_name() -> None:
    assert "animal" not in _construct_checks.name_ids(_exercise_ast(2))


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _exercise_output(3) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_construct(3)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _exercise_output(4) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _assert_construct(4)


@pytest.mark.task(taskno=5)
def test_exercise5_input_flow() -> None:
    _assert_input_cases(5)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_construct(5)


@pytest.mark.task(taskno=6)
def test_exercise6_input_flow() -> None:
    _assert_input_cases(6)


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    _assert_construct(6)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    assert _exercise_output(7) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[7]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    _assert_construct(7)


@pytest.mark.task(taskno=7)
def test_exercise7_uses_plural_text() -> None:
    assert _construct_checks.final_fstring_contains(_exercise_ast(7), "goals")


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    assert _exercise_output(8) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    _assert_construct(8)


@pytest.mark.task(taskno=8)
def test_exercise8_rejects_old_subtraction() -> None:
    assert not _construct_checks.has_operator(_exercise_ast(8), ast.Sub)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _exercise_output(9) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    _assert_construct(9)


@pytest.mark.task(taskno=9)
def test_exercise9_rejects_old_subtraction() -> None:
    assert not _construct_checks.has_operator(_exercise_ast(9), ast.Sub)


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    assert _exercise_output(10) == ex010.EX010_EXPECTED_STATIC_OUTPUTS[10]


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    _assert_construct(10)


@pytest.mark.task(taskno=10)
def test_exercise10_rejects_old_addition() -> None:
    assert not _construct_checks.has_operator(_exercise_ast(10), ast.Add)


@pytest.mark.parametrize(
    "exercise_no",
    [
        pytest.param(exercise_no, marks=pytest.mark.task(taskno=exercise_no))
        for exercise_no in range(1, 11)
    ],
)
def test_explanations_have_content(exercise_no: int) -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH,
        tag=_explanation_tag(exercise_no),
    )
    assert is_valid_explanation(
        explanation,
        min_length=ex010.EX010_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex010.EX010_PLACEHOLDER_PHRASES,
    )
