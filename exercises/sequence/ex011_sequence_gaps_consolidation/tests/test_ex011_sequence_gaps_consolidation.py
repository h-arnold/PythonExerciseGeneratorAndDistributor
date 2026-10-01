from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.execution_variant import ACTIVE_VARIANT_ENV_VAR
from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.student_checker.checks import run_exercise_checks
from exercise_runtime_support.student_checker.checks.base import exercise_tag

EXERCISE_KEY = "ex011_sequence_gaps_consolidation"
NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
CACHE = RuntimeCache()

ex011 = load_exercise_test_module(EXERCISE_KEY, "expectations")

NO_INPUT_CASES = [
    (exercise_tag(exercise_no), ex011.EX011_EXPECTED_STATIC_OUTPUTS[exercise_no])
    for exercise_no in sorted(ex011.EX011_EXPECTED_STATIC_OUTPUTS)
]

INPUT_CASES = [
    (
        exercise_tag(exercise_no),
        ex011.EX011_INPUT_CASES[exercise_no]["inputs"],
        ex011.EX011_INPUT_CASES[exercise_no]["expected_output"],
    )
    for exercise_no in sorted(ex011.EX011_INPUT_CASES)
]


@pytest.mark.parametrize(("tag", "expected"), NO_INPUT_CASES)
def test_no_input_cells(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag, cache=CACHE)
    assert output.strip() == expected


@pytest.mark.parametrize(("tag", "inputs", "expected"), INPUT_CASES)
def test_input_cells(tag: str, inputs: list[str], expected: str) -> None:
    output = run_cell_with_input(
        NOTEBOOK_PATH, tag=tag, inputs=inputs, cache=CACHE)
    assert output.strip() == expected


def test_exercise7_uses_an_f_string() -> None:
    code = extract_tagged_code(NOTEBOOK_PATH, tag="exercise7", cache=CACHE)
    tree = ast.parse(code)
    has_f_string = any(isinstance(node, ast.JoinedStr)
                       for node in ast.walk(tree))
    assert has_f_string, "exercise7 must use an f-string"


def test_self_checks_follow_the_active_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checker checks must read the notebook the runtime resolver selects.

    Regression test: student_checker_support.py once forced
    ``variant="student"``, so solution self-checks reported failures for a
    correct solution notebook.
    """
    monkeypatch.setenv(ACTIVE_VARIANT_ENV_VAR, "solution")
    results = run_exercise_checks(EXERCISE_KEY)
    assert results, "student_checker_support.py must define at least one check"
    failures = [
        f"exercise {result.exercise_no} ({result.title}): "
        f"{', '.join(result.issues)}"
        for result in results
        if not result.passed
    ]
    assert not failures, "self-checks failed:\n" + "\n".join(failures)
