"""Checks for the ex007 notebook."""

from __future__ import annotations

from tests.exercise_expectations import (
    EX007_EXPECTED_STATIC_OUTPUTS,
    EX007_INPUT_CASES,
    EX007_MIN_EXPLANATION_LENGTH,
    EX007_MODIFY_STARTER_BASELINES,
    EX007_NOTEBOOK_PATH,
    EX007_PLACEHOLDER_PHRASES,
)
from tests.exercise_framework.paths import (
    resolve_notebook_path as resolve_framework_notebook_path,
)
from tests.notebook_grader import (
    NotebookGradingError,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from tests.student_checker.checks.base import (
    MODIFY_START_GATE_TITLE,
    ExerciseCheckDefinition,
    build_exercise_check,
    check_explanation_cell,
    check_modify_exercise_started,
    exercise_tag,
)
from tests.student_checker.models import CheckStatus, ExerciseCheckResult


def check_ex007() -> list[str]:
    """Run checks for ex007."""
    return [issue for result in run_ex007_checks() for issue in result.issues]


def run_ex007_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex007."""
    results: list[ExerciseCheckResult] = []
    untouched_exercises: set[int] = set()
    seen_exercises: set[int] = set()
    notebook_path = _resolve_ex007_notebook_path()
    for check in _EX007_CHECKS:
        if check.exercise_no in untouched_exercises:
            continue
        if check.exercise_no not in seen_exercises:
            seen_exercises.add(check.exercise_no)
            gate_issues = check_modify_exercise_started(
                notebook_path,
                check.exercise_no,
                EX007_MODIFY_STARTER_BASELINES,
            )
            if gate_issues:
                gate_status = (
                    CheckStatus.NOT_STARTED
                    if any("NOT STARTED" in issue for issue in gate_issues)
                    else CheckStatus.FAILED
                )
                untouched_exercises.add(check.exercise_no)
                results.append(
                    ExerciseCheckResult(
                        exercise_no=check.exercise_no,
                        title=MODIFY_START_GATE_TITLE,
                        passed=False,
                        issues=gate_issues,
                        status=gate_status,
                    )
                )
                continue
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
    expected = EX007_EXPECTED_STATIC_OUTPUTS[exercise_no]
    output = run_cell_and_capture_output(
        notebook_path, tag=exercise_tag(exercise_no))
    if output != expected:
        errors.append(
            f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_ex007_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex007_notebook_path()
    case = EX007_INPUT_CASES[exercise_no]
    inputs = list(case["inputs"])
    output = run_cell_with_input(
        notebook_path, tag=exercise_tag(exercise_no), inputs=inputs)
    prompts = case["prompts"]
    for prompt in prompts:
        if prompt not in output:
            errors.append(
                f"Exercise {exercise_no}: prompt '{prompt}' missing.")
    stripped_output = output.strip()
    if not stripped_output:
        errors.append(f"Exercise {exercise_no}: no output was produced.")
        return errors
    last_line = stripped_output.splitlines()[-1]
    expected_last_line = case["last_line"]
    if not last_line.endswith(expected_last_line):
        errors.append(
            f"Exercise {exercise_no}: expected last line ending '{expected_last_line}'.")
    return errors


def _check_ex007_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _resolve_ex007_notebook_path(),
        exercise_no,
        EX007_MIN_EXPLANATION_LENGTH,
        EX007_PLACEHOLDER_PHRASES,
    )


def _resolve_ex007_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX007_NOTEBOOK_PATH))


def _build_ex007_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = range(1, 11)
    for exercise_no in exercise_numbers:
        if exercise_no in EX007_EXPECTED_STATIC_OUTPUTS:
            checks.append(
                build_exercise_check(
                    exercise_no, "Static output", _check_ex007_static_output)
            )
        if exercise_no in EX007_INPUT_CASES:
            checks.append(
                build_exercise_check(
                    exercise_no, "Prompt flow", _check_ex007_prompt_flow)
            )
        checks.append(build_exercise_check(
            exercise_no, "Explanation", _check_ex007_explanation))
    return checks


_EX007_CHECKS: list[ExerciseCheckDefinition] = _build_ex007_checks()
EX007_CHECKS = _EX007_CHECKS


__all__ = [
    "EX007_CHECKS",
    "_EX007_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex007",
    "run_ex007_checks",
]
