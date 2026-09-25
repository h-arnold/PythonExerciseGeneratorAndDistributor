"""Specialised self-check definitions for ex003 sequence modify variables."""

from __future__ import annotations

import ast
from typing import Final

from exercise_runtime_support.exercise_framework import extract_tagged_code
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex003_sequence_modify_variables"
_EXERCISE10: Final = 10
ex003 = load_exercise_test_module(_EXERCISE_KEY, "expectations")
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _parse_exercise(exercise_no: int) -> tuple[ast.Module | None, list[str]]:
    """Parse one tagged cell, returning student-facing errors on failure."""
    try:
        code = extract_tagged_code(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
        return ast.parse(code), []
    except Exception as exc:  # noqa: BLE001 - report extraction problems to students
        return None, [f"Could not inspect the exercise code: {exc}"]


def check_static_construct(exercise_no: int) -> list[str]:
    """Check a static cell's straight-line assignment-to-print flow."""
    tree, errors = _parse_exercise(exercise_no)
    if tree is None:
        return errors
    return construct_checks.static_construct_issues(
        tree,
        exercise_no,
        required_values=ex003.EX003_EXPECTED_ASSIGNMENTS.get(exercise_no),
        required_fragments=(
            ex003.EX003_EXERCISE10_REQUIRED_PHRASES if exercise_no == _EXERCISE10 else None
        ),
    )


def check_interactive_construct(exercise_no: int) -> list[str]:
    """Check an interactive cell's prompts, inputs, aliases, and final output."""
    tree, errors = _parse_exercise(exercise_no)
    if tree is None:
        return errors
    case = ex003.EX003_INPUT_CASES[exercise_no]
    issues = construct_checks.interactive_construct_issues(
        tree,
        expected_input_count=len(case["inputs"]),
        message_template=ex003.EX003_EXPECTED_INPUT_MESSAGES[exercise_no],
    )
    issues.extend(
        construct_checks.obsolete_text_issues(
            tree,
            (
                ex003.EX003_ORIGINAL_PROMPTS[exercise_no],
                ex003.EX003_ORIGINAL_MESSAGES[exercise_no],
            ),
        )
    )
    return issues


def _check_static_output(exercise_no: int) -> list[str]:
    """Verify a static exercise cell produces the expected exact output."""
    expected = ex003.EX003_EXPECTED_STATIC_OUTPUTS[exercise_no]
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
        )
    except Exception as exc:  # noqa: BLE001 - report runtime failures as check issues
        return [str(exc)]
    if output != expected:
        return [f"Expected: {expected!r}\n     Got: {output!r}"]
    return []


def _check_input_output(exercise_no: int) -> list[str]:
    """Verify an interactive exercise cell produces the primary exact output."""
    case = ex003.EX003_INPUT_CASES[exercise_no]
    try:
        output = run_cell_with_input(
            _EXERCISE_KEY,
            tag=exercise_tag(exercise_no),
            inputs=list(case["inputs"]),
        )
    except Exception as exc:  # noqa: BLE001 - report runtime failures as check issues
        return [str(exc)]
    if output != case["expected_output"]:
        return [f"Expected: {case['expected_output']!r}\n     Got: {output!r}"]
    return []


def _make_output_check(exercise_no: int, title: str) -> ExerciseCheckDefinition:
    """Build the output check appropriate for the exercise type."""
    if exercise_no in ex003.EX003_INPUT_CASES:
        return build_exercise_check(exercise_no, title, _check_input_output)
    return build_exercise_check(exercise_no, title, _check_static_output)


def _build_checks() -> list[ExerciseCheckDefinition]:
    """Build interleaved output and straight-line construct checks."""
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = sorted(
        set(ex003.EX003_EXPECTED_STATIC_OUTPUTS) | set(ex003.EX003_INPUT_CASES)
    )
    for exercise_no in exercise_numbers:
        checks.append(_make_output_check(exercise_no, "Correct output"))
        if exercise_no in ex003.EX003_INPUT_CASES:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Straight-line input data flow",
                    check_interactive_construct,
                )
            )
        else:
            checks.append(
                build_exercise_check(
                    exercise_no,
                    "Straight-line assignment data flow",
                    check_static_construct,
                )
            )
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
