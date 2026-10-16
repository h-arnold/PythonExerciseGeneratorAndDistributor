"""Small straight-line provenance checks shared by pytest and self-checks."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from typing import cast

Value = tuple[object, ...]


def _value(
    node: ast.AST,
    names: dict[str, Value],
    outputs: list[Value],
    inputs: list[Value],
) -> Value:
    if isinstance(node, ast.Constant):
        return ("constant", node.value)
    if isinstance(node, ast.Name):
        return names.get(node.id, ("name", node.id))
    if isinstance(node, (ast.Tuple, ast.List)):
        return ("sequence", *(_value(element, names, outputs, inputs) for element in node.elts))
    if isinstance(node, ast.BinOp):
        operator = type(node.op).__name__
        return (
            operator,
            _value(node.left, names, outputs, inputs),
            _value(node.right, names, outputs, inputs),
        )
    if isinstance(node, ast.JoinedStr):
        return ("joined", *(_value(part, names, outputs, inputs) for part in node.values))
    if isinstance(node, ast.FormattedValue):
        return ("formatted", _value(node.value, names, outputs, inputs))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        args = tuple(_value(arg, names, outputs, inputs) for arg in node.args)
        if node.func.id == "input":
            ordinal = len(inputs)
            prompt = args[0] if args else ("constant", "")
            inputs.append(("prompt", prompt))
            return ("input", ordinal)
        return (node.func.id, *args)
    return ("unsupported",)


def provenance(source: str) -> tuple[list[Value], list[Value]]:
    """Return immutable print expressions and prompt values in execution order."""
    tree = ast.parse(source)
    names: dict[str, Value] = {}
    printed: list[Value] = []
    inputs: list[Value] = []

    def bind(target: ast.expr, value: Value) -> None:
        if isinstance(target, ast.Name):
            names[target.id] = value
        elif (
            isinstance(target, (ast.Tuple, ast.List))
            and value[0] == "sequence"
            and len(target.elts) == len(value) - 1
        ):
            for child_target, child_value in zip(target.elts, value[1:], strict=True):
                if isinstance(child_value, tuple):
                    bind(child_target, cast(Value, child_value))

    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            # Evaluate the right-hand side against the old environment, then bind all targets.
            value = _value(statement.value, names, printed, inputs)
            for target in statement.targets:
                bind(target, value)
        elif isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            target_name = statement.target.id
            previous = names.get(target_name, ("name", target_name))
            right = _value(statement.value, names, printed, inputs)
            names[target_name] = (type(statement.op).__name__, previous, right)
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
            if isinstance(call.func, ast.Name) and call.func.id == "print":
                printed.append(
                    ("print", *(_value(arg, names, printed, inputs) for arg in call.args))
                )
    return printed, inputs


def _walk(value: Value) -> Iterator[Value]:
    yield value
    for child in value[1:]:
        if isinstance(child, tuple):
            yield from _walk(cast(Value, child))


def _cast_from(expression: Value, cast: str, original: Value) -> bool:
    return any(
        len(node) >= 2 and node[0] == cast and node[1] == original for node in _walk(expression)
    )


def _live_operator(
    expression: Value,
    operator_name: str,
    required_casts: tuple[str, ...] = (),
) -> bool:
    return any(
        node[0] == operator_name
        and all(any(part[0] == cast for part in _walk(node)) for cast in required_casts)
        for node in _walk(expression)
    )


def _evaluate(
    value: Value,
    constants: dict[object, object],
    input_values: dict[int, str],
) -> object:
    """Evaluate the small literal/cast/arithmetic provenance vocabulary used here."""
    kind = value[0]
    if kind == "constant":
        constant = value[1]
        return constants.get(constant, constant)
    if kind == "input":
        ordinal = value[1]
        return input_values.get(ordinal, "") if isinstance(ordinal, int) else ""
    if kind in {"int", "float", "str"} and len(value) > 1 and isinstance(value[1], tuple):
        converted = _evaluate(cast(Value, value[1]), constants, input_values)
        if kind == "int" and isinstance(converted, (int, float, str)):
            return int(converted)
        if kind == "float" and isinstance(converted, (int, float, str)):
            return float(converted)
        if kind == "str":
            return str(converted)
        return NotImplemented
    if kind in {"Add", "Mult"}:
        if len(value) < 3 or not isinstance(value[1], tuple) or not isinstance(value[2], tuple):
            return NotImplemented
        left = _evaluate(cast(Value, value[1]), constants, input_values)
        right = _evaluate(cast(Value, value[2]), constants, input_values)
        if kind == "Add":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
        if kind == "Mult":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left * right
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(left, int) and isinstance(right, str):
                return left * right
        return NotImplemented
    if kind == "formatted" and len(value) > 1 and isinstance(value[1], tuple):
        return str(_evaluate(cast(Value, value[1]), constants, input_values))
    if kind == "joined":
        return "".join(
            str(_evaluate(cast(Value, part), constants, input_values))
            for part in value[1:]
            if isinstance(part, tuple)
        )
    if kind == "print":
        return " ".join(
            str(_evaluate(cast(Value, part), constants, input_values))
            for part in value[1:]
            if isinstance(part, tuple)
        )
    return NotImplemented


def _output_values(
    printed: list[Value],
    constants: dict[object, object] | None = None,
    input_values: dict[int, str] | None = None,
) -> list[object]:
    constant_changes = constants or {}
    supplied_inputs = input_values or {}
    return [_evaluate(line, constant_changes, supplied_inputs) for line in printed]


def complete(task: int, source: str) -> bool:
    """Check required source values, conversions, and operations reach printed output."""
    printed, _ = provenance(source)
    expressions = [
        cast(Value, part) for line in printed for part in line[1:] if isinstance(part, tuple)
    ]

    def has_cast(cast_name: str, original: Value) -> bool:
        return any(_cast_from(expr, cast_name, original) for expr in expressions)

    requirements: dict[int, tuple[tuple[str, Value], ...]] = {
        1: (("int", ("constant", "5")), ("int", ("constant", "10"))),
        2: (("float", ("constant", "2.5")), ("float", ("constant", "3.5"))),
        3: (("int", ("constant", "7")),),
        4: (("str", ("constant", 500)),),
        5: (("int", ("constant", 25.9)),),
        6: (("int", ("input", 0)),),
        7: (("float", ("input", 0)),),
        8: (("int", ("constant", "10")), ("int", ("constant", "5"))),
        9: (("str", ("constant", 5.5)),),
        10: (("float", ("input", 0)), ("float", ("input", 1))),
    }
    if not all(has_cast(cast, original) for cast, original in requirements[task]):
        return False
    required_operators: dict[int, tuple[str, ...]] = {
        1: ("Add",),
        2: ("Add",),
        3: ("Mult",),
        4: ("Add",),
        6: ("Add", "Mult"),
        7: ("Add",),
        8: ("Mult",),
        10: ("Add",),
    }
    operators = required_operators.get(task, ())
    if operators and not any(
        _live_operator(expr, operator_name, tuple(name for name, _ in requirements[task]))
        for expr in expressions
        for operator_name in operators
    ):
        return False

    input_defaults: dict[int, str] = {
        6: {0: "6"},
        7: {0: "1.5"},
        10: {0: "10", 1: "20"},
    }.get(task, {})
    baseline = _output_values(printed, input_values=input_defaults)
    dependencies: dict[int, tuple[tuple[str, object, object], ...]] = {
        1: (("constant", "5", "6"), ("constant", "10", "11")),
        2: (("constant", "2.5", "4.5"), ("constant", "3.5", "4.5")),
        3: (("constant", "7", "8"), ("constant", 4, 5)),
        4: (("constant", 500, 501),),
        5: (("constant", 25.9, 26.9),),
        6: (("input", 0, "8"),),
        7: (("input", 0, "2.75"),),
        8: (("constant", "10", "11"), ("constant", "5", "6")),
        9: (("constant", 5.5, 6.5),),
        10: (("input", 0, "11"), ("input", 1, "21")),
    }
    for source_kind, original, changed in dependencies[task]:
        if source_kind == "constant":
            perturbed = _output_values(
                printed, constants={original: changed}, input_values=input_defaults
            )
        else:
            if not isinstance(original, int) or not isinstance(changed, str):
                return False
            ordinal = original
            perturbed_inputs = {**input_defaults, ordinal: changed}
            perturbed = _output_values(printed, input_values=perturbed_inputs)
        if perturbed == baseline:
            return False
    return True


def matches_segments(output: str, segments: list[str]) -> bool:
    """Match ordered messages, allowing flexible whitespace within and between them."""
    flexible_segments = [
        r"\s+".join(re.escape(word) for word in segment.split()) for segment in segments
    ]
    pattern = r"\A\s*" + r"\s*".join(flexible_segments) + r"\s*\Z"
    return re.fullmatch(pattern, output) is not None
