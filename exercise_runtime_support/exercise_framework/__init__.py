"""Exercise testing framework public surface."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from types import ModuleType
from typing import Any

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

EX002_CHECKS: Any
Ex002CheckDefinition: type[Any]
ExerciseCheckResult: type[Any]
NotebookCheckResult: type[Any]
RuntimeCache: type[Any]
exec_tagged_code: Callable[..., Any]
expected_output_lines: Callable[..., Any]
expected_output_text: Callable[..., Any]
expected_print_call_count: Callable[..., Any]
extract_tagged_code: Callable[..., Any]
get_explanation_cell: Callable[..., Any]
resolve_exercise_notebook_path: Callable[..., Any]
resolve_notebook_path: Callable[..., Any]
run_all_checks: Callable[..., Any]
run_cell_and_capture_output: Callable[..., Any]
run_cell_with_input: Callable[..., Any]
run_detailed_ex002_check: Callable[..., Any]
run_notebook_check: Callable[..., Any]

_ATTRIBUTE_MODULES: dict[str, str] = {
    "EX002_CHECKS": "exercise_runtime_support.exercise_framework.expectations",
    "Ex002CheckDefinition": "exercise_runtime_support.exercise_framework.expectations",
    "ExerciseCheckResult": "exercise_runtime_support.exercise_framework.api",
    "NotebookCheckResult": "exercise_runtime_support.exercise_framework.api",
    "RuntimeCache": "exercise_runtime_support.exercise_framework.runtime",
    "exec_tagged_code": "exercise_runtime_support.exercise_framework.runtime",
    "expected_output_lines": "exercise_runtime_support.exercise_framework.expectations",
    "expected_output_text": "exercise_runtime_support.exercise_framework.expectations",
    "expected_print_call_count": "exercise_runtime_support.exercise_framework.expectations",
    "extract_tagged_code": "exercise_runtime_support.exercise_framework.runtime",
    "get_explanation_cell": "exercise_runtime_support.exercise_framework.runtime",
    "resolve_exercise_notebook_path": "exercise_runtime_support.exercise_framework.paths",
    "resolve_notebook_path": "exercise_runtime_support.exercise_framework.paths",
    "run_all_checks": "exercise_runtime_support.exercise_framework.api",
    "run_cell_and_capture_output": "exercise_runtime_support.exercise_framework.runtime",
    "run_cell_with_input": "exercise_runtime_support.exercise_framework.runtime",
    "run_detailed_ex002_check": "exercise_runtime_support.exercise_framework.api",
    "run_notebook_check": "exercise_runtime_support.exercise_framework.api",
}

_MODULE_CACHE: dict[str, ModuleType] = {}


def _load_module(module_name: str) -> ModuleType:
    """Return a cached module instance, importing it lazily."""
    module = _MODULE_CACHE.get(module_name)
    if module is None:
        module = import_module(module_name)
        _MODULE_CACHE[module_name] = module
    return module


def __getattr__(name: str) -> Any:
    module_name = _ATTRIBUTE_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = _load_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
