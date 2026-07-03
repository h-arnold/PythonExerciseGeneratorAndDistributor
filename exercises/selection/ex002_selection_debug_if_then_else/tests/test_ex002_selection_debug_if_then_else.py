"""Tests for ex002_selection_debug_if_then_else.

This is a debug exercise with 20 parts covering syntax errors, logic errors,
and mixed errors in if/else selection statements.
"""

from __future__ import annotations

import ast
import tokenize
from io import StringIO

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.constructs import (
    check_has_int_constant,
    check_has_string_constant,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex002_selection_debug_if_then_else"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exercise_output(exercise_no: int) -> str:
    """Run the tagged cell with its standard input and return captured stdout."""
    case = _ex.EX002_INPUT_CASES[exercise_no]
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=f"exercise{exercise_no}",
        inputs=case["inputs"],
        cache=_CACHE,
    )


def _exercise_code(exercise_no: int) -> str:
    """Extract the source code for the given exercise."""
    return extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=f"exercise{exercise_no}",
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.AST | None:
    """Return the parsed AST for an exercise, or None if it has a syntax error."""
    code = _exercise_code(exercise_no)
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _has_if_statement(tree: ast.AST | None) -> bool:
    """Check if the AST contains an 'if' statement."""
    if tree is None:
        return False
    return any(isinstance(node, ast.If) for node in ast.walk(tree))


def _has_else_clause(tree: ast.AST | None) -> bool:
    """Check if the AST contains an if/else statement (orelse is non-empty)."""
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            return True
    return False


def _has_comparison(tree: ast.AST | None, left_name: str, ops: tuple, right_val: object) -> bool:
    """Check if the AST contains a specific comparison pattern.

    Example: _has_comparison(tree, 'score', (ast.GtE(),), 90) matches ``score >= 90``.
    """
    if tree is None:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not (isinstance(node.left, ast.Name) and node.left.id == left_name):
            continue
        if len(node.ops) != len(ops):
            continue
        ops_match = all(
            isinstance(op, type(expected_op))
            for op, expected_op in zip(node.ops, ops)
        )
        if not ops_match:
            continue
        if len(node.comparators) != 1:
            continue
        comp = node.comparators[0]
        if isinstance(comp, ast.Constant) and comp.value == right_val:
            return True
    return False


def _has_gt(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (>) comparison operator tuple for AST matching."""
    return (ast.Gt(),)


def _has_gte(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (>=) comparison operator tuple for AST matching."""
    return (ast.GtE(),)


def _has_lt(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (<) comparison operator tuple for AST matching."""
    return (ast.Lt(),)


def _has_lte(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (<=) comparison operator tuple for AST matching."""
    return (ast.LtE(),)


def _has_eq(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (==) comparison operator tuple for AST matching."""
    return (ast.Eq(),)


def _has_not_eq(node_val: object) -> tuple[ast.cmpop, ...]:
    """Return a (!=) comparison operator tuple for AST matching."""
    return (ast.NotEq(),)


def _print_in_if_body(tree: ast.AST, text: str) -> bool:
    """Check if a specific string is printed inside the if-body (not else-body).

    Walks the AST for the first if/else, then checks if any print call in
    the if body (node.body) contains the given text.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            for stmt in node.body:
                for child in ast.walk(stmt):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "print"
                    ):
                        for arg in child.args:
                            if isinstance(arg, ast.Constant) and arg.value == text:
                                return True
            break
    return False


def _print_in_else_body(tree: ast.AST, text: str) -> bool:
    """Check if a specific string is printed inside the else-body (not if-body)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            for stmt in node.orelse:
                for child in ast.walk(stmt):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "print"
                    ):
                        for arg in child.args:
                            if isinstance(arg, ast.Constant) and arg.value == text:
                                return True
            break
    return False


def _code_compiles(code: str) -> bool:
    """Check if code can be compiled without syntax errors."""
    try:
        compile(code, "<test>", "exec")
        return True
    except SyntaxError:
        return False


def _code_has_colon_after_if(code: str) -> bool:
    """Check that there's an 'if' line ending with a colon using tokenize."""
    try:
        tokens = list(tokenize.generate_tokens(StringIO(code).readline))
    except tokenize.TokenError:
        return False
    for i, tok in enumerate(tokens):
        if tok.string == "if":
            # Look for the next NEWLINE and check the previous token before it
            for j in range(i, len(tokens)):
                if tokens[j].type in (tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER):
                    # Check if there's a colon before this line end
                    for k in range(j - 1, i, -1):
                        if tokens[k].string == ":":
                            return True
                        if tokens[k].type in (tokenize.NEWLINE, tokenize.NL):
                            break
                    break
    return False


def _code_has_proper_indent(code: str) -> bool:
    """Check that the code body is properly indented (no IndentationError)."""
    if not code:
        return False
    lines = code.split("\n")
    # Remove blank lines at start/end
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    if not lines:
        return False
    # Find the if/else/for etc line
    seen_keyword = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("if ") or stripped.startswith("else:"):
            seen_keyword = True
            continue
        if seen_keyword and stripped and not stripped.startswith("#"):
            # This line should be indented
            if not line.startswith("    ") and not line.startswith("\t"):
                return False
            break
    return True


# ---------------------------------------------------------------------------
# Exercise 1 — Missing colon (syntax error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    code = _exercise_code(1)
    assert _code_compiles(code), "Code must compile (fix the syntax error)"
    assert "if number % 2 == 0:" in code, "Must use 'if' with a colon"


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation1")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 2 — = instead of > (syntax error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    code = _exercise_code(2)
    assert _code_compiles(code), "Code must compile (fix the syntax error)"
    tree = _exercise_ast(2)
    # Should use > to compare area, not =
    assert _has_comparison(tree, "area", _has_gt(None), 100), (
        "Must use 'area > 100' to check if area exceeds 100"
    )
    # Old broken construct should not be present
    assert "area = 100" not in code, "Remove the assignment 'area = 100'"


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation2")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 3 — Missing indentation (syntax error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    code = _exercise_code(3)
    assert _code_compiles(code), "Code must compile (fix the IndentationError)"
    tree = _exercise_ast(3)
    assert _has_if_statement(tree), "Must use an 'if' statement"


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation3")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 4 — < instead of > (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    assert _has_comparison(tree, "squared", _has_gt(None), 1000), (
        "Must use 'squared > 1000' to check if square exceeds 1000"
    )


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation4")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 5 — Missing quotes on 'blue' (syntax error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(5)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    code = _exercise_code(5)
    assert _code_compiles(code), "Code must compile (fix the NameError)"
    assert check_has_string_constant(code, "blue"), (
        "Must compare against the string 'blue' (with quotes)"
    )


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation5")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 6 — ! instead of != (syntax error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    code = _exercise_code(6)
    assert _code_compiles(code), "Code must compile (fix the syntax error)"
    tree = _exercise_ast(6)
    assert _has_comparison(tree, "pin", _has_not_eq(None), 1234), (
        "Must use 'pin != 1234' (not-equal operator)"
    )


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation6")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 7 — Two errors: = and missing colon (syntax errors)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[7]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    code = _exercise_code(7)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    tree = _exercise_ast(7)
    assert _has_comparison(tree, "answer", _has_eq(None), 8), (
        "Must use 'answer == 8' (not =)"
    )
    assert "answer = 8" not in code.replace("==", "--"), (
        "Remove the incorrect assignment 'answer = 8'"
    )


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation7")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 8 — Three errors: =, missing colon, missing indent (syntax errors)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    code = _exercise_code(8)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    tree = _exercise_ast(8)
    assert _has_comparison(tree, "height", _has_gte(None), 130), (
        "Must use 'height >= 130' (not =)"
    )
    assert "height = 130" not in code.replace(">=", "--"), (
        "Remove the incorrect assignment 'height = 130'"
    )


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation8")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 9 — Four errors: =, missing colon, missing indent, wrong message
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    code = _exercise_code(9)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    tree = _exercise_ast(9)
    assert _has_comparison(tree, "score", _has_gte(None), 50), (
        "Must use 'score >= 50' (not =)"
    )
    # The else branch should print "You failed!", not "You passed!"
    assert check_has_string_constant(code, "You failed!"), (
        "Else branch must print 'You failed!'"
    )


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation9")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 10 — Five errors: =, missing colon, missing quotes, two indentation
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[10]


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    code = _exercise_code(10)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    tree = _exercise_ast(10)
    assert _has_comparison(tree, "name", _has_eq(None), "Bob"), (
        "Must use 'name == \"Bob\"' (with == and quotes)"
    )
    assert check_has_string_constant(code, "Bob"), (
        "Must compare against the string 'Bob' (with quotes)"
    )


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation10")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 11 — Off-by-one: > instead of >= (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=11)
def test_exercise11_logic() -> None:
    output = _exercise_output(11)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[11]


@pytest.mark.task(taskno=11)
def test_exercise11_construct() -> None:
    tree = _exercise_ast(11)
    assert _has_comparison(tree, "score", _has_gte(None), 90), (
        "Must use 'score >= 90' (not just >) to include score of exactly 90"
    )


@pytest.mark.task(taskno=11)
def test_exercise11_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation11")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 12 — Off-by-one: < instead of <= (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=12)
def test_exercise12_logic() -> None:
    output = _exercise_output(12)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[12]


@pytest.mark.task(taskno=12)
def test_exercise12_construct() -> None:
    tree = _exercise_ast(12)
    assert _has_comparison(tree, "age", _has_lte(None), 12), (
        "Must use 'age <= 12' (not <) to include age of exactly 12"
    )


@pytest.mark.task(taskno=12)
def test_exercise12_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation12")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 13 — Reversed comparison: < instead of > (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=13)
def test_exercise13_logic() -> None:
    output = _exercise_output(13)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[13]


@pytest.mark.task(taskno=13)
def test_exercise13_construct() -> None:
    tree = _exercise_ast(13)
    assert _has_comparison(tree, "number", _has_gt(None), 0), (
        "Must use 'number > 0' to check for positive numbers"
    )


@pytest.mark.task(taskno=13)
def test_exercise13_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation13")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 14 — Swapped messages (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=14)
def test_exercise14_logic() -> None:
    output = _exercise_output(14)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[14]


@pytest.mark.task(taskno=14)
def test_exercise14_construct() -> None:
    tree = _exercise_ast(14)
    # The if block should print "Correct password!" and else "Wrong password!"
    # Use branch-aware AST checks to verify the right message is in each branch
    assert _print_in_if_body(tree, "Correct password!"), (
        "If branch must print 'Correct password!'"
    )
    assert _print_in_else_body(tree, "Wrong password!"), (
        "Else branch must print 'Wrong password!'"
    )


@pytest.mark.task(taskno=14)
def test_exercise14_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation14")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 15 — Swapped messages (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=15)
def test_exercise15_logic() -> None:
    output = _exercise_output(15)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[15]


@pytest.mark.task(taskno=15)
def test_exercise15_construct() -> None:
    tree = _exercise_ast(15)
    # The if block should print "It's hot!" and else "It's cold!"
    # Use branch-aware AST checks to verify the right message is in each branch
    assert _print_in_if_body(tree, "It's hot!"), (
        "If branch must print 'It's hot!'"
    )
    assert _print_in_else_body(tree, "It's cold!"), (
        "Else branch must print 'It's cold!'"
    )


@pytest.mark.task(taskno=15)
def test_exercise15_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation15")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 16 — Missing else clause (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=16)
def test_exercise16_logic() -> None:
    output = _exercise_output(16)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[16]


@pytest.mark.task(taskno=16)
def test_exercise16_construct() -> None:
    tree = _exercise_ast(16)
    assert _has_else_clause(tree), (
        "Must have an 'else' clause to handle odd numbers"
    )


@pytest.mark.task(taskno=16)
def test_exercise16_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation16")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 17 — Missing lower bound check (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=17)
def test_exercise17_logic() -> None:
    output = _exercise_output(17)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[17]


@pytest.mark.task(taskno=17)
def test_exercise17_construct() -> None:
    code = _exercise_code(17)
    # Should have both lower and upper bound checks
    assert ">= 0" in code or "age >= 0" in code, (
        "Must include 'age >= 0' lower bound check"
    )
    assert check_has_int_constant(code, 0), (
        "Must include 0 as the lower bound for valid age"
    )


@pytest.mark.task(taskno=17)
def test_exercise17_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation17")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 18 — Wrong variable name (logic error)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=18)
def test_exercise18_logic() -> None:
    output = _exercise_output(18)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[18]


@pytest.mark.task(taskno=18)
def test_exercise18_construct() -> None:
    tree = _exercise_ast(18)
    # Should check 'score', not 'age'
    assert _has_comparison(tree, "score", _has_gte(None), 90), (
        "Must check 'score >= 90', not 'age >= 90'"
    )
    # Verify we're NOT checking the wrong variable
    wrong_checks = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "age"
    ]
    assert not wrong_checks, (
        "Remove the 'age' variable — check the 'score' variable instead"
    )


@pytest.mark.task(taskno=18)
def test_exercise18_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation18")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 19 — Mixed: missing colon (syntax) + > instead of >= (logic)
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=19)
def test_exercise19_logic() -> None:
    output = _exercise_output(19)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[19]


@pytest.mark.task(taskno=19)
def test_exercise19_construct() -> None:
    code = _exercise_code(19)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    tree = _exercise_ast(19)
    # Should use >= to include exactly 10
    assert _has_comparison(tree, "number", _has_gte(None), 10), (
        "Must use 'number >= 10' to include the number 10"
    )


@pytest.mark.task(taskno=19)
def test_exercise19_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation19")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )


# ---------------------------------------------------------------------------
# Exercise 20 — Mixed: missing colon, missing indent (syntax) + swapped messages
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=20)
def test_exercise20_logic() -> None:
    output = _exercise_output(20)
    assert output == _ex.EX002_EXPECTED_OUTPUTS[20]


@pytest.mark.task(taskno=20)
def test_exercise20_construct() -> None:
    code = _exercise_code(20)
    assert _code_compiles(code), "Code must compile (fix syntax errors)"
    # The if block should print "You passed!" and else "You failed!"
    assert check_has_string_constant(code, "You passed!"), (
        "If branch must print 'You passed!'"
    )
    assert check_has_string_constant(code, "You failed!"), (
        "Else branch must print 'You failed!'"
    )


@pytest.mark.task(taskno=20)
def test_exercise20_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag="explanation20")
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX002_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX002_PLACEHOLDER_PHRASES,
    )
