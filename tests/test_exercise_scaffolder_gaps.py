"""Tests for GapsScaffold (scripts/exercise_scaffolder/gaps.py).

Red-phase (TDD) tests — will fail with ModuleNotFoundError until the subclass module exists.
"""

from __future__ import annotations

from scripts.exercise_scaffolder.gaps import GapsScaffold
from tests._scaffold_test_helpers import source_text

_CELLS_FOR_3_PARTS = 9
_CELLS_FOR_2_PARTS = 7
_CELLS_FOR_1_PART = 5

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Cell structure
# ═══════════════════════════════════════════════════════════════════════════════


class TestCellStructure:
    """GapsScaffold produces header + (markdown + code) per part + scratch + check-answers."""

    def test_cell_count_for_parts_3(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 3,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        # header + (markdown + code) * 3 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_3_PARTS

    def test_cell_count_for_parts_2(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        # header + (markdown + code) * 2 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_2_PARTS

    def test_cell_count_for_parts_1(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        # header + 2 + scratch + check-answers
        assert len(cells) == _CELLS_FOR_1_PART

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        assert cells[0]["cell_type"] == "markdown"

    def test_last_two_cells_are_scratch_and_check(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        assert "Self-check scratch cell" in source_text(cells[-2])
        assert "run_notebook_checks(" in source_text(cells[-1])


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Exercise cells contain YOUR CODE HERE
# ═══════════════════════════════════════════════════════════════════════════════


class TestYourCodeHereMarker:
    """Exercise cells must contain the # YOUR CODE HERE placeholder."""

    def test_source_contains_your_code_here(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        code_cell = cells[2]  # header @0, markdown1@1, code1@2
        assert "# YOUR CODE HERE" in source_text(code_cell)

    def test_multiple_parts_all_contain_your_code_here(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        for i in [2, 4]:
            assert "# YOUR CODE HERE" in source_text(cells[i])

    def test_code_cells_tagged_correctly(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        assert cells[2]["metadata"].get("tags") == ["exercise1"]
        assert cells[4]["metadata"].get("tags") == ["exercise2"]


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  No TODO placeholder
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoTodoPlaceholder:
    """GapsScaffold cells must NOT contain the TODO placeholder."""

    def test_no_todo_in_cell_source(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        code_cell = cells[2]
        assert "TODO:" not in source_text(code_cell)

    def test_no_todo_in_any_cell(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        for cell in cells:
            source = source_text(cell)
            if cell["cell_type"] == "code":
                assert "TODO:" not in source, f"Unexpected TODO in code cell: {source[:80]}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  Test lines use gaps-style guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestGapsStyleGuard:
    """build_test_lines() must use gaps-specific assertion wording."""

    def test_includes_cell_produced_no_output_message(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "Cell produced no output" in text

    def test_includes_your_code_here_reference(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "# YOUR CODE HERE" in text

    def test_single_part_has_gaps_guard(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "fill in the # YOUR CODE HERE" in text

    def test_multi_part_has_gaps_guard(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "fill in the # YOUR CODE HERE" in text


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Test lines do NOT contain TODO guard
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoTodoGuardInTestLines:
    """build_test_lines() must NOT contain TODO assertion guards."""

    def test_no_todo_in_assertion_string(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        # Only check actual assert statements, not comment lines
        assertion_lines = [
            ln for ln in lines
            if ln.strip().startswith("assert") and not ln.strip().startswith("#")
        ]
        for ln in assertion_lines:
            assert "TODO" not in ln, f"Unexpected TODO in assertion: {ln.strip()}"

    def test_single_part_no_todo_guard(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "'TODO' not in output" not in text


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  Expected output markdown present
# ═══════════════════════════════════════════════════════════════════════════════


class TestExpectedOutputMarkdown:
    """Markdown cells must contain the expected output section."""

    def test_contains_expected_output_section(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        # Header @0, markdown1@1
        md_cell = cells[1]
        assert "Expected output" in source_text(md_cell)

    def test_all_parts_have_expected_output(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 2,
                                "tests/test_ex001.py", exercise_id=1)
        cells = scaffold.build_notebook(
            "student", exercise_type="gaps")["cells"]
        for i in [1, 3]:  # markdown cells for parts 1 and 2
            assert "Expected output" in source_text(cells[i])


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  README hook
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadmeHook:
    """GapsScaffold._readme_type_hook() returns a line about # YOUR CODE HERE."""

    def test_readme_hook_returns_non_empty_list(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_readme_hook_mentions_your_code_here(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold._readme_type_hook()
        text = "\n".join(lines)
        assert "YOUR CODE HERE" in text

    def test_readme_hook_included_in_build_readme_lines(self) -> None:
        scaffold = GapsScaffold("Title", "ex001", 1,
                                "tests/test_ex001.py", exercise_id=1)
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "YOUR CODE HERE" in text
