"""Shared helpers for student checker exercises."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from exercise_runtime_support.execution_variant import Variant
from exercise_runtime_support.exercise_framework.expectations_helpers import is_valid_explanation
from exercise_runtime_support.notebook_grader import get_explanation_cell


@dataclass(frozen=True)
class ExerciseCheckDefinition:
    """Defines a single detailed exercise check."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


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


def check_explanation_cell(
    exercise_key: str,
    exercise_no: int,
    min_length: int,
    placeholder_phrases: tuple[str, ...],
    *,
    variant: Variant | None = None,
) -> list[str]:
    try:
        explanation = get_explanation_cell(
            exercise_key,
            tag=f"explanation{exercise_no}",
            variant=variant,
        )
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


__all__ = [
    "ExerciseCheckDefinition",
    "build_exercise_check",
    "check_explanation_cell",
    "exercise_tag",
]
