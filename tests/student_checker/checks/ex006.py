"""Checks for the ex006 notebook."""

from __future__ import annotations

from tests.exercise_expectations import (
    EX006_EXPECTED_OUTPUTS,
    EX006_INPUT_EXPECTATIONS,
    EX006_NOTEBOOK_PATH,
)
from tests.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)
from tests.notebook_grader import (
    NotebookGradingError,
    run_cell_and_capture_output,
    run_cell_with_input,
)

from ..models import Ex006CheckResult
from .base import Ex006CheckDefinition, build_ex006_check, exercise_tag


def check_ex006() -> list[str]:
    """Run checks for ex006."""
    return [issue for result in run_ex006_checks() for issue in result.issues]


def run_ex006_checks() -> list[Ex006CheckResult]:
    """Run detailed checks for ex006 and return structured results."""
    results: list[Ex006CheckResult] = []
    for check in _EX006_CHECKS:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            Ex006CheckResult(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def _check_ex006_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex006_notebook_path()
    output = run_cell_and_capture_output(notebook_path, tag=exercise_tag(exercise_no))
    expected = EX006_EXPECTED_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_ex006_input_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex006_notebook_path()
    details = EX006_INPUT_EXPECTATIONS[exercise_no]
    inputs = details["inputs"]
    output = run_cell_with_input(notebook_path, tag=exercise_tag(exercise_no), inputs=inputs)
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


def _resolve_ex006_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX006_NOTEBOOK_PATH))


def _build_ex006_checks() -> list[Ex006CheckDefinition]:
    checks: list[Ex006CheckDefinition] = []
    exercise_numbers = sorted(set(EX006_EXPECTED_OUTPUTS) | set(EX006_INPUT_EXPECTATIONS))
    for exercise_no in exercise_numbers:
        if exercise_no in EX006_EXPECTED_OUTPUTS:
            checks.append(
                build_ex006_check(exercise_no, "Static output", _check_ex006_static_output)
            )
        if exercise_no in EX006_INPUT_EXPECTATIONS:
            checks.append(build_ex006_check(exercise_no, "Prompt flow", _check_ex006_input_flow))
    return checks


_EX006_CHECKS: list[Ex006CheckDefinition] = _build_ex006_checks()
EX006_CHECKS = _EX006_CHECKS


__all__ = [
    "EX006_CHECKS",
    "_EX006_CHECKS",
    "Ex006CheckDefinition",
    "check_ex006",
    "run_ex006_checks",
]
