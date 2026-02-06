from __future__ import annotations

from tests.exercise_expectations import (
    EX001_FUNCTION_NAME,
    EX001_NOTEBOOK_PATH,
    EX001_TAG,
)
from tests.notebook_grader import exec_tagged_code


def test_example_returns_string() -> None:
    ns = exec_tagged_code(EX001_NOTEBOOK_PATH, tag=EX001_TAG)
    assert EX001_FUNCTION_NAME in ns
    result = ns[EX001_FUNCTION_NAME]()
    assert isinstance(result, str)
    assert result != ""
