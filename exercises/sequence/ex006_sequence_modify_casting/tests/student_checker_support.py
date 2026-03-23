"""Exercise-local student checker definitions for ex006 sequence modify casting."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    Ex006CheckDefinition,
    build_ex006_check,
    exercise_tag,
)

_EXERCISE_KEY = "ex006_sequence_modify_casting"
ex006 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    expected = ex006.EX006_EXPECTED_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_input_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    details = ex006.EX006_INPUT_EXPECTATIONS[exercise_no]
    inputs = details["inputs"]
    output = run_cell_with_input(_EXERCISE_KEY, tag=exercise_tag(exercise_no), inputs=inputs)
    prompt_contains = details["prompt_contains"]
    output_contains = details.get("output_contains")
    last_line = details.get("last_line")

    if prompt_contains not in output:
        errors.append(f"Exercise {exercise_no}: prompt text is missing.")
    if output_contains is not None and output_contains not in output:
        errors.append(f"Exercise {exercise_no}: expected message is missing.")
    if last_line is not None:
        stripped_output = output.strip()
        if not stripped_output:
            errors.append(f"Exercise {exercise_no}: no output was produced.")
            return errors
        last_output_line = stripped_output.splitlines()[-1]
        if last_output_line != last_line:
            errors.append(f"Exercise {exercise_no}: expected last line '{last_line}'.")
    return errors


def _build_checks() -> list[Ex006CheckDefinition]:
    checks: list[Ex006CheckDefinition] = []
    exercise_numbers = sorted(set(ex006.EX006_EXPECTED_OUTPUTS) | set(ex006.EX006_INPUT_EXPECTATIONS))
    for exercise_no in exercise_numbers:
        if exercise_no in ex006.EX006_EXPECTED_OUTPUTS:
            checks.append(build_ex006_check(exercise_no, "Static output", _check_static_output))
        if exercise_no in ex006.EX006_INPUT_EXPECTATIONS:
            checks.append(build_ex006_check(exercise_no, "Prompt flow", _check_input_flow))
    return checks


CHECKS: list[Ex006CheckDefinition] = _build_checks()
