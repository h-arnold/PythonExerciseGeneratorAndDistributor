from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

import scripts.new_exercise as ne

_MIN_SELFCHECK_CELLS = 2


NotebookCell = dict[str, Any]
Notebook = dict[str, Any]
NotebookBuilder = Callable[..., Notebook]


def _string_tags(metadata: dict[str, Any]) -> list[str]:
    tags = metadata.get("tags")
    if not isinstance(tags, list):
        return []
    tags_list = cast(list[object], tags)
    string_tags: list[str] = []
    for tag in tags_list:
        if not isinstance(tag, str):
            return []
        string_tags.append(tag)
    return string_tags


def _ensure_source_lines(cell: NotebookCell) -> list[str]:
    source = cell.get("source")
    if not isinstance(source, list):
        raise AssertionError("Notebook cell source must be a list")
    source_lines = cast(list[object], source)
    if not all(isinstance(line, str) for line in source_lines):
        raise AssertionError("Notebook cell source must contain str entries")
    return cast(list[str], source)


def _build_notebook_with_parts(
    title: str,
    *,
    parts: int,
    exercise_type: str | None = None,
    notebook_path: str | None = None,
) -> Notebook:
    builder: NotebookBuilder = ne.__dict__["_make_notebook_with_parts"]
    return builder(
        title,
        parts=parts,
        exercise_type=exercise_type,
        notebook_path=notebook_path,
    )


def _find_tags(cells: Sequence[NotebookCell], tag: str) -> NotebookCell | None:
    for cell in cells:
        metadata = cell.get("metadata")
        if not isinstance(metadata, dict):
            continue
        metadata_dict = cast(dict[str, Any], metadata)
        tags = _string_tags(metadata_dict)
        if tag in tags:
            return cell
    return None


def test_make_notebook_debug_structure():
    nb = _build_notebook_with_parts("Title Debug", parts=2, exercise_type="debug")
    cells_value = nb["cells"]
    assert isinstance(cells_value, list)
    cells = cast(list[NotebookCell], cells_value)

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
        joined = "".join(_ensure_source_lines(prev_cell))
        assert "Expected output" in joined


def test_main_creates_debug_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    cells_value = nb["cells"]
    assert isinstance(cells_value, list)
    cells = cast(list[NotebookCell], cells_value)
    tags: list[str] = []
    for cell in cells:
        metadata = cell.get("metadata")
        if not isinstance(metadata, dict):
            continue
        metadata_dict = cast(dict[str, Any], metadata)
        tags.extend(_string_tags(metadata_dict))
    assert "exercise1" in tags
    assert "explanation1" in tags

    # README should mention explanation tag guidance
    readme = (ex_dir / "README.md").read_text(encoding="utf-8")
    assert "explanation1" in readme or "explanationN" in readme

    # Test file should include an assertion checking explanation content (>10 chars)
    txt = test_path.read_text(encoding="utf-8")
    assert "Explanation must be more than 10 characters" in txt


def test_standard_template_only_grades_exercise_tags_and_selfcheck_untagged() -> None:
    """Ensure the standard template keeps untagged helper cells even once we append the check-your-answers helper."""
    nb = _build_notebook_with_parts(
        "Title Standard",
        parts=3,
        exercise_type=None,
        notebook_path="notebooks/ex001_dummy.ipynb",
    )
    cells_value = nb["cells"]
    assert isinstance(cells_value, list)
    cells = cast(list[NotebookCell], cells_value)

    # Collect exercise tags present on code cells
    exercise_tags: set[str] = set()
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        metadata = cell.get("metadata")
        if not isinstance(metadata, dict):
            continue
        metadata_dict = cast(dict[str, Any], metadata)
        for tag in _string_tags(metadata_dict):
            if re.fullmatch(r"^exercise\d+$", tag):
                exercise_tags.add(tag)

    expected = {f"exercise{i}" for i in range(1, 4)}
    assert exercise_tags == expected

    assert len(cells) >= _MIN_SELFCHECK_CELLS
    self_check_cell = cells[-2]
    assert self_check_cell["cell_type"] == "code"
    metadata = self_check_cell.get("metadata")
    assert isinstance(metadata, dict)
    metadata_dict = cast(dict[str, Any], metadata)
    assert not _string_tags(metadata_dict), "Optional self-check cell should not be tagged"
    assert any("Optional self-check" in line for line in _ensure_source_lines(self_check_cell))

    # The final cell is the auto-generated check-your-answers helper
    check_answers_cell = cells[-1]
    assert check_answers_cell["cell_type"] == "code"
    metadata = check_answers_cell.get("metadata")
    assert isinstance(metadata, dict)
    metadata_dict = cast(dict[str, Any], metadata)
    assert not _string_tags(metadata_dict), "Check-your-answers cell should remain untagged"
    joined_source = "".join(_ensure_source_lines(check_answers_cell))
    assert "from tests.student_checker import run_notebook_checks" in joined_source
    assert "run_notebook_checks(" in joined_source
    assert "notebooks/" not in joined_source
    assert "run_notebook_checks('ex001_dummy.ipynb')" in joined_source
