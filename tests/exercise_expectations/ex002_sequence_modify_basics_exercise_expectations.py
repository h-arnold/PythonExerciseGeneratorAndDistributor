"""Expectations for ex002 sequence modify basics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Final

from tests.notebook_grader import extract_tagged_code, run_cell_and_capture_output

EX002_NOTEBOOK_PATH: Final[str] = "notebooks/ex002_sequence_modify_basics.ipynb"
EX002_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "Hello Python!",
    2: "I go to Bassaleg School",
    3: "15",
    4: "Good Morning Everyone",
    5: "5.0",
    7: "The result is 100",
    8: "24",
    10: "Welcome to Python programming!",
}
EX002_EXPECTED_MULTI_LINE: Final[dict[int, list[str]]] = {
    6: ["Learning", "to", "code rocks"],
    9: ["10 minus 3 equals", "7"],
}
EX002_EXPECTED_NUMERIC: Final[dict[int, int | float]] = {
    3: int(EX002_EXPECTED_SINGLE_LINE[3]),
    5: float(EX002_EXPECTED_SINGLE_LINE[5]),
    8: int(EX002_EXPECTED_SINGLE_LINE[8]),
    9: int(EX002_EXPECTED_MULTI_LINE[9][1]),
}
EX002_EXPECTED_PRINT_CALLS: Final[dict[int, int]] = {
    4: 1,
    6: 3,
    9: 2,
}


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
    output = run_cell_and_capture_output(
        EX002_NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )

    if exercise_no in EX002_EXPECTED_SINGLE_LINE:
        expected = EX002_EXPECTED_SINGLE_LINE[exercise_no]
        if output != f"{expected}\n":
            errors.append(f"Exercise {exercise_no}: expected '{expected}'.")
        return errors

    expected_lines = EX002_EXPECTED_MULTI_LINE.get(exercise_no)
    if expected_lines is None:
        errors.append(f"Exercise {exercise_no}: no expected output configured.")
        return errors

    actual_lines = output.splitlines()
    if actual_lines != expected_lines:
        expected_text = " | ".join(expected_lines)
        errors.append(f"Exercise {exercise_no}: expected '{expected_text}'.")
    return errors


def _check_formatting(exercise_no: int) -> list[str]:
    expected_calls = EX002_EXPECTED_PRINT_CALLS.get(exercise_no)
    if expected_calls is None:
        return []

    output = run_cell_and_capture_output(
        EX002_NOTEBOOK_PATH,
        tag=_exercise_tag(exercise_no),
    )
    actual_calls = len(output.splitlines())
    if actual_calls != expected_calls:
        return [(f"Exercise {exercise_no}: expected {expected_calls} print calls.")]
    return []


def _check_construct(exercise_no: int) -> list[str]:
    errors: list[str] = []
    code = extract_tagged_code(EX002_NOTEBOOK_PATH, tag=_exercise_tag(exercise_no))
    if "print(" not in code:
        errors.append(f"Exercise {exercise_no}: expected a print statement.")

    operator_expectations: dict[int, str] = {
        3: "*",
        5: "/",
        8: "*",
        9: "-",
    }
    operator = operator_expectations.get(exercise_no)
    if operator and operator not in code:
        errors.append(f"Exercise {exercise_no}: expected to use '{operator}' in the calculation.")

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
