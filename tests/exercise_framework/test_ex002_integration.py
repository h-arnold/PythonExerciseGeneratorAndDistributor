"""Integration tests for canonical ex002 task metadata."""

from __future__ import annotations

import importlib.util
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType

from exercise_runtime_support.exercise_framework.fixtures import TaskMark
from tests.exercise_framework.expectations import EX002_CHECKS

pytest_plugins = ("tests.exercise_framework.fixtures",)

_CANONICAL_EX002_TEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py"
)


def _expected_task_names() -> set[str]:
    return {f"Exercise {check.exercise_no}: {check.title}" for check in EX002_CHECKS}


def _load_module(module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        module_name, _CANONICAL_EX002_TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Could not load ex002 test module from {_CANONICAL_EX002_TEST_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ex002_task_marker_distribution_matches_expectations(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
    task_distribution_builder: Callable[[Iterable[TaskMark]], Counter[int]],
) -> None:
    canonical_module = _load_module("repo_ex002_canonical_tests")

    canonical_marks: list[TaskMark] = task_marker_collector(canonical_module)

    expected_distribution: Counter[int] = Counter(
        check.exercise_no for check in EX002_CHECKS)

    canonical_distribution: Counter[int] = task_distribution_builder(
        canonical_marks)

    assert canonical_distribution == expected_distribution


def test_ex002_framework_task_names_are_deterministic(
    task_marker_collector: Callable[[ModuleType], list[TaskMark]],
) -> None:
    canonical_module = _load_module("repo_ex002_canonical_tests_for_names")
    framework_marks = task_marker_collector(canonical_module)
    framework_names: set[str] = set()
    for mark in framework_marks:
        name = mark.kwargs.get("name")
        if isinstance(name, str):
            framework_names.add(name)

    assert framework_names == _expected_task_names()
