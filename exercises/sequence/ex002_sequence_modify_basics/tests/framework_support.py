"""Exercise-local framework checks for ex002 sequence modify basics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from exercise_runtime_support.exercise_framework import assertions, constructs, runtime
from exercise_runtime_support.exercise_framework.expectations import (
    expected_output_lines as _expected_output_lines,
)
from exercise_runtime_support.exercise_framework.expectations import (
    expected_output_text as _expected_output_text,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex002_sequence_modify_basics"
ex002 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


@dataclass(frozen=True)
class Ex002CheckDefinition:
    """Defines a student-friendly check for an ex002 exercise."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _check_logic(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = runtime.run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_exercise_tag(exercise_no),
    )

    expected_text = _expected_output_text(
        exercise_no,
        single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
        multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
    )
    if expected_text is None:
        errors.append(f"Exercise {exercise_no}: no expected output configured.")
        return errors

    if output != expected_text:
        expected_lines = _expected_output_lines(
            exercise_no,
            single_line=ex002.EX002_EXPECTED_SINGLE_LINE,
            multi_line=ex002.EX002_EXPECTED_MULTI_LINE,
        )
        expected_summary = " | ".join(expected_lines or [])
        errors.append(f"Exercise {exercise_no}: expected '{expected_summary}'.")
    return errors


def _check_formatting(exercise_no: int) -> list[str]:
    expected_calls = ex002.EX002_EXPECTED_PRINT_CALLS.get(exercise_no)
    if expected_calls is None:
        return []

    output = runtime.run_cell_and_capture_output(
        _EXERCISE_KEY,
        tag=_exercise_tag(exercise_no),
    )
    actual_calls = len(output.splitlines())
    if actual_calls != expected_calls:
        return [f"Exercise {exercise_no}: expected {expected_calls} print calls."]
    return []


def _check_construct(exercise_no: int) -> list[str]:
    errors: list[str] = []
    code = runtime.extract_tagged_code(
        _EXERCISE_KEY,
        tag=_exercise_tag(exercise_no),
    )
    has_print = constructs.check_has_print_statement(code)
    errors.extend(
        assertions.assert_has_print_statement(
            exercise_no=exercise_no,
            has_print=has_print,
        )
    )

    operator_expectations: dict[int, str] = {
        3: "*",
        5: "/",
        8: "*",
        9: "-",
    }
    operator = operator_expectations.get(exercise_no)
    if operator:
        uses_operator = constructs.check_uses_operator(code, operator=operator)
        errors.extend(
            assertions.assert_uses_operator(
                exercise_no=exercise_no,
                operator=operator,
                used=uses_operator,
            )
        )

    return errors


def _build_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> Ex002CheckDefinition:
    return Ex002CheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


EX002_CHECKS: list[Ex002CheckDefinition] = [
    check
    for exercise_no in range(1, 11)
    for check in (
        _build_check(exercise_no, "Logic", _check_logic),
        _build_check(exercise_no, "Formatting", _check_formatting),
        _build_check(exercise_no, "Construct", _check_construct),
    )
]
