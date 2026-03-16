from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, TypeGuard

import pytest

import scripts.new_exercise as ne

_MIN_SELF_CHECK_CELLS = 2

NotebookCell = dict[str, Any]
Notebook = dict[str, Any]


class _MakeNotebookWithParts(Protocol):
    def __call__(
        self,
        title: str,
        *,
        parts: int,
        exercise_type: str,
        notebook_name: str,
    ) -> Notebook: ...


class _CheckExerciseNotExists(Protocol):
    def __call__(self, construct: str, exercise_type: str, exercise_key: str) -> None: ...


class _ValidateAndParseArgs(Protocol):
    def __call__(self) -> object: ...


_MAKE_NOTEBOOK_WITH_PARTS: _MakeNotebookWithParts = getattr(ne, "_make_notebook_with_parts")  # noqa: B009
_CHECK_EXERCISE_NOT_EXISTS: _CheckExerciseNotExists = getattr(ne, "_check_exercise_not_exists")  # noqa: B009
_VALIDATE_AND_PARSE_ARGS: _ValidateAndParseArgs = getattr(ne, "_validate_and_parse_args")  # noqa: B009


def _is_notebook_cell(value: object) -> TypeGuard[NotebookCell]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_notebook_cells(value: object) -> TypeGuard[list[NotebookCell]]:
    return _is_object_list(value) and all(_is_notebook_cell(item) for item in value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return _is_object_list(value) and all(isinstance(item, str) for item in value)


def _require_cells(notebook: Notebook) -> list[NotebookCell]:
    cells = notebook.get("cells")
    assert _is_notebook_cells(cells), "Notebook cells must be a list of dictionaries"
    return cells


def _string_tags(metadata: dict[str, Any] | None) -> list[str]:
    tags = metadata.get("tags") if metadata else None
    if not _is_string_list(tags):
        return []
    return tags


def _ensure_source_lines(cell: NotebookCell) -> list[str]:
    source = cell.get("source")
    assert _is_string_list(source), "Notebook cell source must be a list[str]"
    return source


def _find_tags(cells: Sequence[NotebookCell], tag: str) -> NotebookCell | None:
    for cell in cells:
        if tag in _string_tags(cell.get("metadata")):
            return cell
    return None


def test_make_notebook_debug_structure() -> None:
    notebook = _MAKE_NOTEBOOK_WITH_PARTS(
        "Title Debug",
        parts=2,
        exercise_type="debug",
        notebook_name="student.ipynb",
    )
    cells = _require_cells(notebook)

    for i in range(1, 3):
        exercise_tag = f"exercise{i}"
        explanation_tag = f"explanation{i}"

        code_cell = _find_tags(cells, exercise_tag)
        assert code_cell is not None, f"Missing code cell tagged {exercise_tag}"
        assert code_cell["cell_type"] == "code"

        explanation_cell = _find_tags(cells, explanation_tag)
        assert explanation_cell is not None, f"Missing explanation cell tagged {explanation_tag}"
        assert explanation_cell["cell_type"] == "markdown"

        cell_index = cells.index(code_cell)
        assert cell_index > 0
        previous_cell = cells[cell_index - 1]
        assert previous_cell["cell_type"] == "markdown"
        assert "Expected output" in "".join(_ensure_source_lines(previous_cell))


def test_main_creates_canonical_debug_scaffold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ne, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex010",
            "Debug Example",
            "--construct",
            "sequence",
            "--type",
            "debug",
            "--slug",
            "syntax",
        ],
    )

    result = ne.main()
    assert result == 0

    exercise_key = "ex010_sequence_debug_syntax"
    exercise_dir = tmp_path / "exercises" / "sequence" / exercise_key
    exercise_json_path = exercise_dir / "exercise.json"
    student_notebook_path = exercise_dir / "notebooks" / "student.ipynb"
    solution_notebook_path = exercise_dir / "notebooks" / "solution.ipynb"
    test_path = exercise_dir / "tests" / f"test_{exercise_key}.py"

    assert exercise_dir.exists(), "Canonical exercise directory should be created"
    assert exercise_json_path.exists(), "exercise.json should be created"
    assert student_notebook_path.exists(), "Student notebook should be created"
    assert solution_notebook_path.exists(), "Solution notebook should be created"
    assert test_path.exists(), "Canonical test file should be created"

    assert not (tmp_path / "notebooks" / f"{exercise_key}.ipynb").exists()
    assert not (tmp_path / "notebooks" / "solutions" / f"{exercise_key}.ipynb").exists()
    assert not (tmp_path / "tests" / f"test_{exercise_key}.py").exists()

    exercise_metadata = json.loads(exercise_json_path.read_text(encoding="utf-8"))
    assert exercise_metadata == {
        "schema_version": 1,
        "exercise_key": exercise_key,
        "exercise_id": 10,
        "slug": exercise_key,
        "title": "Debug Example",
        "construct": "sequence",
        "exercise_type": "debug",
        "parts": 1,
    }

    student_notebook = json.loads(student_notebook_path.read_text(encoding="utf-8"))
    cells = _require_cells(student_notebook)
    tags: list[str] = []
    for cell in cells:
        tags.extend(_string_tags(cell.get("metadata")))
    assert "exercise1" in tags
    assert "explanation1" in tags

    helper_source = "".join(_ensure_source_lines(cells[-1]))
    assert "run_notebook_checks('student.ipynb')" in helper_source
    assert "exercises/sequence" not in helper_source

    assert json.loads(student_notebook_path.read_text(encoding="utf-8")) == json.loads(
        solution_notebook_path.read_text(encoding="utf-8")
    )

    readme = (exercise_dir / "README.md").read_text(encoding="utf-8")
    assert "Open `notebooks/student.ipynb`." in readme
    assert "explanation1" in readme or "explanationN" in readme

    test_text = test_path.read_text(encoding="utf-8")
    assert (
        f"NOTEBOOK_PATH = 'exercises/sequence/{exercise_key}/notebooks/student.ipynb'" in test_text
    )
    assert "runtime.run_cell_and_capture_output" in test_text
    assert "runtime.get_explanation_cell" in test_text


def test_check_exercise_not_exists_rejects_legacy_construct_type_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ne, "ROOT", tmp_path)
    exercise_key = "ex010_sequence_debug_syntax"
    legacy_dir = tmp_path / "exercises" / "sequence" / "debug" / exercise_key
    legacy_dir.mkdir(parents=True)

    with pytest.raises(SystemExit, match=exercise_key):
        _CHECK_EXERCISE_NOT_EXISTS("sequence", "debug", exercise_key)


def test_cli_requires_explicit_construct_and_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["scripts/new_exercise.py", "ex010", "Missing Options"],
    )

    with pytest.raises(SystemExit):
        _VALIDATE_AND_PARSE_ARGS()


def test_standard_template_only_grades_exercise_tags_and_selfcheck_untagged() -> None:
    notebook = _MAKE_NOTEBOOK_WITH_PARTS(
        "Title Standard",
        parts=3,
        exercise_type="modify",
        notebook_name="student.ipynb",
    )
    cells = _require_cells(notebook)

    exercise_tags: set[str] = set()
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        for tag in _string_tags(cell.get("metadata")):
            if re.fullmatch(r"^exercise\d+$", tag):
                exercise_tags.add(tag)

    assert exercise_tags == {"exercise1", "exercise2", "exercise3"}

    assert len(cells) >= _MIN_SELF_CHECK_CELLS
    self_check_cell = cells[-2]
    assert self_check_cell["cell_type"] == "code"
    metadata = self_check_cell.get("metadata")
    assert not _string_tags(metadata), "Self-check cell should not be tagged"
    assert any("Self-check" in line for line in _ensure_source_lines(self_check_cell))

    check_answers_cell = cells[-1]
    assert check_answers_cell["cell_type"] == "code"
    metadata = check_answers_cell.get("metadata")
    assert not _string_tags(metadata), "Check-your-answers cell should remain untagged"
    joined_source = "".join(_ensure_source_lines(check_answers_cell))
    assert (
        "from exercise_runtime_support.student_checker import run_notebook_checks" in joined_source
    )
    assert "run_notebook_checks('student.ipynb')" in joined_source
