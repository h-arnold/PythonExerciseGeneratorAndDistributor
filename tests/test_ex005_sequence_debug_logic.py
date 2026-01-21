from __future__ import annotations

import json

import pytest

from tests.notebook_grader import exec_tagged_code, resolve_notebook_path


def _get_explanation(notebook_path: str, tag: str) -> str:
    """Extract explanation text from a notebook cell by tag."""
    nb_path = resolve_notebook_path(notebook_path)
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            source = cell.get("source", [])
            if isinstance(source, list):
                return "".join(source)
            return source
    raise AssertionError(f"No cell with tag {tag} found in notebook")


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("exercise1", "Hello world"),
        ("exercise2", "Good morning"),
        ("exercise3", "Python is fun"),
        ("exercise4", "I like cheese pizza"),
        ("exercise5", "The answer is 42"),
        ("exercise6", "Welcome to Python!"),
        ("exercise7", "Jane is 16 years old"),
        ("exercise8", "Learning to code is exciting!"),
        ("exercise9", "3 plus 7 equals 10"),
        ("exercise10", "I love pizza and coding"),
    ],
)
def test_exercise_returns_correct_value(tag: str, expected: str) -> None:
    """Test that each exercise's result variable has the expected value."""
    ns = exec_tagged_code(
        "notebooks/ex005_sequence_debug_logic.ipynb", tag=tag)
    assert "result" in ns, f"Exercise cell must define variable 'result' in {tag}"
    assert ns["result"] == expected, f"{tag}: Expected '{expected}', got '{ns['result']}'"


@pytest.mark.parametrize(
    "tag,explanation_tag",
    [
        ("exercise1", "explanation1"),
        ("exercise2", "explanation2"),
        ("exercise3", "explanation3"),
        ("exercise4", "explanation4"),
        ("exercise5", "explanation5"),
        ("exercise6", "explanation6"),
        ("exercise7", "explanation7"),
        ("exercise8", "explanation8"),
        ("exercise9", "explanation9"),
        ("exercise10", "explanation10"),
    ],
)
def test_explanation_has_content(tag: str, explanation_tag: str) -> None:
    """Test that each exercise has a meaningful explanation."""
    explanation = _get_explanation(
        "notebooks/ex005_sequence_debug_logic.ipynb", explanation_tag
    )
    # Explanation must be more than 10 characters of non-whitespace
    assert (
        len(explanation.strip()) > 10
    ), f"{explanation_tag}: Explanation must be more than 10 characters"
