from __future__ import annotations

import pytest

from tests.notebook_grader import run_cell_with_input, run_cell_and_capture_output

NOTEBOOK_PATH = "notebooks/ex006_sequence_modify_casting.ipynb"


@pytest.mark.task(taskno=1)
def test_exercise1_adds_one() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise1", inputs=["14"])
    assert "Enter your age:" in output
    assert output.endswith("Next year you will be 15\n")


@pytest.mark.task(taskno=2)
def test_exercise2_price_times_quantity() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise2", inputs=["2.5", "3"])
    assert "Enter the unit price:" in output
    assert "Enter the quantity:" in output
    assert output.endswith("Total cost: 7.5\n")


@pytest.mark.task(taskno=3)
def test_exercise3_boolean_from_numeric() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise3", inputs=["1"])
    assert "Enter 1 if raining, 0 otherwise:" in output
    assert output.endswith("Take an umbrella: True\n")


@pytest.mark.task(taskno=4)
def test_exercise4_next_year() -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag="exercise4")
    assert output.strip() == "Next year will be 2027"


@pytest.mark.task(taskno=5)
def test_exercise5_c_to_f() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise5", inputs=["20"])
    assert "Enter temperature in C:" in output
    assert output.endswith("Temperature in F: 68.0\n")


@pytest.mark.task(taskno=6)
def test_exercise6_phone_assembly() -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag="exercise6")
    assert output.strip() == "Your phone number is 12-345678"


@pytest.mark.task(taskno=7)
def test_exercise7_total_pounds() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise7", inputs=["4", "150"])
    assert "Enter quantity:" in output
    assert "Enter price in pence (e.g. 150):" in output
    assert output.endswith("Total in pounds: 6.0\n")


@pytest.mark.task(taskno=8)
def test_exercise8_member_yes() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise8", inputs=["yes"])
    assert "Are you a member? (yes/no)" in output
    assert output.endswith("Access granted: True\n")


@pytest.mark.task(taskno=9)
def test_exercise9_average() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise9", inputs=["3", "4"])
    assert "Enter first number:" in output
    assert "Enter second number:" in output
    assert output.endswith("Average: 3.5\n")


@pytest.mark.task(taskno=10)
def test_exercise10_final_total() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise10", inputs=["2", "25.0", "10"])
    assert "Enter number of items:" in output
    assert "Enter price per item:" in output
    assert "Enter tax percent (e.g. 5):" in output
    assert output.endswith("Total: 55.0\n")


@pytest.mark.parametrize("exercise_no", range(1, 11))
@pytest.mark.task(taskno=0)
def test_exercise_cells_execute(exercise_no: int) -> None:
    # Ensure every tagged cell executes (use either input or capture helper)
    tag = f"exercise{exercise_no}"
    # For cells requiring input, provide a reasonable default set of values
    if exercise_no in {1, 2, 3, 5, 7, 8, 9, 10}:
        # Provide two or three inputs for those that ask; extra inputs are ignored
        sample_inputs = ["1", "2", "3"]
        output = run_cell_with_input(NOTEBOOK_PATH, tag=tag, inputs=sample_inputs)
    else:
        output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)
    assert output is not None


import json
import re
from pathlib import Path


def test_only_expected_exercise_tags_in_notebook() -> None:
    """Ensure only exercise1..exercise10 appear as code-cell tags in the notebook."""
    nb = json.loads(Path(NOTEBOOK_PATH).read_text(encoding="utf-8"))
    found: set[str] = set()
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        meta = cell.get("metadata", {})
        for tag in meta.get("tags", []) or []:
            if re.fullmatch(r"^exercise\d+$", tag):
                found.add(tag)

    expected = {f"exercise{i}" for i in range(1, 11)}
    assert found == expected, f"Unexpected exercise tags found: {sorted(found)}"
