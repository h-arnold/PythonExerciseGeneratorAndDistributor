"""Compatibility wrapper for :mod:`exercise_runtime_support.student_checker.notebook_runtime`."""

from __future__ import annotations

import sys
from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_impl = _import_module("exercise_runtime_support.student_checker.notebook_runtime")

for _name, _value in vars(_impl).items():
    if _name.startswith("__") and _name not in {"__all__", "__doc__"}:
        continue
    globals()[_name] = _value

__all__ = getattr(_impl, "__all__", [name for name in globals() if not name.startswith("_")])


class _CompatibilityModule(ModuleType):
    """Mirror monkeypatched wrapper attributes onto the implementation module."""

    def __getattr__(self, name: str) -> Any:
        return getattr(_impl, name)

    def __setattr__(self, name: str, value: Any) -> None:
        ModuleType.__setattr__(self, name, value)
        setattr(_impl, name, value)


module = sys.modules[__name__]
if not isinstance(module, _CompatibilityModule):
    module.__class__ = _CompatibilityModule
