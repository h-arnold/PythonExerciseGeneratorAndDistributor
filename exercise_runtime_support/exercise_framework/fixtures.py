"""Shared fixtures for exercise framework tests."""

from __future__ import annotations

import inspect
from collections import Counter
from collections.abc import Callable, Iterable
from types import ModuleType
from typing import Protocol, TypeGuard, runtime_checkable

import pytest

_MIN_PARAMETRIZE_ARGS = 2
_PARAMETRIZE_ARGVALUES_INDEX = 1


@runtime_checkable
class TaskMark(Protocol):
    """Protocol for pytest task marks."""

    name: str
    kwargs: dict[str, object]


def _is_task_mark(value: object) -> TypeGuard[TaskMark]:
    return isinstance(value, TaskMark)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_object_tuple(value: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(value, tuple)


def _is_object_iterable(value: object) -> TypeGuard[Iterable[object]]:
    if isinstance(value, (str, bytes, dict)):
        return False
    return isinstance(value, Iterable)


def _normalise_marks(value: object) -> list[object]:
    if value is None:
        return []
    if _is_object_list(value):
        return value
    if _is_object_tuple(value):
        return list(value)
    return [value]


@runtime_checkable
class _HasMark(Protocol):
    """Protocol for pytest mark decorators exposing a mark attribute."""

    mark: object


def _unwrap_mark(value: object) -> object:
    if isinstance(value, _HasMark):
        return value.mark
    return value


@runtime_checkable
class _HasNameArgsKwargs(Protocol):
    """Protocol for pytest marks exposing name/args/kwargs."""

    name: str
    args: tuple[object, ...]
    kwargs: dict[str, object]


def _is_mark_with_args(value: object) -> TypeGuard[_HasNameArgsKwargs]:
    return isinstance(value, _HasNameArgsKwargs)


@runtime_checkable
class _HasMarks(Protocol):
    """Protocol for pytest parameter sets exposing marks."""

    marks: Iterable[object]


def _is_marks_container(value: object) -> TypeGuard[_HasMarks]:
    return isinstance(value, _HasMarks)


def _normalise_param_values(values: object) -> list[object]:
    if values is None:
        return []
    if _is_object_list(values):
        return values
    if _is_object_tuple(values):
        return list(values)
    if _is_object_iterable(values):
        return list(values)
    return [values]


def _iter_parametrize_marks(mark_value: object) -> Iterable[TaskMark]:
    if not _is_mark_with_args(mark_value):
        return
    if mark_value.name != "parametrize":
        return

    argvalues = mark_value.kwargs.get("argvalues")
    if argvalues is None and len(mark_value.args) >= _MIN_PARAMETRIZE_ARGS:
        argvalues = mark_value.args[_PARAMETRIZE_ARGVALUES_INDEX]

    for param in _normalise_param_values(argvalues):
        if not _is_marks_container(param):
            continue
        for param_mark in _normalise_marks(param.marks):
            param_mark_value = _unwrap_mark(param_mark)
            if _is_task_mark(param_mark_value) and param_mark_value.name == "task":
                yield param_mark_value


def _iter_test_functions(module: ModuleType) -> Iterable[Callable[..., object]]:
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if func.__module__ != module.__name__:
            continue
        if name.startswith("test_"):
            yield func


def _iter_task_marks(test_func: Callable[..., object]) -> Iterable[TaskMark]:
    marks_obj: object = vars(test_func).get("pytestmark", [])
    for mark in _normalise_marks(marks_obj):
        mark_value = _unwrap_mark(mark)
        if _is_task_mark(mark_value) and mark_value.name == "task":
            yield mark_value
        yield from _iter_parametrize_marks(mark_value)


def collect_task_marks(module: ModuleType) -> list[TaskMark]:
    """Collect task marks from test functions in the given module."""
    marks: list[TaskMark] = []
    for test_func in _iter_test_functions(module):
        marks.extend(_iter_task_marks(test_func))
    return marks


def task_mark_distribution(marks: Iterable[TaskMark]) -> Counter[int]:
    """Return task number counts from task marks."""
    counter: Counter[int] = Counter()
    for mark in marks:
        taskno = getattr(mark, "kwargs", {}).get("taskno")
        if taskno is None:
            continue
        counter[int(taskno)] += 1
    return counter


@pytest.fixture
def task_marker_collector() -> Callable[[ModuleType], list[TaskMark]]:
    """Provide a helper for collecting task marks from a module."""
    return collect_task_marks


@pytest.fixture
def task_distribution_builder() -> Callable[[Iterable[TaskMark]], Counter[int]]:
    """Provide a helper for building task distributions from marks."""
    return task_mark_distribution
