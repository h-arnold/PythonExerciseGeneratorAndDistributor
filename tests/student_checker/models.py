"""Dataclasses used by the student checker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class NotebookCheckSpec:
    """Represents a summary check and optional detailed notebook report."""

    label: str
    summary_runner: Callable[[], list[str]]
    detailed_printer: Callable[[], None] | None = None


@dataclass(frozen=True)
class ExerciseCheckResult:
    """Represents a single grouped exercise check result."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]


@dataclass(frozen=True)
class Ex002CheckResult:
    """Represents a single ex002 check result."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]


@dataclass(frozen=True)
class Ex006CheckResult(ExerciseCheckResult):
    """Represents a single ex006 check result."""


@dataclass(frozen=True)
class NotebookTagCheckResult:
    """Represents the status of a tagged exercise cell."""

    tag: str
    passed: bool
    message: str


@dataclass(frozen=True)
class DetailedCheckResult:
    """Represents a single row in a grouped detailed report."""

    exercise_label: str
    check_label: str
    passed: bool
    issues: list[str]
