"""Tests for ex002 sequence modify basics."""

from __future__ import annotations

import pytest

from tests.exercise_expectations.ex002_sequence_modify_basics_exercise_expectations import (
    EX002_CHECKS,
    Ex002CheckDefinition,
)


def _check_id(check: Ex002CheckDefinition) -> str:
    slug = check.title.lower().replace(" ", "-")
    return f"exercise{check.exercise_no}-{slug}"


def _check_mark(check: Ex002CheckDefinition) -> pytest.MarkDecorator:
    return pytest.mark.task(
        name=f"Exercise {check.exercise_no}: {check.title}",
        taskno=check.exercise_no,
    )


@pytest.mark.parametrize(
    "check",
    [pytest.param(check, id=_check_id(check), marks=_check_mark(check)) for check in EX002_CHECKS],
)
def test_ex002_check_definitions(check: Ex002CheckDefinition) -> None:
    errors = check.check()
    assert errors == [], "; ".join(errors)
