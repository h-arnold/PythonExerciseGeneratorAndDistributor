"""Tests for DebugScaffold (scripts/exercise_scaffolder/debug.py).

Red-phase (TDD) tests — will fail with ModuleNotFoundError until the subclass module exists.
"""

from __future__ import annotations

from scripts.exercise_scaffolder.debug import DebugScaffold
from tests._scaffold_test_helpers import source_text

_CELLS_FOR_3_PARTS = 12
_CELLS_FOR_2_PARTS = 9
_CELLS_FOR_1_PART = 6

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Cell structure
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellStructure:
    """DebugScaffold produces header + (markdown + code + explanation) per part
    + scratch + check-answers."""

    def test_cell_count_for_parts_3(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 3, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header + (markdown + code + explanation) * 3 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_3_PARTS

    def test_cell_count_for_parts_2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header + (markdown + code + explanation) * 2 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_2_PARTS

    def test_cell_count_for_parts_1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header + 3 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_1_PART

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert cells[0]["cell_type"] == "markdown"

    def test_last_two_cells_are_scratch_and_check(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert "Self-check scratch cell" in source_text(cells[-2])
        assert "run_notebook_checks(" in source_text(cells[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Exercise cells tagged correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestExerciseCellTags:
    """Code cells must carry the correct exerciseN metadata tags."""

    def test_first_exercise_cell_tagged_exercise1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # Header is index 0; exercise cells start at 1: markdown, code(exercise1), explanation
        code_cell = cells[2]  # first code cell
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise1"]

    def test_second_exercise_cell_tagged_exercise2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # Second exercise code cell is at index 5 (header @0, markdown1@1, code1@2, expl1@3,
        # markdown2@4, code2@5, expl2@6)
        code_cell = cells[5]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise2"]

    def test_code_cells_have_execution_count_none(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [2, 5]:
            assert cells[i]["execution_count"] is None

    def test_code_cells_have_empty_outputs(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [2, 5]:
            assert cells[i]["outputs"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  Explanation cells tagged correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplanationCellTags:
    """Explanation markdown cells must carry the correct explanationN tags."""

    def test_first_explanation_tagged_explanation1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # Explanation 1 is at index 3
        expl_cell = cells[3]
        assert expl_cell["cell_type"] == "markdown"
        assert expl_cell["metadata"].get("tags") == ["explanation1"]

    def test_second_explanation_tagged_explanation2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # Explanation 2 is at index 6
        expl_cell = cells[6]
        assert expl_cell["cell_type"] == "markdown"
        assert expl_cell["metadata"].get("tags") == ["explanation2"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  Buggy code marker present
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuggyCodeMarker:
    """Exercise cells must contain the BUGGY CODE comment."""

    def test_source_contains_buggy_code_comment(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # First exercise code cell is at index 2: header@0, markdown1@1, code1@2, expl1@3
        code_cell = cells[2]
        assert "BUGGY CODE" in source_text(code_cell)

    def test_multiple_parts_all_contain_buggy_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [2, 5]:
            assert "BUGGY CODE" in source_text(cells[i])

    def test_source_contains_todo_placeholder(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert "print('TODO: Fix this code')" in source_text(cells[2])


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Explanation markdown exists
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplanationMarkdown:
    """Explanation cells must contain the expected markdown content."""

    def test_contains_what_actually_happened(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # Explanation cell is at index 3
        expl_cell = cells[3]
        assert "What actually happened" in source_text(expl_cell)

    def test_all_parts_have_explanation_section(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [3, 6]:
            assert "What actually happened" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  README hook
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadmeHook:
    """DebugScaffold._readme_type_hook() returns a line about explaining behaviour."""

    def test_readme_hook_returns_non_empty_list(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_readme_hook_mentions_explanation(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        text = "\n".join(lines)
        assert "describe what happened" in text.lower()

    def test_readme_hook_included_in_build_readme_lines(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "describe what happened" in text.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  Test lines include debug helpers
# ═══════════════════════════════════════════════════════════════════════════════


class TestDebugHelpersInTestLines:
    """build_test_lines() must include debug-specific imports and constants."""

    def test_includes_get_explanation_cell_import(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "get_explanation_cell" in text

    def test_includes_min_explanation_length_constant(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_MIN_EXPLANATION_LENGTH" in text

    def test_includes_placeholder_phrases_constant(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_PLACEHOLDER_PHRASES" in text

    def test_includes_is_valid_explanation_import(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "is_valid_explanation" in text

    def test_debug_helpers_present_for_multi_part(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "get_explanation_cell" in text
        assert "_MIN_EXPLANATION_LENGTH" in text
        assert "_PLACEHOLDER_PHRASES" in text


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  Test lines include explanation checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplanationCheckLines:
    """build_test_lines() must include explanation-specific test functions."""

    def test_single_part_has_test_explanation_has_content(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "def test_explanation_has_content" in text

    def test_multi_part_has_test_explanations_have_content(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "def test_explanations_have_content" in text

    def test_explanation_checks_reference_explanation_tag(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "explanation1" in text or "EXPLANATION_TAGS" in text
