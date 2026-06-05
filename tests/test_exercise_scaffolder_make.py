"""Tests for MakeScaffold (scripts/exercise_scaffolder/make.py).

Red-phase (TDD) tests — will fail with ModuleNotFoundError until the subclass module exists.

MakeScaffold currently shares the same cell/test structure as ModifyScaffold.
The classes are kept separate to allow future divergence in exercise semantics.
"""

from __future__ import annotations

from scripts.exercise_scaffolder.make import MakeScaffold

from tests._scaffold_test_helpers import source_text

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Cell structure (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellStructure:
    """MakeScaffold produces header + (markdown + code) per part + scratch + check-answers."""

    def test_cell_count_for_parts_3(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 3, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        # header + (markdown + code) * 3 + scratch + check-answers
        assert len(cells) == 9  # noqa: PLR2004

    def test_cell_count_for_parts_2(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        # header + (markdown + code) * 2 + scratch + check-answers
        assert len(cells) == 7  # noqa: PLR2004

    def test_cell_count_for_parts_1(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        # header + 2 + scratch + check-answers
        assert len(cells) == 5  # noqa: PLR2004

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        assert cells[0]["cell_type"] == "markdown"

    def test_last_two_cells_are_scratch_and_check(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        assert "Self-check scratch cell" in source_text(cells[-2])
        assert "run_notebook_checks(" in source_text(cells[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Exercise cells tagged correctly (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestExerciseCellTags:
    """Code cells must carry the correct exerciseN metadata tags."""

    def test_first_exercise_cell_tagged_exercise1(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        # Header @0, markdown1@1, code1@2, markdown2@3, code2@4
        code_cell = cells[2]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise1"]

    def test_second_exercise_cell_tagged_exercise2(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        code_cell = cells[4]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise2"]

    def test_code_cells_have_execution_count_none(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        for i in [2, 4]:
            assert cells[i]["execution_count"] is None

    def test_code_cells_have_empty_outputs(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        for i in [2, 4]:
            assert cells[i]["outputs"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  TODO placeholder present (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestTodoPlaceholder:
    """Exercise cells must contain the TODO: Write your solution placeholder."""

    def test_source_contains_todo_placeholder(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        code_cell = cells[2]
        assert "TODO: Write your solution" in source_text(code_cell)

    def test_multiple_parts_all_contain_todo(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="make")["cells"]
        for i in [2, 4]:
            assert "TODO: Write your solution" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  No debug-specific lines in tests (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoDebugSpecificLines:
    """build_test_lines() must NOT include debug-only imports and constants."""

    def test_no_get_explanation_cell_import(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "get_explanation_cell" not in text

    def test_no_min_explanation_length_constant(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_MIN_EXPLANATION_LENGTH" not in text

    def test_no_placeholder_phrases_constant(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_PLACEHOLDER_PHRASES" not in text

    def test_no_is_valid_explanation_import(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "is_valid_explanation" not in text


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Test lines include TODO guard (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestTodoGuardInTestLines:
    """build_test_lines() must include ``assert 'TODO' not in output`` guard."""

    def test_single_part_includes_todo_guard(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" in text

    def test_single_part_todo_guard_in_assertion(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" in text

    def test_multi_part_includes_todo_guard(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" in text


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  README hook returns empty (identical to ModifyScaffold)
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadmeHook:
    """MakeScaffold._readme_type_hook() returns an empty list."""

    def test_readme_hook_returns_empty_list(self) -> None:
        scaffold = MakeScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        assert lines == []
