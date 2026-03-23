"""Generic expectation helpers for exercise checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import ModuleType
from typing import Any

from exercise_runtime_support.exercise_catalogue import get_catalogue_key_for_exercise_id
from exercise_runtime_support.exercise_test_support import load_exercise_test_module


def expected_output_lines(
    exercise_no: int,
    *,
    single_line: Mapping[int, str],
    multi_line: Mapping[int, Sequence[str]],
) -> list[str] | None:
    """Return expected output lines for an exercise, or None when missing."""
    if exercise_no in single_line:
        return [single_line[exercise_no]]
    if exercise_no in multi_line:
        return list(multi_line[exercise_no])
    return None


def expected_output_text(
    exercise_no: int,
    *,
    single_line: Mapping[int, str],
    multi_line: Mapping[int, Sequence[str]],
) -> str | None:
    """Return expected output text with trailing newline, or None when missing."""
    lines = expected_output_lines(
        exercise_no,
        single_line=single_line,
        multi_line=multi_line,
    )
    if lines is None:
        return None
    return "\n".join(lines) + "\n"


def expected_print_call_count(
    exercise_no: int,
    *,
    expectations: Mapping[int, int],
) -> int | None:
    """Return expected print-call count, or None when not defined."""
    return expectations.get(exercise_no)


_ex002_support_module: ModuleType | None = None
EX002_CHECKS: Any
Ex002CheckDefinition: Any


def _load_ex002_support() -> ModuleType:
    global _ex002_support_module
    if _ex002_support_module is None:
        _ex002_support_module = load_exercise_test_module(
            get_catalogue_key_for_exercise_id(2),
            "framework_support",
        )
    return _ex002_support_module


def get_ex002_checks() -> list[Any]:
    """Return the detailed ex002 check definitions from exercise-local support."""
    return list(_load_ex002_support().EX002_CHECKS)


def __getattr__(name: str) -> Any:
    if name in {"EX002_CHECKS", "Ex002CheckDefinition"}:
        value = getattr(_load_ex002_support(), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EX002_CHECKS",
    "Ex002CheckDefinition",
    "expected_output_lines",
    "expected_output_text",
    "expected_print_call_count",
    "get_ex002_checks",
]
