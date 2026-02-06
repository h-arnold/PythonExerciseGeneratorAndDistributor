from __future__ import annotations

import json
import re
import sys

import scripts.new_exercise as ne


def _find_tags(cells, tag):
    for cell in cells:
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            return cell
    return None


def test_make_notebook_debug_structure():
    nb = ne._make_notebook_with_parts("Title Debug", parts=2, exercise_type="debug")
    cells = nb["cells"]

    # For each part check we have expected-output, exercise tag and explanation tag
    for i in range(1, 3):
        ex_tag = f"exercise{i}"
        expl_tag = f"explanation{i}"

        # code cell with ex_tag exists
        code_cell = _find_tags(cells, ex_tag)
        assert code_cell is not None, f"Missing code cell tagged {ex_tag}"
        assert code_cell["cell_type"] == "code"

        # markdown explanation cell exists
        expl_cell = _find_tags(cells, expl_tag)
        assert expl_cell is not None, f"Missing explanation cell tagged {expl_tag}"
        assert expl_cell["cell_type"] == "markdown"

        # Expected output markdown exists prior to the code cell
        # Find index of code cell and check previous cell is markdown containing 'Expected output'
        idx = cells.index(code_cell)
        assert idx > 0
        prev_cell = cells[idx - 1]
        assert prev_cell["cell_type"] == "markdown"
        joined = "".join(prev_cell.get("source", []))
        assert "Expected output" in joined


def test_main_creates_debug_files(tmp_path, monkeypatch):
    # Point the module ROOT to a temporary directory
    monkeypatch.setattr(ne, "ROOT", tmp_path)

    # Ensure target dirs exist so the script can write files
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "notebooks").mkdir(parents=True)
    (tmp_path / "notebooks" / "solutions").mkdir(parents=True)

    # Simulate CLI argv
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex010",
            "Debug Example",
            "--slug",
            "debug_example",
            "--type",
            "debug",
        ],
    )

    # Run main
    result = ne.main()
    assert result == 0

    exercise_key = "ex010_debug_example"
    ex_dir = tmp_path / "exercises" / exercise_key
    nb_path = tmp_path / "notebooks" / f"{exercise_key}.ipynb"
    nb_solution = tmp_path / "notebooks" / "solutions" / f"{exercise_key}.ipynb"
    test_path = tmp_path / "tests" / f"test_{exercise_key}.py"

    assert ex_dir.exists(), "Exercise directory should be created"
    assert nb_path.exists(), "Student notebook should be created"
    assert nb_solution.exists(), "Solution notebook should be created"
    assert test_path.exists(), "Test file should be created"

    # Notebook should include exercise1 and explanation1 tags
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    tags = [t for cell in nb["cells"] for t in cell.get("metadata", {}).get("tags", [])]
    assert "exercise1" in tags
    assert "explanation1" in tags

    # README should mention explanation tag guidance
    readme = (ex_dir / "README.md").read_text(encoding="utf-8")
    assert "explanation1" in readme or "explanationN" in readme

    # Test file should include an assertion checking explanation content (>10 chars)
    txt = test_path.read_text(encoding="utf-8")
    assert (
        "Explanation must be more than 10 characters" in txt
        or "Explanation must be more than 10 characters" in txt
    )


def test_standard_template_only_grades_exercise_tags_and_selfcheck_untagged() -> None:
    """Ensure the standard (non-debug) template tags only graded exercise code cells with 'exerciseN' and leaves the optional self-check cell untagged."""
    nb = ne._make_notebook_with_parts("Title Standard", parts=3, exercise_type=None)
    cells = nb["cells"]

    # Collect exercise tags present on code cells
    exercise_tags = {
        t
        for cell in cells
        if cell.get("cell_type") == "code"
        for t in cell.get("metadata", {}).get("tags", [])
        if re.fullmatch(r"^exercise\d+$", t)
    }

    expected = {f"exercise{i}" for i in range(1, 4)}
    assert exercise_tags == expected

    # The last cell should be the optional self-check code cell and must have no tags
    last_cell = cells[-1]
    assert last_cell["cell_type"] == "code"
    assert not last_cell.get("metadata", {}).get("tags", []), (
        "Optional self-check cell should not be tagged"
    )
