"""Expectation helpers for exercise checks."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Final

from tests.exercise_expectations import (
    EX002_EXPECTED_MULTI_LINE,
    EX002_EXPECTED_PRINT_CALLS,
    EX002_EXPECTED_SINGLE_LINE,
)
from tests.exercise_expectations import (
    EX002_NOTEBOOK_PATH as EX002_NOTEBOOK_PATH_VALUE,
)

from . import assertions, constructs, paths, runtime


@dataclass(frozen=True)
class Ex002CheckDefinition:
    """Defines a student-friendly check for an ex002 exercise."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


def expected_output_lines(
    exercise_no: int,
    *,
    single_line: Mapping[int, str],
    multi_line: Mapping[int, Sequence[str]],
) -> list[str] | None:
    """Return expected output lines for an exercise, or None when missing."""
    if exercise_no in single_line:
        return [single_line[exercise_no]]
    if exercise_no in multi_line:
        return list(multi_line[exercise_no])
    return None


def expected_output_text(
    exercise_no: int,
    *,
    single_line: Mapping[int, str],
    multi_line: Mapping[int, Sequence[str]],
) -> str | None:
    """Return expected output text with trailing newline, or None when missing."""
    lines = expected_output_lines(
        exercise_no,
        single_line=single_line,
        multi_line=multi_line,
    )
    if lines is None:
        return None
    return "\n".join(lines) + "\n"


def expected_print_call_count(
    exercise_no: int,
    *,
    expectations: Mapping[int, int],
) -> int | None:
    """Return expected print-call count, or None when not defined."""
    return expectations.get(exercise_no)


def _exercise_tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


EX002_NOTEBOOK_PATH: Final[str] = EX002_NOTEBOOK_PATH_VALUE


def _resolve_ex002_notebook_path() -> Path:
    return paths.resolve_notebook_path(EX002_NOTEBOOK_PATH)


def _check_logic(exercise_no: int) -> list[str]:
    errors: list[str] = []
    output = runtime.run_cell_and_capture_output(
        _resolve_ex002_notebook_path(),
        tag=_exercise_tag(exercise_no),
    )

    expected_text = expected_output_text(
        exercise_no,
        single_line=EX002_EXPECTED_SINGLE_LINE,
        multi_line=EX002_EXPECTED_MULTI_LINE,
    )
    if expected_text is None:
        errors.append(f"Exercise {exercise_no}: no expected output configured.")
        return errors

    if output != expected_text:
        expected_lines = expected_output_lines(
            exercise_no,
            single_line=EX002_EXPECTED_SINGLE_LINE,
            multi_line=EX002_EXPECTED_MULTI_LINE,
        )
        expected_summary = " | ".join(expected_lines or [])
        errors.append(f"Exercise {exercise_no}: expected '{expected_summary}'.")
    return errors


def _check_formatting(exercise_no: int) -> list[str]:
    expected_calls = expected_print_call_count(
        exercise_no,
        expectations=EX002_EXPECTED_PRINT_CALLS,
    )
    if expected_calls is None:
        return []

    output = runtime.run_cell_and_capture_output(
        _resolve_ex002_notebook_path(),
        tag=_exercise_tag(exercise_no),
    )
    actual_calls = len(output.splitlines())
    if actual_calls != expected_calls:
        return [f"Exercise {exercise_no}: expected {expected_calls} print calls."]
    return []


def _check_construct(exercise_no: int) -> list[str]:
    errors: list[str] = []
    code = runtime.extract_tagged_code(
        _resolve_ex002_notebook_path(),
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


EX002_CHECKS: Final[list[Ex002CheckDefinition]] = [
    check
    for exercise_no in range(1, 11)
    for check in (
        _build_check(exercise_no, "Logic", _check_logic),
        _build_check(exercise_no, "Formatting", _check_formatting),
        _build_check(exercise_no, "Construct", _check_construct),
    )
]
