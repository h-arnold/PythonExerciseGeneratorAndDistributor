"""Checks for the ex005 notebook."""

from __future__ import annotations

from tests.exercise_expectations import (
    EX005_EXERCISE_INPUTS,
    EX005_EXPECTED_SINGLE_LINE,
    EX005_FULL_NAME_EXERCISE,
    EX005_INPUT_PROMPTS,
    EX005_MIN_EXPLANATION_LENGTH,
    EX005_MODIFY_STARTER_BASELINES,
    EX005_NOTEBOOK_PATH,
    EX005_PLACEHOLDER_PHRASES,
    EX005_PROFILE_EXERCISE,
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


def check_ex005() -> list[str]:
    """Run checks for ex005."""
    return [issue for result in run_ex005_checks() for issue in result.issues]


def run_ex005_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex005."""
    results: list[ExerciseCheckResult] = []
    untouched_exercises: set[int] = set()
    seen_exercises: set[int] = set()
    notebook_path = _resolve_ex005_notebook_path()
    for check in _EX005_CHECKS:
        if check.exercise_no in untouched_exercises:
            continue
        if check.exercise_no not in seen_exercises:
            seen_exercises.add(check.exercise_no)
            gate_issues = check_modify_exercise_started(
                notebook_path,
                check.exercise_no,
                EX005_MODIFY_STARTER_BASELINES,
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


def _check_ex005_static_output(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex005_notebook_path()
    expected = EX005_EXPECTED_SINGLE_LINE[exercise_no]
    output = run_cell_and_capture_output(
        notebook_path, tag=exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _check_ex005_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex005_notebook_path()
    if exercise_no == EX005_FULL_NAME_EXERCISE:
        inputs = EX005_EXERCISE_INPUTS[exercise_no]
        output = run_cell_with_input(
            notebook_path,
            tag=exercise_tag(exercise_no),
            inputs=inputs,
        )
        prompt_first, prompt_second = EX005_INPUT_PROMPTS[exercise_no]
        first, last = inputs
        expected = f"{prompt_first}{prompt_second}{first} {last}\n"
        if output != expected:
            errors.append(
                "Exercise 5: output does not match the expected full name flow.")
    elif exercise_no == EX005_PROFILE_EXERCISE:
        inputs = EX005_EXERCISE_INPUTS[exercise_no]
        output = run_cell_with_input(
            notebook_path,
            tag=exercise_tag(exercise_no),
            inputs=inputs,
        )
        profile_prompt_first, profile_prompt_second = EX005_INPUT_PROMPTS[exercise_no]
        age, city = inputs
        expected = f"{profile_prompt_first}{profile_prompt_second}You are {age} years old and live in {city}\n"
        if output != expected:
            errors.append(
                "Exercise 10: output does not match the expected profile flow.")
    return errors


def _check_ex005_explanation(exercise_no: int) -> list[str]:
    return check_explanation_cell(
        _resolve_ex005_notebook_path(),
        exercise_no,
        EX005_MIN_EXPLANATION_LENGTH,
        EX005_PLACEHOLDER_PHRASES,
    )


def _resolve_ex005_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX005_NOTEBOOK_PATH))


def _build_ex005_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    prompt_exercises = {EX005_FULL_NAME_EXERCISE, EX005_PROFILE_EXERCISE}
    for exercise_no in range(1, 11):
        if exercise_no in EX005_EXPECTED_SINGLE_LINE:
            checks.append(
                build_exercise_check(
                    exercise_no, "Static output", _check_ex005_static_output)
            )
        if exercise_no in prompt_exercises:
            checks.append(
                build_exercise_check(
                    exercise_no, "Prompt flow", _check_ex005_prompt_flow)
            )
        checks.append(build_exercise_check(
            exercise_no, "Explanation", _check_ex005_explanation))
    return checks


_EX005_CHECKS: list[ExerciseCheckDefinition] = _build_ex005_checks()
EX005_CHECKS = _EX005_CHECKS


__all__ = [
    "EX005_CHECKS",
    "_EX005_CHECKS",
    "ExerciseCheckDefinition",
    "check_ex005",
    "run_ex005_checks",
]
