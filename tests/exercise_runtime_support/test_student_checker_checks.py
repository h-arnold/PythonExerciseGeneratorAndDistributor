"""Tests for ``exercise_runtime_support.student_checker.checks``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

import exercise_runtime_support.student_checker.checks as student_checks

_EX002_CHECK_RESULT_COUNT = 30


def _make_check(
    def_cls: Callable[..., student_checks.ExerciseCheckDefinition],
    exercise_no: int,
    title: str,
) -> student_checks.ExerciseCheckDefinition:
    def _check() -> list[str]:
        return []

    return def_cls(
        exercise_no=exercise_no,
        title=title,
        check=_check,
    )


@pytest.mark.parametrize(
    ("exercise_key", "def_cls"),
    [
        ("ex003_sequence_modify_variables", student_checks.ExerciseCheckDefinition),
        ("ex004_sequence_debug_syntax", student_checks.ExerciseCheckDefinition),
        ("ex005_sequence_debug_logic", student_checks.ExerciseCheckDefinition),
        ("ex006_sequence_modify_casting", student_checks.ExerciseCheckDefinition),
        ("ex007_sequence_debug_casting", student_checks.ExerciseCheckDefinition),
    ],
)
def test_cached_checks_override_loader(
    monkeypatch: pytest.MonkeyPatch,
    exercise_key: str,
    def_cls: Callable[..., student_checks.ExerciseCheckDefinition],
) -> None:
    sentinel_title = f"Sentinel {exercise_key}"
    sentinel_no = 999
    sentinel_checks = [_make_check(def_cls, sentinel_no, sentinel_title)]
    cache: dict[str, list[Any]] = {}

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    cache[exercise_key] = sentinel_checks

    results = student_checks.run_exercise_checks(exercise_key)

    assert [(result.exercise_no, result.title) for result in results] == [
        (sentinel_no, sentinel_title)
    ]
    assert isinstance(results[0], student_checks.ExerciseCheckResult)


def test_run_exercise_checks_loads_lazily(monkeypatch: pytest.MonkeyPatch) -> None:
    exercise_key = "ex003_sequence_modify_variables"
    sentinel_title = "Sentinel ex003"
    sentinel_no = 303
    sentinel_checks = [
        _make_check(student_checks.ExerciseCheckDefinition, sentinel_no, sentinel_title)
    ]
    cache: dict[str, list[Any]] = {}
    load_calls: list[str] = []

    def fake_load_check_list(requested_exercise_key: str) -> list[Any]:
        load_calls.append(requested_exercise_key)
        return sentinel_checks

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.setattr(student_checks, "_load_check_list", fake_load_check_list)

    first_results = student_checks.run_exercise_checks(exercise_key)
    second_results = student_checks.run_exercise_checks(exercise_key)

    assert load_calls == [exercise_key]
    assert [(result.exercise_no, result.title) for result in first_results] == [
        (sentinel_no, sentinel_title)
    ]
    assert [(result.exercise_no, result.title) for result in second_results] == [
        (sentinel_no, sentinel_title)
    ]
    assert len(cache) == 1
    assert cache[exercise_key] is sentinel_checks


def test_run_exercise_checks_supports_generic_ex002_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache: dict[str, list[Any]] = {}

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)

    results = student_checks.run_exercise_checks("ex002_sequence_modify_basics")

    assert len(results) == _EX002_CHECK_RESULT_COUNT
    assert {result.title for result in results} == {"Construct", "Formatting", "Logic"}
    assert {result.exercise_no for result in results} == set(range(1, 11))
