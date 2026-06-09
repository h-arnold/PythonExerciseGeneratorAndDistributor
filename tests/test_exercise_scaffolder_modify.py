"""Tests for ModifyScaffold (scripts/exercise_scaffolder/modify.py).

Red-phase (TDD) tests — will fail with ModuleNotFoundError until the subclass module exists.
"""

from __future__ import annotations

from scripts.exercise_scaffolder.modify import ModifyScaffold
from tests._scaffold_test_helpers import source_text

_CELLS_FOR_3_PARTS = 9
_CELLS_FOR_2_PARTS = 7
_CELLS_FOR_1_PART = 5

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Cell structure
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellStructure:
    """ModifyScaffold produces header + (markdown + code) per part + scratch + check-answers."""

    def test_cell_count_for_parts_3(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 3, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        # header + (markdown + code) * 3 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_3_PARTS

    def test_cell_count_for_parts_2(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        # header + (markdown + code) * 2 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_2_PARTS

    def test_cell_count_for_parts_1(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        # header + 2 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_1_PART

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        assert cells[0]["cell_type"] == "markdown"

    def test_last_two_cells_are_scratch_and_check(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        assert "Self-check scratch cell" in source_text(cells[-2])
        assert "run_notebook_checks(" in source_text(cells[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Exercise cells tagged correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestExerciseCellTags:
    """Code cells must carry the correct exerciseN metadata tags."""

    def test_first_exercise_cell_tagged_exercise1(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        # Header @0, markdown1@1, code1@2, markdown2@3, code2@4
        code_cell = cells[2]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise1"]

    def test_second_exercise_cell_tagged_exercise2(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        code_cell = cells[4]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise2"]

    def test_code_cells_have_execution_count_none(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        for i in [2, 4]:
            assert cells[i]["execution_count"] is None

    def test_code_cells_have_empty_outputs(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        for i in [2, 4]:
            assert cells[i]["outputs"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  TODO placeholder present
# ═══════════════════════════════════════════════════════════════════════════════


class TestTodoPlaceholder:
    """Exercise cells must contain the TODO: Write your solution placeholder."""

    def test_source_contains_todo_placeholder(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        code_cell = cells[2]  # header @0, markdown1@1, code1@2
        assert "TODO: Write your solution" in source_text(code_cell)

    def test_multiple_parts_all_contain_todo(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="modify")["cells"]
        for i in [2, 4]:
            assert "TODO: Write your solution" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  No debug-specific lines in tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoDebugSpecificLines:
    """build_test_lines() must NOT include debug-only imports and constants."""

    def test_no_get_explanation_cell_import(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "get_explanation_cell" not in text

    def test_no_min_explanation_length_constant(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_MIN_EXPLANATION_LENGTH" not in text

    def test_no_placeholder_phrases_constant(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_PLACEHOLDER_PHRASES" not in text

    def test_no_is_valid_explanation_import(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "is_valid_explanation" not in text


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Test lines include TODO guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestTodoGuardInTestLines:
    """build_test_lines() must include ``assert 'TODO' not in output`` guard."""

    def test_single_part_includes_todo_guard(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "TODO" in text

    def test_single_part_todo_guard_in_assertion(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" in text

    def test_multi_part_includes_todo_guard(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" in text


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  README hook returns empty
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadmeHook:
    """ModifyScaffold._readme_type_hook() returns an empty list."""

    def test_readme_hook_returns_empty_list(self) -> None:
        scaffold = ModifyScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        assert lines == []
