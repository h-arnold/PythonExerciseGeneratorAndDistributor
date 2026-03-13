"""Compatibility wrapper for :mod:`exercise_runtime_support.exercise_framework.expectations`."""

from __future__ import annotations

from exercise_runtime_support.exercise_framework.expectations import (
    EX002_CHECKS,
    Ex002CheckDefinition,
    expected_output_lines,
    expected_output_text,
    expected_print_call_count,
)

__all__ = [
    "EX002_CHECKS",
    "Ex002CheckDefinition",
    "expected_output_lines",
    "expected_output_text",
    "expected_print_call_count",
]
