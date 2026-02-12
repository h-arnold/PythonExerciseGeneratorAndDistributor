from __future__ import annotations

from tests.exercise_framework import exec_tagged_code, resolve_notebook_path
from tests.notebooks.ex001_sanity import expectations as ex001

_NOTEBOOK_PATH = resolve_notebook_path(ex001.EX001_NOTEBOOK_PATH)


def test_example_returns_string() -> None:
    ns = exec_tagged_code(_NOTEBOOK_PATH, tag=ex001.EX001_TAG)
    assert ex001.EX001_FUNCTION_NAME in ns
    result = ns[ex001.EX001_FUNCTION_NAME]()
    assert isinstance(result, str)
    assert result != ""
