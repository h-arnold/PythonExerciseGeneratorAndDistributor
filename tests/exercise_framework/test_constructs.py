"""Tests for AST-first construct checks."""

from __future__ import annotations

from exercise_runtime_support.exercise_framework import constructs, runtime

_EX002_EXERCISE_KEY = "ex002_sequence_modify_basics"


def _exercise_code(exercise_no: int) -> str:
    return runtime.extract_tagged_code(
        _EX002_EXERCISE_KEY,
        tag=f"exercise{exercise_no}",
        variant="solution",
    )


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


# ── check_has_string_constant ────────────────────────────────────────────────


def test_string_constant_found_in_double_quotes() -> None:
    assert constructs.check_has_string_constant('x = "hello"', "hello")


def test_string_constant_found_in_single_quotes() -> None:
    assert constructs.check_has_string_constant("x = 'hello'", "hello")


def test_string_constant_not_found() -> None:
    assert not constructs.check_has_string_constant('x = "goodbye"', "hello")


def test_string_constant_in_if_condition() -> None:
    code = 'if name == "Bob":\n    print("Hi")'
    assert constructs.check_has_string_constant(code, "Bob")
    assert constructs.check_has_string_constant(code, "Hi")


def test_string_constant_fallback_on_syntax_error() -> None:
    # Invalid syntax — falls back to raw string search.
    assert constructs.check_has_string_constant('x = "hello" AND', "hello")
    assert not constructs.check_has_string_constant('x = "hello" AND', "world")


# ── check_has_int_constant ───────────────────────────────────────────────────


def test_int_constant_found() -> None:
    assert constructs.check_has_int_constant("x = 25", 25)


def test_int_constant_not_found() -> None:
    assert not constructs.check_has_int_constant("x = 25", 30)


def test_int_constant_in_comparison() -> None:
    assert constructs.check_has_int_constant("if x > 85:", 85)
    assert not constructs.check_has_int_constant("if x > 85:", 50)


def test_int_constant_ignores_booleans() -> None:
    # bool is a subclass of int in Python; must not match.
    assert not constructs.check_has_int_constant("x = True", 1)
    assert not constructs.check_has_int_constant("x = False", 0)


def test_int_constant_fallback_on_syntax_error() -> None:
    # Invalid syntax — falls back to tokenizer search.
    assert constructs.check_has_int_constant("x = 25 AND", 25)
    assert not constructs.check_has_int_constant("x = 25 AND", 30)
