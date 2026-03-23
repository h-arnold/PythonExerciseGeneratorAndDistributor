from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import pytest

import exercise_runtime_support.student_checker.checks as student_checks

CheckDef = TypeVar(
    "CheckDef", student_checks.ExerciseCheckDefinition, student_checks.Ex006CheckDefinition
)


def _make_check(def_cls: Callable[..., CheckDef], exercise_no: int, title: str) -> CheckDef:
    def _check() -> list[str]:
        return []

    return def_cls(
        exercise_no=exercise_no,
        title=title,
        check=_check,
    )


@pytest.mark.parametrize(
    ("exercise_id", "def_cls", "runner_name"),
    [
        (3, student_checks.ExerciseCheckDefinition, "run_ex003_checks"),
        (4, student_checks.ExerciseCheckDefinition, "run_ex004_checks"),
        (5, student_checks.ExerciseCheckDefinition, "run_ex005_checks"),
        (6, student_checks.Ex006CheckDefinition, "run_ex006_checks"),
        (7, student_checks.ExerciseCheckDefinition, "run_ex007_checks"),
    ],
)
def test_cached_checks_override_loader(
    monkeypatch: pytest.MonkeyPatch,
    exercise_id: int,
    def_cls: Callable[..., CheckDef],
    runner_name: str,
) -> None:
    sentinel_title = f"Sentinel ex{exercise_id:03d}"
    sentinel_no = 999
    sentinel_checks = [_make_check(def_cls, sentinel_no, sentinel_title)]
    cache: dict[int, list[Any]] = {}

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    cache[exercise_id] = sentinel_checks

    run_checks = getattr(student_checks, runner_name)
    results = run_checks()

    assert [(result.exercise_no, result.title) for result in results] == [
        (sentinel_no, sentinel_title)
    ]


def test_run_ex003_checks_loads_lazily(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel_title = "Sentinel ex003"
    sentinel_no = 303
    sentinel_checks = [
        _make_check(student_checks.ExerciseCheckDefinition,
                    sentinel_no, sentinel_title)
    ]
    cache: dict[int, list[Any]] = {}
    load_calls: list[int] = []

    def fake_load_check_list(exercise_id: int) -> list[Any]:
        load_calls.append(exercise_id)
        return sentinel_checks

    monkeypatch.setattr(student_checks, "_CHECK_CACHE", cache)
    monkeypatch.setattr(student_checks, "_load_check_list", fake_load_check_list)

    first_results = student_checks.run_ex003_checks()
    second_results = student_checks.run_ex003_checks()

    assert load_calls == [3]
    assert [(result.exercise_no, result.title) for result in first_results] == [
        (sentinel_no, sentinel_title)
    ]
    assert [(result.exercise_no, result.title) for result in second_results] == [
        (sentinel_no, sentinel_title)
    ]
    assert len(cache) == 1
    assert cache[3] is sentinel_checks
