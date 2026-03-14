"""Definitive consumer matrix for the shared runtime execution contract.

This module is the source of truth for which repository surfaces consume
runtime helpers, which entry points they currently use, and which canonical
entry points they target.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


@dataclass(frozen=True)
class ConsumerMatrixEntry:
    """Describe one runtime consumer surface and its entry-point contract."""

    surface: str
    files: tuple[Path, ...]
    current_entry_point: str
    target_entry_point: str


CONSUMER_MATRIX: Final[tuple[ConsumerMatrixEntry, ...]] = (
    ConsumerMatrixEntry(
        surface="runtime/grading wrapper",
        files=(Path("tests/notebook_grader.py"),),
        current_entry_point="tests.notebook_grader wrapper",
        target_entry_point="exercise_runtime_support.notebook_grader",
    ),
    ConsumerMatrixEntry(
        surface="framework and student-checker APIs",
        files=(
            Path("tests/exercise_framework/runtime.py"),
            Path("tests/student_checker/notebook_runtime.py"),
        ),
        current_entry_point="tests.* compatibility wrappers",
        target_entry_point="exercise_runtime_support.exercise_framework.* and exercise_runtime_support.student_checker.*",
    ),
    ConsumerMatrixEntry(
        surface="packager and collector CLI",
        files=(
            Path("scripts/template_repo_cli/core/collector.py"),
            Path("scripts/template_repo_cli/core/packager.py"),
        ),
        current_entry_point="scripts/template_repo_cli/core/* imports and packaging surfaces",
        target_entry_point="exercise_runtime_support package copied and referenced",
    ),
    ConsumerMatrixEntry(
        surface="exercise scaffolder",
        files=(Path("scripts/new_exercise.py"),),
        current_entry_point="emitted import from exercise_runtime_support.exercise_framework.runtime",
        target_entry_point="emitted import from exercise_runtime_support.exercise_framework.runtime",
    ),
    ConsumerMatrixEntry(
        surface="repository workflows",
        files=(
            Path(".github/workflows/tests.yml"),
            Path(".github/workflows/tests-solutions.yml"),
        ),
        current_entry_point="scripts/run_pytest_variant.py --variant solution",
        target_entry_point="scripts/run_pytest_variant.py --variant solution",
    ),
    ConsumerMatrixEntry(
        surface="classroom template workflow",
        files=(Path("template_repo_files/.github/workflows/classroom.yml"),),
        current_entry_point="scripts/build_autograde_payload.py --variant student",
        target_entry_point="scripts/build_autograde_payload.py --variant student",
    ),
    ConsumerMatrixEntry(
        surface="contributor documentation",
        files=(
            Path("docs/testing-framework.md"),
            Path("docs/exercise-generation-cli.md"),
            Path("docs/execution-model.md"),
        ),
        current_entry_point="legacy and transition guidance scattered across docs",
        target_entry_point="single contract documented in docs/execution-model.md",
    ),
)
