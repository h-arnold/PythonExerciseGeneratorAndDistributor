"""Tests for AST-first construct checks."""

from __future__ import annotations

from tests.exercise_framework import constructs, paths, runtime
from tests.exercise_framework.expectations import EX002_NOTEBOOK_PATH


def _exercise_code(exercise_no: int) -> str:
    notebook_path = paths.resolve_notebook_path(EX002_NOTEBOOK_PATH)
    return runtime.extract_tagged_code(notebook_path, tag=f"exercise{exercise_no}")


def test_ex002_print_usage_is_detected_via_ast() -> None:
    for exercise_no in range(1, 11):
        code = _exercise_code(exercise_no)
        assert constructs.check_has_print_statement(code)


def test_ex002_required_operators_are_detected_via_ast() -> None:
    operator_expectations = {
        3: "*",
        5: "/",
        8: "*",
        9: "-",
    }
    for exercise_no, operator in operator_expectations.items():
        code = _exercise_code(exercise_no)
        assert constructs.check_uses_operator(code, operator)


def test_constructs_fall_back_on_invalid_code() -> None:
    code = "print ("
    assert constructs.check_has_print_statement(code)
    assert constructs.check_uses_operator("value = 6 *", "*")


def test_operator_fallback_ignores_strings_and_comments() -> None:
    code_with_string = "value = '6 * 3'\nprint("
    assert not constructs.check_uses_operator(code_with_string, "*")

    code_with_comment = "value = 6\n# uses *\nprint("
    assert not constructs.check_uses_operator(code_with_comment, "*")
