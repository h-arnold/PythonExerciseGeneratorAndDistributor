"""Checks for the ex004 notebook."""

from __future__ import annotations

from collections.abc import Callable

from tests.exercise_expectations import (
    EX004_EXPECTED_SINGLE_LINE,
    EX004_FORMAT_VALIDATION,
    EX004_MIN_EXPLANATION_LENGTH,
    EX004_MODIFY_STARTER_BASELINES,
    EX004_NOTEBOOK_PATH,
    EX004_PLACEHOLDER_PHRASES,
    EX004_PROMPT_STRINGS,
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


def check_ex004() -> list[str]:
    """Run checks for ex004."""
    return [issue for result in run_ex004_checks() for issue in result.issues]


def run_ex004_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex004."""
    results: list[ExerciseCheckResult] = []
    untouched_exercises: set[int] = set()
    seen_exercises: set[int] = set()
    notebook_path = _resolve_ex004_notebook_path()
    for check in _EX004_CHECKS:
        if check.exercise_no in untouched_exercises:
            continue
        if check.exercise_no not in seen_exercises:
            seen_exercises.add(check.exercise_no)
            gate_issues = check_modify_exercise_started(
                notebook_path,
                check.exercise_no,
                EX004_MODIFY_STARTER_BASELINES,
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


def _check_ex004_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex004_notebook_path()
    expected = EX004_EXPECTED_SINGLE_LINE[exercise_no]
    output = run_cell_and_capture_output(
        notebook_path, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _validate_ex004_prompt_7(notebook_path: str) -> list[str]:
    output = run_cell_with_input(
        notebook_path, tag=exercise_tag(7), inputs=["5"])
    if EX004_PROMPT_STRINGS[7] not in output or EX004_FORMAT_VALIDATION[7] not in output:
        return ["Exercise 7: output does not match the expected prompt or total."]
    return []


def _validate_ex004_prompt_8(notebook_path: str) -> list[str]:
    output = run_cell_with_input(
        notebook_path, tag=exercise_tag(8), inputs=["Alice"])
    expected = f"{EX004_PROMPT_STRINGS[8]} {EX004_FORMAT_VALIDATION[8]}\n"
    if output != expected:
        return ["Exercise 8: output does not match the expected greeting."]
    return []


def _validate_ex004_prompt_10(notebook_path: str) -> list[str]:
    output = run_cell_with_input(
        notebook_path, tag=exercise_tag(10), inputs=["Blue"])
    expected = f"{EX004_PROMPT_STRINGS[10]} {EX004_FORMAT_VALIDATION[10]}\n"
    if output != expected:
        return ["Exercise 10: output does not match the expected response."]
    return []


_EX004_PROMPT_FLOW_HANDLERS: dict[int, Callable[[str], list[str]]] = {
    7: _validate_ex004_prompt_7,
    8: _validate_ex004_prompt_8,
    10: _validate_ex004_prompt_10,
}


def _check_ex004_prompt_flow(exercise_no: int) -> list[str]:
    handler = _EX004_PROMPT_FLOW_HANDLERS.get(exercise_no)
    if handler is None:
        return []
    notebook_path = _resolve_ex004_notebook_path()
    return handler(notebook_path)


def _check_ex004_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _resolve_ex004_notebook_path(),
        exercise_no,
        EX004_MIN_EXPLANATION_LENGTH,
        EX004_PLACEHOLDER_PHRASES,
    )


def _resolve_ex004_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX004_NOTEBOOK_PATH))


def _build_ex004_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    prompt_exercises = {7, 8, 10}
    for exercise_no in range(1, 11):
        if exercise_no in EX004_EXPECTED_SINGLE_LINE:
            checks.append(
                build_exercise_check(
                    exercise_no, "Static output", _check_ex004_static_output)
            )
        if exercise_no in prompt_exercises:
            checks.append(
                build_exercise_check(
                    exercise_no, "Prompt flow", _check_ex004_prompt_flow)
            )
        checks.append(build_exercise_check(
            exercise_no, "Explanation", _check_ex004_explanation))
    return checks


_EX004_CHECKS: list[ExerciseCheckDefinition] = _build_ex004_checks()
EX004_CHECKS = _EX004_CHECKS


__all__ = [
    "EX004_CHECKS",
    "_EX004_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex004",
    "run_ex004_checks",
]
