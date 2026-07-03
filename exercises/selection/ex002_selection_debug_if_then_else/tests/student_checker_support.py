"""Exercise-local student checker definitions for ex002_selection_debug_if_then_else."""
from __future__ import annotations

from exercise_runtime_support.exercise_test_support import (
    load_exercise_test_module,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = 'ex002_selection_debug_if_then_else'
expectations_mod = load_exercise_test_module(_EXERCISE_KEY, "expectations")
EX002_EXPECTED_OUTPUTS = expectations_mod.EX002_EXPECTED_OUTPUTS

# TODO: Define check functions and build the CHECKS list.
# See exercises/sequence/ex012_sequence_modify_maths_operators/tests/student_checker_support.py for an example.
CHECKS: list[ExerciseCheckDefinition] = []
