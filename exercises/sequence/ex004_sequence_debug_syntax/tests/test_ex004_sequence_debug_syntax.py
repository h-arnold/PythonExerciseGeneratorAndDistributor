from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Final, TypeGuard

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

_EXERCISE_KEY = "ex004_sequence_debug_syntax"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_input(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


_ALLOWED_BINARY_OPERATORS: Final[tuple[type[ast.operator], ...]] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
)
_ALLOWED_UNARY_OPERATORS: Final[tuple[type[ast.unaryop], ...]] = (
    ast.UAdd,
    ast.USub,
)


@dataclass(frozen=True)
class _Value:
    """Small symbolic value used to follow straight-line assignments."""

    text: str | None = None
    fragments: tuple[str, ...] = ()
    number: int | float | None = None
    source_names: frozenset[str] = frozenset()
    input_names: frozenset[str] = frozenset()
    has_input: bool = False
    has_add: bool = False
    is_product: bool = False


@dataclass
class _SequenceAnalysis:
    """Validation and data-flow result for one tagged code cell."""

    issues: list[str]
    bindings: dict[str, _Value]
    final_print_values: list[_Value]


def _named_value(value: _Value, name: str) -> _Value:
    input_names = value.input_names
    if value.has_input:
        input_names = input_names | frozenset({name})
    return _Value(
        text=value.text,
        fragments=value.fragments,
        number=value.number,
        source_names=value.source_names | frozenset({name}),
        input_names=input_names,
        has_input=value.has_input,
        has_add=value.has_add,
        is_product=value.is_product,
    )


def _is_int_value(value: int | float | None, expected: int) -> bool:
    return type(value) is int and value == expected


class _StraightLineAnalyzer:
    """Analyze only assignments, annotated assignments, and expression statements."""

    def __init__(self) -> None:
        self.issues: list[str] = []
        self.bindings: dict[str, _Value] = {}
        self.final_print_values: list[_Value] = []

    def analyze(self, tree: ast.Module) -> _SequenceAnalysis:
        """Analyze top-level statements in execution order."""
        for statement in tree.body:
            self._analyze_statement(statement)
        return _SequenceAnalysis(
            issues=self.issues,
            bindings=self.bindings,
            final_print_values=self.final_print_values,
        )

    def _issue(self, message: str) -> None:
        self.issues.append(message)

    def _analyze_statement(self, statement: ast.stmt) -> None:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1:
                self._issue("chained assignments are not allowed")
                self._analyze_expression(statement.value)
                return
            self._bind_target(statement.targets[0], self._analyze_expression(statement.value))
            return

        if isinstance(statement, ast.AnnAssign):
            if statement.value is None:
                self._issue("annotated assignments need a value")
                return
            self._bind_target(statement.target, self._analyze_expression(statement.value))
            return

        if isinstance(statement, ast.Expr):
            if self._is_print_call(statement.value):
                self.final_print_values = self._analyze_print_call(statement.value)
            else:
                self._analyze_expression(statement.value)
            return

        self._issue(f"{type(statement).__name__} is not a straight-line statement")

    def _bind_target(self, target: ast.expr, value: _Value) -> None:
        if not isinstance(target, ast.Name):
            self._issue("assignment targets must be simple names")
            return
        if target.id in {"print", "input"}:
            self._issue(f"do not rebind {target.id}")
            return
        self.bindings[target.id] = _named_value(value, target.id)

    @staticmethod
    def _is_print_call(node: ast.expr) -> TypeGuard[ast.Call]:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        )

    def _analyze_print_call(self, call: ast.Call) -> list[_Value]:
        values = [self._analyze_expression(argument) for argument in call.args]
        for keyword in call.keywords:
            if keyword.arg not in {"sep", "end", "file", "flush"}:
                self._issue("print() has an unsupported keyword")
            self._analyze_expression(keyword.value)
        return values

    def _analyze_call(self, node: ast.Call) -> _Value:
        if not isinstance(node.func, ast.Name):
            return self._analyze_unsupported_call(node)
        if node.func.id == "print":
            self._issue("print() must be a top-level expression")
            self._analyze_print_call(node)
            return _Value()
        if node.func.id == "input":
            return self._analyze_input_call(node)
        return self._analyze_unsupported_call(node)

    def _analyze_input_call(self, node: ast.Call) -> _Value:
        if node.keywords:
            self._issue("input() does not accept keywords here")
        for argument in node.args:
            self._analyze_expression(argument)
        return _Value(has_input=True)

    def _analyze_unsupported_call(self, node: ast.Call) -> _Value:
        if isinstance(node.func, ast.Name):
            self._issue(f"unsupported function call: {node.func.id}")
        else:
            self._issue("only direct print() and input() calls are allowed")
        for argument in node.args:
            self._analyze_expression(argument)
        for keyword in node.keywords:
            self._analyze_expression(keyword.value)
        return _Value()

    def _analyze_expression(self, node: ast.expr) -> _Value:
        if isinstance(node, ast.Constant):
            return self._analyze_constant(node)
        if isinstance(node, ast.Name):
            return self._analyze_name(node)
        if isinstance(node, ast.BinOp):
            return self._analyze_binary(node)
        if isinstance(node, ast.UnaryOp):
            return self._analyze_unary(node)
        if isinstance(node, ast.Call):
            return self._analyze_call(node)
        self._issue(f"{type(node).__name__} is not allowed in a straight-line expression")
        return _Value()

    @staticmethod
    def _analyze_constant(node: ast.Constant) -> _Value:
        if isinstance(node.value, str):
            return _Value(text=node.value, fragments=(node.value,))
        if type(node.value) is int or type(node.value) is float:
            return _Value(number=node.value)
        return _Value()

    def _analyze_name(self, node: ast.Name) -> _Value:
        if node.id in self.bindings:
            return self.bindings[node.id]
        if node.id in {"print", "input"}:
            self._issue(f"{node.id} must be called, not used as a value")
        else:
            self._issue(f"unknown name: {node.id}")
        return _Value()

    def _analyze_binary(self, node: ast.BinOp) -> _Value:
        if not isinstance(node.op, _ALLOWED_BINARY_OPERATORS):
            self._issue("unsupported binary operator")
        left = self._analyze_expression(node.left)
        right = self._analyze_expression(node.right)
        return self._combine_binary(node, left, right)

    def _analyze_unary(self, node: ast.UnaryOp) -> _Value:
        if not isinstance(node.op, _ALLOWED_UNARY_OPERATORS):
            self._issue("unsupported unary operator")
        operand = self._analyze_expression(node.operand)
        if operand.number is None:
            return _Value(source_names=operand.source_names)
        if isinstance(node.op, ast.USub):
            return _Value(number=-operand.number, source_names=operand.source_names)
        return _Value(number=operand.number, source_names=operand.source_names)

    @staticmethod
    def _combine_binary(node: ast.BinOp, left: _Value, right: _Value) -> _Value:
        source_names = left.source_names | right.source_names
        input_names = left.input_names | right.input_names
        has_input = left.has_input or right.has_input
        if isinstance(node.op, ast.Add):
            text = (
                left.text + right.text if left.text is not None and right.text is not None else None
            )
            number = (
                left.number + right.number
                if left.number is not None and right.number is not None
                else None
            )
            return _Value(
                text=text,
                fragments=left.fragments + right.fragments,
                number=number,
                source_names=source_names,
                input_names=input_names,
                has_input=has_input,
                has_add=True,
            )
        if isinstance(node.op, ast.Mult):
            number = (
                left.number * right.number
                if left.number is not None and right.number is not None
                else None
            )
            is_product = (_is_int_value(left.number, 5) and _is_int_value(right.number, 10)) or (
                _is_int_value(left.number, 10) and _is_int_value(right.number, 5)
            )
            return _Value(
                number=number,
                source_names=source_names,
                input_names=input_names,
                has_input=has_input,
                is_product=is_product,
            )
        number = (
            left.number - right.number
            if left.number is not None and right.number is not None
            else None
        )
        return _Value(
            number=number,
            source_names=source_names,
            input_names=input_names,
            has_input=has_input,
        )


def _analyze_straight_line(tree: ast.Module) -> _SequenceAnalysis:
    return _StraightLineAnalyzer().analyze(tree)


def _analyze_source(source: str) -> _SequenceAnalysis:
    return _analyze_straight_line(ast.parse(source))


def _has_exact_print_value(analysis: _SequenceAnalysis, text: str) -> bool:
    return any(value.text == text for value in analysis.final_print_values)


def _has_learning_python_concatenation(analysis: _SequenceAnalysis) -> bool:
    return any(
        value.has_add
        and any("Learning" in fragment for fragment in value.fragments)
        and any("Python" in fragment for fragment in value.fragments)
        for value in analysis.final_print_values
    )


def _has_required_concatenation(
    analysis: _SequenceAnalysis,
    required_fragments: tuple[str, ...],
    require_input: bool,
) -> bool:
    return any(
        value.has_add
        and (not require_input or value.has_input)
        and all(
            any(required in fragment for fragment in value.fragments)
            for required in required_fragments
        )
        for value in analysis.final_print_values
    )


def _has_product(analysis: _SequenceAnalysis) -> bool:
    return any(value.is_product for value in analysis.final_print_values)


def _require_exact_output(analysis: _SequenceAnalysis, expected: str) -> None:
    assert _has_exact_print_value(analysis, expected)


def _require_learning_python(analysis: _SequenceAnalysis) -> None:
    assert _has_learning_python_concatenation(analysis)


def _require_product(analysis: _SequenceAnalysis) -> None:
    assert _has_product(analysis)


def _require_named_binding(
    analysis: _SequenceAnalysis,
    name: str,
    expected: str,
) -> None:
    binding = analysis.bindings.get(name)
    assert binding is not None and binding.text == expected
    assert any(name in value.source_names for value in analysis.final_print_values)


def _require_exercise_7(analysis: _SequenceAnalysis) -> None:
    assert _has_required_concatenation(
        analysis,
        ("You have ", " apples"),
        require_input=True,
    )


def _require_exercise_8(analysis: _SequenceAnalysis) -> None:
    assert _has_required_concatenation(analysis, ("Hello ",), require_input=True)


def _require_exercise_10(analysis: _SequenceAnalysis) -> None:
    assert _has_required_concatenation(
        analysis,
        ("My favourite colour is ",),
        require_input=True,
    )


_CONSTRUCT_CHECKS: Final[dict[int, Callable[[_SequenceAnalysis], None]]] = {
    1: partial(_require_exact_output, expected=_ex.EX004_EXPECTED_STATIC_OUTPUTS[1]),
    2: partial(_require_exact_output, expected=_ex.EX004_EXPECTED_STATIC_OUTPUTS[2]),
    3: _require_learning_python,
    4: _require_product,
    5: partial(_require_named_binding, name="name", expected="Alice"),
    6: partial(
        _require_named_binding,
        name="greeting",
        expected=_ex.EX004_EXPECTED_STATIC_OUTPUTS[6],
    ),
    7: _require_exercise_7,
    8: _require_exercise_8,
    9: partial(_require_exact_output, expected=_ex.EX004_EXPECTED_STATIC_OUTPUTS[9]),
    10: _require_exercise_10,
}


def _assert_canonical_construct(exercise_no: int) -> None:
    analysis = _analyze_straight_line(_exercise_ast(exercise_no))
    assert not analysis.issues, "; ".join(analysis.issues)
    check = _CONSTRUCT_CHECKS.get(exercise_no)
    if check is None:
        raise AssertionError(f"no construct rule for exercise {exercise_no}")
    check(analysis)


def _input_case_params(exercise_no: int) -> list[tuple[list[str], str]]:
    return [
        (list(case["inputs"]), case["expected_output"])
        for case in _ex.EX004_INPUT_CASES[exercise_no]
    ]


def _assert_valid_explanation(exercise_no: int) -> None:
    explanation = get_explanation_cell(
        _NOTEBOOK_PATH,
        tag=_explanation_tag(exercise_no),
    )
    assert is_valid_explanation(
        explanation,
        min_length=_ex.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex.EX004_PLACEHOLDER_PHRASES,
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _exercise_output(1) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    assert _exercise_output(1) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_canonical_construct(1)


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    _assert_valid_explanation(1)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _exercise_output(2) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    assert _exercise_output(2) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_canonical_construct(2)


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    _assert_valid_explanation(2)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _exercise_output(3) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    assert _exercise_output(3) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_canonical_construct(3)


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    _assert_valid_explanation(3)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _exercise_output(4) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    assert _exercise_output(4) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[4]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _assert_canonical_construct(4)


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    _assert_valid_explanation(4)


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    assert _exercise_output(5) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    assert _exercise_output(5) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_canonical_construct(5)


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    _assert_valid_explanation(5)


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    assert _exercise_output(6) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    assert _exercise_output(6) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[6]


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    _assert_canonical_construct(6)


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    _assert_valid_explanation(6)


@pytest.mark.task(taskno=7)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(7))
def test_exercise7_logic(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(7, inputs) == expected


@pytest.mark.task(taskno=7)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(7))
def test_exercise7_formatting(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(7, inputs) == expected


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    _assert_canonical_construct(7)


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    _assert_valid_explanation(7)


@pytest.mark.task(taskno=8)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(8))
def test_exercise8_logic(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(8, inputs) == expected


@pytest.mark.task(taskno=8)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(8))
def test_exercise8_formatting(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(8, inputs) == expected


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    _assert_canonical_construct(8)


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    _assert_valid_explanation(8)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _exercise_output(9) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    assert _exercise_output(9) == _ex.EX004_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    _assert_canonical_construct(9)


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    _assert_valid_explanation(9)


@pytest.mark.task(taskno=10)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(10))
def test_exercise10_logic(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(10, inputs) == expected


@pytest.mark.task(taskno=10)
@pytest.mark.parametrize(("inputs", "expected"), _input_case_params(10))
def test_exercise10_formatting(inputs: list[str], expected: str) -> None:
    assert _exercise_output_with_input(10, inputs) == expected


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    _assert_canonical_construct(10)


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    _assert_valid_explanation(10)


@pytest.mark.task(taskno=4)
def test_exercise4_rejects_false_branch() -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source("if False:\n    print(5 * 10)\nprint(50)")
    assert analysis.issues


@pytest.mark.task(taskno=4)
def test_exercise4_rejects_false_conditional() -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source("print(5 * 10 if False else 50)")
    assert analysis.issues


@pytest.mark.task(taskno=3)
def test_exercise3_rejects_dead_branch() -> None:
    _assert_canonical_construct(3)
    analysis = _analyze_source(
        "if False:\n    print('Learning' + 'Python')\nprint('Learning Python')"
    )
    assert analysis.issues


@pytest.mark.task(taskno=4)
def test_exercise4_rejects_boolean_neutralization() -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source("print((5 * 10) and 50)")
    assert analysis.issues


@pytest.mark.task(taskno=3)
def test_exercise3_rejects_conditional_concatenation() -> None:
    _assert_canonical_construct(3)
    analysis = _analyze_source("print('Learning' + 'Python' if False else 'Learning Python')")
    assert analysis.issues


@pytest.mark.task(taskno=3)
def test_exercise3_rejects_boolean_concatenation() -> None:
    _assert_canonical_construct(3)
    analysis = _analyze_source("print(('Learning' + 'Python') and 'Learning Python')")
    assert analysis.issues


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize(
    "source",
    [
        "left = 'Learning '\nright = 'Python'\nmessage = left + right\nprint(message)",
        "left = 'Learning'\nright = ' Python'\nmessage = left + right\nprint(message)",
    ],
)
def test_exercise3_accepts_alias_data_flow(source: str) -> None:
    _assert_canonical_construct(3)
    analysis = _analyze_source(source)
    assert not analysis.issues
    assert _has_learning_python_concatenation(analysis)


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("name", ["product", "result"])
def test_exercise4_accepts_product_alias(name: str) -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source(f"{name} = 5 * 10\nprint({name}, sep='')")
    assert not analysis.issues
    assert _has_product(analysis)


@pytest.mark.task(taskno=4)
def test_exercise4_accepts_annotated_product_alias() -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source("product: int = 5 * 10\nprint(product)")
    assert not analysis.issues
    assert _has_product(analysis)


@pytest.mark.task(taskno=7)
def test_exercise7_accepts_message_alias() -> None:
    _assert_canonical_construct(7)
    analysis = _analyze_source(
        "apples = input('How many apples? ')\n"
        "message = 'You have ' + apples + ' apples'\n"
        "print(message, sep='')"
    )
    assert not analysis.issues
    assert _has_required_concatenation(
        analysis,
        ("You have ", " apples"),
        require_input=True,
    )


@pytest.mark.task(taskno=8)
def test_exercise8_accepts_message_alias() -> None:
    _assert_canonical_construct(8)
    analysis = _analyze_source(
        "entered_name = input('Enter your name: ')\n"
        "message = 'Hello ' + entered_name\n"
        "print(message)"
    )
    assert not analysis.issues
    assert _has_required_concatenation(analysis, ("Hello ",), require_input=True)


@pytest.mark.task(taskno=10)
def test_exercise10_accepts_message_alias() -> None:
    _assert_canonical_construct(10)
    analysis = _analyze_source(
        "favourite_colour = input('What is your favourite colour? ')\n"
        "message = 'My favourite colour is ' + favourite_colour\n"
        "print(message)"
    )
    assert not analysis.issues
    assert _has_required_concatenation(
        analysis,
        ("My favourite colour is ",),
        require_input=True,
    )


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("keyword", ["end", "file", "flush"])
def test_exercise4_non_positional_keywords_do_not_count(keyword: str) -> None:
    _assert_canonical_construct(4)
    analysis = _analyze_source(f"print({keyword}=5 * 10)")
    assert not analysis.issues
    assert not _has_product(analysis)


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize(
    "source",
    [
        "if True:\n    print('Learning Python')",
        "print('Learning Python' if True else '')",
        "print(True and 'Learning Python')",
        "print(1 == 1)",
        "for _ in []:\n    print('Learning Python')",
        "while True:\n    print('Learning Python')",
        "def helper():\n    return 'Learning Python'",
        "import math",
        "message = ''\nmessage += 'Learning Python'",
        "print((message := 'Learning Python'))",
        "values = ['Learning Python']\nprint(values[0])",
        "print('Learning Python'.upper())",
        "print = print\nprint('Learning Python')",
        "input = input\nprint('Learning Python')",
    ],
)
def test_exercise3_rejects_non_straight_line_construct(source: str) -> None:
    _assert_canonical_construct(3)
    assert _analyze_source(source).issues
