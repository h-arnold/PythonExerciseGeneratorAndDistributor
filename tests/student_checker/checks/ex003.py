"""Checks for the ex003 notebook."""

from __future__ import annotations

from tests.exercise_expectations import (
    EX003_EXPECTED_INPUT_MESSAGES,
    EX003_EXPECTED_PROMPTS,
    EX003_EXPECTED_STATIC_OUTPUT,
    EX003_NOTEBOOK_PATH,
)
from tests.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)
from tests.notebook_grader import (
    NotebookGradingError,
    run_cell_and_capture_output,
    run_cell_with_input,
)

from ..models import ExerciseCheckResult
from .base import ExerciseCheckDefinition, build_exercise_check, exercise_tag


def check_ex003() -> list[str]:
    """Run checks for ex003."""
    return [issue for result in run_ex003_checks() for issue in result.issues]


def run_ex003_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex003."""
    results: list[ExerciseCheckResult] = []
    for check in _EX003_CHECKS:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            ExerciseCheckResult(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def _check_ex003_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex003_notebook_path()
    expected = EX003_EXPECTED_STATIC_OUTPUT[exercise_no]
    output = run_cell_and_capture_output(notebook_path, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _check_ex003_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex003_notebook_path()
    inputs = _EX003_PROMPT_FLOW_INPUTS[exercise_no]
    output = run_cell_with_input(
        notebook_path,
        tag=exercise_tag(exercise_no),
        inputs=inputs,
    )
    expected = _format_ex003_prompt_flow_output(exercise_no)
    if output != expected:
        errors.append(f"Exercise {exercise_no}: output does not match the expected prompt flow.")
    return errors


def _format_ex003_prompt_flow_output(exercise_no: int) -> str:
    prompts = EX003_EXPECTED_PROMPTS[exercise_no]
    template = EX003_EXPECTED_INPUT_MESSAGES[exercise_no]
    placeholders = _EX003_PROMPT_FLOW_PLACEHOLDERS[exercise_no]
    inputs = _EX003_PROMPT_FLOW_INPUTS[exercise_no]
    values = dict(zip(placeholders, inputs, strict=True))
    lines = [*prompts, template.format(**values)]
    return "".join(f"{line}\n" for line in lines)


def _resolve_ex003_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX003_NOTEBOOK_PATH))


_EX003_PROMPT_FLOW_INPUTS: dict[int, list[str]] = {
    4: ["mango", "tropical"],
    5: ["Cardiff", "Wales"],
    6: ["Alex", "Morgan"],
}

_EX003_PROMPT_FLOW_PLACEHOLDERS: dict[int, tuple[str, str]] = {
    4: ("value1", "value2"),
    5: ("town", "country"),
    6: ("first", "last"),
}


def _build_ex003_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = sorted(set(EX003_EXPECTED_STATIC_OUTPUT) | set(_EX003_PROMPT_FLOW_INPUTS))
    for exercise_no in exercise_numbers:
        if exercise_no in EX003_EXPECTED_STATIC_OUTPUT:
            checks.append(
                build_exercise_check(exercise_no, "Static output", _check_ex003_static_output)
            )
        if exercise_no in _EX003_PROMPT_FLOW_INPUTS:
            checks.append(
                build_exercise_check(exercise_no, "Prompt flow", _check_ex003_prompt_flow)
            )
    return checks


_EX003_CHECKS: list[ExerciseCheckDefinition] = _build_ex003_checks()
EX003_CHECKS = _EX003_CHECKS


__all__ = [
    "EX003_CHECKS",
    "_EX003_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex003",
    "run_ex003_checks",
]
