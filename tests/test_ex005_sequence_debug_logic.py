from __future__ import annotations

import json

import pytest

from tests.notebook_grader import exec_tagged_code, resolve_notebook_path

EXPECTED = {
    "exercise1": "Hi there!",
    "exercise2": "I enjoy coding lessons.",
    "exercise3": "My favourite food is sushi",
    "exercise4": "Type the name of your favourite fruit:\nI like mango",
    "exercise5": "Which town do you like the most?\nI would visit Cardiff",
    "exercise6": "Please enter your name:\nWelcome, Alex!",
    "exercise7": "Variables matter",
    "exercise8": "Keep experimenting",
    "exercise9": "Good evening everyone!",
    "exercise10": "Variables and strings make a message!",
}

MIN_EXPLANATION_LENGTH = 10


@pytest.mark.parametrize("tag", list(EXPECTED.keys()))
def test_exercise_cells_run(tag: str) -> None:
    ns = exec_tagged_code(
        "notebooks/ex005_sequence_debug_logic.ipynb", tag=tag)
    assert "solve" in ns, "Student cell must define solve()"
    assert ns["solve"]() == EXPECTED[tag]


# Explanation cell checks for debug exercises
def _get_explanation(notebook_path: str, tag: str = "explanation1") -> str:
    path = resolve_notebook_path(notebook_path)
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            return "".join(cell.get("source", []))
    raise AssertionError(f"No explanation cell with tag {tag}")


PLACEHOLDER = "### What actually happened\nDescribe briefly what happened when you ran the code (include any error messages or incorrect output)."
TAGS = [f"explanation{i}" for i in range(1, 10 + 1)]


@pytest.mark.parametrize("tag", TAGS)
def test_explanations_have_content(tag: str) -> None:
    explanation = _get_explanation(
        "notebooks/ex005_sequence_debug_logic.ipynb", tag=tag)
    assert len(explanation.strip(
    )) > MIN_EXPLANATION_LENGTH, f"Explanation must be more than {MIN_EXPLANATION_LENGTH} characters"
    assert explanation.strip() != PLACEHOLDER, (
        "Explanation must be replaced by student with a brief description"
    )
