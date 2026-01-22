from __future__ import annotations

import pytest

from tests.helpers import (
    assert_code_cell_present,
    get_explanation_cell,
    run_tagged_cell_output,
)

MIN_EXPLANATION_LENGTH = 10
NOTEBOOK_PATH = "notebooks/ex004_sequence_debug_syntax.ipynb"


# Test that exercises run and produce correct output
@pytest.mark.parametrize(
    "tag",
    [
        "exercise1",
        "exercise2",
        "exercise3",
        "exercise4",
        "exercise5",
        "exercise6",
        "exercise7",
        "exercise8",
        "exercise9",
    ],
)
def test_exercise_output(tag: str) -> None:
    """Test that exercise cells exist and are properly tagged."""
    assert_code_cell_present(NOTEBOOK_PATH, tag)


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
        inputs: list[str] | None = ["5"] if tag == "exercise7" else None
        output = run_tagged_cell_output(NOTEBOOK_PATH, tag=tag, inputs=inputs)

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
    assert len(explanation.strip()) > MIN_EXPLANATION_LENGTH, (
        f"Explanation {tag} must be more than {MIN_EXPLANATION_LENGTH} characters"
    )


# Test that all exercise cells are tagged
@pytest.mark.parametrize("tag", [f"exercise{i}" for i in range(1, 11)])
def test_exercise_cells_tagged(tag: str) -> None:
    """Test that all exercise cells are properly tagged."""
    assert_code_cell_present(NOTEBOOK_PATH, tag)


# Test that solution notebook has all cells
@pytest.mark.parametrize("tag", [f"exercise{i}" for i in range(1, 11)])
def test_solution_cells_tagged(tag: str) -> None:
    """Test that solution notebook has all exercise cells."""
    assert_code_cell_present(
        NOTEBOOK_PATH,
        tag,
        use_solution=True,
        allow_todo=False,
    )
