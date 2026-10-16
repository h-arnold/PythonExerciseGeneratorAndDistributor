"""Student self-checks for ex006 sequence casting tasks."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
)

_EXERCISE_KEY = "ex006_sequence_modify_casting"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_checks = load_exercise_test_module(_EXERCISE_KEY, "checks")


def _check_part(number: int) -> list[str]:
    source = extract_tagged_code(_EXERCISE_KEY, tag=f"exercise{number}")
    if number in _ex.EX006_EXPECTED_OUTPUTS:
        output = run_cell_and_capture_output(_EXERCISE_KEY, tag=f"exercise{number}")
        expected_segments = [_ex.EX006_EXPECTED_OUTPUTS[number]]
    else:
        case = _ex.EX006_INPUT_EXPECTATIONS[number]
        output = ""
        expected_segments = []
        for inputs, segments in (
            (case["inputs"], case["expected_segments"]),
            (case["alternate_inputs"], case["alternate_segments"]),
        ):
            output = run_cell_with_input(_EXERCISE_KEY, tag=f"exercise{number}", inputs=inputs)
            if not _checks.matches_segments(output, segments):
                return [f"Expected ordered complete messages: {segments!r}."]
        if not _checks.complete(number, source):
            return ["Required conversions and calculation must reach the output."]
        return []
    if not _checks.matches_segments(output, expected_segments):
        return [f"Expected complete output: {expected_segments!r}."]
    if not _checks.complete(number, source):
        return ["Required conversions and calculation must reach the output."]
    return []


CHECKS: list[ExerciseCheckDefinition] = [
    build_exercise_check(number, "Output and required conversions", _check_part)
    for number in range(1, 11)
]
