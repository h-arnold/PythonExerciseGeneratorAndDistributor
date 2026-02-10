"""Student-friendly checks for the first six notebooks.

Uses a grid table with emoji status markers for student readability.
This is an intentional exception to the ASCII-only output preference.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

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
from tests.exercise_framework.reporting import (
    normalise_issue_text,
    render_grouped_table_with_errors,
    render_table,
)
from tests.notebook_grader import (
    NotebookGradingError,
    exec_tagged_code,
    get_explanation_cell,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)


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


@dataclass(frozen=True)
class NotebookTagCheckResult:
    """Represents the status of a tagged exercise cell."""

    tag: str
    passed: bool
    message: str


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
        raise ValueError(
            f"Unknown notebook '{notebook_slug}'. Available: {available}")
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
    table = render_table([(label, passed) for label, passed, _ in results])
    print(table)

    failures = [(label, issues)
                for label, passed, issues in results if not passed]
    if not failures:
        print("\nGreat work! Everything that can be checked here looks good.")


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
        errors.append(
            "The `example` function should not return an empty string.")
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
        error_message = "" if result.passed else normalise_issue_text(
            result.issues)
        rows.append((label, result.title, result.passed, error_message))
        last_exercise = result.exercise_no

    table = render_grouped_table_with_errors(rows)
    print(table)

    failures = [result for result in results if not result.passed]
    if not failures:
        print("\nGreat work! Everything that can be checked here looks good.")


def _check_ex003() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX003_EXPECTED_STATIC_OUTPUT.items():
        output = run_cell_and_capture_output(
            EX003_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
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
        errors.append(
            "Exercise 4: output does not match the expected prompt flow.")

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
        errors.append(
            "Exercise 5: output does not match the expected prompt flow.")

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
        errors.append(
            "Exercise 6: output does not match the expected prompt flow.")

    return errors


def _check_ex004() -> list[str]:
    errors: list[str] = []
    errors.extend(_check_ex004_outputs())
    errors.extend(_check_ex004_explanations())
    return errors


def _check_ex004_outputs() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX004_EXPECTED_SINGLE_LINE.items():
        output = run_cell_and_capture_output(
            EX004_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != f"{expected}\n":
            errors.append(f"Exercise {exercise_no}: expected '{expected}'.")

    exercise7 = run_cell_with_input(
        EX004_NOTEBOOK_PATH, tag=_exercise_tag(7), inputs=["5"])
    if EX004_PROMPT_STRINGS[7] not in exercise7 or EX004_FORMAT_VALIDATION[7] not in exercise7:
        errors.append(
            "Exercise 7: output does not match the expected prompt or total.")

    exercise8 = run_cell_with_input(
        EX004_NOTEBOOK_PATH, tag=_exercise_tag(8), inputs=["Alice"])
    expected8 = f"{EX004_PROMPT_STRINGS[8]} {EX004_FORMAT_VALIDATION[8]}\n"
    if exercise8 != expected8:
        errors.append(
            "Exercise 8: output does not match the expected greeting.")

    exercise10 = run_cell_with_input(
        EX004_NOTEBOOK_PATH, tag=_exercise_tag(10), inputs=["Blue"])
    expected10 = f"{EX004_PROMPT_STRINGS[10]} {EX004_FORMAT_VALIDATION[10]}\n"
    if exercise10 != expected10:
        errors.append(
            "Exercise 10: output does not match the expected response.")

    return errors


def _check_ex004_explanations() -> list[str]:
    errors: list[str] = []
    for exercise_no in range(1, 11):
        explanation_tag = f"explanation{exercise_no}"
        try:
            explanation = get_explanation_cell(
                EX004_NOTEBOOK_PATH, tag=explanation_tag)
        except AssertionError:
            errors.append(f"Exercise {exercise_no}: explanation is missing.")
            continue
        if not is_valid_explanation(
            explanation,
            min_length=EX004_MIN_EXPLANATION_LENGTH,
            placeholder_phrases=EX004_PLACEHOLDER_PHRASES,
        ):
            errors.append(
                f"Exercise {exercise_no}: explanation needs more detail.")

    return errors


def _check_ex005() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX005_EXPECTED_SINGLE_LINE.items():
        output = run_cell_and_capture_output(
            EX005_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
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
        errors.append(
            "Exercise 5: output does not match the expected full name flow.")

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
        errors.append(
            "Exercise 10: output does not match the expected profile flow.")

    for exercise_no in range(1, 11):
        explanation_tag = f"explanation{exercise_no}"
        try:
            explanation = get_explanation_cell(
                EX005_NOTEBOOK_PATH, tag=explanation_tag)
        except AssertionError:
            errors.append(f"Exercise {exercise_no}: explanation is missing.")
            continue
        if not is_valid_explanation(
            explanation,
            min_length=EX005_MIN_EXPLANATION_LENGTH,
            placeholder_phrases=EX005_PLACEHOLDER_PHRASES,
        ):
            errors.append(
                f"Exercise {exercise_no}: explanation needs more detail.")

    return errors


def _check_ex006() -> list[str]:
    errors: list[str] = []
    for exercise_no, expected in EX006_EXPECTED_OUTPUTS.items():
        output = run_cell_and_capture_output(
            EX006_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
        if output != expected:
            errors.append(
                f"Exercise {exercise_no}: expected '{expected.strip()}'.")

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
            errors.append(
                f"Exercise {exercise_no}: expected message is missing.")
        if last_line is not None:
            last_output_line = output.strip().splitlines()[-1]
            if last_output_line != last_line:
                errors.append(
                    f"Exercise {exercise_no}: expected last line '{last_line}'.")

    return errors


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def run_notebook_checks(notebook_path: str) -> None:
    """Execute each tagged exercise cell and print a friendly status table."""

    resolved_path = resolve_notebook_path(notebook_path)
    tags = _collect_exercise_tags(resolved_path)
    if not tags:
        print(f"No exercise tags found in {resolved_path}.")
        return

    results = _run_notebook_checks(resolved_path, tags)
    _print_notebook_check_results(results)


def _collect_exercise_tags(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotebookGradingError(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NotebookGradingError(
            f"Unable to parse notebook JSON: {path}") from exc

    cells = data.get("cells")
    if not isinstance(cells, list):
        return []

    tags: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        metadata = cell.get("metadata")
        if not isinstance(metadata, dict):
            continue
        cell_tags = metadata.get("tags")
        if isinstance(cell_tags, str):
            cell_tags = [cell_tags]
        if isinstance(cell_tags, list):
            for tag in cell_tags:
                if isinstance(tag, str) and re.fullmatch(r"exercise\d+", tag):
                    tags.append(tag)
    return tags


def _run_notebook_checks(path: Path, tags: list[str]) -> list[NotebookTagCheckResult]:
    results: list[NotebookTagCheckResult] = []
    for tag in tags:
        try:
            run_cell_and_capture_output(str(path), tag=tag)
            results.append(NotebookTagCheckResult(
                tag=tag, passed=True, message=""))
        except NotebookGradingError as exc:
            results.append(NotebookTagCheckResult(
                tag=tag, passed=False, message=str(exc)))
    return results


def _print_notebook_check_results(results: list[NotebookTagCheckResult]) -> None:
    rows = [
        (_format_tag_label(result.tag), result.tag, result.passed, result.message)
        for result in results
    ]
    print(render_grouped_table_with_errors(rows))

    failures = [result for result in results if not result.passed]
    if failures:
        print("\nFix the failing cells above, then re-run this cell.")
    else:
        print("\nGreat work! All exercise cells ran without errors.")


def _format_tag_label(tag: str) -> str:
    match = re.match(r"exercise(\d+)", tag)
    return f"Exercise {match.group(1)}" if match else tag
