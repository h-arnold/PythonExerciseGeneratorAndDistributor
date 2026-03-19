from __future__ import annotations

import argparse
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
        exercise_key: str,
        test_target: str,
    ) -> Notebook: ...


class _CheckExerciseNotExists(Protocol):
    def __call__(
        self,
        construct: str,
        exercise_type: str,
        exercise_key: str,
    ) -> None: ...


class _ValidateAndParseArgs(Protocol):
    def __call__(self) -> object: ...


class _BuildReadmeLines(Protocol):
    def __call__(
        self,
        title: str,
        created_date: str,
        *,
        exercise_type: str,
        test_target: str,
    ) -> list[str]: ...


class _BuildTestLines(Protocol):
    def __call__(
        self,
        exercise_key: str,
        *,
        parts: int,
        exercise_type: str,
    ) -> list[str]: ...


# These private helpers are part of the scaffold contract under test, but they remain
# module-private in production code, so the focused tests bind them explicitly here.
_MAKE_NOTEBOOK_WITH_PARTS: _MakeNotebookWithParts = getattr(ne, "_make_notebook_with_parts")  # noqa: B009
_CHECK_EXERCISE_NOT_EXISTS: _CheckExerciseNotExists = getattr(ne, "_check_exercise_not_exists")  # noqa: B009
_VALIDATE_AND_PARSE_ARGS: _ValidateAndParseArgs = getattr(ne, "_validate_and_parse_args")  # noqa: B009
_BUILD_README_LINES: _BuildReadmeLines = getattr(ne, "_build_readme_lines")  # noqa: B009
_BUILD_TEST_LINES: _BuildTestLines = getattr(ne, "_build_test_lines")  # noqa: B009


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
    assert _is_notebook_cells(
        cells), "Notebook cells must be a list of dictionaries"
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
        exercise_key="ex000_sequence_debug_example",
        test_target="exercises/sequence/ex000/tests/test_ex000.py",
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
        assert "Expected output" in "".join(
            _ensure_source_lines(previous_cell))


def test_make_notebook_make_structure_matches_standard_non_debug_scaffold() -> None:
    notebook = _MAKE_NOTEBOOK_WITH_PARTS(
        "Title Make",
        parts=2,
        exercise_type="make",
        exercise_key="ex000_sequence_make_example",
        test_target="exercises/sequence/ex000/tests/test_ex000.py",
    )
    cells = _require_cells(notebook)

    for i in range(1, 3):
        exercise_tag = f"exercise{i}"
        code_cell = _find_tags(cells, exercise_tag)
        assert code_cell is not None, f"Missing code cell tagged {exercise_tag}"
        assert code_cell["cell_type"] == "code"

        code_source = "".join(_ensure_source_lines(code_cell))
        assert "# The tests will execute the code in this cell and verify the output." in code_source
        assert "print('TODO: Write your solution here')" in code_source
        assert "def solve(" not in code_source

        cell_index = cells.index(code_cell)
        assert cell_index > 0
        prompt_cell = cells[cell_index - 1]
        assert prompt_cell["cell_type"] == "markdown"

        prompt_source = "".join(_ensure_source_lines(prompt_cell))
        assert f"## Exercise {i}" in prompt_source
        assert "(Write the prompt here.)" in prompt_source


def test_build_readme_lines_uses_canonical_exercise_local_test_target() -> None:
    exercise_key = "ex010_sequence_debug_syntax"
    test_target = f"exercises/sequence/{exercise_key}/tests/test_{exercise_key}.py"

    readme_lines = _BUILD_README_LINES(
        "Debug Example",
        "2026-01-01",
        exercise_type="debug",
        test_target=test_target,
    )

    readme = "\n".join(readme_lines)
    assert f"From the repository root, run `uv run pytest -q {test_target}` until all tests pass." in readme
    assert "Run `pytest -q` until all tests pass." not in readme


def test_make_notebook_instructions_use_canonical_exercise_local_test_target() -> None:
    test_target = (
        "exercises/sequence/ex010_sequence_debug_syntax/tests/test_ex010_sequence_debug_syntax.py"
    )
    notebook = _MAKE_NOTEBOOK_WITH_PARTS(
        "Title Debug",
        parts=1,
        exercise_type="debug",
        exercise_key="ex010_sequence_debug_syntax",
        test_target=test_target,
    )
    cells = _require_cells(notebook)
    intro_source = "".join(_ensure_source_lines(cells[0]))
    assert f"From the repository root, run `uv run pytest -q {test_target}`" in intro_source
    assert "- Run `pytest -q`\n" not in intro_source


def test_build_make_test_lines_use_output_capture_helpers() -> None:
    test_text = "\n".join(
        _BUILD_TEST_LINES(
            "ex000_sequence_make_example",
            parts=2,
            exercise_type="make",
        )
    )

    assert "from exercise_runtime_support.exercise_framework import (" in test_text
    assert "import pytest" in test_text
    assert "    RuntimeCache," in test_text
    assert "    resolve_exercise_notebook_path," in test_text
    assert "    run_cell_and_capture_output," in test_text
    assert "_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)" in test_text
    assert "_CACHE = RuntimeCache()" in test_text
    assert "run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)" in test_text
    assert "@pytest.mark.parametrize('tag', ['exercise1', 'exercise2'])" in test_text
    assert "assert output.strip(), f'{tag} should produce output'" in test_text
    assert "assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'" in test_text
    assert "exec_tagged_code" not in test_text
    assert "def _solve(" not in test_text
    assert "get_explanation_cell" not in test_text


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
    assert not (tmp_path / "notebooks" / "solutions" /
                f"{exercise_key}.ipynb").exists()
    assert not (tmp_path / "tests" / f"test_{exercise_key}.py").exists()

    exercise_metadata = json.loads(
        exercise_json_path.read_text(encoding="utf-8"))
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

    student_notebook = json.loads(
        student_notebook_path.read_text(encoding="utf-8"))
    cells = _require_cells(student_notebook)
    tags: list[str] = []
    for cell in cells:
        tags.extend(_string_tags(cell.get("metadata")))
    assert "exercise1" in tags
    assert "explanation1" in tags

    helper_source = "".join(_ensure_source_lines(cells[-1]))
    assert f"run_notebook_checks('{exercise_key}')" in helper_source

    assert json.loads(student_notebook_path.read_text(encoding="utf-8")) == json.loads(
        solution_notebook_path.read_text(encoding="utf-8")
    )

    readme = (exercise_dir / "README.md").read_text(encoding="utf-8")
    assert "Open `notebooks/student.ipynb` in this exercise folder." in readme
    assert "explanation1" in readme or "explanationN" in readme
    assert (
        f"From the repository root, run `uv run pytest -q exercises/sequence/{exercise_key}/tests/test_{exercise_key}.py` "
        "until all tests pass."
    ) in readme
    assert "Run `pytest -q` until all tests pass." not in readme

    test_text = test_path.read_text(encoding="utf-8")
    assert f"_EXERCISE_KEY = '{exercise_key}'" in test_text
    assert "_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)" in test_text
    assert "_CACHE = RuntimeCache()" in test_text
    assert "run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)" in test_text
    assert "get_explanation_cell(_NOTEBOOK_PATH, tag='explanation1')" in test_text
    assert "assert is_valid_explanation(" in test_text
    assert "min_length=_MIN_EXPLANATION_LENGTH" in test_text
    assert "placeholder_phrases=_PLACEHOLDER_PHRASES" in test_text
    assert "_MIN_EXPLANATION_LENGTH = 50" in test_text
    assert "_PLACEHOLDER_PHRASES = (" in test_text
    assert "import pytest" not in test_text
    assert "runtime.run_cell_and_capture_output" not in test_text
    assert "runtime.get_explanation_cell" not in test_text
    assert "len(explanation.strip()) > 10" not in test_text
    assert (
        f"NOTEBOOK_PATH = 'exercises/sequence/{exercise_key}/notebooks/student.ipynb'"
        not in test_text
    )


def test_main_creates_canonical_make_scaffold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ne, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex012",
            "Make Example",
            "--construct",
            "sequence",
            "--type",
            "make",
            "--slug",
            "function_contract",
        ],
    )

    result = ne.main()
    assert result == 0

    exercise_key = "ex012_sequence_make_function_contract"
    exercise_dir = tmp_path / "exercises" / "sequence" / exercise_key
    student_notebook_path = exercise_dir / "notebooks" / "student.ipynb"
    test_path = exercise_dir / "tests" / f"test_{exercise_key}.py"

    student_notebook = json.loads(
        student_notebook_path.read_text(encoding="utf-8"))
    cells = _require_cells(student_notebook)
    exercise_cell = _find_tags(cells, "exercise1")
    assert exercise_cell is not None

    notebook_source = "".join(_ensure_source_lines(exercise_cell))
    assert "# The tests will execute the code in this cell and verify the output." in notebook_source
    assert "print('TODO: Write your solution here')" in notebook_source
    assert "def solve(" not in notebook_source

    prompt_cell = cells[cells.index(exercise_cell) - 1]
    assert prompt_cell["cell_type"] == "markdown"
    prompt_source = "".join(_ensure_source_lines(prompt_cell))
    assert "## Exercise 1" in prompt_source
    assert "(Write the prompt here.)" in prompt_source

    test_text = test_path.read_text(encoding="utf-8")
    assert f"_EXERCISE_KEY = '{exercise_key}'" in test_text
    assert "_CACHE = RuntimeCache()" in test_text
    assert "run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)" in test_text
    assert "def test_exercise1_output() -> None:" in test_text
    assert "assert output.strip(), 'Exercise should produce output'" in test_text
    assert "assert 'TODO' not in output, 'Replace the TODO placeholder with your solution'" in test_text
    assert "import pytest" not in test_text
    assert "exec_tagged_code" not in test_text


def test_main_creates_multi_part_debug_scaffold_with_helper_based_explanation_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ne, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex011",
            "Debug Example",
            "--construct",
            "sequence",
            "--type",
            "debug",
            "--slug",
            "logic",
            "--parts",
            "3",
        ],
    )

    result = ne.main()
    assert result == 0

    exercise_key = "ex011_sequence_debug_logic"
    test_path = (
        tmp_path
        / "exercises"
        / "sequence"
        / exercise_key
        / "tests"
        / f"test_{exercise_key}.py"
    )
    test_text = test_path.read_text(encoding="utf-8")

    assert "EXPLANATION_TAGS = [f'explanation{i}' for i in range(1, 3 + 1)]" in test_text
    assert "@pytest.mark.parametrize('tag', EXPLANATION_TAGS)" in test_text
    assert "explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=tag)" in test_text
    assert "assert is_valid_explanation(" in test_text
    assert "import pytest" in test_text
    assert "len(explanation.strip()) > 10" not in test_text


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


def test_validate_and_parse_args_accepts_canonical_construct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex010",
            "Data Types Example",
            "--construct",
            "data_types",
            "--type",
            "modify",
        ],
    )

    args = _VALIDATE_AND_PARSE_ARGS()

    assert isinstance(args, argparse.Namespace)
    assert args.construct == "data_types"


def test_validate_and_parse_args_rejects_unknown_construct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scripts/new_exercise.py",
            "ex010",
            "Unknown Construct",
            "--construct",
            "made_up_construct",
            "--type",
            "modify",
        ],
    )

    with pytest.raises(
        SystemExit,
        match=r"Unknown construct: made_up_construct\. Use one of:",
    ):
        _VALIDATE_AND_PARSE_ARGS()


def test_standard_template_only_grades_exercise_tags_and_selfcheck_untagged() -> None:
    notebook = _MAKE_NOTEBOOK_WITH_PARTS(
        "Title Standard",
        parts=3,
        exercise_type="modify",
        exercise_key="ex000_sequence_modify_example",
        test_target="exercises/sequence/ex000/tests/test_ex000.py",
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
    assert any(
        "Self-check" in line for line in _ensure_source_lines(self_check_cell))

    check_answers_cell = cells[-1]
    assert check_answers_cell["cell_type"] == "code"
    metadata = check_answers_cell.get("metadata")
    assert not _string_tags(
        metadata), "Check-your-answers cell should remain untagged"
    joined_source = "".join(_ensure_source_lines(check_answers_cell))
    assert (
        "from exercise_runtime_support.student_checker import run_notebook_checks" in joined_source
    )
    assert "run_notebook_checks('ex000_sequence_modify_example')" in joined_source
