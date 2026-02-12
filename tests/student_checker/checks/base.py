"""Shared helpers for student checker exercises."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial

from tests.exercise_framework.expectations_helpers import is_valid_explanation
from tests.exercise_framework.runtime import is_tagged_cell_semantically_modified
from tests.notebook_grader import get_explanation_cell


@dataclass(frozen=True)
class ExerciseCheckDefinition:
    """Defines a single detailed exercise check."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


@dataclass(frozen=True)
class Ex006CheckDefinition(ExerciseCheckDefinition):
    """Defines a detailed student-friendly ex006 check."""


MODIFY_START_GATE_TITLE = "Started"


def build_exercise_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> ExerciseCheckDefinition:
    return ExerciseCheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


def build_ex006_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> Ex006CheckDefinition:
    return Ex006CheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


def check_explanation_cell(
    notebook_path: str,
    exercise_no: int,
    min_length: int,
    placeholder_phrases: tuple[str, ...],
) -> list[str]:
    try:
        explanation = get_explanation_cell(
            notebook_path, tag=f"explanation{exercise_no}")
    except AssertionError:
        return [f"Exercise {exercise_no}: explanation is missing."]
    if not is_valid_explanation(
        explanation,
        min_length=min_length,
        placeholder_phrases=placeholder_phrases,
    ):
        return [f"Exercise {exercise_no}: explanation needs more detail."]
    return []


def exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def check_modify_exercise_started(
    notebook_path: str,
    exercise_no: int,
    starter_baselines: Mapping[str, str],
) -> list[str]:
    """Check whether a modify exercise has moved past starter code."""
    tag = exercise_tag(exercise_no)
    starter_code = starter_baselines.get(tag)
    if starter_code is None:
        return [
            f"Exercise {exercise_no}: missing starter baseline for '{tag}'. "
            "Update the exercise expectations baseline mapping."
        ]
    if is_tagged_cell_semantically_modified(notebook_path, tag=tag, starter_code=starter_code):
        return []
    return [f"Exercise {exercise_no}: NOT STARTED."]


__all__ = [
    "MODIFY_START_GATE_TITLE",
    "Ex006CheckDefinition",
    "ExerciseCheckDefinition",
    "build_ex006_check",
    "build_exercise_check",
    "check_explanation_cell",
    "check_modify_exercise_started",
    "exercise_tag",
]
