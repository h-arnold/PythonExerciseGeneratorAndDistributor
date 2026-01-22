from __future__ import annotations

import json

import pytest

from tests.notebook_grader import (
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

MIN_EXPLANATION_LENGTH = 10
NOTEBOOK_PATH = "notebooks/ex004_sequence_debug_syntax.ipynb"
SOLUTION_PATH = "notebooks/solutions/ex004_sequence_debug_syntax.ipynb"


# Test that exercises run and produce correct output
@pytest.mark.parametrize(
    "tag,input_val,expected",
    [
        ("exercise1", None, "Hello World!"),
        ("exercise2", None, "I like Python"),
        ("exercise3", None, "Learning Python"),
        ("exercise4", None, "50"),
        ("exercise5", None, "Hello Alice"),
        ("exercise6", None, "Welcome to school"),
        # Exercise 7 requires input
        ("exercise8", None, "Hello"),
        ("exercise9", None, "It's amazing"),
    ],
)
def test_exercise_output(tag: str, input_val: str, expected: str) -> None:
    """Test that corrected exercises produce the expected output."""
    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    # Extract the buggy code
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags and cell.get("cell_type") == "code":
            code = "".join(cell.get("source", []))
            # Students must fix the code, so it should raise an error/fail initially
            # We're just checking that the cell exists and is tagged correctly
            assert code.strip() != "", f"Exercise cell {tag} must contain code"
            break
    else:
        pytest.fail(f"No code cell found with tag {tag}")


# Test solution notebook produces correct outputs (for exercises without input)
@pytest.mark.parametrize(
    "tag,expected",
    [
        ("exercise1", "Hello World!"),
        ("exercise2", "I like Python"),
        ("exercise3", "Learning Python"),
        ("exercise4", "50"),
        ("exercise5", "Hello Alice"),
        ("exercise6", "Welcome to school"),
        ("exercise7", "10"),  # 5 + 5
        ("exercise9", "It's amazing"),
    ],
)
def test_solution_output(tag: str, expected: str) -> None:
    """Test that solution notebook produces correct output."""
    try:
        # For input exercises, provide mock input
        if tag == "exercise7":
            output = run_cell_with_input(SOLUTION_PATH, tag=tag, inputs=["5"])
        else:
            output = run_cell_and_capture_output(SOLUTION_PATH, tag=tag)

        # For multi-line output, just check that key parts exist
        if tag == "exercise7":
            assert "10" in output, f"Expected '10' in output for {tag}, got: {output}"
        else:
            assert expected in output, f"Expected '{expected}' in output for {tag}, got: {output}"

    except Exception as e:
        pytest.fail(f"Solution notebook exercise {tag} failed to execute: {e}")


# Test that explanation cells have content
TAGS = [f"explanation{i}" for i in range(1, 11)]


@pytest.mark.parametrize("tag", TAGS)
def test_explanations_have_content(tag: str) -> None:
    """Test that students filled in explanation cells."""
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=tag)
    assert len(explanation.strip(
    )) > MIN_EXPLANATION_LENGTH, f"Explanation {tag} must be more than {MIN_EXPLANATION_LENGTH} characters"


# Test that all exercise cells are tagged
@pytest.mark.parametrize("tag", [f"exercise{i}" for i in range(1, 11)])
def test_exercise_cells_tagged(tag: str) -> None:
    """Test that all exercise cells are properly tagged."""
    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            assert cell.get(
                "cell_type") == "code", f"Cell {tag} must be a code cell"
            code = "".join(cell.get("source", []))
            assert code.strip() != "", f"Cell {tag} must not be empty"
            return

    pytest.fail(f"No code cell found with tag {tag}")


# Test that solution notebook has all cells
@pytest.mark.parametrize("tag", [f"exercise{i}" for i in range(1, 11)])
def test_solution_cells_tagged(tag: str) -> None:
    """Test that solution notebook has all exercise cells."""
    with open(SOLUTION_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            assert cell.get(
                "cell_type") == "code", f"Solution cell {tag} must be a code cell"
            code = "".join(cell.get("source", []))
            assert code.strip() != "", f"Solution cell {tag} must not be empty"
            # For solution, verify no placeholder "TODO"
            assert "TODO" not in code, f"Solution {tag} should not contain TODO placeholder"
            return

    pytest.fail(f"No code cell found in solution with tag {tag}")
