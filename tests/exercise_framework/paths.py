"""Compatibility wrapper for :mod:`exercise_runtime_support.exercise_framework.paths`."""

from __future__ import annotations

from exercise_runtime_support.exercise_framework.paths import (
    resolve_exercise_notebook_path,
    resolve_notebook_path,
)

__all__ = ["resolve_exercise_notebook_path", "resolve_notebook_path"]
