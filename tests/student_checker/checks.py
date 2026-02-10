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

from .models import Ex002CheckResult, Ex006CheckResult, ExerciseCheckResult


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
    output = run_cell_and_capture_output(notebook_path, tag=_exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _check_ex003_prompt_flow(exercise_no: int) -> list[str]:
    errors: list[str] = []
    notebook_path = _resolve_ex003_notebook_path()
    inputs = _EX003_PROMPT_FLOW_INPUTS[exercise_no]
    output = run_cell_with_input(
        notebook_path,
        tag=_exercise_tag(exercise_no),
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


def check_ex004() -> list[str]:
    """Run checks for ex004."""
    return [issue for result in run_ex004_checks() for issue in result.issues]


def run_ex004_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex004."""
    results: list[ExerciseCheckResult] = []
    for check in _EX004_CHECKS:
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
    output = run_cell_and_capture_output(notebook_path, tag=_exercise_tag(exercise_no))
    if output != f"{expected}\n":
        errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
    return errors


def _validate_ex004_prompt_7(notebook_path: str) -> list[str]:
    output = run_cell_with_input(notebook_path, tag=_exercise_tag(7), inputs=["5"])
    if EX004_PROMPT_STRINGS[7] not in output or EX004_FORMAT_VALIDATION[7] not in output:
        return ["Exercise 7: output does not match the expected prompt or total."]
    return []


def _validate_ex004_prompt_8(notebook_path: str) -> list[str]:
    output = run_cell_with_input(notebook_path, tag=_exercise_tag(8), inputs=["Alice"])
    expected = f"{EX004_PROMPT_STRINGS[8]} {EX004_FORMAT_VALIDATION[8]}\n"
    if output != expected:
        return ["Exercise 8: output does not match the expected greeting."]
    return []


def _validate_ex004_prompt_10(notebook_path: str) -> list[str]:
    output = run_cell_with_input(notebook_path, tag=_exercise_tag(10), inputs=["Blue"])
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
    return _check_explanation_cell(
        _resolve_ex004_notebook_path(),
        exercise_no,
        EX004_MIN_EXPLANATION_LENGTH,
        EX004_PLACEHOLDER_PHRASES,
    )


def check_ex005() -> list[str]:
    """Run checks for ex005."""
    return [issue for result in run_ex005_checks() for issue in result.issues]


def run_ex005_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex005."""
    results: list[ExerciseCheckResult] = []
    for check in _EX005_CHECKS:
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
    output = run_cell_and_capture_output(notebook_path, tag=_exercise_tag(exercise_no))
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
            tag=_exercise_tag(exercise_no),
            inputs=inputs,
        )
        prompt_first, prompt_second = EX005_INPUT_PROMPTS[exercise_no]
        first, last = inputs
        expected = f"{prompt_first}{prompt_second}{first} {last}\n"
        if output != expected:
            errors.append("Exercise 5: output does not match the expected full name flow.")
    elif exercise_no == EX005_PROFILE_EXERCISE:
        inputs = EX005_EXERCISE_INPUTS[exercise_no]
        output = run_cell_with_input(
            notebook_path,
            tag=_exercise_tag(exercise_no),
            inputs=inputs,
        )
        profile_prompt_first, profile_prompt_second = EX005_INPUT_PROMPTS[exercise_no]
        age, city = inputs
        expected = f"{profile_prompt_first}{profile_prompt_second}You are {age} years old and live in {city}\n"
        if output != expected:
            errors.append("Exercise 10: output does not match the expected profile flow.")
    return errors


def _check_ex005_explanation(exercise_no: int) -> list[str]:
    return _check_explanation_cell(
        _resolve_ex005_notebook_path(),
        exercise_no,
        EX005_MIN_EXPLANATION_LENGTH,
        EX005_PLACEHOLDER_PHRASES,
    )


def _check_explanation_cell(
    notebook_path: str,
    exercise_no: int,
    min_length: int,
    placeholder_phrases: tuple[str, ...],
) -> list[str]:
    try:
        explanation = get_explanation_cell(notebook_path, tag=f"explanation{exercise_no}")
    except AssertionError:
        return [f"Exercise {exercise_no}: explanation is missing."]
    if not is_valid_explanation(
        explanation,
        min_length=min_length,
        placeholder_phrases=placeholder_phrases,
    ):
        return [f"Exercise {exercise_no}: explanation needs more detail."]
    return []


def _resolve_ex004_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX004_NOTEBOOK_PATH))


def _resolve_ex005_notebook_path() -> str:
    return str(resolve_framework_notebook_path(EX005_NOTEBOOK_PATH))


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
class ExerciseCheckDefinition:
    """Defines a single detailed exercise check."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


@dataclass(frozen=True)
class Ex006CheckDefinition(ExerciseCheckDefinition):
    """Defines a detailed student-friendly ex006 check."""


def _build_exercise_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> ExerciseCheckDefinition:
    return ExerciseCheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


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


def _build_ex003_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    exercise_numbers = sorted(set(EX003_EXPECTED_STATIC_OUTPUT) | set(_EX003_PROMPT_FLOW_INPUTS))
    for exercise_no in exercise_numbers:
        if exercise_no in EX003_EXPECTED_STATIC_OUTPUT:
            checks.append(
                _build_exercise_check(exercise_no, "Static output", _check_ex003_static_output)
            )
        if exercise_no in _EX003_PROMPT_FLOW_INPUTS:
            checks.append(
                _build_exercise_check(exercise_no, "Prompt flow", _check_ex003_prompt_flow)
            )
    return checks


def _build_ex004_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    prompt_exercises = {7, 8, 10}
    for exercise_no in range(1, 11):
        if exercise_no in EX004_EXPECTED_SINGLE_LINE:
            checks.append(
                _build_exercise_check(exercise_no, "Static output", _check_ex004_static_output)
            )
        if exercise_no in prompt_exercises:
            checks.append(
                _build_exercise_check(exercise_no, "Prompt flow", _check_ex004_prompt_flow)
            )
        checks.append(_build_exercise_check(exercise_no, "Explanation", _check_ex004_explanation))
    return checks


def _build_ex005_checks() -> list[ExerciseCheckDefinition]:
    checks: list[ExerciseCheckDefinition] = []
    prompt_exercises = {EX005_FULL_NAME_EXERCISE, EX005_PROFILE_EXERCISE}
    for exercise_no in range(1, 11):
        if exercise_no in EX005_EXPECTED_SINGLE_LINE:
            checks.append(
                _build_exercise_check(exercise_no, "Static output", _check_ex005_static_output)
            )
        if exercise_no in prompt_exercises:
            checks.append(
                _build_exercise_check(exercise_no, "Prompt flow", _check_ex005_prompt_flow)
            )
        checks.append(_build_exercise_check(exercise_no, "Explanation", _check_ex005_explanation))
    return checks


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


_EX003_CHECKS: list[ExerciseCheckDefinition] = _build_ex003_checks()
_EX004_CHECKS: list[ExerciseCheckDefinition] = _build_ex004_checks()
_EX005_CHECKS: list[ExerciseCheckDefinition] = _build_ex005_checks()
_EX006_CHECKS: list[Ex006CheckDefinition] = _build_ex006_checks()


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"
