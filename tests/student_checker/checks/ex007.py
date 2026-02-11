"""Checks for the ex007 notebook."""

from __future__ import annotations

from tests.exercise_expectations import ex007_data_types_debug_casting as ex007
from tests.exercise_framework.expectations_helpers import is_valid_explanation
from tests.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)
from tests.notebook_grader import (
    NotebookGradingError,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

from ..models import ExerciseCheckResult
from .base import ExerciseCheckDefinition, _build_exercise_check, _exercise_tag


def check_ex007() -> list[str]:
    """Run checks for ex007."""
    return [issue for result in run_ex007_checks() for issue in result.issues]


def run_ex007_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex007."""
    results: list[ExerciseCheckResult] = []
    for check in _EX007_CHECKS:
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


def _check_ex007_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex007_notebook_path()
    expected = ex007.EX007_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(notebook_path, tag=_exercise_tag(exercise_no))
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_ex007_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex007_notebook_path()
    case = ex007.EX007_INPUT_CASES[exercise_no]
    inputs = list(case["inputs"])
    output = run_cell_with_input(notebook_path, tag=_exercise_tag(exercise_no), inputs=inputs)
    prompts = case["prompts"]
    for prompt in prompts:
        if prompt not in output:
            errors.append(f"Exercise {exercise_no}: prompt '{prompt}' missing.")
    stripped_output = output.strip()
    if not stripped_output:
        errors.append(f"Exercise {exercise_no}: no output was produced.")
        return errors
    last_line = stripped_output.splitlines()[-1]
    expected_last_line = case["last_line"]
    if not last_line.endswith(expected_last_line):
        errors.append(f"Exercise {exercise_no}: expected last line ending '{expected_last_line}'.")
    return errors


def _check_ex007_explanation(exercise_no: int) -> list[str]:
    try:
        explanation = get_explanation_cell(
            _resolve_ex007_notebook_path(),
            tag=f"explanation{exercise_no}",
        )
    except AssertionError:
        return [f"Exercise {exercise_no}: explanation is missing."]
    if not is_valid_explanation(
        explanation,
        min_length=ex007.EX007_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex007.EX007_PLACEHOLDER_PHRASES,
    ):
        return [f"Exercise {exercise_no}: explanation needs more detail."]
    return []


def _resolve_ex007_notebook_path() -> str:
    return str(resolve_framework_notebook_path(ex007.EX007_NOTEBOOK_PATH))


def _build_ex007_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = range(1, 11)
    for exercise_no in exercise_numbers:
        if exercise_no in ex007.EX007_EXPECTED_STATIC_OUTPUTS:
            checks.append(
                _build_exercise_check(exercise_no, "Static output", _check_ex007_static_output)
            )
        if exercise_no in ex007.EX007_INPUT_CASES:
            checks.append(
                _build_exercise_check(exercise_no, "Prompt flow", _check_ex007_prompt_flow)
            )
        checks.append(_build_exercise_check(exercise_no, "Explanation", _check_ex007_explanation))
    return checks


_EX007_CHECKS: list[ExerciseCheckDefinition] = _build_ex007_checks()


__all__ = [
    "_EX007_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex007",
    "run_ex007_checks",
]
