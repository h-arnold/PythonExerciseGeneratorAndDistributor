"""Conservative straight-line AST helpers for ex007 construct checks."""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from typing import Final, Literal, TypeGuard

ValueKind = Literal["text", "numeric", "tuple"]


@dataclass(frozen=True)
class _CastUse:
    name: str
    source_names: frozenset[str]
    input_names: frozenset[str]
    has_input_origin: bool
    operand_kind: ValueKind


@dataclass(frozen=True)
class _OperationUse:
    op_type: type[ast.operator]
    source_names: frozenset[str]
    input_names: frozenset[str]
    has_input_origin: bool


@dataclass(frozen=True)
class _ValueFacts:
    kind: ValueKind
    source_names: frozenset[str] = frozenset()
    input_names: frozenset[str] = frozenset()
    input_origin: bool = False
    empty_text: bool = False
    calls: frozenset[str] = frozenset()
    casts: tuple[_CastUse, ...] = ()
    operations: tuple[_OperationUse, ...] = ()
    elements: tuple[_ValueFacts, ...] = ()


@dataclass(frozen=True)
class OutputFlowAnalysis:
    input_names: frozenset[str]
    call_names: frozenset[str]
    op_types: frozenset[type[ast.operator]]
    input_dependent_calls: frozenset[str] = frozenset()
    input_dependent_ops: frozenset[type[ast.operator]] = frozenset()
    uses_lookup: bool = False
    uses_control_flow: bool = False


@dataclass(frozen=True)
class _FinalFlow:
    payload: _ValueFacts
    input_names: frozenset[str]
    input_count: int
    numeric_names: frozenset[str]


@dataclass(frozen=True)
class _ConstructConfig:
    expected_input_count: int
    required_calls: tuple[str, ...]
    required_ops: tuple[type[ast.operator], ...]
    forbidden_ops: tuple[type[ast.operator], ...]
    relevant_names: tuple[str, ...]


@dataclass
class _EvalContext:
    bindings: dict[str, _ValueFacts]


@dataclass
class _WalkState:
    context: _EvalContext
    input_names: set[str]
    input_count: int = 0
    payload: _ValueFacts | None = None


_RESERVED_NAMES: Final[frozenset[str]] = frozenset(
    {"input", "int", "float", "str", "print", "builtins", "__builtins__"}
)
_OPERATORS: Final[tuple[type[ast.operator], ...]] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)
_INPUTS: Final[frozenset[str]] = frozenset({"input", "builtins.input"})
_CASTS: Final[frozenset[str]] = frozenset({"int", "float", "str"})


def has_call(tree: ast.AST, name: str) -> bool:
    """Return whether the tree contains a named call."""
    return any(isinstance(node, ast.Call) and _call_name(node) == name for node in ast.walk(tree))


def has_binop(tree: ast.AST, op_type: type[ast.operator]) -> bool:
    """Return whether the tree contains a binary operator."""
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, op_type) for node in ast.walk(tree)
    )


def input_assigned_names(tree: ast.AST) -> set[str]:
    """Return direct input targets, including compact casts and tuple targets."""
    names: set[str] = set()
    if not isinstance(tree, ast.Module):
        return names
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            _collect_input_targets(statement.targets[0], statement.value, names)
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            _collect_input_targets(statement.target, statement.value, names)
    return names


def static_construct_issues(
    tree: ast.AST,
    *,
    required_calls: tuple[str, ...] = (),
    required_ops: tuple[type[ast.operator], ...] = (),
    forbidden_ops: tuple[type[ast.operator], ...] = (),
    relevant_names: tuple[str, ...] = (),
) -> list[str]:
    """Return issues for a conservative straight-line static cell."""
    return _construct_issues(
        tree,
        _ConstructConfig(0, required_calls, required_ops, forbidden_ops, relevant_names),
    )


def interactive_construct_issues(
    tree: ast.AST,
    *,
    expected_input_count: int,
    required_calls: tuple[str, ...] = (),
    required_ops: tuple[type[ast.operator], ...] = (),
    forbidden_ops: tuple[type[ast.operator], ...] = (),
) -> list[str]:
    """Return issues for a conservative straight-line input cell."""
    return _construct_issues(
        tree,
        _ConstructConfig(expected_input_count, required_calls, required_ops, forbidden_ops, ()),
    )


def _construct_issues(tree: ast.AST, config: _ConstructConfig) -> list[str]:
    flow, issue = _analyze_straight_line(tree)
    if issue is not None:
        return [issue]
    assert flow is not None
    if (
        flow.input_count != config.expected_input_count
        or len(flow.input_names) != config.expected_input_count
    ):
        return ["Use one clearly named variable for each entered value."]
    relevant = set(config.relevant_names) or set(flow.input_names) or set(flow.numeric_names)
    if not relevant:
        return ["Printed output must use a relevant task value."]
    if not relevant.issubset(flow.payload.source_names):
        return ["Printed output must use all relevant task values."]
    return _requirement_issues(flow, relevant, config)


def _analyze_straight_line(tree: ast.AST) -> tuple[_FinalFlow | None, str | None]:
    if not isinstance(tree, ast.Module):
        return None, "Use a simple straight-line Python cell."
    state = _WalkState(_EvalContext({}), set())
    issue = _walk_statements(tree.body, state)
    if issue is not None:
        return None, issue
    if state.payload is None:
        return None, "Print the final answer from the calculation."
    return _make_final_flow(state), None


def _walk_statements(statements: list[ast.stmt], state: _WalkState) -> str | None:
    for index, statement in enumerate(statements):
        if state.payload is not None:
            return "Put the final print after all calculations."
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            issue = _apply_assignment(statement, state)
            if issue is not None:
                return issue
            continue
        if isinstance(statement, ast.Expr) and _is_print_call(statement.value):
            if index != len(statements) - 1:
                return "Put the final print after all calculations."
            state.payload, issue = _analyze_print(statement.value, state.context)
            if issue is not None:
                return issue
            continue
        return _unsupported_statement_message(statement)
    return None


def _apply_assignment(statement: ast.Assign | ast.AnnAssign, state: _WalkState) -> str | None:
    bindings, counts, issue = _analyze_assignment(statement, state.context)
    if issue is not None:
        return issue
    for name, facts in bindings:
        if name in _RESERVED_NAMES:
            return "Do not rebind Python built-ins used by this exercise."
        state.context.bindings[name] = _bind_name(facts, name)
        if counts[name] > 0:
            state.input_names.add(name)
    state.input_count += sum(counts.values())
    return None


def _make_final_flow(state: _WalkState) -> _FinalFlow:
    payload = state.payload
    assert payload is not None
    return _FinalFlow(
        payload=payload,
        input_names=frozenset(state.input_names),
        input_count=state.input_count,
        numeric_names=frozenset(
            name for name, facts in state.context.bindings.items() if facts.kind == "numeric"
        ),
    )


def _analyze_assignment(
    statement: ast.Assign | ast.AnnAssign,
    context: _EvalContext,
) -> tuple[list[tuple[str, _ValueFacts]], dict[str, int], str | None]:
    target, issue = _single_target(statement)
    if issue is not None or target is None:
        return [], {}, issue or "Use a simple assignment target."
    value_node = statement.value
    if value_node is None:
        return [], {}, "Assignments need a value."
    value, value_issue = _eval_expr(value_node, context)
    if value_issue is not None or value is None:
        return [], {}, value_issue or "Use a supported expression."
    return _bind_assignment_value(target, value_node, value)


def _single_target(
    statement: ast.Assign | ast.AnnAssign,
) -> tuple[ast.expr | None, str | None]:
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1:
            return None, "Use one simple assignment target at a time."
        return statement.targets[0], None
    return statement.target, None


def _bind_assignment_value(
    target: ast.expr,
    value_node: ast.expr,
    value: _ValueFacts,
) -> tuple[list[tuple[str, _ValueFacts]], dict[str, int], str | None]:
    if isinstance(target, ast.Name):
        if value.kind == "tuple":
            return [], {}, "Assign tuple values to separate names."
        return [(target.id, value)], {target.id: _count_input_calls(value_node)}, None
    return _bind_tuple_assignment(target, value_node, value)


def _bind_tuple_assignment(
    target: ast.expr,
    value_node: ast.expr,
    value: _ValueFacts,
) -> tuple[list[tuple[str, _ValueFacts]], dict[str, int], str | None]:
    if not isinstance(target, ast.Tuple) or not isinstance(value_node, ast.Tuple):
        return [], {}, "Use simple names for assignments."
    if value.kind != "tuple" or len(target.elts) != len(value.elements):
        return [], {}, "Tuple assignments must have matching names and values."
    if any(isinstance(element, ast.Starred) for element in target.elts):
        return [], {}, "Use simple tuple assignment targets."
    bindings: list[tuple[str, _ValueFacts]] = []
    counts: dict[str, int] = {}
    for index, (target_element, value_facts) in enumerate(
        zip(target.elts, value.elements, strict=True)
    ):
        if not isinstance(target_element, ast.Name) or value_facts.kind == "tuple":
            return [], {}, "Use simple names for tuple assignments."
        bindings.append((target_element.id, value_facts))
        counts[target_element.id] = _count_input_calls(value_node.elts[index])
    return bindings, counts, None


def _analyze_print(
    print_call: ast.Call,
    context: _EvalContext,
) -> tuple[_ValueFacts | None, str | None]:
    if not _is_print_call(print_call):
        return None, "Use a simple print statement for the final answer."
    if print_call.keywords or not print_call.args:
        return None, "Use positional arguments in the final print statement."
    values: list[_ValueFacts] = []
    for argument in print_call.args:
        if _count_input_calls(argument) > 0:
            return None, "Assign each input value before printing."
        value, issue = _eval_expr(argument, context)
        if issue is not None or value is None:
            return None, issue or "Use supported print arguments."
        if value.kind == "tuple":
            return None, "Print simple values rather than tuple lookup data."
        values.append(value)
    return _combine_values(values, "tuple"), None


def _eval_expr(node: ast.AST, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    if isinstance(node, ast.Constant):
        result = _constant_facts(node.value)
    elif isinstance(node, ast.Name):
        result = _name_facts(node, context)
    elif isinstance(node, ast.Call):
        result = _call_facts(node, context)
    elif isinstance(node, ast.BinOp):
        result = _binop_facts(node, context)
    elif isinstance(node, ast.UnaryOp):
        result = _unary_facts(node, context)
    elif isinstance(node, ast.Tuple):
        result = _tuple_facts(node, context)
    elif isinstance(node, ast.JoinedStr):
        result = _joined_string_facts(node, context)
    else:
        return None, _unsupported_expression_message(node)
    return result


def _constant_facts(value: object) -> tuple[_ValueFacts | None, str | None]:
    if isinstance(value, str):
        return _ValueFacts(kind="text", empty_text=not value), None
    if type(value) in {int, float}:
        return _ValueFacts(kind="numeric"), None
    return None, "Use only text or numeric constants in this exercise."


def _name_facts(node: ast.Name, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    if node.id in context.bindings:
        return context.bindings[node.id], None
    return None, f"Use a value assigned earlier in the cell: {node.id}."


def _call_facts(node: ast.Call, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    if node.keywords:
        return None, "Use simple positional calls in this exercise."
    name = _call_name(node)
    if name in _INPUTS:
        return _input_call_facts(node, context, name)
    if name in _CASTS:
        return _cast_call_facts(node, context, name)
    if name == "print":
        return None, "Use print() only as the final top-level statement."
    return None, "Use only input(), int(), float(), str(), and print() in this exercise."


def _input_call_facts(
    node: ast.Call,
    context: _EvalContext,
    name: str,
) -> tuple[_ValueFacts | None, str | None]:
    if len(node.args) > 1:
        return None, "input() accepts at most one prompt value."
    if node.args:
        prompt, issue = _eval_expr(node.args[0], context)
        if issue is not None or prompt is None or prompt.kind == "tuple":
            return None, "Use a text prompt with input()."
    return _ValueFacts(kind="text", input_origin=True, calls=frozenset({name})), None


def _cast_call_facts(
    node: ast.Call,
    context: _EvalContext,
    name: str,
) -> tuple[_ValueFacts | None, str | None]:
    if len(node.args) != 1:
        return None, f"Use {name}() with one value."
    operand, issue = _eval_expr(node.args[0], context)
    if issue is not None or operand is None:
        return None, issue or "Use a supported cast operand."
    if operand.kind == "tuple":
        return None, "Do not cast tuple or lookup data."
    return _cast_facts(name, operand), None


def _cast_facts(name: str, operand: _ValueFacts) -> _ValueFacts:
    use = _CastUse(
        name=name,
        source_names=operand.source_names,
        input_names=operand.input_names,
        has_input_origin=operand.input_origin,
        operand_kind=operand.kind,
    )
    kind: ValueKind = "text" if name == "str" else "numeric"
    return replace(
        operand,
        kind=kind,
        empty_text=operand.empty_text if kind == "text" and operand.kind == "text" else False,
        calls=operand.calls | {name},
        casts=(*operand.casts, use),
    )


def _binop_facts(node: ast.BinOp, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    if not isinstance(node.op, _OPERATORS):
        return None, "Use only the arithmetic operators taught in this exercise."
    left, left_issue = _eval_expr(node.left, context)
    right, right_issue = _eval_expr(node.right, context)
    if left is None or right is None:
        return None, left_issue or right_issue or "Use supported operands."
    operator_type = type(node.op)
    if isinstance(node.op, ast.Add) and left.kind == "text" and right.kind == "text":
        return _combine_values([left, right], "text"), None
    if isinstance(node.op, ast.Mult) and {left.kind, right.kind} == {"text", "numeric"}:
        return _operation_values(left, right, operator_type, "text"), None
    if left.kind == "numeric" and right.kind == "numeric":
        return _operation_values(left, right, operator_type, "numeric"), None
    return None, "Do not mix text and numbers in arithmetic."


def _operation_values(
    left: _ValueFacts,
    right: _ValueFacts,
    operator_type: type[ast.operator],
    kind: ValueKind,
) -> _ValueFacts:
    use = _OperationUse(
        op_type=operator_type,
        source_names=left.source_names | right.source_names,
        input_names=left.input_names | right.input_names,
        has_input_origin=left.input_origin or right.input_origin,
    )
    return replace(
        _combine_values([left, right], kind),
        operations=(*left.operations, *right.operations, use),
    )


def _unary_facts(node: ast.UnaryOp, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    if not isinstance(node.op, (ast.UAdd, ast.USub)):
        return None, "Use only simple numeric unary operators."
    operand, issue = _eval_expr(node.operand, context)
    if issue is not None or operand is None:
        return None, issue or "Use a supported numeric operand."
    if operand.kind != "numeric":
        return None, "Unary operators require a number."
    return replace(operand, kind="numeric"), None


def _tuple_facts(node: ast.Tuple, context: _EvalContext) -> tuple[_ValueFacts | None, str | None]:
    values: list[_ValueFacts] = []
    for element in node.elts:
        value, issue = _eval_expr(element, context)
        if issue is not None or value is None:
            return None, issue or "Use simple tuple values."
        values.append(value)
    return _combine_values(values, "tuple"), None


def _joined_string_facts(
    node: ast.JoinedStr,
    context: _EvalContext,
) -> tuple[_ValueFacts | None, str | None]:
    values: list[_ValueFacts] = []
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            continue
        if not isinstance(part, ast.FormattedValue):
            return None, "Use simple f-string values only."
        if part.conversion != -1 or part.format_spec is not None:
            return None, "Use explicit casts in f-strings for this exercise."
        value, issue = _eval_expr(part.value, context)
        if issue is not None or value is None or value.kind == "tuple":
            return None, issue or "Use a simple value in the f-string."
        values.append(value)
    if not values:
        return _ValueFacts(kind="text", empty_text=True), None
    return replace(_combine_values(values, "text"), empty_text=False), None


def _combine_values(values: list[_ValueFacts], kind: ValueKind) -> _ValueFacts:
    return _ValueFacts(
        kind=kind,
        source_names=frozenset(name for value in values for name in value.source_names),
        input_names=frozenset(name for value in values for name in value.input_names),
        input_origin=any(value.input_origin for value in values),
        empty_text=kind == "text" and all(value.empty_text for value in values),
        calls=frozenset(name for value in values for name in value.calls),
        casts=tuple(use for value in values for use in value.casts),
        operations=tuple(use for value in values for use in value.operations),
        elements=tuple(values) if kind == "tuple" else (),
    )


def _bind_name(facts: _ValueFacts, name: str) -> _ValueFacts:
    return replace(
        facts,
        source_names=facts.source_names | {name},
        input_names=facts.input_names | ({name} if facts.input_origin else frozenset()),
    )


def _requirement_issues(
    flow: _FinalFlow,
    relevant_names: set[str],
    config: _ConstructConfig,
) -> list[str]:
    issues: list[str] = []
    for call_name in config.required_calls:
        if not any(_cast_matches(use, call_name, relevant_names) for use in flow.payload.casts):
            issues.append(f"Required cast {call_name}() must be applied to a relevant task value.")
    actual_ops = {
        use.op_type
        for use in flow.payload.operations
        if use.source_names & relevant_names or use.has_input_origin
    }
    for operator_type in config.required_ops:
        if operator_type not in actual_ops:
            issues.append(
                f"Required calculation operator {_operator_token(operator_type)} "
                "must operate on the relevant numeric values."
            )
    used_forbidden = [
        op
        for op in config.forbidden_ops
        if any(use.op_type is op for use in flow.payload.operations)
    ]
    if used_forbidden:
        issues.append(
            "Do not use "
            + ", ".join(_operator_token(op) for op in used_forbidden)
            + " in the final calculation."
        )
    return issues


def _cast_matches(use: _CastUse, call_name: str, relevant_names: set[str]) -> bool:
    if use.name != call_name:
        return False
    if call_name in {"int", "float"}:
        return use.has_input_origin or bool(use.input_names & relevant_names)
    if call_name == "str":
        return use.operand_kind == "numeric" and (
            bool(use.source_names & relevant_names) or use.has_input_origin
        )
    return bool(use.source_names & relevant_names)


def _count_input_calls(expression: ast.AST) -> int:
    return sum(1 for node in ast.walk(expression) if _is_input_call(node))


def _collect_input_targets(target: ast.expr, value: ast.expr, names: set[str]) -> None:
    if isinstance(target, ast.Name) and _count_input_calls(value) > 0:
        names.add(target.id)
        return
    if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple):
        if len(target.elts) != len(value.elts):
            return
        for target_element, value_element in zip(target.elts, value.elts, strict=True):
            if isinstance(target_element, ast.Name) and _count_input_calls(value_element) > 0:
                names.add(target_element.id)


def _is_print_call(node: ast.AST) -> TypeGuard[ast.Call]:
    return isinstance(node, ast.Call) and _call_name(node) == "print"


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "input"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "builtins"
    ):
        return "builtins.input"
    return None


def _is_input_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node) in _INPUTS


def _unsupported_statement_message(node: ast.AST) -> str:
    if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.Match)):
        return "Use straight-line code without conditionals or loops."
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
        return "Use simple assignments and expressions, not functions or classes."
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "Do not add imports to this exercise."
    if isinstance(node, (ast.AugAssign, ast.NamedExpr, ast.Subscript, ast.Attribute)):
        return "Use simple names, casts, and operators only."
    return "Use only simple assignments and one final print in this exercise."


def _unsupported_expression_message(node: ast.AST) -> str:
    if isinstance(node, (ast.BoolOp, ast.Compare, ast.IfExp)):
        return "Conditional expressions and boolean branches are not allowed."
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        return "Lookup tables and attribute side effects are not allowed."
    if isinstance(node, ast.NamedExpr):
        return "Named expressions are not allowed in this exercise."
    return "Use only simple assignments, casts, operators, and print()."


def _operator_token(operator_type: type[ast.operator]) -> str:
    mapping: dict[type[ast.operator], str] = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "//",
        ast.Mod: "%",
        ast.Pow: "**",
    }
    return mapping.get(operator_type, operator_type.__name__)
