"""Integration tests for ex002 framework parity during transition."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from types import ModuleType

from tests.exercise_framework.expectations import EX002_CHECKS
from tests.exercise_framework.fixtures import TaskMark

pytest_plugins = ("tests.exercise_framework.fixtures",)


def _expected_task_names() -> set[str]:
    return {f"Exercise {check.exercise_no}: {check.title}" for check in EX002_CHECKS}


def _import_module(path: str) -> ModuleType:
    module = __import__(path, fromlist=["__name__"])
    return module


def test_ex002_task_marker_distribution_parity(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
    task_distribution_builder: Callable[[Iterable[TaskMark]], Counter[int]],
) -> None:
    legacy_module = _import_module("tests.test_ex002_sequence_modify_basics")
    framework_module = _import_module(
        "tests.ex002_sequence_modify_basics.test_ex002_sequence_modify_basics"
    )

    legacy_marks: list[TaskMark] = task_marker_collector(legacy_module)
    framework_marks: list[TaskMark] = task_marker_collector(framework_module)

    expected_distribution: Counter[int] = Counter(check.exercise_no for check in EX002_CHECKS)

    legacy_distribution: Counter[int] = task_distribution_builder(legacy_marks)
    framework_distribution: Counter[int] = task_distribution_builder(framework_marks)

    assert legacy_distribution == expected_distribution
    assert framework_distribution == expected_distribution


def test_ex002_framework_task_names_are_deterministic(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
) -> None:
    framework_module = _import_module(
        "tests.ex002_sequence_modify_basics.test_ex002_sequence_modify_basics"
    )
    framework_marks = task_marker_collector(framework_module)
    framework_names: set[str] = set()
    for mark in framework_marks:
        name = mark.kwargs.get("name")
        if isinstance(name, str):
            framework_names.add(name)

    assert framework_names == _expected_task_names()
