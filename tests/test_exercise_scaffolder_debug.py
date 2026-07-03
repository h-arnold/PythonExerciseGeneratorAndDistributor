"""Tests for DebugScaffold (scripts/exercise_scaffolder/debug.py).

Red-phase (TDD) tests — will fail with ModuleNotFoundError until the subclass module exists.
"""

from __future__ import annotations

from scripts.exercise_scaffolder.debug import DebugScaffold
from tests._scaffold_test_helpers import source_text

# New structure: 5 cells per part (md + readonly + explanation + debug_header + code)
# Assembly: header(1) + parts * (5 + 1 prompt) + scratch(1) + heading(1) + checker(1)
_CELLS_FOR_3_PARTS = 22  # 1 + 3*6 + 3
_CELLS_FOR_2_PARTS = 16  # 1 + 2*6 + 3
_CELLS_FOR_1_PART = 10  # 1 + 1*6 + 3

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Cell structure
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellStructure:
    """DebugScaffold produces header + (md + readonly + explanation + debug_header + code + prompt) per part
    + scratch + check-answers."""

    def test_cell_count_for_parts_3(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 3, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header + (5 exercise cells + 1 prompt) * 3 + scratch + heading + checker
        assert len(cells) == _CELLS_FOR_3_PARTS

    def test_cell_count_for_parts_2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert len(cells) == _CELLS_FOR_2_PARTS

    def test_cell_count_for_parts_1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert len(cells) == _CELLS_FOR_1_PART

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert cells[0]["cell_type"] == "markdown"

    def test_last_three_cells_are_scratch_heading_and_check(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert "Self-check scratch cell" in source_text(cells[-3])
        assert cells[-2]["cell_type"] == "markdown"  # heading
        assert "run_notebook_checks(" in source_text(cells[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Exercise cells tagged correctly (editable code cell)
# ═══════════════════════════════════════════════════════════════════════════════


class TestExerciseCellTags:
    """Editable code cells must carry the correct exerciseN metadata tags."""

    def test_first_exercise_cell_tagged_exercise1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # New structure: header@0, md1@1, ro1@2, expl1@3, debug_hdr1@4, code1@5
        code_cell = cells[5]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise1"]

    def test_second_exercise_cell_tagged_exercise2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3, dh1@4, code1@5, prompt@6,
        # md2@7, ro2@8, expl2@9, dh2@10, code2@11
        code_cell = cells[11]
        assert code_cell["cell_type"] == "code"
        assert code_cell["metadata"].get("tags") == ["exercise2"]

    def test_code_cells_have_execution_count_none(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [5, 11]:
            assert cells[i]["execution_count"] is None

    def test_code_cells_have_empty_outputs(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [5, 11]:
            assert cells[i]["outputs"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  Explanation cells tagged correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplanationCellTags:
    """Explanation markdown cells must carry the correct explanationN tags."""

    def test_first_explanation_tagged_explanation1(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3
        expl_cell = cells[3]
        assert expl_cell["cell_type"] == "markdown"
        assert expl_cell["metadata"].get("tags") == ["explanation1"]

    def test_second_explanation_tagged_explanation2(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3, dh1@4, code1@5, prompt@6,
        # md2@7, ro2@8, expl2@9
        expl_cell = cells[9]
        assert expl_cell["cell_type"] == "markdown"
        assert expl_cell["metadata"].get("tags") == ["explanation2"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  Buggy code marker present (editable cell)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuggyCodeMarker:
    """Editable exercise cells must contain the BUGGY CODE comment."""

    def test_source_contains_buggy_code_comment(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3, dh1@4, code1@5
        code_cell = cells[5]
        assert "BUGGY CODE" in source_text(code_cell)

    def test_multiple_parts_all_contain_buggy_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [5, 11]:
            assert "BUGGY CODE" in source_text(cells[i])

    def test_source_contains_todo_placeholder(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        assert "print('TODO: Fix this code')" in source_text(cells[5])


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Explanation markdown exists
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplanationMarkdown:
    """Explanation cells must contain the expected markdown content."""

    def test_contains_what_actually_happened(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3
        expl_cell = cells[3]
        assert "What actually happened" in source_text(expl_cell)

    def test_all_parts_have_explanation_section(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [3, 9]:
            assert "What actually happened" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  Read-only buggy code cell metadata
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadOnlyBuggyCodeCell:
    """Read-only buggy code cells must have deletable:false and editable:false metadata."""

    def test_readonly_cell_has_deletable_false(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2
        ro_cell = cells[2]
        assert ro_cell["cell_type"] == "code"
        assert ro_cell["metadata"].get("deletable") is False

    def test_readonly_cell_has_editable_false(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        ro_cell = cells[2]
        assert ro_cell["metadata"].get("editable") is False

    def test_readonly_cell_has_no_exercise_tag(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        ro_cell = cells[2]
        tags = ro_cell["metadata"].get("tags", [])
        assert "exercise1" not in tags

    def test_readonly_cell_contains_same_buggy_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        ro_source = source_text(cells[2])
        editable_source = source_text(cells[5])
        # Both should contain the same buggy placeholder code
        assert "print('TODO: Fix this code')" in ro_source
        assert "print('TODO: Fix this code')" in editable_source

    def test_readonly_cell_has_different_comment(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        ro_source = source_text(cells[2])
        editable_source = source_text(cells[5])
        # The read-only cell should have a distinct comment from the editable cell
        assert ro_source != editable_source

    def test_multiple_parts_all_have_readonly_cells(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [2, 8]:
            assert cells[i]["cell_type"] == "code"
            assert cells[i]["metadata"].get("deletable") is False
            assert cells[i]["metadata"].get("editable") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  Debug this code header cell
# ═══════════════════════════════════════════════════════════════════════════════


class TestDebugThisCodeHeader:
    """A 'Debug this code' markdown header must appear before each editable buggy code cell."""

    def test_debug_header_exists_before_editable_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, md1@1, ro1@2, expl1@3, debug_hdr1@4, code1@5
        debug_hdr = cells[4]
        assert debug_hdr["cell_type"] == "markdown"
        assert "Debug this code" in source_text(debug_hdr)

    def test_debug_header_contains_emoji(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        debug_hdr = cells[4]
        source = source_text(debug_hdr)
        assert "\U0001f41e" in source  # beetle emoji 🐞

    def test_debug_header_has_no_tag(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        debug_hdr = cells[4]
        tags = debug_hdr["metadata"].get("tags", [])
        assert len(tags) == 0

    def test_multiple_parts_all_have_debug_headers(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 2, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        for i in [4, 10]:
            assert cells[i]["cell_type"] == "markdown"
            assert "Debug this code" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  Cell ordering within each exercise part
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellOrdering:
    """Cells within each exercise part must follow the correct order."""

    def test_part_order_is_md_readonly_explanation_debug_header_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # header@0, then part 1: md@1, ro@2, expl@3, debug_hdr@4, code@5
        assert cells[1]["cell_type"] == "markdown"  # expected behaviour
        assert cells[2]["cell_type"] == "code"  # read-only buggy code
        assert cells[3]["cell_type"] == "markdown"  # explanation
        assert cells[4]["cell_type"] == "markdown"  # debug this code header
        assert cells[5]["cell_type"] == "code"  # editable buggy code

    def test_check_prompt_follows_editable_code(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook("student", exercise_type="debug")["cells"]
        # code1@5, prompt@6
        prompt_cell = cells[6]
        assert prompt_cell["cell_type"] == "markdown"
        assert "Check your work" in source_text(prompt_cell)


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  README hook
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadmeHook:
    """DebugScaffold.readme_type_hook() returns a line about explaining behaviour."""

    def test_readme_hook_returns_non_empty_list(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.readme_type_hook()
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_readme_hook_mentions_explanation(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.readme_type_hook()
        text = "\n".join(lines)
        assert "describe what happened" in text.lower()

    def test_readme_hook_included_in_build_readme_lines(self) -> None:
        scaffold = DebugScaffold("Title", "ex001", 1, "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "describe what happened" in text.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 10.  Test lines include debug helpers
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
# 11.  Test lines include explanation checks
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
