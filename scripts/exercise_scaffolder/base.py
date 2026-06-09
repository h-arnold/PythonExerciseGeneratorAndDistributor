"""Abstract base class for exercise scaffolding.

Each exercise type (debug, modify, make, gaps) gets its own concrete subclass
that inherits from ``ExerciseScaffold`` and overrides the type-specific hooks.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any


def _make_meta(language: str, *, tags: list[str] | None = None) -> dict[str, Any]:
    """Create cell metadata dictionary with a unique ID."""
    meta: dict[str, object] = {"id": uuid.uuid4().hex[:8], "language": language}
    if tags:
        meta["tags"] = tags
    return meta


class ExerciseScaffold(ABC):
    """Abstract base for exercise-type-specific scaffold classes.

    Shared notebook-cell generation, README, test file, and supporting file
    creation lives here.  Subclasses override type-specific hooks for cell
    structure, test body assertions, and README extras.
    """

    def __init__(
        self,
        title: str,
        exercise_key: str,
        parts: int,
        test_target: str,
        *,
        exercise_id: int,
    ) -> None:
        self.title = title
        self.exercise_key = exercise_key
        self.parts = parts
        self.test_target = test_target
        self.exercise_id = exercise_id

    # ── Notebook assembly ────────────────────────────────────────────────────

    def build_notebook(self, variant: str, exercise_type: str) -> dict[str, Any]:
        """Assemble a full notebook dict for the given *variant*.

        Parameters
        ----------
        variant : str
            ``"student"`` or ``"solution"`` — controls the
            ``PYTUTOR_ACTIVE_VARIANT`` value in the self-check cell.
        exercise_type : str
            One of ``"debug"``, ``"modify"``, ``"make"``, ``"gaps"`` — used
            to select the appropriate header instructions.
        """
        cells: list[dict[str, Any]] = []

        cells.extend(self._build_header_cells(exercise_type, self.test_target))
        cells.extend(self._build_exercise_cells())
        cells.append(self._build_scratch_cell())
        cells.append(self.build_check_answers_cell(variant))

        return {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {"name": "python", "version": "3"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

    # ── Header cells ─────────────────────────────────────────────────────────

    def _build_header_cells(
        self,
        exercise_type: str,
        test_target: str,
    ) -> list[dict[str, Any]]:
        """Build the orientation markdown cell at the top of every notebook."""
        if exercise_type == "gaps":
            how_to_work = [
                "## How to work\n",
                "- Find the ``# YOUR CODE HERE`` comment in each exercise cell\n",
                "- Delete the comment and write the missing line(s) of code in its place\n",
                f"- From the repository root, run ``uv run pytest -q {test_target}``\n",
            ]
        elif exercise_type == "debug":
            how_to_work = [
                "## How to work\n",
                "- Write your corrected solution in the exercise cell(s)\n",
                "- After running your corrected solution, describe what happened "
                "in the explanation cell(s)\n",
                f"- From the repository root, run ``uv run pytest -q {test_target}``\n",
            ]
        else:
            how_to_work = [
                "## How to work\n",
                "- Write your solution(s) in the exercise cell(s)\n",
                f"- From the repository root, run ``uv run pytest -q {test_target}``\n",
            ]

        return [
            {
                "cell_type": "markdown",
                "metadata": _make_meta("markdown"),
                "source": [
                    f"# {self.title}\n",
                    "\n",
                    "## Goal\n",
                    "Complete each exercise cell, then run the tests from the repository root.\n",
                    "\n",
                    *how_to_work,
                ],
            }
        ]

    # ── Abstract: type-specific exercise cells ───────────────────────────────

    @abstractmethod
    def _build_exercise_cells(self) -> list[dict[str, Any]]:
        """Return the type-specific tagged exercise cells."""

    # ── Shared cells ─────────────────────────────────────────────────────────

    def _build_scratch_cell(self) -> dict[str, Any]:
        """Return the shared scratch-pad cell."""
        return {
            "cell_type": "code",
            "metadata": _make_meta("python"),
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Self-check scratch cell (not graded)\n",
                "# You can run small experiments here.\n",
            ],
        }

    def build_check_answers_cell(self, variant: str) -> dict[str, Any]:
        """Return the self-checker cell that sets the notebook variant."""
        return {
            "cell_type": "code",
            "metadata": _make_meta("python"),
            "execution_count": None,
            "outputs": [],
            "source": [
                "import os\n",
                "\n",
                f'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "{variant}"\n',
                "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                "\n",
                "# Pass the canonical exercise_key here; do not pass a notebook path.\n",
                f"run_notebook_checks({self.exercise_key!r})\n",
            ],
        }

    # ── README ───────────────────────────────────────────────────────────────

    def build_readme_lines(self, created_date: str) -> list[str]:
        """Build README content for a scaffolded exercise."""
        lines = [
            f"# {self.title}",
            "",
            "## Student prompt",
            "- Open ``notebooks/student.ipynb`` in this exercise folder.",
            "- Write your solution in the notebook cell tagged ``exercise1`` "
            "(or ``exercise2``, …).",
            f"- From the repository root, run ``uv run pytest -q {self.test_target}`` "
            "until all tests pass.",
            "",
            "## Teacher notes",
            f"- Created: {created_date}",
            "- Target concepts: (fill in)",
        ]
        type_lines = self._readme_type_hook()
        if type_lines:
            # Insert type-specific lines after the test-target line (index 5),
            # before the blank line (index 6) — matching original order in
            # new_exercise.py:_build_readme_lines().
            insert_at = 6
            for line in reversed(type_lines):  # reversed to maintain order
                lines.insert(insert_at, line)
        return lines

    def _readme_type_hook(self) -> list[str]:
        """Override in subclasses to inject type-specific README lines."""
        return []

    # ── Test file generation ─────────────────────────────────────────────────

    def build_test_lines(self) -> list[str]:
        """Build the complete test file content.

        Emits shared boilerplate (imports, constants, helper), then delegates
        type-specific body assertions and type-specific extra checks to abstract
        / hook methods.
        """
        lines: list[str] = [
            "from __future__ import annotations",
            "",
        ]

        # Imports
        if self.parts > 1:
            lines.extend(
                [
                    "import pytest",
                    "",
                ]
            )

        lines.extend(
            [
                "from exercise_runtime_support.exercise_framework import (",
                "    RuntimeCache,",
            ]
        )

        type_specific_lines = self._build_type_specific_test_lines()
        # Check if debug imports are needed
        has_debug_imports = any("get_explanation_cell" in line for line in type_specific_lines)
        if has_debug_imports:
            lines.append("    get_explanation_cell,")

        lines.extend(
            [
                "    resolve_exercise_notebook_path,",
                "    run_cell_and_capture_output,",
                ")",
            ]
        )

        if has_debug_imports:
            lines.extend(
                [
                    "from exercise_runtime_support.exercise_framework.expectations_helpers import (",
                    "    is_valid_explanation,",
                    ")",
                ]
            )

        lines.extend(
            [
                "",
                f"_EXERCISE_KEY = {self.exercise_key!r}",
                "_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)",
                "_CACHE = RuntimeCache()",
            ]
        )

        if has_debug_imports:
            lines.extend(
                [
                    "_MIN_EXPLANATION_LENGTH = 50",
                    "_PLACEHOLDER_PHRASES = (",
                    "    'describe what',",
                    "    'describe briefly',",
                    "    'your explanation',",
                    "    'explain here',",
                    "    'write your',",
                    "    'todo',",
                    "    '...',",
                    "    'include any error',",
                    ")",
                ]
            )

        lines.extend(
            [
                "",
                "",
                "def _run_and_capture(tag: str) -> str:",
                '    """Execute the tagged cell and capture its print output."""',
                "    return run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)",
                "",
                "",
            ]
        )

        lines.extend(self._build_exercise_body_test_lines())
        lines.extend(type_specific_lines)

        return lines

    @abstractmethod
    def _build_exercise_body_test_lines(self) -> list[str]:
        """Return type-specific test assertions for the exercise body cells."""

    def _build_type_specific_test_lines(self) -> list[str]:
        """Hook for type-specific test lines (e.g. debug explanation checks).

        Returns an empty list by default; subclasses may override.
        """
        return []

    # ── Supporting files ─────────────────────────────────────────────────────

    def build_expectations_module(self) -> str:
        """Return the content of ``tests/expectations.py`` as a string."""
        comma_separated_keys = ", ".join(f'{i}: ""' for i in range(1, self.parts + 1))
        return (
            f'"""Exercise-local expectations for {self.exercise_key}."""\n'
            "from __future__ import annotations\n"
            "\n"
            "from typing import Final\n"
            "\n"
            f"EX{self.exercise_id:03d}_EXPECTED_OUTPUTS: Final[dict[int, str]]"
            f" = {{\n"
            f"    {comma_separated_keys}\n"
            "}\n"
        )

    def build_student_checker_support(self) -> str:
        """Return the content of ``tests/student_checker_support.py`` as a string."""
        expectations_var = f"EX{self.exercise_id:03d}_EXPECTED_OUTPUTS"
        return (
            f'"""Exercise-local student checker definitions for {self.exercise_key}."""\n'
            "from __future__ import annotations\n"
            "\n"
            "from exercise_runtime_support.exercise_test_support import (\n"
            "    load_exercise_test_module,\n"
            ")\n"
            "from exercise_runtime_support.student_checker.checks.base import (\n"
            "    ExerciseCheckDefinition,\n"
            "    build_exercise_check,\n"
            "    exercise_tag,\n"
            ")\n"
            "\n"
            f"_EXERCISE_KEY = {self.exercise_key!r}\n"
            f'expectations_mod = load_exercise_test_module(_EXERCISE_KEY, "expectations")\n'
            f"{expectations_var} = expectations_mod.{expectations_var}\n"
            "\n"
            "# TODO: Define check functions and build the CHECKS list.\n"
            "# See exercises/sequence/ex012_sequence_modify_maths_operators/tests/"
            "student_checker_support.py for an example.\n"
            "CHECKS: list[ExerciseCheckDefinition] = []\n"
        )
