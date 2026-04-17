"""Exercise testing framework public surface."""

from __future__ import annotations

from typing import Any

from . import expectations as _expectations
from .expectations import expected_output_lines, expected_output_text, expected_print_call_count
from .paths import resolve_exercise_notebook_path, resolve_notebook_path
from .runtime import (
    RuntimeCache,
    exec_tagged_code,
    extract_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

__all__ = [
    "EX002_CHECKS",
    "Ex002CheckDefinition",
    "ExerciseCheckResult",
    "NotebookCheckResult",
    "RuntimeCache",
    "exec_tagged_code",
    "expected_output_lines",
    "expected_output_text",
    "expected_print_call_count",
    "extract_tagged_code",
    "get_explanation_cell",
    "resolve_exercise_notebook_path",
    "resolve_notebook_path",
    "run_all_checks",
    "run_cell_and_capture_output",
    "run_cell_with_input",
    "run_detailed_ex002_check",
    "run_notebook_check",
]


def __getattr__(name: str) -> Any:
    if name in {"EX002_CHECKS", "Ex002CheckDefinition"}:
        value = getattr(_expectations, name)
        globals()[name] = value
        return value
    if name in {
        "ExerciseCheckResult",
        "NotebookCheckResult",
        "run_all_checks",
        "run_detailed_ex002_check",
        "run_notebook_check",
    }:
        from . import api as _api

        value = getattr(_api, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
