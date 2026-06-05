"""Tests for the ExerciseScaffold abstract base class (scripts/exercise_scaffolder/base.py).

Red-phase (test-first) tests for Stage 1 of the exercise scaffolder refactor.
These tests will fail until ``scripts/exercise_scaffolder/base.py`` is implemented.
"""

from __future__ import annotations

from typing import Any

import pytest

from scripts.exercise_scaffolder.base import ExerciseScaffold


class _ConcreteScaffold(ExerciseScaffold):
    """Minimal concrete subclass for testing base-class behaviour."""

    def _build_exercise_cells(self) -> list[dict[str, Any]]:
        return []

    def _build_exercise_body_test_lines(self) -> list[str]:
        return ["def test_placeholder() -> None:\n    assert True\n"]


# ── helpers ──────────────────────────────────────────────────────────────────


def _source_text(cell: dict[str, Any]) -> str:
    """Join a notebook cell's source lines into a single string."""
    return "".join(cell["source"])


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  ABC enforcement
# ═══════════════════════════════════════════════════════════════════════════════


class TestAbcEnforcement:
    """ExerciseScaffold must not be directly instantiable."""

    def test_cannot_instantiate_abstract_class_directly(self) -> None:
        with pytest.raises(TypeError):
            ExerciseScaffold(  # type: ignore[abstract]
                "Title", "ex000", 1, "tests/test_ex000.py", exercise_id=0,
            )

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex000", 1, "tests/test_ex000.py", exercise_id=0,
        )
        assert isinstance(scaffold, ExerciseScaffold)

    def test_concrete_subclass_is_subclass(self) -> None:
        assert issubclass(_ConcreteScaffold, ExerciseScaffold)


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  _build_check_answers_cell
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildCheckAnswersCell:
    """The self-checker cell must set ``PYTUTOR_ACTIVE_VARIANT`` per variant."""

    @pytest.fixture
    def scaffold(self) -> _ConcreteScaffold:
        return _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )

    def test_student_variant_sets_student_env_var(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        source = _source_text(cell)

        assert 'os.environ["PYTUTOR_ACTIVE_VARIANT"]' in source
        assert '"student"' in source

    def test_student_variant_does_not_contain_solution(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        source = _source_text(cell)

        assert '"solution"' not in source

    def test_solution_variant_sets_solution_env_var(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("solution")
        source = _source_text(cell)

        assert 'os.environ["PYTUTOR_ACTIVE_VARIANT"]' in source
        assert '"solution"' in source

    def test_solution_variant_does_not_contain_student(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("solution")
        source = _source_text(cell)

        assert '"student"' not in source

    def test_cell_type_is_code(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        assert cell["cell_type"] == "code"

    def test_cell_contains_run_notebook_checks(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        source = _source_text(cell)

        assert "run_notebook_checks(" in source
        assert "'ex014'" in source

    def test_cell_has_execution_count_none(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        assert cell["execution_count"] is None

    def test_cell_has_empty_outputs(self, scaffold: _ConcreteScaffold) -> None:
        cell = scaffold.build_check_answers_cell("student")
        assert cell["outputs"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  build_expectations_module
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildExpectationsModule:
    """The expectations module must use exercise-ID-prefixed naming."""

    def test_variable_name_is_exercise_id_prefixed(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        assert "EX014_EXPECTED_OUTPUTS" in module

    def test_contains_final_type_annotation(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        assert "Final[dict[int, str]]" in module

    def test_keys_match_parts_count(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        assert '1: ""' in module
        assert '2: ""' in module
        assert '3: ""' in module

    def test_single_part_produces_single_key(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex015", 1, "tests/test_ex015.py", exercise_id=15,
        )
        module = scaffold.build_expectations_module()
        assert '1: ""' in module
        assert "2:" not in module

    def test_five_parts_produces_five_keys(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex020", 5, "tests/test_ex020.py", exercise_id=20,
        )
        module = scaffold.build_expectations_module()
        for i in range(1, 6):
            assert f'{i}: ""' in module
        assert "6:" not in module

    def test_has_docstring_with_exercise_key(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        first_line = module.splitlines()[0]
        assert "ex014" in first_line, "Docstring should reference the exercise key"

    def test_has_future_annotations_import(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        assert "from __future__ import annotations" in module

    def test_has_typing_import(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        module = scaffold.build_expectations_module()
        assert "from typing import Final" in module


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  build_student_checker_support
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildStudentCheckerSupport:
    """The student checker support module must follow the ex012 pattern."""

    @pytest.fixture
    def scaffold(self) -> _ConcreteScaffold:
        return _ConcreteScaffold(
            "Title", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )

    def test_contains_checks_list(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "CHECKS: list[ExerciseCheckDefinition] = []" in source

    def test_contains_todo_comment(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "TODO" in source

    def test_references_exercise_id_prefixed_expectations(
        self, scaffold: _ConcreteScaffold,
    ) -> None:
        source = scaffold.build_student_checker_support()
        assert "EX014_EXPECTED_OUTPUTS" in source

    def test_references_ex012_example(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "ex012" in source

    def test_loads_expectations_via_load_exercise_test_module(
        self, scaffold: _ConcreteScaffold,
    ) -> None:
        source = scaffold.build_student_checker_support()
        assert "load_exercise_test_module" in source
        assert "_EXERCISE_KEY" in source
        assert '"expectations"' in source or "'expectations'" in source

    def test_contains_exercise_key_constant(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "_EXERCISE_KEY = 'ex014'" in source

    def test_imports_base_check_types(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "ExerciseCheckDefinition" in source
        assert "build_exercise_check" in source
        assert "exercise_tag" in source

    def test_has_docstring_with_exercise_key(self, scaffold: _ConcreteScaffold) -> None:
        source = scaffold.build_student_checker_support()
        assert "ex014" in source.split('"""')[1]


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  build_readme_lines
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildReadmeLines:
    """Smoke tests for the shared README generation."""

    def test_returns_non_empty_list(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Exercise", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_readme_lines("2026-06-05")
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_contains_title(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Exercise", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "My Exercise" in text

    def test_contains_created_date(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Exercise", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "2026-06-05" in text

    def test_contains_uv_run_pytest_instruction(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Exercise", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "uv run pytest" in text
        assert "tests/test_ex014.py" in text

    def test_contains_student_notebook_reference(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Exercise", "ex014", 3, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_readme_lines("2026-06-05")
        text = "\n".join(lines)
        assert "notebooks/student.ipynb" in text


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  build_test_lines
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildTestLines:
    """Smoke tests for the shared test file generation."""

    def test_contains_shared_imports(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "from __future__ import annotations" in text
        assert "_EXERCISE_KEY" in text
        assert "_NOTEBOOK_PATH" in text
        assert "_CACHE = RuntimeCache()" in text
        assert "_run_and_capture" in text

    def test_contains_exercise_key_constant(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "_EXERCISE_KEY = 'ex014'" in text

    def test_contains_resolve_exercise_notebook_path(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "resolve_exercise_notebook_path(_EXERCISE_KEY)" in text

    def test_includes_concrete_body_test_lines(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        assert "test_placeholder" in text

    def test_no_debug_specific_lines_by_default(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        lines = scaffold.build_test_lines()
        text = "\n".join(lines)
        # The base class _build_type_specific_test_lines returns [];
        # debug-only helpers should not appear from the base alone.
        assert "_MIN_EXPLANATION_LENGTH" not in text
        assert "_PLACEHOLDER_PHRASES" not in text
        assert "get_explanation_cell" not in text


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  build_notebook
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildNotebook:
    """Smoke tests for the notebook assembly."""

    def test_returns_notebook_dict(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        assert isinstance(notebook, dict)
        assert "cells" in notebook
        assert "nbformat" in notebook
        assert "metadata" in notebook

    def test_nbformat_is_4(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        assert notebook["nbformat"] == 4  # noqa: PLR2004

    def test_cells_is_non_empty_list(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        cells: list[Any] = notebook["cells"]
        assert isinstance(cells, list)
        assert len(cells) > 0

    def test_first_cell_is_header_markdown(self) -> None:
        scaffold = _ConcreteScaffold(
            "My Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        cells: list[Any] = notebook["cells"]
        assert cells[0]["cell_type"] == "markdown"
        source = _source_text(cells[0])
        assert "My Title" in source

    def test_scratch_cell_is_before_check_cell(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        cells: list[Any] = notebook["cells"]
        # The last two cells should be scratch + check-answers
        assert cells[-2]["cell_type"] == "code"
        assert cells[-1]["cell_type"] == "code"
        scratch_source = _source_text(cells[-2])
        assert "Self-check scratch cell" in scratch_source

    def test_last_cell_is_check_answers(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        cells: list[Any] = notebook["cells"]
        last_source = _source_text(cells[-1])
        assert "run_notebook_checks(" in last_source
        assert "'ex014'" in last_source

    def test_notebook_has_kernelspec_metadata(self) -> None:
        scaffold = _ConcreteScaffold(
            "Title", "ex014", 1, "tests/test_ex014.py", exercise_id=14,
        )
        notebook = scaffold.build_notebook("student")
        metadata = notebook.get("metadata", {})
        assert "kernelspec" in metadata
        assert metadata["kernelspec"]["language"] == "python"
