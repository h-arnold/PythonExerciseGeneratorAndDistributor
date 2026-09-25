from __future__ import annotations

import ast
import builtins
import math
from typing import Any, NoReturn, TypeGuard, cast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex005_sequence_debug_logic"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()
_MISSING = object()
_AVERAGE_DIVISOR = 2
_SENTENCE_GAP_COUNT = 3
_BUILTIN_NAMES = frozenset(dir(builtins)) | {"__builtins__"}
_ALLOWED_CALL_NAMES = frozenset({"print", "input", "abs"})
_ALLOWED_BINARY_OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
_ALLOWED_UNARY_OPERATORS = (ast.UAdd, ast.USub)
_ALLOWED_ANNOTATION_NAMES = frozenset({"str", "int", "float"})
_EXPECTED_INPUT_CALL_COUNT = 2


# ---------------------------------------------------------------------------
# Straight-line grammar
# ---------------------------------------------------------------------------


def _reject(message: str) -> NoReturn:
    raise AssertionError(message)


def _is_direct_call(node: ast.AST, name: str) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    function_name = node.func.id
    return function_name == name


def _validate_target(target: ast.AST) -> None:
    if not isinstance(target, ast.Name):
        _reject("Assignments must target one simple variable name")
    target_name = target.id
    if target_name in _BUILTIN_NAMES:
        _reject(f"Built-in names cannot be reassigned: {target_name}")


def _validate_input_arguments(node: ast.Call) -> None:
    if len(node.args) > 1:
        _reject("input() accepts at most one prompt")
    if node.args:
        prompt = node.args[0]
        if not isinstance(prompt, ast.Constant) or not isinstance(prompt.value, str):
            _reject("input() prompts must be literal strings")


def _validate_call_arguments(node: ast.Call, name: str) -> None:
    if node.keywords:
        _reject("Keyword arguments are not allowed in this exercise")
    if name == "print" and not node.args:
        _reject("print() needs one positional payload")
    if name == "input":
        _validate_input_arguments(node)
    if name == "abs" and len(node.args) != 1:
        _reject("abs() needs exactly one positional argument")
    for argument in node.args:
        _validate_expression(argument)


def _validate_call(node: ast.Call, *, allow_print: bool) -> None:
    if not isinstance(node.func, ast.Name):
        _reject("Only direct calls to print(), input(), and abs() are allowed")
    name = node.func.id
    if name not in _ALLOWED_CALL_NAMES:
        _reject(f"Call to {name}() is not part of this sequence exercise")
    if name == "print" and not allow_print:
        _reject("print() may only be the final top-level statement")
    _validate_call_arguments(node, name)


def _validate_constant(node: ast.Constant) -> None:
    if not isinstance(node.value, (str, int, float)) or isinstance(node.value, bool):
        _reject("Only text and numeric literals are allowed")


def _validate_binary(node: ast.BinOp, *, allow_print: bool) -> None:
    if not isinstance(node.op, _ALLOWED_BINARY_OPERATORS):
        _reject(f"Operator {type(node.op).__name__} is not allowed")
    _validate_expression(node.left, allow_print=allow_print)
    _validate_expression(node.right, allow_print=allow_print)


def _validate_unary(node: ast.UnaryOp, *, allow_print: bool) -> None:
    if not isinstance(node.op, _ALLOWED_UNARY_OPERATORS):
        _reject(f"Unary operator {type(node.op).__name__} is not allowed")
    _validate_expression(node.operand, allow_print=allow_print)


def _validate_expression(node: ast.AST, *, allow_print: bool = False) -> None:
    if isinstance(node, ast.Constant):
        _validate_constant(node)
    elif isinstance(node, ast.Name):
        if not isinstance(node.ctx, ast.Load):
            _reject("A name cannot be used as a store or delete target here")
    elif isinstance(node, ast.BinOp):
        _validate_binary(node, allow_print=allow_print)
    elif isinstance(node, ast.UnaryOp):
        _validate_unary(node, allow_print=allow_print)
    elif isinstance(node, ast.Call):
        _validate_call(node, allow_print=allow_print)
    else:
        _reject(f"Expression node {type(node).__name__} is not allowed")


def _validate_assign(statement: ast.Assign) -> None:
    if len(statement.targets) != 1:
        _reject("Chained assignment targets are not allowed")
    _validate_target(statement.targets[0])
    _validate_expression(statement.value)


def _validate_ann_assign(statement: ast.AnnAssign) -> None:
    _validate_target(statement.target)
    if statement.value is None:
        _reject("An annotated assignment must have a value")
    if not isinstance(statement.annotation, ast.Name):
        _reject("Annotations must be a simple taught type name")
    annotation_name = statement.annotation.id
    if annotation_name not in _ALLOWED_ANNOTATION_NAMES:
        _reject("Only str, int, and float annotations are allowed")
    _validate_expression(statement.value)


def _validate_expression_statement(statement: ast.Expr) -> None:
    if not isinstance(statement.value, ast.Call) or not _is_direct_call(statement.value, "print"):
        _reject("Only a final top-level print() expression is allowed")
    _validate_call(statement.value, allow_print=True)


def _validate_statement(statement: ast.stmt) -> None:
    if isinstance(statement, ast.Assign):
        _validate_assign(statement)
    elif isinstance(statement, ast.AnnAssign):
        _validate_ann_assign(statement)
    elif isinstance(statement, ast.Expr):
        _validate_expression_statement(statement)
    else:
        _reject(f"Statement {type(statement).__name__} is not allowed in straight-line code")


def _assert_straight_line(tree: ast.Module) -> None:
    """Enforce the novice sequence grammar before inspecting data flow."""
    for statement in tree.body:
        _validate_statement(statement)


# ---------------------------------------------------------------------------
# Notebook execution and final-binding tracing
# ---------------------------------------------------------------------------


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _exercise_source(exercise_no: int) -> str:
    return extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    return ast.parse(_exercise_source(exercise_no))


def _static_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _input_output(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _input_cases(exercise_no: int) -> tuple[dict[str, Any], ...]:
    return cast(tuple[dict[str, Any], ...], _ex.EX005_INPUT_CASES[exercise_no])


def _assert_input_cases(exercise_no: int) -> None:
    cases = _input_cases(exercise_no)
    actual = [_input_output(exercise_no, list(case["inputs"])) for case in cases]
    expected = [case["expected_output"] for case in cases]
    assert actual == expected, (
        f"Exercise {exercise_no} output mismatch for cases "
        f"{[list(case['inputs']) for case in cases]}: "
        f"expected {expected!r}, got {actual!r}"
    )


def _print_index(tree: ast.Module) -> int:
    _assert_straight_line(tree)
    indexes = [
        index
        for index, statement in enumerate(tree.body)
        if isinstance(statement, ast.Expr) and _is_direct_call(statement.value, "print")
    ]
    assert len(indexes) == 1, "Each exercise cell must contain one final print()"
    return indexes[0]


def _print_argument(tree: ast.Module) -> ast.expr:
    statement = tree.body[_print_index(tree)]
    assert isinstance(statement, ast.Expr)
    call = statement.value
    assert isinstance(call, ast.Call)
    assert len(call.args) == 1 and not call.keywords
    return call.args[0]


def _bindings_before_print(tree: ast.Module) -> dict[str, ast.expr]:
    bindings: dict[str, ast.expr] = {}
    for statement in tree.body[: _print_index(tree)]:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
        else:
            continue
        if isinstance(target, ast.Name) and statement.value is not None:
            bindings[target.id] = statement.value
    return bindings


def _final_binding(tree: ast.Module, name: str) -> ast.expr:
    value = _bindings_before_print(tree).get(name)
    assert value is not None, f"'{name}' must be assigned before print"
    return value


def _assert_printed_payload(tree: ast.Module, expected_name: str) -> ast.expr:
    payload = _print_argument(tree)
    assert isinstance(payload, ast.Name) and payload.id == expected_name, (
        f"print() must use the final positional payload '{expected_name}'"
    )
    return _final_binding(tree, expected_name)


# ---------------------------------------------------------------------------
# Constant, concatenation, and input provenance checks
# ---------------------------------------------------------------------------


def _is_numeric_value(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _constant_value(node: ast.expr) -> object:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float)) and not isinstance(node.value, bool):
            return node.value
        return _MISSING
    if isinstance(node, ast.UnaryOp):
        return _unary_constant_value(node)
    if isinstance(node, ast.BinOp):
        return _binary_constant_value(node)
    return _MISSING


def _unary_constant_value(node: ast.UnaryOp) -> object:
    if not isinstance(node.op, _ALLOWED_UNARY_OPERATORS):
        return _MISSING
    operand = _constant_value(node.operand)
    if not _is_numeric_value(operand):
        return _MISSING
    return -operand if isinstance(node.op, ast.USub) else operand


def _binary_constant_value(node: ast.BinOp) -> object:
    left = _constant_value(node.left)
    right = _constant_value(node.right)
    if isinstance(left, str) and isinstance(right, str) and isinstance(node.op, ast.Add):
        return left + right
    if not _is_numeric_value(left) or not _is_numeric_value(right):
        return _MISSING
    return _numeric_binary_value(node.op, left, right)


def _numeric_binary_value(
    operator: ast.operator,
    left: int | float,
    right: int | float,
) -> object:
    try:
        if isinstance(operator, ast.Add):
            return left + right
        if isinstance(operator, ast.Sub):
            return left - right
        if isinstance(operator, ast.Mult):
            return left * right
        if isinstance(operator, ast.Div):
            return left / right
    except ZeroDivisionError:
        return _MISSING
    return _MISSING


def _assert_scaffold_values(tree: ast.Module, exercise_no: int) -> None:
    for name, expected in _ex.EX005_SCAFFOLD_ASSIGNMENTS[exercise_no].items():
        actual = _constant_value(_final_binding(tree, name))
        assert actual == expected, (
            f"Exercise {exercise_no} must keep '{name}' at {expected!r}; "
            f"the final binding is {actual!r}"
        )


def _expression_names(node: ast.expr) -> set[str]:
    names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
    function_names = {
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    return names - function_names


def _string_constants(node: ast.expr) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def _is_concatenation(node: ast.expr, names: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in names
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and _is_concatenation(node.left, names)
        and _is_concatenation(node.right, names)
    )


def _assert_concatenation_provenance(value: ast.expr, exercise_no: int) -> None:
    expected = set(_ex.EX005_CONCATENATION_VARIABLES[exercise_no])
    assert _is_concatenation(value, expected), (
        f"Exercise {exercise_no} must build its message with +"
    )
    assert _expression_names(value) == expected, (
        f"Exercise {exercise_no} must use exactly these live variables: "
        f"{sorted(expected)}"
    )


def _is_name_product(node: ast.expr, left_name: str, right_name: str) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return False
    return (
        isinstance(node.left, ast.Name)
        and isinstance(node.right, ast.Name)
        and {node.left.id, node.right.id} == {left_name, right_name}
    )


def _is_name_sum(node: ast.expr, left_name: str, right_name: str) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and isinstance(node.left, ast.Name)
        and isinstance(node.right, ast.Name)
        and {node.left.id, node.right.id} == {left_name, right_name}
    )


def _is_input_call(node: ast.AST, prompt: str | None = None) -> bool:
    if not isinstance(node, ast.Call) or not _is_direct_call(node, "input") or node.keywords:
        return False
    if prompt is None:
        return True
    return (
        len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == prompt
    )


def _assert_input_bindings(
    tree: ast.Module,
    exercise_no: int,
    names: tuple[str, str],
) -> None:
    prompts = _ex.EX005_INPUT_PROMPTS[exercise_no]
    for name, prompt in zip(names, prompts, strict=True):
        assert _is_input_call(_final_binding(tree, name), prompt), (
            f"Exercise {exercise_no} must assign '{name}' from input({prompt!r})"
        )
    bindings = _bindings_before_print(tree)
    assigned_inputs = {name for name, value in bindings.items() if _is_input_call(value)}
    assert assigned_inputs == set(names), (
        f"Exercise {exercise_no} must use exactly the two live input bindings"
    )
    input_calls = [node for node in ast.walk(tree) if _is_input_call(node)]
    assert len(input_calls) == _EXPECTED_INPUT_CALL_COUNT, (
        "Exercise cells must contain exactly two input() calls"
    )


def _assert_interactive_concatenation(
    tree: ast.Module,
    exercise_no: int,
    names: tuple[str, str],
    target: str,
) -> ast.expr:
    value = _assert_printed_payload(tree, target)
    _assert_input_bindings(tree, exercise_no, names)
    _assert_concatenation_provenance(value, exercise_no)
    return value


# ---------------------------------------------------------------------------
# Exercise-specific semantic checks
# ---------------------------------------------------------------------------


def _is_directed_subtraction(node: ast.expr, left_name: str, right_name: str) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Sub)
        and isinstance(node.left, ast.Name)
        and isinstance(node.right, ast.Name)
        and node.left.id == left_name
        and node.right.id == right_name
    )


def _is_difference(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Sub)
        and isinstance(node.left, ast.Name)
        and isinstance(node.right, ast.Name)
        and {node.left.id, node.right.id} == {"paid", "cost"}
    )


def _is_valid_change_expression(node: ast.expr) -> bool:
    if _is_directed_subtraction(node, "paid", "cost"):
        return True
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "abs"
        and not node.keywords
        and len(node.args) == 1
    ):
        return False
    return _is_difference(node.args[0])


def _linear_form(node: ast.expr) -> tuple[dict[str, float], float] | None:
    if isinstance(node, ast.Name):
        return ({node.id: 1.0}, 0.0) if node.id in {"length", "width"} else None
    if isinstance(node, ast.Constant):
        if not _is_numeric_value(node.value):
            return None
        return ({}, float(node.value))
    if isinstance(node, ast.UnaryOp):
        return _linear_unary(node)
    if isinstance(node, ast.BinOp):
        return _linear_binary(node)
    return None


def _linear_unary(node: ast.UnaryOp) -> tuple[dict[str, float], float] | None:
    if not isinstance(node.op, _ALLOWED_UNARY_OPERATORS):
        return None
    form = _linear_form(node.operand)
    if form is None:
        return None
    coefficients, constant = form
    if isinstance(node.op, ast.USub):
        return ({name: -value for name, value in coefficients.items()}, -constant)
    return coefficients, constant


def _linear_binary(node: ast.BinOp) -> tuple[dict[str, float], float] | None:
    left = _linear_form(node.left)
    right = _linear_form(node.right)
    if left is None or right is None:
        return None
    if isinstance(node.op, ast.Add):
        return _linear_sum(left, right, subtract=False)
    if isinstance(node.op, ast.Sub):
        return _linear_sum(left, right, subtract=True)
    if isinstance(node.op, ast.Div):
        return _linear_division(left, right)
    if isinstance(node.op, ast.Mult):
        return _linear_product(left, right)
    return None


def _linear_sum(
    left: tuple[dict[str, float], float],
    right: tuple[dict[str, float], float],
    *,
    subtract: bool,
) -> tuple[dict[str, float], float]:
    left_coefficients, left_constant = left
    right_coefficients, right_constant = right
    coefficients = dict(left_coefficients)
    for name, value in right_coefficients.items():
        sign = -1.0 if subtract else 1.0
        coefficients[name] = coefficients.get(name, 0.0) + sign * value
    constant = left_constant - right_constant if subtract else left_constant + right_constant
    return coefficients, constant


def _linear_division(
    left: tuple[dict[str, float], float],
    right: tuple[dict[str, float], float],
) -> tuple[dict[str, float], float] | None:
    left_coefficients, left_constant = left
    right_coefficients, right_constant = right
    if right_coefficients or math.isclose(right_constant, 0.0):
        return None
    return (
        {name: value / right_constant for name, value in left_coefficients.items()},
        left_constant / right_constant,
    )


def _linear_product(
    left: tuple[dict[str, float], float],
    right: tuple[dict[str, float], float],
) -> tuple[dict[str, float], float] | None:
    left_coefficients, left_constant = left
    right_coefficients, right_constant = right
    if left_coefficients and right_coefficients:
        return None
    if left_coefficients:
        return _scale_linear(left, right_constant)
    return _scale_linear(right, left_constant)


def _scale_linear(
    form: tuple[dict[str, float], float],
    factor: float,
) -> tuple[dict[str, float], float]:
    coefficients, constant = form
    return (
        {name: value * factor for name, value in coefficients.items()},
        constant * factor,
    )


def _assert_perimeter_expression(value: ast.expr) -> None:
    form = _linear_form(value)
    assert form is not None, "Exercise 9 must calculate from length and width"
    coefficients, constant = form
    assert math.isclose(coefficients.get("length", 0.0), 2.0)
    assert math.isclose(coefficients.get("width", 0.0), 2.0)
    assert math.isclose(constant, 0.0)


# ---------------------------------------------------------------------------
# Adversarial grammar and equivalence coverage
# ---------------------------------------------------------------------------

_ADVERSARIAL_SOURCES: tuple[str, ...] = (
    "total = 1\ntotal += 1\nprint(total)",
    "if True:\n    total = 1\nprint(total)",
    "total = 1 if True else 2\nprint(total)",
    "total = True and 1\nprint(total)",
    "total = 1 == 1\nprint(total)",
    "for value in (1,):\n    total = value\nprint(total)",
    "while True:\n    total = 1\nprint(total)",
    "try:\n    total = 1\nexcept Exception:\n    total = 2\nprint(total)",
    "with open('x') as stream:\n    total = 1\nprint(total)",
    "match 1:\n    case 1:\n        total = 1\nprint(total)",
    "def helper():\n    return 1\ntotal = helper()\nprint(total)",
    "total = (lambda: 1)()\nprint(total)",
    "class Helper:\n    pass\ntotal = 1\nprint(total)",
    "import os\ntotal = 1\nprint(total)",
    "from os import path\ntotal = 1\nprint(total)",
    "total = (value := 50)\nprint(total)",
    "values = [50]\ntotal = values[0]\nprint(total)",
    "values = {}\nvalues['key'] = 50\nprint(values)",
    "item = object()\ntotal = item.value\nprint(total)",
    "item = object()\nitem.value = 50\nprint(item)",
    "print = lambda value: value\ntotal = 1\nprint(total)",
    "input = lambda prompt='': 'x'\ntotal = 1\nprint(total)",
    "abs = lambda value: value\ntotal = 1\nprint(total)",
    "total = str(50)\nprint(total)",
    "total = [50]\nprint(total)",
    (
        "first_name = input('Enter first name: ')\n"
        "last_name = input('Enter last name: ')\n"
        "full_name = 'Maria Jones' if first_name == 'Maria' else 'Ada Lovelace'\n"
        "print(full_name)"
    ),
    (
        "age = input('Enter your age: ')\n"
        "city = input('Enter your city: ')\n"
        "message = 'You are 16' if age == '16' else 'You are 15'\n"
        "print(message)"
    ),
)

_PAYLOAD_BYPASS_SOURCES: tuple[str, ...] = (
    "total = 50\nprint(50)",
    'total = "50"\nprint("50")',
    "total = 50\nprint(total, 0)",
    "total = 50\nprint(total, sep='')",
    "total = 50 if True else 50\nprint(total)",
    "total = 50\nprint(total.value)",
)

_PROVENANCE_BYPASS_SOURCES: tuple[tuple[int, str, str], ...] = (
    (4, "message", "word1 = 'Hello'\nword2 = 'World'\nmessage = 'Hello' + ' ' + 'World'\nprint(message)"),
    (
        8,
        "sentence",
        "word1 = 'I'\nword2 = 'love'\nword3 = 'learning'\nword4 = 'Python'\n"
        "sentence = 'I' + ' ' + 'love' + ' ' + 'learning' + ' ' + 'Python'\n"
        "print(sentence)",
    ),
    (
        5,
        "full_name",
        "first_name = input('Enter first name: ')\nlast_name = input('Enter last name: ')\n"
        "full_name = 'Maria Jones'\nprint(full_name)",
    ),
    (
        10,
        "message",
        "age = input('Enter your age: ')\ncity = input('Enter your city: ')\n"
        "message = 'You are 16 years old and live in Birmingham'\nprint(message)",
    ),
)

_VALID_STRAIGHT_LINE_SOURCES: tuple[str, ...] = (
    "price = 10\nquantity = 5\ntotal = price * quantity\nprint(total)",
    "price: int = 10\nquantity: int = 5\ntotal: int = price * quantity\nprint(total)",
)


def _assert_guard_rejects(source: str) -> None:
    try:
        _assert_straight_line(ast.parse(source))
    except AssertionError:
        return
    raise AssertionError(f"Straight-line guard accepted a bypass:\n{source}")


def _assert_payload_guard_rejects(source: str, expected_name: str) -> None:
    try:
        _assert_printed_payload(ast.parse(source), expected_name)
    except AssertionError:
        return
    raise AssertionError(f"Printed-payload guard accepted a bypass:\n{source}")


def _assert_provenance_guard_rejects(
    source: str,
    exercise_no: int,
    target: str,
) -> None:
    try:
        value = _assert_printed_payload(ast.parse(source), target)
        _assert_concatenation_provenance(value, exercise_no)
    except AssertionError:
        return
    raise AssertionError(f"Concatenation provenance guard accepted a bypass:\n{source}")


def _assert_final_product_rejects(source: str) -> None:
    tree = ast.parse(source)
    value = _assert_printed_payload(tree, "total")
    if _is_name_product(value, "price", "quantity"):
        raise AssertionError(f"Final-binding guard accepted a hard-coded overwrite:\n{source}")


def _assert_adversarial_guards() -> None:
    for source in _ADVERSARIAL_SOURCES:
        _assert_guard_rejects(source)
    for source in _PAYLOAD_BYPASS_SOURCES:
        _assert_payload_guard_rejects(source, "total")
    for exercise_no, target, source in _PROVENANCE_BYPASS_SOURCES:
        _assert_provenance_guard_rejects(source, exercise_no, target)
    for overwrite_source in (
        "price = 10\nquantity = 5\ntotal = price * quantity\ntotal = 50\nprint(total)",
        "price = 10\nquantity = 5\ntotal = price * quantity\ntotal: int = 50\nprint(total)",
    ):
        _assert_final_product_rejects(overwrite_source)
    for source in _VALID_STRAIGHT_LINE_SOURCES:
        _assert_straight_line(ast.parse(source))


def _expression_from_source(source: str) -> ast.expr:
    statement = ast.parse(source).body[0]
    assert isinstance(statement, ast.Expr)
    return statement.value


def _check_explanation(exercise_no: int) -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH,
        tag=_explanation_tag(exercise_no),
    )
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX005_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX005_PLACEHOLDER_PHRASES,
    ), f"Exercise {exercise_no} needs a meaningful explanation"


# ---------------------------------------------------------------------------
# Canonical exercise tests
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_adversarial_construct_guards() -> None:
    _assert_adversarial_guards()
    value = _assert_printed_payload(_exercise_ast(1), "total")
    assert _is_name_product(value, "price", "quantity")


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _static_output(1) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    value = _assert_printed_payload(tree, "total")
    _assert_scaffold_values(tree, 1)
    assert _is_name_product(value, "price", "quantity")


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    _check_explanation(1)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _static_output(2) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    value = _assert_printed_payload(tree, "name")
    _assert_scaffold_values(tree, 2)
    assert isinstance(value, ast.Constant) and value.value == "Alice"


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    _check_explanation(2)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _static_output(3) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    value = _assert_printed_payload(tree, "area")
    _assert_scaffold_values(tree, 3)
    assert _is_name_product(value, "width", "height")


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    _check_explanation(3)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _static_output(4) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    value = _assert_printed_payload(tree, "message")
    _assert_scaffold_values(tree, 4)
    _assert_concatenation_provenance(value, 4)
    assert " " in _string_constants(value)


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    _check_explanation(4)


@pytest.mark.task(taskno=5)
def test_exercise5_input_flow() -> None:
    _assert_input_cases(5)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    value = _assert_interactive_concatenation(
        tree,
        5,
        ("first_name", "last_name"),
        "full_name",
    )
    assert " " in _string_constants(value)


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    _check_explanation(5)


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    assert _static_output(6) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    for source in ("paid - cost", "abs(cost - paid)", "abs(paid - cost)"):
        assert _is_valid_change_expression(_expression_from_source(source))
    tree = _exercise_ast(6)
    value = _assert_printed_payload(tree, "change")
    _assert_scaffold_values(tree, 6)
    assert _is_valid_change_expression(value)


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    _check_explanation(6)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    assert _static_output(7) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[7]


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    total = _final_binding(tree, "total")
    average = _assert_printed_payload(tree, "average")
    _assert_scaffold_values(tree, 7)
    assert _is_name_sum(total, "score1", "score2")
    assert (
        isinstance(average, ast.BinOp)
        and isinstance(average.op, ast.Div)
        and isinstance(average.right, ast.Constant)
        and average.right.value == _AVERAGE_DIVISOR
        and _expression_names(average) == {"total"}
    )


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    _check_explanation(7)


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    assert _static_output(8) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    value = _assert_printed_payload(tree, "sentence")
    _assert_scaffold_values(tree, 8)
    _assert_concatenation_provenance(value, 8)
    assert _string_constants(value).count(" ") >= _SENTENCE_GAP_COUNT


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    _check_explanation(8)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _static_output(9) == _ex.EX005_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    for source in (
        "length + length + width + width",
        "2 * length + 2 * width",
        "2 * (length + width)",
        "(2 * length + 2 * width) / 1",
    ):
        _assert_perimeter_expression(_expression_from_source(source))
    tree = _exercise_ast(9)
    value = _assert_printed_payload(tree, "perimeter")
    _assert_scaffold_values(tree, 9)
    _assert_perimeter_expression(value)


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    _check_explanation(9)


@pytest.mark.task(taskno=10)
def test_exercise10_input_flow() -> None:
    _assert_input_cases(10)


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    value = _assert_interactive_concatenation(tree, 10, ("age", "city"), "message")
    constants = _string_constants(value)
    assert any("live in " in constant for constant in constants) or {
        "live in",
        " ",
    } <= set(constants)


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    _check_explanation(10)
