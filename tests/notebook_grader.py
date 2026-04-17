"""Compatibility wrapper for :mod:`exercise_runtime_support.notebook_grader`."""

from importlib import import_module as _import_module

_impl = _import_module("exercise_runtime_support.notebook_grader")

for _name, _value in vars(_impl).items():
    if _name.startswith("__") and _name not in {"__all__", "__doc__"}:
        continue
    globals()[_name] = _value

__all__ = getattr(_impl, "__all__", [name for name in globals() if not name.startswith("_")])
