"""Exercise-local student checker definitions for ex008 sequence make consolidation."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_framework import extract_tagged_code
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_and_capture_output,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex008_sequence_make_consolidation"
ex008 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
checks = load_exercise_test_module(_EXERCISE_KEY, "checks")
construct_errors = checks.construct_errors
output_errors = checks.output_errors
capture_interactive_events = checks.capture_interactive_events
interactive_event_errors = checks.interactive_event_errors


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    errors.extend(output_errors(exercise_no, output))
    errors.extend(
        construct_errors(
            exercise_no,
            ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(exercise_no))),
        )
    )
    return errors


def _check_interactive_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    for case in ex008.EX008_INTERACTIVE_CASES[exercise_no]:
        tree = ast.parse(extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(exercise_no)))
        events = capture_interactive_events(_EXERCISE_KEY, exercise_no, list(case["inputs"]))
        errors.extend(interactive_event_errors(exercise_no, events, list(case["inputs"])))
        errors.extend(construct_errors(exercise_no, tree))
        if errors:
            break
    return errors


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    for exercise_no in range(1, 6):
        if exercise_no in ex008.EX008_EXPECTED_STATIC_OUTPUTS:
            checks.append(
                build_exercise_check(
                    exercise_no, "Task result and constructs", _check_static_output
                )
            )
        else:
            checks.append(
                build_exercise_check(
                    exercise_no, "Task result and constructs", _check_interactive_output
                )
            )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
