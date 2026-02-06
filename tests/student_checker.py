"""Student-friendly checks for the first six notebooks.

Uses a Unicode box table and emoji status markers for student readability.
This is an intentional exception to the ASCII-only output preference.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

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
    is_valid_explanation,
)
from tests.exercise_expectations.ex002_sequence_modify_basics_exercise_expectations import (
    EX002_CHECKS,
)
from tests.notebook_grader import (
    NotebookGradingError,
    exec_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

PASS_STATUS_LABEL: Final[str] = "🟢 Pass"
FAIL_STATUS_LABEL: Final[str] = "🔴 Fix"
ERROR_COLUMN_WIDTH: Final[int] = 48


@dataclass(frozen=True)
class CheckItem:
    """Represents a notebook check."""

    label: str
    runner: Callable[[], list[str]]


@dataclass(frozen=True)
class Ex002CheckResult:
    """Represents a single ex002 check result."""

    exercise_no: int
    title: str
    passed: bool
    issues: list[str]


def check_exercises() -> None:
    """Run a simple check for exercises 1-6 and print a summary table."""
    results = _run_checks(list(_get_checks().values()))
    _print_results(results)


def check_notebook(notebook_slug: str) -> None:
    """Run a simple check for a single notebook and print a summary table."""
    if notebook_slug == "ex002_sequence_modify_basics":
        check_ex002_notebook()
        return
    checks = _get_checks()
    check = checks.get(notebook_slug)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown notebook '{notebook_slug}'. Available: {available}")
    results = _run_checks([check])
    _print_results(results)


def check_ex002_notebook() -> None:
    """Run the detailed checks for ex002 and print a grouped summary table."""
    results = _run_ex002_checks()
    _print_ex002_results(results)


def _get_checks() -> dict[str, CheckItem]:
    return {
        "ex001_sanity": CheckItem("ex001 Sanity", _check_ex001),
        "ex002_sequence_modify_basics": CheckItem("ex002 Sequence Modify Basics", _check_ex002),
        "ex003_sequence_modify_variables": CheckItem(
            "ex003 Sequence Modify Variables", _check_ex003
        ),
        "ex004_sequence_debug_syntax": CheckItem("ex004 Debug Syntax Errors", _check_ex004),
        "ex005_sequence_debug_logic": CheckItem("ex005 Debug Logical Errors", _check_ex005),
        "ex006_sequence_modify_casting": CheckItem(
            "ex006 Casting and Type Conversion", _check_ex006
        ),
    }


def _run_checks(checks: list[CheckItem]) -> list[tuple[str, bool, list[str]]]:
    results: list[tuple[str, bool, list[str]]] = []
    for check in checks:
        try:
            issues = check.runner()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append((check.label, len(issues) == 0, issues))
    return results


def _print_results(results: list[tuple[str, bool, list[str]]]) -> None:
    table = _render_table([(label, passed) for label, passed, _ in results])
    print(table)

    failures = [(label, issues) for label, passed, issues in results if not passed]
    if failures:
        print("\nDetails:")
        for label, issues in failures:
            print(f"- {label}:")
            for issue in issues:
                print(f"  - {issue}")
    else:
        print("\nGreat work! Everything that can be checked here looks good.")


def _render_table(rows: list[tuple[str, bool]]) -> str:
    name_width = max(len(label) for label, _ in rows)
    status_width = len(PASS_STATUS_LABEL)

    top = f"┌{'─' * (name_width + 2)}┬{'─' * (status_width + 2)}┐"
    mid = f"├{'─' * (name_width + 2)}┼{'─' * (status_width + 2)}┤"
    bottom = f"└{'─' * (name_width + 2)}┴{'─' * (status_width + 2)}┘"

    lines = [top]
    for index, (label, passed) in enumerate(rows):
        status = PASS_STATUS_LABEL if passed else FAIL_STATUS_LABEL
        lines.append(f"│ {label.ljust(name_width)} │ {status.ljust(status_width)} │")
        if index != len(rows) - 1:
            lines.append(mid)
    lines.append(bottom)
    return "\n".join(lines)


def _render_grouped_table(rows: list[tuple[str, str, bool]]) -> str:
    exercise_width = max(len(label) for label, _, _ in rows)
    check_width = max(len(title) for _, title, _ in rows)
    status_width = len(PASS_STATUS_LABEL)

    top = f"┌{'─' * (exercise_width + 2)}┬{'─' * (check_width + 2)}┬{'─' * (status_width + 2)}┐"
    mid = f"├{'─' * (exercise_width + 2)}┼{'─' * (check_width + 2)}┼{'─' * (status_width + 2)}┤"
    bottom = f"└{'─' * (exercise_width + 2)}┴{'─' * (check_width + 2)}┴{'─' * (status_width + 2)}┘"

    lines = [top]
    for index, (exercise_label, title, passed) in enumerate(rows):
        status = PASS_STATUS_LABEL if passed else FAIL_STATUS_LABEL
        lines.append(
            f"│ {exercise_label.ljust(exercise_width)} "
            f"│ {title.ljust(check_width)} "
            f"│ {status.ljust(status_width)} │"
        )
        if index != len(rows) - 1:
            lines.append(mid)
    lines.append(bottom)
    return "\n".join(lines)


def _strip_exercise_prefix(message: str) -> str:
    match = re.match(r"^Exercise\s+\d+:\s*", message)
    if match:
        return message[match.end() :]
    return message


def _wrap_text_to_width(message: str, width: int) -> list[str]:
    if message == "":
        return [""]
    return textwrap.wrap(
        message,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _render_grouped_table_with_errors(rows: list[tuple[str, str, bool, str]]) -> str:
    exercise_width = max(len(label) for label, _, _, _ in rows)
    check_width = max(len(title) for _, title, _, _ in rows)
    status_width = len(PASS_STATUS_LABEL)
    error_width = ERROR_COLUMN_WIDTH

    top = (
        f"┌{'─' * (exercise_width + 2)}┬{'─' * (check_width + 2)}"
        f"┬{'─' * (status_width + 2)}┬{'─' * (error_width + 2)}┐"
    )
    mid = (
        f"├{'─' * (exercise_width + 2)}┼{'─' * (check_width + 2)}"
        f"┼{'─' * (status_width + 2)}┼{'─' * (error_width + 2)}┤"
    )
    bottom = (
        f"└{'─' * (exercise_width + 2)}┴{'─' * (check_width + 2)}"
        f"┴{'─' * (status_width + 2)}┴{'─' * (error_width + 2)}┘"
    )

    lines = [top]
    rendered_rows: list[tuple[str, str, str, str]] = []
    for exercise_label, title, passed, error in rows:
        status = PASS_STATUS_LABEL if passed else FAIL_STATUS_LABEL
        trimmed_error = _strip_exercise_prefix(error)
        uses_long_word_wrap = any(len(word) > error_width for word in trimmed_error.split())
        if uses_long_word_wrap:
            wrapped_error = textwrap.wrap(
                trimmed_error,
                width=error_width,
                break_long_words=True,
                break_on_hyphens=False,
            )
        else:
            wrapped_error = _wrap_text_to_width(trimmed_error, error_width)
        for index, line in enumerate(wrapped_error):
            if index == 0:
                rendered_rows.append((exercise_label, title, status, line))
            else:
                rendered_rows.append(("", "", "", line))

    for index, (exercise_label, title, status, error) in enumerate(rendered_rows):
        lines.append(
            f"│ {exercise_label.ljust(exercise_width)} "
            f"│ {title.ljust(check_width)} "
            f"│ {status.ljust(status_width)} "
            f"│ {error.ljust(error_width)} │"
        )
        if index != len(rendered_rows) - 1:
            lines.append(mid)
    lines.append(bottom)
    return "\n".join(lines)


def _check_ex001() -> list[str]:
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


def _check_ex002() -> list[str]:
    return [issue for result in _run_ex002_checks() for issue in result.issues]


def _run_ex002_checks() -> list[Ex002CheckResult]:
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


def _print_ex002_results(results: list[Ex002CheckResult]) -> None:
    rows: list[tuple[str, str, bool, str]] = []
    last_exercise: int | None = None
    for result in results:
        label = f"Exercise {result.exercise_no}" if result.exercise_no != last_exercise else ""
        if result.passed:
            error_message = ""
        else:
            stripped = [_strip_exercise_prefix(issue) for issue in result.issues]
            error_message = "; ".join(stripped)
        rows.append((label, result.title, result.passed, error_message))
        last_exercise = result.exercise_no

    table = _render_grouped_table_with_errors(rows)
    print(table)

    failures = [result for result in results if not result.passed]
    if failures:
        print("\nDetails:")
        for result in failures:
            label = f"Exercise {result.exercise_no}: {result.title}"
            print(f"- {label}:")
            for issue in result.issues:
                print(f"  - {_strip_exercise_prefix(issue)}")
    else:
        print("\nGreat work! Everything that can be checked here looks good.")


def _check_ex003() -> list[str]:
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


def _check_ex004() -> list[str]:
    errors: list[str] = []
    errors.extend(_check_ex004_outputs())
    errors.extend(_check_ex004_explanations())
    return errors


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


def _check_ex005() -> list[str]:
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


def _check_ex006() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX006_EXPECTED_OUTPUTS.items():
        output = run_cell_and_capture_output(EX006_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != expected:
            errors.append(f"Exercise {exercise_no}: expected '{expected.strip()}'.")

    for exercise_no, details in EX006_INPUT_EXPECTATIONS.items():
        inputs = details["inputs"]
        output = run_cell_with_input(
            EX006_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no), inputs=inputs
        )
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


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"
