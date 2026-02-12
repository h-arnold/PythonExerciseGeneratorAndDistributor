"""Checks for the ex001 sanity notebook."""

from __future__ import annotations

from tests.exercise_expectations import EX001_FUNCTION_NAME, EX001_NOTEBOOK_PATH, EX001_TAG
from tests.notebook_grader import exec_tagged_code


def check_ex001() -> list[str]:
    """Run checks for ex001."""
    errors: list[str] = []
    ns = exec_tagged_code(EX001_NOTEBOOK_PATH, tag=EX001_TAG)
    example = ns.get(EX001_FUNCTION_NAME)
    if example is None:
        errors.append("The `example` function is missing.")
        return errors
    if not callable(example):
        errors.append("The `example` function must be callable.")
        return errors
    result = example()
    if not isinstance(result, str):
        errors.append("The `example` function must return a string.")
    elif result == "":
        errors.append("The `example` function should not return an empty string.")
    return errors


__all__ = ["check_ex001"]
