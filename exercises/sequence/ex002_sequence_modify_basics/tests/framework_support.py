"""Exercise-local framework checks for ex002 sequence modify basics."""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Final, TypeGuard

from exercise_runtime_support.exercise_framework import (
    extract_tagged_code,
    run_cell_and_capture_output,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import NotebookGradingError

_EXERCISE_KEY = "ex002_sequence_modify_basics"
ex002 = load_exercise_test_module(_EXERCISE_KEY, "expectations")

_WORD_EXERCISE: Final[int] = 4
_MULTI_PRINT_EXERCISE: Final[int] = 6
_RESULT_JOIN_EXERCISE: Final[int] = 7
_CALCULATION_EXERCISE: Final[int] = 9
_LONG_MESSAGE_EXERCISE: Final[int] = 10
_DIVISION_EXERCISE: Final[int] = 5
_MIN_STRING_PARTS: Final[int] = 2
_MIN_CALCULATION_PRINTS: Final[int] = 2

_OLD_TEXT_BY_EXERCISE: Final[dict[int, str]] = {
    1: "Hello World",
    2: "Greenfield",
}
_OLD_BINARY_OPERATORS: Final[dict[int, str]] = {
    3: "+",
    5: "-",
    8: "+",
}
_OPERATOR_SYMBOLS: Final[dict[type[ast.operator], str]] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
}


@dataclass(frozen=True)
class Ex002CheckDefinition:
    """Defines a student-friendly check for an ex002 exercise."""

    exercise_no: int
    title: str
    check: Callable[[], list[str]]


def _expected_output(exercise_no: int) -> str:
    return ex002.EX002_EXPECTED_OUTPUTS[exercise_no]


def _expected_print_calls(exercise_no: int) -> int:
    return ex002.EX002_EXPECTED_PRINT_CALLS[exercise_no]


def _output_mismatch(exercise_no: int, output: str) -> list[str]:
    expected = _expected_output(exercise_no)
    if output == expected:
        return []
    return [f"Exercise {exercise_no}: expected {expected!r}, got {output!r}."]


def _literal_logic(exercise_no: int, output: str) -> list[str]:
    expected = _expected_output(exercise_no)
    old_text = _OLD_TEXT_BY_EXERCISE[exercise_no]
    issues: list[str] = []
    if expected not in output:
        issues.append(f"Exercise {exercise_no}: should include {expected!r}.")
    if old_text in output:
        issues.append(f"Exercise {exercise_no}: old value {old_text!r} remains.")
    return issues


def _numeric_logic(exercise_no: int, output: str) -> list[str]:
    converter = float if exercise_no == _DIVISION_EXERCISE else int
    try:
        value = converter(output)
        expected_value = converter(_expected_output(exercise_no))
    except ValueError:
        return [f"Exercise {exercise_no}: output should be a number."]
    if value != expected_value:
        return [f"Exercise {exercise_no}: wrong numeric result."]
    return []


def _word_logic(exercise_no: int, output: str) -> list[str]:
    expected_words = ["Good", "Morning", "Everyone"]
    if output.split() != expected_words:
        return [f"Exercise {exercise_no}: expected the three words {expected_words!r}."]
    return []


def _multi_print_logic(exercise_no: int, output: str) -> list[str]:
    if output.splitlines() != _expected_output(exercise_no).splitlines():
        return [f"Exercise {exercise_no}: the three expected lines are missing or incorrect."]
    return []


def _result_join_logic(exercise_no: int, output: str) -> list[str]:
    issues: list[str] = []
    if "The result is" not in output:
        issues.append(f"Exercise {exercise_no}: the result text is missing.")
    if "100" not in output:
        issues.append(f"Exercise {exercise_no}: the string '100' is missing.")
    return issues


def _calculation_logic(exercise_no: int, output: str) -> list[str]:
    expected_lines = _expected_output(exercise_no).splitlines()
    if output.splitlines() != expected_lines:
        return [f"Exercise {exercise_no}: the calculation line is missing or incorrect."]
    return []


def _long_message_logic(exercise_no: int, output: str) -> list[str]:
    issues: list[str] = []
    if "Welcome" not in output:
        issues.append(f"Exercise {exercise_no}: the message should start with 'Welcome'.")
    if "Python programming!" not in output:
        issues.append(f"Exercise {exercise_no}: the final phrase is missing.")
    return issues


_LOGIC_HANDLERS: Final[dict[int, Callable[[int, str], list[str]]]] = {
    1: _literal_logic,
    2: _literal_logic,
    3: _numeric_logic,
    _WORD_EXERCISE: _word_logic,
    _DIVISION_EXERCISE: _numeric_logic,
    _MULTI_PRINT_EXERCISE: _multi_print_logic,
    _RESULT_JOIN_EXERCISE: _result_join_logic,
    8: _numeric_logic,
    _CALCULATION_EXERCISE: _calculation_logic,
    _LONG_MESSAGE_EXERCISE: _long_message_logic,
}


def logic_issues(exercise_no: int, output: str) -> list[str]:
    """Return issues with the exercise-specific result (logic) of a cell."""
    handler = _LOGIC_HANDLERS.get(exercise_no)
    if handler is None:
        return [f"Exercise {exercise_no}: no logic expectation configured."]
    return handler(exercise_no, output)


def _print_calls(tree: ast.AST) -> list[ast.Call]:
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    return sorted(calls, key=lambda call: (call.lineno, call.col_offset))


def _final_print_expression(calls: list[ast.Call]) -> ast.expr | None:
    if not calls or not calls[-1].args:
        return None
    return calls[-1].args[0]


def _is_string_literal(expression: ast.expr) -> TypeGuard[ast.Constant]:
    return isinstance(expression, ast.Constant) and isinstance(expression.value, str)


def _string_constants(tree: ast.AST) -> list[str]:
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _formatting_tree_issues(exercise_no: int, code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Exercise {exercise_no}: code is not valid Python (line {exc.lineno})."]
    calls = _print_calls(tree)
    expected_calls = _expected_print_calls(exercise_no)
    if len(calls) != expected_calls:
        return [f"Exercise {exercise_no}: expected {expected_calls} print calls."]
    return []


def formatting_issues(exercise_no: int, output: str, code: str) -> list[str]:
    """Return issues with exact output or the expected number of print calls."""
    return [*_output_mismatch(exercise_no, output), *_formatting_tree_issues(exercise_no, code)]


def _string_join_parts(expression: ast.expr) -> list[str] | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return [expression.value]
    if not isinstance(expression, ast.BinOp) or not isinstance(expression.op, ast.Add):
        return None
    left = _string_join_parts(expression.left)
    right = _string_join_parts(expression.right)
    if left is None or right is None:
        return None
    return [*left, *right]


def _binary_expression_parts(
    expression: ast.expr,
) -> tuple[list[int | float], list[str]] | None:
    if (
        isinstance(expression, ast.Constant)
        and isinstance(expression.value, (int, float))
        and not isinstance(expression.value, bool)
    ):
        return [expression.value], []
    if not isinstance(expression, ast.BinOp):
        return None
    operator_symbol = _OPERATOR_SYMBOLS.get(type(expression.op))
    if operator_symbol is None:
        return None
    left = _binary_expression_parts(expression.left)
    right = _binary_expression_parts(expression.right)
    if left is None or right is None:
        return None
    left_values, left_operators = left
    right_values, right_operators = right
    return (
        [*left_values, *right_values],
        [*left_operators, operator_symbol, *right_operators],
    )


def _contains_operator(tree: ast.AST, symbol: str) -> bool:
    operator_type = next(
        operator for operator, name in _OPERATOR_SYMBOLS.items() if name == symbol
    )
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


def _literal_construct_issues(
    exercise_no: int,
    tree: ast.AST,
    calls: list[ast.Call],
) -> list[str]:
    expression = _final_print_expression(calls)
    expected = _expected_output(exercise_no)
    if expression is None or not _is_string_literal(expression):
        return [f"Exercise {exercise_no}: final print must use the updated string literal."]
    issues: list[str] = []
    if expression.value != expected:
        issues.append(f"Exercise {exercise_no}: final print has the wrong string literal.")
    old_text = _OLD_TEXT_BY_EXERCISE[exercise_no]
    if any(old_text in value for value in _string_constants(tree)):
        issues.append(f"Exercise {exercise_no}: the old value {old_text!r} remains in code.")
    return issues


def _binary_construct_issues(
    exercise_no: int,
    tree: ast.AST,
    calls: list[ast.Call],
) -> list[str]:
    expression = _final_print_expression(calls)
    if expression is None:
        return [f"Exercise {exercise_no}: final print must contain the calculation."]
    parts = _binary_expression_parts(expression)
    if parts is None:
        return [
            f"Exercise {exercise_no}: final print must contain the required arithmetic expression."
        ]

    actual_operands, actual_operators = parts
    expected_operands = ex002.EX002_EXPECTED_BINARY_OPERANDS[exercise_no]
    expected_operators = ex002.EX002_EXPECTED_BINARY_OPERATORS[exercise_no]
    issues: list[str] = []
    if Counter(actual_operators) != Counter(expected_operators):
        issues.append(
            f"Exercise {exercise_no}: final print must use {' '.join(expected_operators)}."
        )
    if exercise_no in ex002.EX002_ORDERED_BINARY_OPERANDS:
        operands_match = actual_operands == list(expected_operands)
    else:
        operands_match = Counter(actual_operands) == Counter(expected_operands)
    if not operands_match:
        issues.append(
            f"Exercise {exercise_no}: final print must use operands {list(expected_operands)!r}."
        )
    old_operator = _OLD_BINARY_OPERATORS.get(exercise_no)
    if old_operator is not None and _contains_operator(tree, old_operator):
        issues.append(
            f"Exercise {exercise_no}: the old operator {old_operator!r} must be removed."
        )
    return issues


def _old_word_construct_issues(exercise_no: int, tree: ast.AST) -> list[str]:
    if exercise_no != _WORD_EXERCISE:
        return []
    constants = _string_constants(tree)
    issues: list[str] = []
    if any("Hello" in value for value in constants):
        issues.append(f"Exercise {exercise_no}: the old value 'Hello' remains in code.")
    if any("World" in value for value in constants):
        issues.append(f"Exercise {exercise_no}: the old value 'World' remains in code.")
    return issues


def _string_join_construct_issues(
    exercise_no: int,
    tree: ast.AST,
    calls: list[ast.Call],
) -> list[str]:
    expression = _final_print_expression(calls)
    if expression is None:
        return [f"Exercise {exercise_no}: final print must contain the joined strings."]

    issues: list[str] = []
    parts = _string_join_parts(expression)
    if parts is None or len(parts) < _MIN_STRING_PARTS:
        issues.append(f"Exercise {exercise_no}: use + to join at least two strings in final print.")
    else:
        if any(not part for part in parts):
            issues.append(f"Exercise {exercise_no}: every string part in final print must be meaningful.")
        if "".join(parts) != _expected_output(exercise_no):
            issues.append(f"Exercise {exercise_no}: joined strings must produce the expected message.")
        expected_parts = ex002.EX002_EXPECTED_STRING_PARTS.get(exercise_no)
        if expected_parts is not None and tuple(parts) != expected_parts:
            issues.append(f"Exercise {exercise_no}: use the specified string parts in final print.")

    issues.extend(_old_word_construct_issues(exercise_no, tree))
    return issues


def _multiple_print_construct_issues(
    exercise_no: int,
    calls: list[ast.Call],
) -> list[str]:
    expected_lines = _expected_output(exercise_no).splitlines()
    if len(calls) != len(expected_lines):
        return [f"Exercise {exercise_no}: expected {len(expected_lines)} separate print calls."]
    issues: list[str] = []
    for call, expected_line in zip(calls, expected_lines, strict=True):
        if (
            len(call.args) != 1
            or not _is_string_literal(call.args[0])
            or call.args[0].value != expected_line
        ):
            issues.append(f"Exercise {exercise_no}: each print call must output one expected line.")
    return issues


def _exercise9_construct_issues(
    exercise_no: int,
    tree: ast.AST,
    calls: list[ast.Call],
) -> list[str]:
    if len(calls) < _MIN_CALCULATION_PRINTS:
        return [f"Exercise {exercise_no}: add a second print call for the calculation."]
    issues: list[str] = []
    first = calls[0]
    first_line = _expected_output(exercise_no).splitlines()[0]
    if (
        len(first.args) != 1
        or not _is_string_literal(first.args[0])
        or first.args[0].value != first_line
    ):
        issues.append(f"Exercise {exercise_no}: the first print must contain the calculation label.")
    issues.extend(_binary_construct_issues(exercise_no, tree, calls))
    return issues


def _multiple_print_handler(
    exercise_no: int,
    _tree: ast.AST,
    calls: list[ast.Call],
) -> list[str]:
    return _multiple_print_construct_issues(exercise_no, calls)


_CONSTRUCT_HANDLERS: Final[
    dict[int, Callable[[int, ast.AST, list[ast.Call]], list[str]]]
] = {
    1: _literal_construct_issues,
    2: _literal_construct_issues,
    3: _binary_construct_issues,
    _WORD_EXERCISE: _string_join_construct_issues,
    5: _binary_construct_issues,
    _MULTI_PRINT_EXERCISE: _multiple_print_handler,
    _RESULT_JOIN_EXERCISE: _string_join_construct_issues,
    8: _binary_construct_issues,
    _CALCULATION_EXERCISE: _exercise9_construct_issues,
    _LONG_MESSAGE_EXERCISE: _string_join_construct_issues,
}


def construct_issues(exercise_no: int, code: str) -> list[str]:
    """Return issues with the required constructs in the tagged cell."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Exercise {exercise_no}: code is not valid Python (line {exc.lineno})."]

    calls = _print_calls(tree)
    issues: list[str] = []
    expected_calls = _expected_print_calls(exercise_no)
    if len(calls) != expected_calls:
        issues.append(f"Exercise {exercise_no}: expected {expected_calls} print calls.")

    handler = _CONSTRUCT_HANDLERS.get(exercise_no)
    if handler is None:
        issues.append(f"Exercise {exercise_no}: no construct expectation configured.")
    else:
        issues.extend(handler(exercise_no, tree, calls))
    return issues


def _check_logic(exercise_no: int) -> list[str]:
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
    except NotebookGradingError as exc:
        return [f"Exercise {exercise_no}: the cell could not run: {exc}"]
    return logic_issues(exercise_no, output)


def _check_formatting(exercise_no: int) -> list[str]:
    try:
        output = run_cell_and_capture_output(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
        code = extract_tagged_code(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
    except NotebookGradingError as exc:
        return [f"Exercise {exercise_no}: the cell could not be checked: {exc}"]
    return formatting_issues(exercise_no, output, code)


def _check_construct(exercise_no: int) -> list[str]:
    try:
        code = extract_tagged_code(
            _EXERCISE_KEY,
            tag=f"exercise{exercise_no}",
        )
    except NotebookGradingError as exc:
        return [f"Exercise {exercise_no}: the cell could not be read: {exc}"]
    return construct_issues(exercise_no, code)


def _build_check(
    exercise_no: int,
    title: str,
    check_fn: Callable[[int], list[str]],
) -> Ex002CheckDefinition:
    return Ex002CheckDefinition(
        exercise_no=exercise_no,
        title=title,
        check=partial(check_fn, exercise_no),
    )


EX002_CHECKS: list[Ex002CheckDefinition] = [
    check
    for exercise_no in range(1, 11)
    for check in (
        _build_check(exercise_no, "Logic", _check_logic),
        _build_check(exercise_no, "Formatting", _check_formatting),
        _build_check(exercise_no, "Construct", _check_construct),
    )
]

__all__ = [
    "EX002_CHECKS",
    "Ex002CheckDefinition",
    "construct_issues",
    "formatting_issues",
    "logic_issues",
]
