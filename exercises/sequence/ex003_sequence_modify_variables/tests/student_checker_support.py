"""Exercise-local student checker definitions for ex003 sequence modify variables."""

from __future__ import annotations

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
ex003 = load_exercise_test_module(_EXERCISE_KEY, "expectations")

_PROMPT_FLOW_INPUTS: dict[int, list[str]] = {
    4: ["mango", "tropical"],
    5: ["Cardiff", "Wales"],
    6: ["Alex", "Morgan"],
}

_PROMPT_FLOW_PLACEHOLDERS: dict[int, tuple[str, str]] = {
    4: ("value1", "value2"),
    5: ("town", "country"),
    6: ("first", "last"),
}


def _check_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    expected = ex003.EX003_EXPECTED_STATIC_OUTPUT[exercise_no]
    output = run_cell_and_capture_output(_EXERCISE_KEY, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _check_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    inputs = _PROMPT_FLOW_INPUTS[exercise_no]
    output = run_cell_with_input(
        _EXERCISE_KEY,
        tag=exercise_tag(exercise_no),
        inputs=inputs,
    )
    expected = _format_prompt_flow_output(exercise_no)
    if output != expected:
        errors.append(f"Exercise {exercise_no}: output does not match the expected prompt flow.")
    return errors


def _format_prompt_flow_output(exercise_no: int) -> str:
    prompts = ex003.EX003_EXPECTED_PROMPTS[exercise_no]
    template = ex003.EX003_EXPECTED_INPUT_MESSAGES[exercise_no]
    placeholders = _PROMPT_FLOW_PLACEHOLDERS[exercise_no]
    inputs = _PROMPT_FLOW_INPUTS[exercise_no]
    values = dict(zip(placeholders, inputs, strict=True))
    lines = [*prompts, template.format(**values)]
    return "".join(f"{line}\n" for line in lines)


def _build_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = sorted(set(ex003.EX003_EXPECTED_STATIC_OUTPUT) | set(_PROMPT_FLOW_INPUTS))
    for exercise_no in exercise_numbers:
        if exercise_no in ex003.EX003_EXPECTED_STATIC_OUTPUT:
            checks.append(build_exercise_check(exercise_no, "Static output", _check_static_output))
        if exercise_no in _PROMPT_FLOW_INPUTS:
            checks.append(build_exercise_check(exercise_no, "Prompt flow", _check_prompt_flow))
    return checks


CHECKS: list[ExerciseCheckDefinition] = _build_checks()
