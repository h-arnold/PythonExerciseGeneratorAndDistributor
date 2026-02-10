"""Check implementations for each notebook."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from tests.exercise_expectations import (
    EX001_FUNCTION_NAME,
    EX001_NOTEBOOK_PATH,
    EX001_TAG,
    EX003_EXPECTED_INPUT_MESSAGES,
    EX003_EXPECTED_PROMPTS,
    EX003_EXPECTED_STATIC_OUTPUT,
    EX003_NOTEBOOK_PATH,
    EX004_EXPECTED_SINGLE_LINE,
    EX004_FORMAT_VALIDATION,
    EX004_MIN_EXPLANATION_LENGTH,
    EX004_NOTEBOOK_PATH,
    EX004_PLACEHOLDER_PHRASES,
    EX004_PROMPT_STRINGS,
    EX005_EXERCISE_INPUTS,
    EX005_EXPECTED_SINGLE_LINE,
    EX005_FULL_NAME_EXERCISE,
    EX005_INPUT_PROMPTS,
    EX005_MIN_EXPLANATION_LENGTH,
    EX005_NOTEBOOK_PATH,
    EX005_PLACEHOLDER_PHRASES,
    EX005_PROFILE_EXERCISE,
    EX006_EXPECTED_OUTPUTS,
    EX006_INPUT_EXPECTATIONS,
    EX006_NOTEBOOK_PATH,
)
from tests.exercise_framework.expectations import EX002_CHECKS
from tests.exercise_framework.expectations_helpers import is_valid_explanation
from tests.exercise_framework.paths import resolve_notebook_path as resolve_framework_notebook_path
from tests.notebook_grader import (
    NotebookGradingError,
    exec_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

from .models import Ex002CheckResult, Ex006CheckResult


def check_ex001() -> list[str]:
    """Run checks for ex001."""
    errors: list[str] = []
    ns = exec_tagged_code(EX001_NOTEBOOK_PATH, tag=EX001_TAG)
    example = ns.get(EX001_FUNCTION_NAME)
    if example is None:
        errors.append("The `example` function is missing.")
        return errors
    result = example()
    if not isinstance(result, str):
        errors.append("The `example` function must return a string.")
    elif result == "":
        errors.append("The `example` function should not return an empty string.")
    return errors


def check_ex002_summary() -> list[str]:
    """Run summary checks for ex002."""
    return [issue for result in run_ex002_checks() for issue in result.issues]


def run_ex002_checks() -> list[Ex002CheckResult]:
    """Run detailed checks for ex002."""
    results: list[Ex002CheckResult] = []
    for check in EX002_CHECKS:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            Ex002CheckResult(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def check_ex003() -> list[str]:
    """Run checks for ex003."""
    errors: list[str] = []
    for exercise_no, expected in EX003_EXPECTED_STATIC_OUTPUT.items():
        output = run_cell_and_capture_output(EX003_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != f"{expected}\n":
            errors.append(f"Exercise {exercise_no}: expected '{expected}'.")

    fruit_output = run_cell_with_input(
        EX003_NOTEBOOK_PATH,
        tag=_exercise_tag(4),
        inputs=["mango", "tropical"],
    )
    expected_fruit = (
        f"{EX003_EXPECTED_PROMPTS[4][0]}\n"
        f"{EX003_EXPECTED_PROMPTS[4][1]}\n"
        f"{EX003_EXPECTED_INPUT_MESSAGES[4].format(value1='mango', value2='tropical')}\n"
    )
    if fruit_output != expected_fruit:
        errors.append("Exercise 4: output does not match the expected prompt flow.")

    town_output = run_cell_with_input(
        EX003_NOTEBOOK_PATH,
        tag=_exercise_tag(5),
        inputs=["Cardiff", "Wales"],
    )
    expected_town = (
        f"{EX003_EXPECTED_PROMPTS[5][0]}\n"
        f"{EX003_EXPECTED_PROMPTS[5][1]}\n"
        f"{EX003_EXPECTED_INPUT_MESSAGES[5].format(town='Cardiff', country='Wales')}\n"
    )
    if town_output != expected_town:
        errors.append("Exercise 5: output does not match the expected prompt flow.")

    name_output = run_cell_with_input(
        EX003_NOTEBOOK_PATH,
        tag=_exercise_tag(6),
        inputs=["Alex", "Morgan"],
    )
    expected_name = (
        f"{EX003_EXPECTED_PROMPTS[6][0]}\n"
        f"{EX003_EXPECTED_PROMPTS[6][1]}\n"
        f"{EX003_EXPECTED_INPUT_MESSAGES[6].format(first='Alex', last='Morgan')}\n"
    )
    if name_output != expected_name:
        errors.append("Exercise 6: output does not match the expected prompt flow.")

    return errors


def check_ex004() -> list[str]:
    """Run checks for ex004."""
    errors: list[str] = []
    errors.extend(_check_ex004_outputs())
    errors.extend(_check_ex004_explanations())
    return errors


def check_ex005() -> list[str]:
    """Run checks for ex005."""
    errors: list[str] = []
    for exercise_no, expected in EX005_EXPECTED_SINGLE_LINE.items():
        output = run_cell_and_capture_output(EX005_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != f"{expected}\n":
            errors.append(f"Exercise {exercise_no}: expected '{expected}'.")

    full_name_output = run_cell_with_input(
        EX005_NOTEBOOK_PATH,
        tag=_exercise_tag(EX005_FULL_NAME_EXERCISE),
        inputs=EX005_EXERCISE_INPUTS[EX005_FULL_NAME_EXERCISE],
    )
    prompt_first, prompt_second = EX005_INPUT_PROMPTS[EX005_FULL_NAME_EXERCISE]
    first, last = EX005_EXERCISE_INPUTS[EX005_FULL_NAME_EXERCISE]
    expected_full_name = f"{prompt_first}{prompt_second}{first} {last}\n"
    if full_name_output != expected_full_name:
        errors.append("Exercise 5: output does not match the expected full name flow.")

    profile_output = run_cell_with_input(
        EX005_NOTEBOOK_PATH,
        tag=_exercise_tag(EX005_PROFILE_EXERCISE),
        inputs=EX005_EXERCISE_INPUTS[EX005_PROFILE_EXERCISE],
    )
    profile_prompt_first, profile_prompt_second = EX005_INPUT_PROMPTS[EX005_PROFILE_EXERCISE]
    age, city = EX005_EXERCISE_INPUTS[EX005_PROFILE_EXERCISE]
    expected_profile = (
        f"{profile_prompt_first}{profile_prompt_second}You are {age} years old and live in {city}\n"
    )
    if profile_output != expected_profile:
        errors.append("Exercise 10: output does not match the expected profile flow.")

    for exercise_no in range(1, 11):
        explanation_tag = f"explanation{exercise_no}"
        try:
            explanation = get_explanation_cell(EX005_NOTEBOOK_PATH, tag=explanation_tag)
        except AssertionError:
            errors.append(f"Exercise {exercise_no}: explanation is missing.")
            continue
        if not is_valid_explanation(
            explanation,
            min_length=EX005_MIN_EXPLANATION_LENGTH,
            placeholder_phrases=EX005_PLACEHOLDER_PHRASES,
        ):
            errors.append(f"Exercise {exercise_no}: explanation needs more detail.")

    return errors


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
    output = run_cell_and_capture_output(notebook_path, tag=_exercise_tag(exercise_no))
    expected = EX006_EXPECTED_OUTPUTS[exercise_no]
    if output != expected:
        errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")
    return errors


def _check_ex006_input_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex006_notebook_path()
    details = EX006_INPUT_EXPECTATIONS[exercise_no]
    inputs = details["inputs"]
    output = run_cell_with_input(notebook_path, tag=_exercise_tag(exercise_no), inputs=inputs)
    prompt_contains = details["prompt_contains"]
    output_contains = details.get("output_contains")
    last_line = details.get("last_line")

    if prompt_contains not in output:
        errors.append(f"Exercise {exercise_no}: prompt text is missing.")
    if output_contains is not None and output_contains not in output:
        errors.append(f"Exercise {exercise_no}: expected message is missing.")
    if last_line is not None:
        last_output_line = output.strip().splitlines()[-1]
        if last_output_line != last_line:
            errors.append(f"Exercise {exercise_no}: expected last line '{last_line}'.")
    return errors


def _resolve_ex006_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX006_NOTEBOOK_PATH))


@dataclass(frozen=True)
class Ex006CheckDefinition:
    """Defines a detailed student-friendly ex006 check."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


def _build_ex006_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> Ex006CheckDefinition:
    return Ex006CheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


def _build_ex006_checks() -> list[Ex006CheckDefinition]:
    checks: list[Ex006CheckDefinition] = []
    exercise_numbers = sorted(set(EX006_EXPECTED_OUTPUTS) | set(EX006_INPUT_EXPECTATIONS))
    for exercise_no in exercise_numbers:
        if exercise_no in EX006_EXPECTED_OUTPUTS:
            checks.append(
                _build_ex006_check(exercise_no, "Static output", _check_ex006_static_output)
            )
        if exercise_no in EX006_INPUT_EXPECTATIONS:
            checks.append(_build_ex006_check(exercise_no, "Prompt flow", _check_ex006_input_flow))
    return checks


_EX006_CHECKS: list[Ex006CheckDefinition] = _build_ex006_checks()


def _check_ex004_outputs() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX004_EXPECTED_SINGLE_LINE.items():
        output = run_cell_and_capture_output(EX004_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != f"{expected}\n":
            errors.append(f"Exercise {exercise_no}: expected '{expected}'.")

    exercise7 = run_cell_with_input(EX004_NOTEBOOK_PATH, tag=_exercise_tag(7), inputs=["5"])
    if EX004_PROMPT_STRINGS[7] not in exercise7 or EX004_FORMAT_VALIDATION[7] not in exercise7:
        errors.append("Exercise 7: output does not match the expected prompt or total.")

    exercise8 = run_cell_with_input(EX004_NOTEBOOK_PATH, tag=_exercise_tag(8), inputs=["Alice"])
    expected8 = f"{EX004_PROMPT_STRINGS[8]} {EX004_FORMAT_VALIDATION[8]}\n"
    if exercise8 != expected8:
        errors.append("Exercise 8: output does not match the expected greeting.")

    exercise10 = run_cell_with_input(EX004_NOTEBOOK_PATH, tag=_exercise_tag(10), inputs=["Blue"])
    expected10 = f"{EX004_PROMPT_STRINGS[10]} {EX004_FORMAT_VALIDATION[10]}\n"
    if exercise10 != expected10:
        errors.append("Exercise 10: output does not match the expected response.")

    return errors


def _check_ex004_explanations() -> list[str]:
    errors: list[str] = []
    for exercise_no in range(1, 11):
        explanation_tag = f"explanation{exercise_no}"
        try:
            explanation = get_explanation_cell(EX004_NOTEBOOK_PATH, tag=explanation_tag)
        except AssertionError:
            errors.append(f"Exercise {exercise_no}: explanation is missing.")
            continue
        if not is_valid_explanation(
            explanation,
            min_length=EX004_MIN_EXPLANATION_LENGTH,
            placeholder_phrases=EX004_PLACEHOLDER_PHRASES,
        ):
            errors.append(f"Exercise {exercise_no}: explanation needs more detail.")

    return errors


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"
