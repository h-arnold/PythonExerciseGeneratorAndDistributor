"""Integration tests for ex002 framework task metadata."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from types import ModuleType

from tests.exercise_framework.expectations import EX002_CHECKS
from tests.exercise_framework.fixtures import TaskMark

pytest_plugins = ("tests.exercise_framework.fixtures",)


def _import_module(path: str) -> ModuleType:
    module = __import__(path, fromlist=["__name__"])
    return module


def test_ex002_task_marker_distribution_parity(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
    task_distribution_builder: Callable[[Iterable[TaskMark]], Counter[int]],
) -> None:
    notebook_module = _import_module("tests.notebooks.ex002_sequence_modify_basics.test_notebook")
    notebook_marks: list[TaskMark] = task_marker_collector(notebook_module)

    expected_distribution: Counter[int] = Counter(check.exercise_no for check in EX002_CHECKS)
    for exercise_no in range(1, 11):
        expected_distribution[exercise_no] += 1
    notebook_distribution: Counter[int] = task_distribution_builder(notebook_marks)
    assert notebook_distribution == expected_distribution


def test_ex002_framework_task_names_are_deterministic(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
) -> None:
    notebook_module = _import_module("tests.notebooks.ex002_sequence_modify_basics.test_notebook")
    notebook_marks = task_marker_collector(notebook_module)
    assert all(mark.kwargs.get("name") is None for mark in notebook_marks)
