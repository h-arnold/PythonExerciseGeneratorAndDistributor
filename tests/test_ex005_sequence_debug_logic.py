from __future__ import annotations

import json

import pytest

from tests.notebook_grader import (
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

MIN_EXPLANATION_LENGTH = 10
NOTEBOOK_PATH = "notebooks/ex005_sequence_debug_logic.ipynb"
SOLUTION_PATH = "notebooks/solutions/ex005_sequence_debug_logic.ipynb"


# Test that solution notebook produces correct outputs
@pytest.mark.parametrize(
    "tag,expected",
    [
        ("exercise1", "50"),
        ("exercise2", "Alice"),
        ("exercise3", "24"),
        ("exercise4", "Hello World"),
        ("exercise6", "5"),
        ("exercise7", "25.0"),
        ("exercise8", "I love learning Python"),
        ("exercise9", "30"),
    ],
)
def test_solution_output(tag: str, expected: str) -> None:
    """Test that solution notebook produces correct output."""
    try:
        output = run_cell_and_capture_output(SOLUTION_PATH, tag=tag)
        assert (
            expected in output
        ), f"Expected '{expected}' in output for {tag}, got: {output}"

    except Exception as e:
        pytest.fail(f"Solution notebook exercise {tag} failed to execute: {e}")


# Test exercise 5 with input
def test_solution_exercise5_with_input() -> None:
    """Test exercise 5 which requires user input."""
    try:
        output = run_cell_with_input(
            SOLUTION_PATH, tag="exercise5", inputs=["Alice", "Smith"]
        )
        assert "Alice Smith" in output, f"Expected 'Alice Smith' in output, got: {output}"

    except Exception as e:
        pytest.fail(f"Solution notebook exercise5 failed to execute: {e}")


# Test exercise 10 with input
def test_solution_exercise10_with_input() -> None:
    """Test exercise 10 which requires user input."""
    try:
        output = run_cell_with_input(
            SOLUTION_PATH, tag="exercise10", inputs=["15", "London"]
        )
        assert "You are 15 years old and live in London" in output, f"Expected message in output, got: {output}"

    except Exception as e:
        pytest.fail(f"Solution notebook exercise10 failed to execute: {e}")


# Test that explanation cells have content
TAGS = [f"explanation{i}" for i in range(1, 11)]


@pytest.mark.parametrize("tag", TAGS)
def test_explanations_have_content(tag: str) -> None:
    """Test that explanation cells exist in student notebook."""
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=tag)
    # In student notebook, explanations are initially just prompts
    assert (
        len(explanation.strip()) > MIN_EXPLANATION_LENGTH
    ), f"Explanation {tag} must be more than {MIN_EXPLANATION_LENGTH} characters"


# Test that all exercise cells are tagged
@pytest.mark.parametrize("tag", [f"exercise{i}" for i in range(1, 11)])
def test_exercise_cells_tagged(tag: str) -> None:
    """Test that all exercise cells are properly tagged."""
    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            assert cell.get("cell_type") == "code", f"Cell {tag} must be a code cell"
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
            assert (
                cell.get("cell_type") == "code"
            ), f"Solution cell {tag} must be a code cell"
            code = "".join(cell.get("source", []))
            assert code.strip() != "", f"Solution cell {tag} must not be empty"
            return

    pytest.fail(f"No code cell found in solution with tag {tag}")

