"""Small straight-line provenance checks for ex007's input and output flows."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputFlowAnalysis:
    input_names: frozenset[str]
    call_names: frozenset[str]
    op_types: frozenset[type[ast.operator]]
    numeric_inputs: frozenset[str]
    numeric_ops: frozenset[type[ast.operator]]
    source_ops: frozenset[type[ast.operator]]


@dataclass
class _Value:
    inputs: set[str]
    calls: set[str]
    ops: set[type[ast.operator]]
    numeric_inputs: set[str]
    numeric_ops: set[type[ast.operator]]
    source_ops: set[type[ast.operator]]
    numeric_value: bool = False
    math_expr: ast.expr | None = None


def _empty() -> _Value:
    return _Value(set(), set(), set(), set(), set(), set())


def _merge(target: _Value, source: _Value) -> None:
    target.inputs.update(source.inputs)
    target.calls.update(source.calls)
    target.ops.update(source.ops)
    target.numeric_inputs.update(source.numeric_inputs)
    target.numeric_ops.update(source.numeric_ops)
    target.numeric_value = target.numeric_value or source.numeric_value
    target.source_ops.update(source.source_ops)
    if source.math_expr is not None:
        target.math_expr = source.math_expr


def _call_name(node: ast.Call) -> str | None:
    return node.func.id if isinstance(node.func, ast.Name) else None


def _evaluate(node: ast.expr, env: dict[str, _Value]) -> _Value:
    value = _empty()
    if isinstance(node, ast.Name):
        if node.id in env:
            _merge(value, env[node.id])
        return value
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        value.numeric_value = True
        value.math_expr = node
        return value
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        return _combine(left, type(node.op), right)
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.expr):
            _merge(value, _evaluate(child, env))
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name:
            value.calls.add(name)
            if name in {"int", "float"}:
                value.numeric_inputs.update(value.inputs)
                value.numeric_value = True
        if name == "str":
            # Numeric provenance is retained only when str wraps the actual value.
            value.numeric_inputs.update(
                _evaluate(node.args[0], env).numeric_inputs if node.args else ()
            )
            if node.args:
                value.numeric_value = _evaluate(node.args[0], env).numeric_value
            if value.numeric_value:
                value.calls.add("str_numeric")
    return value


def _simplify_binop(
    left: ast.expr, op: type[ast.operator], right: ast.expr
) -> ast.expr:
    """Fold numeric constants and harmless arithmetic identities."""
    left_number = _numeric_constant(left)
    right_number = _numeric_constant(right)
    if left_number is not None and right_number is not None:
        if op is ast.Add:
            return ast.Constant(value=left_number + right_number)
        if op is ast.Sub:
            return ast.Constant(value=left_number - right_number)
        if op is ast.Mult:
            return ast.Constant(value=left_number * right_number)
    if op is ast.Add and _is_number(left, 0):
        return right
    if op is ast.Add and _is_number(right, 0):
        return left
    if op is ast.Sub and _is_number(right, 0):
        return left
    if op is ast.Mult and (_is_number(left, 1) or _is_number(right, 1)):
        return right if _is_number(left, 1) else left
    if op is ast.Mult and (_is_number(left, 0) or _is_number(right, 0)):
        return ast.Constant(value=0)
    if op in {ast.Div, ast.FloorDiv} and _is_number(left, 0):
        return ast.Constant(value=0)
    if op in {ast.Div, ast.FloorDiv} and _is_number(right, 1):
        return left
    return ast.BinOp(left=left, op=op(), right=right)


def _combine(left: _Value, op: type[ast.operator], right: _Value) -> _Value:
    if op is ast.Mult and (
        _is_number(left.math_expr, 0) or _is_number(right.math_expr, 0)
    ):
        zero = _empty()
        zero.numeric_value = True
        zero.math_expr = ast.Constant(value=0)
        return zero
    if left.math_expr is None or right.math_expr is None:
        combined = _empty()
        _merge(combined, left)
        _merge(combined, right)
        combined.ops.add(op)
        combined.numeric_ops.add(op)
        return combined
    expression = _simplify_binop(left.math_expr, op, right.math_expr)
    if ast.dump(expression) == ast.dump(left.math_expr):
        combined = _copy_value(left)
    elif ast.dump(expression) == ast.dump(right.math_expr):
        combined = _copy_value(right)
    else:
        combined = _empty()
        _merge(combined, left)
        _merge(combined, right)
        combined.ops.add(op)
        combined.numeric_ops.add(op)
    combined.math_expr = expression
    combined.source_ops = {
        type(child.op) for child in ast.walk(expression) if isinstance(child, ast.BinOp)
    }
    return combined


def _copy_value(value: _Value) -> _Value:
    return _Value(
        inputs=set(value.inputs),
        calls=set(value.calls),
        ops=set(value.ops),
        numeric_inputs=set(value.numeric_inputs),
        numeric_ops=set(value.numeric_ops),
        source_ops=set(value.source_ops),
        numeric_value=value.numeric_value,
        math_expr=value.math_expr,
    )


def _numeric_constant(node: ast.expr) -> int | float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    return None


def _is_number(node: ast.expr | None, number: int) -> bool:
    if node is None:
        return False
    value = _numeric_constant(node)
    return value == number


def _analyze(tree: ast.AST) -> tuple[list[OutputFlowAnalysis], int]:
    env: dict[str, _Value] = {}
    outputs: list[OutputFlowAnalysis] = []
    inputs = 0
    for statement in getattr(tree, "body", []):
        if isinstance(statement, ast.Assign):
            value = _evaluate(statement.value, env)
            direct_input = sum(
                1
                for n in ast.walk(statement.value)
                if isinstance(n, ast.Call) and _call_name(n) == "input"
            )
            inputs += direct_input
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    stored = _Value(
                        inputs=set(value.inputs),
                        calls=set(value.calls),
                        ops=set(value.ops),
                        numeric_inputs=set(value.numeric_inputs),
                        numeric_ops=set(value.numeric_ops),
                        source_ops=set(value.source_ops),
                        numeric_value=value.numeric_value,
                        math_expr=value.math_expr,
                    )
                    if direct_input:
                        stored.inputs.add(target.id)
                    if direct_input and stored.math_expr is None:
                        stored.math_expr = ast.Name(id=target.id, ctx=ast.Load())
                    env[target.id] = stored
        elif isinstance(statement, ast.AugAssign) and isinstance(
            statement.target, ast.Name
        ):
            prior = env.get(statement.target.id, _empty())
            right = _evaluate(statement.value, env)
            env[statement.target.id] = _combine(prior, type(statement.op), right)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value
        ):
            assigned = _evaluate(statement.value, env)
            env[statement.target.id] = assigned
        elif (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _call_name(statement.value) == "print"
        ):
            value = _empty()
            for arg in statement.value.args:
                _merge(value, _evaluate(arg, env))
            outputs.append(
                OutputFlowAnalysis(
                    frozenset(value.inputs),
                    frozenset(value.calls),
                    frozenset(value.ops),
                    frozenset(value.numeric_inputs),
                    frozenset(value.numeric_ops),
                    frozenset(value.source_ops or ()),
                )
            )
    return outputs, inputs


def input_assigned_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for statement in getattr(tree, "body", []):
        if isinstance(statement, ast.Assign) and any(
            isinstance(node, ast.Call) and _call_name(node) == "input"
            for node in ast.walk(statement.value)
        ):
            names.update(
                target.id
                for target in statement.targets
                if isinstance(target, ast.Name)
            )
    return names


def printed_output_has_call(tree: ast.AST, name: str) -> bool:
    return any(
        ("str_numeric" if name == "str" else name) in output.call_names
        for output in _analyze(tree)[0]
    )


def printed_output_has_operator(tree: ast.AST, op_type: type[ast.operator]) -> bool:
    return any(op_type in output.numeric_ops for output in _analyze(tree)[0])


def printed_output_has_source_operator(
    tree: ast.AST, op_type: type[ast.operator]
) -> bool:
    """Check that an operator combines values traced to assigned source variables."""
    return any(op_type in output.source_ops for output in _analyze(tree)[0])


def interactive_construct_issues(
    tree: ast.AST,
    *,
    expected_input_count: int,
    required_calls: tuple[str, ...] = (),
    required_ops: tuple[type[ast.operator], ...] = (),
    forbidden_ops: tuple[type[ast.operator], ...] = (),
) -> list[str]:
    outputs, input_count = _analyze(tree)
    if input_count != expected_input_count:
        return ["Use a variable for each entered value before doing the calculation."]
    inputs = frozenset(input_assigned_names(tree))
    relevant = [output for output in outputs if inputs.issubset(output.input_names)]
    if not relevant:
        return ["Printed output must use all entered value variables."]
    if any(
        set(required_calls).issubset(o.call_names)
        and set(required_ops).issubset(o.numeric_ops)
        and not set(forbidden_ops).intersection(o.numeric_ops)
        for o in relevant
    ):
        return []
    issues: list[str] = []
    if required_calls and not any(
        set(required_calls).issubset(o.call_names) for o in relevant
    ):
        issues.append(
            "Printed result must come from calculations that use "
            + ", ".join(f"{c}()" for c in required_calls)
            + "."
        )
    if required_ops and not any(
        set(required_ops).issubset(o.numeric_ops) for o in relevant
    ):
        issues.append(
            "Printed result must come from calculations that use "
            + ", ".join(_operator_token(o) for o in required_ops)
            + "."
        )
    forbidden = [
        op for op in forbidden_ops if any(op in o.numeric_ops for o in relevant)
    ]
    if forbidden:
        issues.append(
            "Printed result must not use "
            + ", ".join(_operator_token(o) for o in forbidden)
            + "."
        )
    return issues


def _operator_token(operator_type: type[ast.operator]) -> str:
    tokens: dict[type[ast.operator], str] = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "//",
    }
    return tokens.get(operator_type, operator_type.__name__)
