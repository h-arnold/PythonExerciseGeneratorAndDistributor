from __future__ import annotations

from tests.notebook_grader import exec_tagged_code


def test_example_returns_string() -> None:
    ns = exec_tagged_code("notebooks/ex001_sanity.ipynb", tag="exercise1")
    assert "example" in ns
    result = ns["example"]()
    assert isinstance(result, str)
    assert result != ""
