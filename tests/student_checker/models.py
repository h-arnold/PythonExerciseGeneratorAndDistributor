"""Dataclasses used by the student checker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class CheckStatus(StrEnum):
    """Explicit checker status used in student-facing tables."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_STARTED = "NOT STARTED"


def _derive_status(passed: bool, issues: list[str]) -> CheckStatus:
    if passed:
        return CheckStatus.PASSED
    return CheckStatus.FAILED


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
    status: CheckStatus | None = None

    def __post_init__(self) -> None:
        if self.status is None:
            object.__setattr__(self, "status", _derive_status(
                self.passed, self.issues))


@dataclass(frozen=True)
class Ex002CheckResult:
    """Represents a single ex002 check result."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]
    status: CheckStatus | None = None

    def __post_init__(self) -> None:
        if self.status is None:
            object.__setattr__(self, "status", _derive_status(
                self.passed, self.issues))


@dataclass(frozen=True)
class Ex006CheckResult(ExerciseCheckResult):
    """Represents a single ex006 check result."""


@dataclass(frozen=True)
class NotebookTagCheckResult:
    """Represents the status of a tagged exercise cell."""

    tag: str
    passed: bool
    message: str
    status: CheckStatus | None = None

    def __post_init__(self) -> None:
        if self.status is None:
            object.__setattr__(self, "status", _derive_status(
                self.passed, [self.message]))


@dataclass(frozen=True)
class DetailedCheckResult:
    """Represents a single row in a grouped detailed report."""

    exercise_label: str
    check_label: str
    passed: bool
    issues: list[str]
    status: CheckStatus | None = None

    def __post_init__(self) -> None:
        if self.status is None:
            object.__setattr__(self, "status", _derive_status(
                self.passed, self.issues))
