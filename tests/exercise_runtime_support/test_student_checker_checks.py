"""Tests for ``exercise_runtime_support.student_checker.checks``."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import pytest

import exercise_runtime_support.student_checker.checks as student_checks
from exercise_runtime_support.student_checker.checks import base as student_check_base
from exercise_runtime_support.execution_variant import (
    ACTIVE_VARIANT_ENV_VAR,
    get_active_variant,
)

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
        ("ex008_sequence_make_consolidation",
         student_checks.ExerciseCheckDefinition),
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
        _make_check(student_checks.ExerciseCheckDefinition,
                    sentinel_no, sentinel_title)
    ]
    cache: dict[str, list[Any]] = {}
    load_calls: list[str] = []

    def fake_load_check_list(requested_exercise_key: str) -> list[Any]:
        load_calls.append(requested_exercise_key)
        return sentinel_checks

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.setattr(student_checks, "_load_check_list",
                        fake_load_check_list)

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

    results = student_checks.run_exercise_checks(
        "ex002_sequence_modify_basics")

    assert len(results) == _EX002_CHECK_RESULT_COUNT
    assert {result.title for result in results} == {
        "Construct", "Formatting", "Logic"}
    assert {result.exercise_no for result in results} == set(range(1, 11))


def test_run_exercise_checks_defaults_to_student_variant_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_variants: list[str] = []
    cache: dict[str, list[Any]] = {}

    def record_variant() -> list[str]:
        observed_variants.append(get_active_variant())
        return []

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.delenv(ACTIVE_VARIANT_ENV_VAR, raising=False)
    cache["variant_probe"] = [
        student_checks.ExerciseCheckDefinition(
            exercise_no=1,
            title="Variant",
            check=record_variant,
        )
    ]

    results = student_checks.run_exercise_checks("variant_probe")

    assert [result.passed for result in results] == [True]
    assert observed_variants == ["student"]
    assert ACTIVE_VARIANT_ENV_VAR not in os.environ


def test_run_exercise_checks_preserves_explicit_solution_variant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_variants: list[str] = []
    cache: dict[str, list[Any]] = {}

    def record_variant() -> list[str]:
        observed_variants.append(get_active_variant())
        return []

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.setenv(ACTIVE_VARIANT_ENV_VAR, "solution")
    cache["variant_probe"] = [
        student_checks.ExerciseCheckDefinition(
            exercise_no=1,
            title="Variant",
            check=record_variant,
        )
    ]

    results = student_checks.run_exercise_checks("variant_probe")

    assert [result.passed for result in results] == [True]
    assert observed_variants == ["solution"]
    assert os.environ[ACTIVE_VARIANT_ENV_VAR] == "solution"


def test_run_exercise_checks_reports_failures_for_unsolved_ex002_without_variant_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache: dict[str, list[Any]] = {}

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.delenv(ACTIVE_VARIANT_ENV_VAR, raising=False)

    results = student_checks.run_exercise_checks(
        "ex002_sequence_modify_basics")

    assert any(not result.passed for result in results)
    assert any(
        "Hello Python!" in issue
        for result in results
        for issue in result.issues
    )


def test_check_explanation_cell_forwards_variant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_get_explanation_cell(
        exercise_key: str,
        *,
        tag: str,
        variant: str | None = None,
    ) -> str:
        captured["exercise_key"] = exercise_key
        captured["tag"] = tag
        captured["variant"] = variant
        return "This explanation is detailed enough to pass the checker."

    monkeypatch.setattr(
        student_check_base,
        "get_explanation_cell",
        fake_get_explanation_cell,
    )

    result = student_check_base.check_explanation_cell(
        "ex007_sequence_debug_casting",
        3,
        10,
        (),
        variant="student",
    )

    assert result == []
    assert captured == {
        "exercise_key": "ex007_sequence_debug_casting",
        "tag": "explanation3",
        "variant": "student",
    }
