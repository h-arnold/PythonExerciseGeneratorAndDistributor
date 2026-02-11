from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import pytest

import tests.student_checker.checks as student_checks

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
    ("attr_name", "def_cls", "runner_name"),
    [
        ("_EX003_CHECKS", student_checks.ExerciseCheckDefinition, "run_ex003_checks"),
        ("_EX004_CHECKS", student_checks.ExerciseCheckDefinition, "run_ex004_checks"),
        ("_EX005_CHECKS", student_checks.ExerciseCheckDefinition, "run_ex005_checks"),
        ("_EX006_CHECKS", student_checks.Ex006CheckDefinition, "run_ex006_checks"),
        ("_EX007_CHECKS", student_checks.ExerciseCheckDefinition, "run_ex007_checks"),
    ],
)
def test_private_alias_assignment_updates_submodule_checks(
    monkeypatch: pytest.MonkeyPatch,
    attr_name: str,
    def_cls: Callable[..., CheckDef],
    runner_name: str,
) -> None:
    sentinel_title = f"Sentinel {attr_name}"
    sentinel_no = 999
    sentinel_checks = [_make_check(def_cls, sentinel_no, sentinel_title)]

    monkeypatch.setattr(student_checks, attr_name, sentinel_checks)

    run_checks = getattr(student_checks, runner_name)
    results = run_checks()

    assert [(result.exercise_no, result.title) for result in results] == [
        (sentinel_no, sentinel_title)
    ]
