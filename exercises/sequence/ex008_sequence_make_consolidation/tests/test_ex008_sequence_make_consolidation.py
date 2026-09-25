from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Final, Literal, cast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex008_sequence_make_consolidation"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()

_EXPECTED_INPUT_CALLS: Final = 2
_EXPECTED_EXERCISE1_VALUES: Final = ("Oakwood", "Coding", "Club")
_RESERVED_NAMES: Final[frozenset[str]] = frozenset({"print", "input", "int", "float", "str"})
_ALLOWED_CALLS: Final[frozenset[str]] = frozenset({"input", "int", "float", "str"})


class _StraightLineError(ValueError):
    """Raised when code falls outside the novice straight-line subset."""


@dataclass(frozen=True)
class _InputOrigin:
    key: tuple[int, int]
    cast: str | None


@dataclass(frozen=True)
class _Product:
    literal_dependencies: frozenset[str | int | float]
    dependencies: frozenset[str]
    origins: tuple[_InputOrigin, ...]


@dataclass(frozen=True)
class _FlowValue:
    literal: str | int | float | None
    literal_dependencies: frozenset[str | int | float]
    dependencies: frozenset[str]
    origins: tuple[_InputOrigin, ...]
    products: tuple[_Product, ...]


@dataclass(frozen=True)
class _PrintRecord:
    payloads: tuple[_FlowValue, ...]


@dataclass(frozen=True)
class _StraightLineAnalysis:
    bindings: dict[str, _FlowValue]
    inputs: tuple[_InputOrigin, ...]
    products: tuple[_Product, ...]
    prints: tuple[_PrintRecord, ...]


def _merge_origins(
    origin_groups: tuple[tuple[_InputOrigin, ...], ...],
) -> tuple[_InputOrigin, ...]:
    result: list[_InputOrigin] = []
    seen: set[tuple[tuple[int, int], str | None]] = set()
    for group in origin_groups:
        for origin in group:
            identity = (origin.key, origin.cast)
            if identity not in seen:
                seen.add(identity)
                result.append(origin)
    return tuple(result)


def _merge_products(
    product_groups: tuple[tuple[_Product, ...], ...],
) -> tuple[_Product, ...]:
    return tuple(product for group in product_groups for product in group)


def _combine_values(
    values: tuple[_FlowValue, ...],
    *,
    literal: str | int | float | None = None,
) -> _FlowValue:
    literal_dependencies: set[str | int | float] = set()
    dependencies: set[str] = set()
    for value in values:
        literal_dependencies.update(value.literal_dependencies)
        dependencies.update(value.dependencies)
    return _FlowValue(
        literal=literal,
        literal_dependencies=frozenset(literal_dependencies),
        dependencies=frozenset(dependencies),
        origins=_merge_origins(tuple(value.origins for value in values)),
        products=_merge_products(tuple(value.products for value in values)),
    )


def _add_name_dependency(value: _FlowValue, name: str) -> _FlowValue:
    return _FlowValue(
        literal=value.literal,
        literal_dependencies=value.literal_dependencies,
        dependencies=value.dependencies | {name},
        origins=value.origins,
        products=value.products,
    )


def _same_literal(value: str | int | float | None, expected: str | int | float) -> bool:
    return type(value) is type(expected) and value == expected


def _constant_value(node: ast.Constant) -> _FlowValue:
    value = node.value
    if isinstance(value, str):
        literal: str | int | float = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        literal = value
    else:
        raise _StraightLineError("Only text and numeric constants are allowed.")
    return _FlowValue(
        literal=literal,
        literal_dependencies=frozenset({literal}),
        dependencies=frozenset(),
        origins=(),
        products=(),
    )


def _try_add_literals(left: str | int | float, right: str | int | float) -> str | int | float:
    if isinstance(left, str) and isinstance(right, str):
        return left + right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left + right
    raise _StraightLineError("The two values cannot be joined with +.")


def _try_multiply_literals(left: str | int | float, right: str | int | float) -> str | int | float:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left * right
    if isinstance(left, str) and isinstance(right, int):
        return left * right
    if isinstance(left, int) and isinstance(right, str):
        return left * right
    raise _StraightLineError("The two values cannot be multiplied.")


def _cast_value(value: _FlowValue, cast_name: Literal["int", "float", "str"]) -> _FlowValue:
    origins = tuple(_InputOrigin(origin.key, cast_name) for origin in value.origins)
    literal = value.literal
    if cast_name == "str":
        literal = literal if isinstance(literal, str) else None
    elif cast_name == "int":
        if isinstance(literal, float) and literal.is_integer():
            literal = int(literal)
        elif not isinstance(literal, int):
            literal = None
    elif isinstance(literal, int):
        literal = float(literal)
    else:
        literal = None
    return _FlowValue(
        literal=literal,
        literal_dependencies=value.literal_dependencies,
        dependencies=value.dependencies,
        origins=origins,
        products=value.products,
    )


class _StraightLineAnalyzer:
    """Analyze only the simple top-level sequence used by this exercise."""

    def __init__(self) -> None:
        self.bindings: dict[str, _FlowValue] = {}
        self.inputs: list[_InputOrigin] = []
        self.products: list[_Product] = []
        self.prints: list[_PrintRecord] = []

    def analyze(self, tree: ast.Module) -> _StraightLineAnalysis:
        for statement in tree.body:
            self._analyze_statement(statement)
        return _StraightLineAnalysis(
            bindings=dict(self.bindings),
            inputs=tuple(self.inputs),
            products=tuple(self.products),
            prints=tuple(self.prints),
        )

    def _analyze_statement(self, statement: ast.stmt) -> None:
        if isinstance(statement, ast.Assign):
            self._analyze_assign(statement)
            return
        if isinstance(statement, ast.AnnAssign):
            self._analyze_annassign(statement)
            return
        if isinstance(statement, ast.Expr):
            self._analyze_expression_statement(statement)
            return
        raise _StraightLineError(f"Unsupported top-level statement: {type(statement).__name__}.")

    def _analyze_assign(self, statement: ast.Assign) -> None:
        if len(statement.targets) != 1:
            raise _StraightLineError("Use one target for each assignment.")
        self._bind_target(statement.targets[0], statement.value)

    def _analyze_annassign(self, statement: ast.AnnAssign) -> None:
        self._validate_annotation(statement.annotation)
        self._bind_annotated_target(statement.target, statement.value)

    def _validate_annotation(self, annotation: ast.expr | None) -> None:
        if annotation is not None and not isinstance(annotation, ast.Name):
            raise _StraightLineError("Annotations must be simple names.")

    def _bind_annotated_target(
        self,
        target: ast.AST,
        value_node: ast.expr | None,
    ) -> None:
        if value_node is None:
            raise _StraightLineError("An annotated assignment needs a value.")
        self._bind_target(target, value_node)

    def _analyze_expression_statement(self, statement: ast.Expr) -> None:
        if not isinstance(statement.value, ast.Call):
            raise _StraightLineError("Only print expressions are allowed.")
        if not self._is_print_call(statement.value):
            raise _StraightLineError("Only direct print() calls are allowed.")
        self._analyze_print(statement.value)

    def _bind_target(self, target: ast.AST, value_node: ast.expr) -> None:
        if isinstance(target, ast.Name):
            if target.id in _RESERVED_NAMES:
                raise _StraightLineError(f"Do not rebind {target.id}.")
            if target.id in self.bindings:
                raise _StraightLineError(f"Variable {target.id} is assigned more than once.")
            self.bindings[target.id] = self._evaluate_expression(value_node)
            return
        if isinstance(target, ast.Tuple):
            if not isinstance(value_node, ast.Tuple):
                raise _StraightLineError("Tuple targets need a tuple value.")
            if len(target.elts) != len(value_node.elts):
                raise _StraightLineError("Tuple targets and values need equal lengths.")
            for target_element, value_element in zip(
                target.elts,
                value_node.elts,
                strict=True,
            ):
                self._bind_target(target_element, value_element)
            return
        raise _StraightLineError("Only names and tuple targets are allowed.")

    def _analyze_print(self, call: ast.Call) -> None:
        if call.keywords:
            raise _StraightLineError("print() keywords are not part of this exercise.")
        payloads = tuple(self._evaluate_expression(argument) for argument in call.args)
        self.prints.append(_PrintRecord(payloads))

    @staticmethod
    def _is_print_call(call: ast.Call) -> bool:
        return isinstance(call.func, ast.Name) and call.func.id == "print"

    def _evaluate_expression(self, node: ast.expr) -> _FlowValue:
        if isinstance(node, ast.Constant):
            return _constant_value(node)
        if isinstance(node, ast.Name):
            if not isinstance(node.ctx, ast.Load):
                raise _StraightLineError("A name cannot be assigned in an expression.")
            if node.id in _RESERVED_NAMES or node.id not in self.bindings:
                raise _StraightLineError(f"Unknown or reserved name: {node.id}.")
            return _add_name_dependency(self.bindings[node.id], node.id)
        if isinstance(node, ast.BinOp):
            return self._evaluate_binop(node)
        if isinstance(node, ast.JoinedStr):
            return self._evaluate_joined_string(node)
        if isinstance(node, ast.Call):
            return self._evaluate_call(node)
        raise _StraightLineError(f"Unsupported expression: {type(node).__name__}.")

    def _evaluate_binop(self, node: ast.BinOp) -> _FlowValue:
        left = self._evaluate_expression(node.left)
        right = self._evaluate_expression(node.right)
        if isinstance(node.op, ast.Add):
            literal = None
            if left.literal is not None and right.literal is not None:
                literal = _try_add_literals(left.literal, right.literal)
            return _combine_values((left, right), literal=literal)
        if isinstance(node.op, ast.Mult):
            literal = None
            if left.literal is not None and right.literal is not None:
                literal = _try_multiply_literals(left.literal, right.literal)
            origins = _merge_origins((left.origins, right.origins))
            product = _Product(
                literal_dependencies=left.literal_dependencies | right.literal_dependencies,
                dependencies=left.dependencies | right.dependencies,
                origins=origins,
            )
            self.products.append(product)
            return _FlowValue(
                literal=literal,
                literal_dependencies=left.literal_dependencies | right.literal_dependencies,
                dependencies=left.dependencies | right.dependencies,
                origins=origins,
                products=left.products + right.products + (product,),
            )
        raise _StraightLineError("Only + and * are allowed.")

    def _evaluate_joined_string(self, node: ast.JoinedStr) -> _FlowValue:
        values: list[_FlowValue] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                values.append(_constant_value(part))
                continue
            if isinstance(part, ast.FormattedValue):
                if part.format_spec is not None or part.conversion != -1:
                    raise _StraightLineError("Only ordinary f-string values are allowed.")
                values.append(self._evaluate_expression(part.value))
                continue
            raise _StraightLineError("Unsupported f-string component.")
        return _combine_values(tuple(values))

    def _evaluate_call(self, node: ast.Call) -> _FlowValue:
        if not isinstance(node.func, ast.Name):
            raise _StraightLineError("Calls must name an allowed built-in directly.")
        name = node.func.id
        if name not in _ALLOWED_CALLS or node.keywords:
            raise _StraightLineError(f"Unsupported call: {name}.")
        if name == "input":
            return self._evaluate_input_call(node)
        return self._evaluate_cast_call(node, cast(Literal["int", "float", "str"], name))

    def _evaluate_input_call(self, node: ast.Call) -> _FlowValue:
        if len(node.args) > 1:
            raise _StraightLineError("input() accepts at most one prompt argument.")
        if node.args:
            prompt = self._evaluate_expression(node.args[0])
            if not isinstance(prompt.literal, str):
                raise _StraightLineError("The input prompt must be text.")
        origin = _InputOrigin((node.lineno, node.col_offset), None)
        self.inputs.append(origin)
        return _FlowValue(
            literal=None,
            literal_dependencies=frozenset(),
            dependencies=frozenset(),
            origins=(origin,),
            products=(),
        )

    def _evaluate_cast_call(
        self, node: ast.Call, cast_name: Literal["int", "float", "str"]
    ) -> _FlowValue:
        if len(node.args) != 1:
            raise _StraightLineError(f"{cast_name}() needs one positional value.")
        return _cast_value(self._evaluate_expression(node.args[0]), cast_name)


def _analyze_straight_line(tree: ast.Module) -> _StraightLineAnalysis:
    return _StraightLineAnalyzer().analyze(tree)


def _analyze_source(source: str) -> _StraightLineAnalysis:
    return _analyze_straight_line(ast.parse(source))


def _analysis(exercise_no: int) -> _StraightLineAnalysis:
    return _analyze_straight_line(_exercise_ast(exercise_no))


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=f"exercise{exercise_no}",
        cache=_CACHE,
    )
    return ast.parse(code)


def _run_static(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=f"exercise{exercise_no}",
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=f"exercise{exercise_no}",
        inputs=inputs,
        cache=_CACHE,
    )


def _input_case_params(exercise_no: int) -> list[object]:
    return [
        pytest.param(case, id=cast(str, case["id"])) for case in _ex.EX008_INPUT_CASES[exercise_no]
    ]


def _final_print_flow(analysis: _StraightLineAnalysis) -> _FlowValue:
    if not analysis.prints:
        raise _StraightLineError("A final print() is required.")
    payloads = analysis.prints[-1].payloads
    if not payloads:
        raise _StraightLineError("The final print() needs a positional payload.")
    return _combine_values(payloads)


def _all_print_flow(analysis: _StraightLineAnalysis) -> _FlowValue:
    if not analysis.prints:
        raise _StraightLineError("A print() is required.")
    return _combine_values(
        tuple(payload for record in analysis.prints for payload in record.payloads)
    )


def _names_for_literal(
    analysis: _StraightLineAnalysis,
    expected: str | int | float,
) -> set[str]:
    return {
        name for name, value in analysis.bindings.items() if _same_literal(value.literal, expected)
    }


def _assert_exercise1_flow(analysis: _StraightLineAnalysis) -> None:
    final_flow = _final_print_flow(analysis)
    names: dict[str, set[str]] = {
        expected: _names_for_literal(analysis, expected) & final_flow.dependencies
        for expected in _EXPECTED_EXERCISE1_VALUES
    }
    if not all(names.values()):
        raise _StraightLineError("The final message must use all three required variables.")
    required_names: set[str] = set()
    for expected in _EXPECTED_EXERCISE1_VALUES:
        required_names.update(names[expected])
    if len(required_names) != len(_EXPECTED_EXERCISE1_VALUES):
        raise _StraightLineError("Oakwood, Coding, and Club need distinct variables.")


def _assert_exercise2_flow(analysis: _StraightLineAnalysis) -> None:
    final_flow = _final_print_flow(analysis)
    all_print_flow = _all_print_flow(analysis)
    snack_names = _names_for_literal(analysis, "muffins") & all_print_flow.dependencies
    quantity_names = _names_for_literal(analysis, 4)
    price_names = _names_for_literal(analysis, 2)
    if not snack_names or not quantity_names or not price_names:
        raise _StraightLineError("The snack, quantity, and price variables are required.")
    for product in final_flow.products:
        quantity = {name for name in quantity_names if name in product.dependencies}
        price = {name for name in price_names if name in product.dependencies}
        if (
            len(quantity) == 1
            and len(price) == 1
            and len({next(iter(snack_names)), next(iter(quantity)), next(iter(price))})
            == len(_EXPECTED_EXERCISE1_VALUES)
        ):
            return
    raise _StraightLineError(
        "The final output must print a product made from the quantity and price variables."
    )


def _assert_exercise3_flow(analysis: _StraightLineAnalysis) -> None:
    if len(analysis.inputs) != _EXPECTED_INPUT_CALLS:
        raise _StraightLineError("Exercise 3 needs exactly two input() values.")
    final_flow = _final_print_flow(analysis)
    final_keys = {origin.key for origin in final_flow.origins}
    input_keys = {origin.key for origin in analysis.inputs}
    if not input_keys.issubset(final_keys):
        raise _StraightLineError("The final sentence must use both input values.")
    for origin in analysis.inputs:
        assigned_names = {
            name
            for name, value in analysis.bindings.items()
            if any(source.key == origin.key for source in value.origins)
        }
        if not assigned_names & final_flow.dependencies:
            raise _StraightLineError("Each input must be assigned before the final sentence.")


def _product_casts(product: _Product) -> dict[tuple[int, int], set[str | None]]:
    result: dict[tuple[int, int], set[str | None]] = {}
    for origin in product.origins:
        result.setdefault(origin.key, set()).add(origin.cast)
    return result


def _assert_numeric_flow(
    analysis: _StraightLineAnalysis,
    expected_casts: tuple[Literal["int", "float", "str"], ...],
) -> None:
    if len(analysis.inputs) != _EXPECTED_INPUT_CALLS:
        raise _StraightLineError("The numeric exercise needs exactly two input() values.")
    final_flow = _final_print_flow(analysis)
    input_keys = [origin.key for origin in analysis.inputs]
    for product in final_flow.products:
        casts = _product_casts(product)
        if not all(key in casts for key in input_keys):
            continue
        if len(expected_casts) == 1:
            if all(expected_casts[0] in casts[key] for key in input_keys):
                return
        elif (
            expected_casts[0] in casts[input_keys[0]] and expected_casts[1] in casts[input_keys[1]]
        ):
            return
    raise _StraightLineError(
        "The final positional print payload must contain the cast input product."
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _run_static(1) == _ex.EX008_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_exercise1_flow(_analysis(1))


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _run_static(2) == _ex.EX008_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_exercise2_flow(_analysis(2))


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize("case", _input_case_params(3))
def test_exercise3_logic(case: dict[str, object]) -> None:
    inputs = cast(list[str], case["inputs"])
    output = _run_with_inputs(3, inputs)
    assert output == cast(str, case["expected_output"]), (
        f"Exercise 3 with inputs {inputs!r} produced {output!r}."
    )


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_exercise3_flow(_analysis(3))


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("case", _input_case_params(4))
def test_exercise4_logic(case: dict[str, object]) -> None:
    inputs = cast(list[str], case["inputs"])
    output = _run_with_inputs(4, inputs)
    assert output == cast(str, case["expected_output"]), (
        f"Exercise 4 with inputs {inputs!r} produced {output!r}."
    )


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _assert_numeric_flow(_analysis(4), ("int",))


@pytest.mark.task(taskno=5)
@pytest.mark.parametrize("case", _input_case_params(5))
def test_exercise5_logic(case: dict[str, object]) -> None:
    inputs = cast(list[str], case["inputs"])
    output = _run_with_inputs(5, inputs)
    assert output == cast(str, case["expected_output"]), (
        f"Exercise 5 with inputs {inputs!r} produced {output!r}."
    )


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_numeric_flow(_analysis(5), ("float", "int"))


_ADVERSARIAL_SOURCES: Final[tuple[tuple[str, str], ...]] = (
    (
        "if-expression",
        "name = input()\nmessage = 'hello' if name else 'hi'\nprint(message)\n",
    ),
    (
        "boolean-expression",
        "name = input()\nmessage = name or 'unknown'\nprint(message)\n",
    ),
    (
        "comparison",
        "name = input()\nmessage = name == 'Aisha'\nprint(message)\n",
    ),
    (
        "if-statement",
        "name = input()\nif name == 'Aisha':\n    print('hello')\n",
    ),
    (
        "for-loop",
        "for value in ['Aisha']:\n    print(value)\n",
    ),
    (
        "while-loop",
        "count = 0\nwhile count < 1:\n    print(count)\n",
    ),
    (
        "helper-function",
        "def helper(value):\n    return value\nprint(helper('Aisha'))\n",
    ),
    ("import", "import os\nprint(os.getcwd())\n"),
    ("augmented-assignment", "value = 1\nvalue += 1\nprint(value)\n"),
    ("named-expression", "print((name := input()))\n"),
    ("subscript", "values = ['Aisha']\nprint(values[0])\n"),
    ("attribute", "value = 'Aisha'\nprint(value.upper())\n"),
    ("arbitrary-call", "print(len('Aisha'))\n"),
    ("print-rebinding", "print = input\nprint('Aisha')\n"),
    ("input-rebinding", "input = str\nname = input()\nprint(name)\n"),
)


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize(
    "source",
    [pytest.param(source, id=case_id) for case_id, source in _ADVERSARIAL_SOURCES],
)
def test_straight_line_analyzer_rejects_bypasses(source: str) -> None:
    _assert_exercise3_flow(_analysis(3))
    with pytest.raises(_StraightLineError):
        _analyze_source(source)


@pytest.mark.task(taskno=3)
def test_straight_line_analyzer_rejects_dead_source_last_print() -> None:
    _assert_exercise3_flow(_analysis(3))
    analysis = _analyze_source(
        "name = input()\nhobby = input()\n"
        "print('Hello ' + name + '! Your hobby is ' + hobby + '.')\n"
        "print('Hello Aisha! Your hobby is drawing.')\n"
    )
    with pytest.raises(_StraightLineError):
        _assert_exercise3_flow(analysis)


@pytest.mark.task(taskno=2)
def test_straight_line_analyzer_accepts_aliases_and_fstrings() -> None:
    _assert_exercise2_flow(_analysis(2))
    analysis = _analyze_source(
        "snack_name = 'muffins'\n"
        "quantity = 4\n"
        "price = 2\n"
        "result: int = price * quantity\n"
        "print(f'Snack box: {snack_name}')\n"
        "print(f'Total cost: {result} pounds')\n"
    )
    _assert_exercise2_flow(analysis)


@pytest.mark.task(taskno=3)
def test_straight_line_analyzer_accepts_tuple_inputs_and_fstrings() -> None:
    _assert_exercise3_flow(_analysis(3))
    analysis = _analyze_source(
        "name, hobby = input(), input()\nprint(f'Hello {name}! Your hobby is {hobby}.')\n"
    )
    _assert_exercise3_flow(analysis)


@pytest.mark.task(taskno=5)
def test_straight_line_analyzer_accepts_aliases_and_inline_casts() -> None:
    _assert_numeric_flow(_analysis(5), ("float", "int"))
    alias_case = _analyze_source(
        "first_text = input()\n"
        "second_text = input()\n"
        "first = int(first_text)\n"
        "second = int(second_text)\n"
        "left = first\n"
        "right = second\n"
        "result = left * right\n"
        "print('Total: ' + str(result))\n"
    )
    _assert_numeric_flow(alias_case, ("int",))
    inline_case = _analyze_source(
        "distance = float(input())\n"
        "walks = int(input())\n"
        "print('Total distance: ' + str(distance * walks) + ' km')\n"
    )
    _assert_numeric_flow(inline_case, ("float", "int"))
    direct_cast_case = _analyze_source(
        "print('Distance for one walk in km:')\n"
        "print('Number of walks:')\n"
        "print('Total distance: ' + str(float(input()) * int(input())) + ' km')\n"
    )
    _assert_numeric_flow(direct_cast_case, ("float", "int"))
