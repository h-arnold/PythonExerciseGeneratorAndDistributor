"""Exercise-local student checker contract for ex002 sequence modify basics."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.student_checker.checks.base import ExerciseCheckDefinition

_EXERCISE_KEY = "ex002_sequence_modify_basics"
framework_support = load_exercise_test_module(
    _EXERCISE_KEY, "framework_support")

CHECKS = [
    ExerciseCheckDefinition(
        exercise_no=check.exercise_no,
        title=check.title,
        check=check.check,
    )
    for check in framework_support.EX002_CHECKS
]
