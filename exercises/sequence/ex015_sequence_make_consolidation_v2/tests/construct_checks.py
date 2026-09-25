"""Conservative sequence validation and data-flow checks for ex015."""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Final, TypeGuard

_Position = tuple[int, int]
_Literal = str | int | float
_Operator = type[ast.operator]

_MAX_INPUT_ARGS = 1
_MAX_ROUND_ARGS = 2
_PENCIL_PACK_SIZE = 24
_ERASER_PACK_SIZE = 15
_EXERCISE_PART_COUNT = 10
_PROTECTED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "abs",
        "eval",
        "exec",
        "float",
        "input",
        "int",
        "len",
        "max",
        "min",
        "open",
        "print",
        "round",
        "str",
        "sum",
    }
)
_ALLOWED_VALUE_CALLS: Final[frozenset[str]] = frozenset(
    {"float", "input", "int", "round", "str"}
)
_ALLOWED_OPERATORS: Final[frozenset[_Operator]] = frozenset(
    {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow}
)


@dataclass(frozen=True)
class _Binding:
    """One top-level name binding and its source-order index."""

    name: str
    value: ast.expr
    index: int


@dataclass(frozen=True)
class _Flow:
    """Names, literals, input provenance, and live operations in an expression."""

    names: frozenset[str] = frozenset()
    constants: frozenset[_Literal] = frozenset()
    input_ids: frozenset[int] = frozenset()
    casts: frozenset[tuple[int, str]] = frozenset()
    operations: tuple[_Operation, ...] = ()
    rounds: tuple[_RoundCall, ...] = ()
    formatted_names: frozenset[str] = frozenset()
    has_fstring: bool = False


@dataclass(frozen=True)
class _Operation:
    """One allowed binary operation and its operand flows."""

    operator: _Operator
    left: _Flow
    right: _Flow
    position: _Position


@dataclass(frozen=True)
class _RoundCall:
    """One live round call and the flow of its value argument."""

    digits: int | None
    flow: _Flow
    position: _Position


@dataclass(frozen=True)
class _Spec:
    """Construct requirements for one exercise part."""

    input_count: int
    casts: tuple[str, ...]
    operators: tuple[_Operator, ...]
    round_digits: tuple[int, ...]


@dataclass(frozen=True)
class _Pattern:
    """Required properties of one operand or operation."""

    source_ids: frozenset[int] = frozenset()
    names: frozenset[str] = frozenset()
    constants: frozenset[_Literal] = frozenset()


@dataclass(frozen=True)
class _OperationPattern:
    """A required operation and optional operand constraints."""

    operator: _Operator
    left: _Pattern | None = None
    right: _Pattern | None = None
    names: frozenset[str] = frozenset()
    constants: frozenset[_Literal] = frozenset()
    allow_reversed: bool = False


@dataclass(frozen=True)
class SequenceAnalysis:
    """Public result of conservative sequence analysis."""

    issues: tuple[str, ...]
    flow: _Flow
    payload_names: frozenset[str]
    payload_operators: tuple[_Operator, ...]
    payload_rounds: tuple[int | None, ...]
    payload_constants: frozenset[_Literal]
    payload_input_ids: frozenset[int]
    payload_casts: frozenset[tuple[int, str]]


_SPECS: Final[dict[int, _Spec]] = {
    1: _Spec(0, (), (ast.FloorDiv, ast.Mod), ()),
    2: _Spec(0, (), (ast.Mult, ast.Add, ast.Sub, ast.FloorDiv), ()),
    3: _Spec(1, ("int",), (ast.Mult,), ()),
    4: _Spec(2, ("int", "int"), (ast.Mult, ast.FloorDiv, ast.Mod), ()),
    5: _Spec(2, ("float", "float"), (ast.Mult,), (2,)),
    6: _Spec(1, ("int",), (ast.Mult, ast.Div, ast.Add), (1,)),
    7: _Spec(2, ("int", "int"), (ast.FloorDiv, ast.Mod), ()),
    8: _Spec(1, ("int",), (ast.Mult, ast.Pow), (2,)),
    9: _Spec(3, ("float", "int", "int"), (ast.Mult, ast.Div, ast.Add), (2,)),
    10: _Spec(
        3,
        ("int", "int", "int"),
        (ast.Mult, ast.Add, ast.Sub, ast.FloorDiv),
        (),
    ),
}
_STATIC_ORDER: Final[dict[int, tuple[tuple[str, int | None], ...]]] = {
    1: (
        ("total_sweets", 50),
        ("sweets_per_bag", 7),
        ("full_bags", None),
        ("sweets_left", None),
    ),
    2: (
        ("width", 5),
        ("height", 3),
        ("coverage_per_can", 12),
        ("area", None),
        ("cans_needed", None),
        ("paint_left", None),
    ),
}


def analyze_sequence(tree: ast.AST) -> SequenceAnalysis:
    """Analyze only positional f-string payload of top-level result prints."""

    if not isinstance(tree, ast.Module):
        return _public_analysis(("The exercise code must be a top-level Python module.",), _Flow())

    issues = _validate_tree(tree)
    assignments = _assignments_by_name(tree)
    input_positions = _input_positions(tree)
    input_ids = {position: index for index, position in enumerate(input_positions, 1)}
    result_prints = _result_prints(tree, input_positions)
    if not result_prints:
        issues.append("Print the result with a top-level positional f-string.")

    flows: list[_Flow] = []
    for call, before in result_prints:
        flows.append(
            _payload_flow(
                call,
                _Context(assignments, before, input_ids, frozenset()),
                issues,
            )
        )
    payload = _merge_flows(flows)
    issues.extend(_dead_operation_issues(tree, payload))
    return _public_analysis(tuple(_deduplicate(issues)), payload)


def construct_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return structural, input-count, and printed-construct problems."""

    analysis = analyze_sequence(tree)
    issues = list(analysis.issues)
    spec = _SPECS.get(exercise_no)
    if spec is None:
        return [*issues, f"No construct specification exists for exercise {exercise_no}."]

    input_positions = _input_positions(tree) if isinstance(tree, ast.Module) else []
    if len(input_positions) != spec.input_count:
        issues.append(
            f"Use exactly {spec.input_count} input() call(s); found {len(input_positions)}."
        )
    if not analysis.flow.has_fstring:
        issues.append("Each result line must use a positional f-string.")
    issues.extend(
        f"The printed payload must use {_operator_name(operator)}."
        for operator in spec.operators
        if not _has_operation(analysis.flow, _OperationPattern(operator))
    )
    issues.extend(
        f"The printed payload must use round(..., {digits})."
        for digits in spec.round_digits
        if not _has_round(analysis.flow, digits)
    )
    return _deduplicate(issues)


def data_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return provenance, cast, and task-specific calculated-flow problems."""

    analysis = analyze_sequence(tree)
    issues = list(analysis.issues)
    spec = _SPECS.get(exercise_no)
    if spec is None:
        return [*issues, f"No data-flow specification exists for exercise {exercise_no}."]

    input_positions = _input_positions(tree) if isinstance(tree, ast.Module) else []
    if len(input_positions) != spec.input_count:
        issues.append(
            f"Use exactly {spec.input_count} input() call(s); found {len(input_positions)}."
        )
    else:
        for index in range(1, len(input_positions) + 1):
            if index not in analysis.flow.input_ids:
                issues.append(f"The value from input() {index} must reach the printed payload.")
            elif spec.casts[index - 1] not in {
                cast_name for source_id, cast_name in analysis.flow.casts if source_id == index
            }:
                issues.append(
                    f"Input {index} must be converted with {spec.casts[index - 1]}() "
                    "before it reaches the printed payload."
                )
    if isinstance(tree, ast.Module):
        issues.extend(_task_flow_issues(tree, exercise_no, analysis.flow))
    return _deduplicate(issues)


# ---------------------------------------------------------------------------
# Grammar validation
# ---------------------------------------------------------------------------


def _validate_tree(tree: ast.Module) -> list[str]:
    issues: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            issues.extend(_validate_assignment(statement))
        elif isinstance(statement, ast.AnnAssign):
            issues.extend(_validate_annassign(statement))
        elif isinstance(statement, ast.Expr) and _is_print_call(statement.value):
            issues.extend(_validate_print_call(statement.value))
        else:
            issues.append(_statement_issue(statement))
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            issues.extend(_validate_fstring(node))
    return _deduplicate(issues)


def _validate_assignment(statement: ast.Assign) -> list[str]:
    issues: list[str] = []
    if len(statement.targets) != 1:
        issues.append("Use one assignment target per statement.")
    for target in statement.targets:
        issues.extend(_validate_target(target))
    issues.extend(_validate_expression(statement.value, allow_tuple=True))
    return issues


def _validate_annassign(statement: ast.AnnAssign) -> list[str]:
    issues = _validate_target(statement.target)
    if statement.value is None:
        issues.append("An annotated assignment must have a value.")
    else:
        issues.extend(_validate_expression(statement.value, allow_tuple=True))
    return issues


def _validate_target(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [f"Do not rebind the protected name {target.id!r}."] if target.id in _PROTECTED_NAMES else []
    if isinstance(target, ast.Tuple):
        return [issue for element in target.elts for issue in _validate_target(element)]
    return ["Use only name or tuple assignment targets."]


def _validate_print_call(call: ast.Call) -> list[str]:
    issues: list[str] = []
    for argument in call.args:
        issues.extend(_validate_expression(argument, allow_tuple=False))
    for keyword in call.keywords:
        issues.extend(_validate_expression(keyword.value, allow_tuple=False))
    return issues


def _validate_expression(expression: ast.AST, *, allow_tuple: bool) -> list[str]:
    if isinstance(expression, ast.Constant):
        return _validate_constant(expression)
    if isinstance(expression, ast.Name):
        return _validate_name(expression)
    if isinstance(expression, ast.BinOp):
        return _validate_binop(expression)
    if isinstance(expression, ast.UnaryOp):
        return _validate_unary(expression)
    if isinstance(expression, ast.Call):
        return _validate_value_call(expression)
    return _validate_other_expression(expression, allow_tuple=allow_tuple)


def _validate_other_expression(expression: ast.AST, *, allow_tuple: bool) -> list[str]:
    if isinstance(expression, ast.JoinedStr):
        return _validate_fstring(expression)
    if isinstance(expression, ast.Tuple):
        return _validate_tuple_expression(expression, allow_tuple=allow_tuple)
    if isinstance(expression, ast.List):
        return ["List expressions are not allowed in this sequence exercise."]
    return [_unsupported_expression_issue(expression)]


def _validate_constant(expression: ast.Constant) -> list[str]:
    if isinstance(expression.value, bool) or not isinstance(expression.value, (str, int, float)):
        return ["Use only text or numeric constants."]
    return []


def _validate_name(expression: ast.Name) -> list[str]:
    if expression.id in _PROTECTED_NAMES:
        return [f"Do not use or rebind the protected name {expression.id!r}."]
    return []


def _validate_binop(expression: ast.BinOp) -> list[str]:
    issues: list[str] = []
    if type(expression.op) not in _ALLOWED_OPERATORS:
        issues.append("Use only the taught arithmetic operators.")
    issues.extend(_validate_expression(expression.left, allow_tuple=False))
    issues.extend(_validate_expression(expression.right, allow_tuple=False))
    return issues


def _validate_unary(expression: ast.UnaryOp) -> list[str]:
    if type(expression.op) not in {ast.UAdd, ast.USub}:
        return ["Unary operators are limited to positive and negative signs."]
    return _validate_expression(expression.operand, allow_tuple=False)


def _validate_tuple_expression(expression: ast.Tuple, *, allow_tuple: bool) -> list[str]:
    if not allow_tuple:
        return ["Tuple expressions are only allowed for tuple assignments."]
    return [
        issue
        for element in expression.elts
        for issue in _validate_expression(element, allow_tuple=False)
    ]


def _validate_value_call(call: ast.Call) -> list[str]:
    if not isinstance(call.func, ast.Name):
        return ["Calls must use direct taught function names."]
    name = call.func.id
    if name == "print":
        return ["print() may only be a top-level expression statement."]
    if name not in _ALLOWED_VALUE_CALLS:
        return [f"Arbitrary side-effect call {name!r} is not allowed."]
    if name == "input":
        return _validate_input_call(call)
    if name == "round":
        return _validate_round_call(call)
    return _validate_cast_call(call, name)


def _validate_input_call(call: ast.Call) -> list[str]:
    issues: list[str] = []
    if len(call.args) > _MAX_INPUT_ARGS:
        issues.append("input() accepts at most one prompt argument.")
    if any(keyword.arg != "prompt" for keyword in call.keywords):
        issues.append("input() only accepts a prompt keyword.")
    for argument in call.args:
        issues.extend(_validate_expression(argument, allow_tuple=False))
    for keyword in call.keywords:
        if keyword.arg == "prompt":
            issues.extend(_validate_expression(keyword.value, allow_tuple=False))
    return issues


def _validate_round_call(call: ast.Call) -> list[str]:
    issues: list[str] = []
    if len(call.args) > _MAX_ROUND_ARGS or any(
        keyword.arg != "ndigits" for keyword in call.keywords
    ):
        issues.append("round() accepts only its value and optional ndigits argument.")
    for argument in call.args:
        issues.extend(_validate_expression(argument, allow_tuple=False))
    for keyword in call.keywords:
        if keyword.arg == "ndigits":
            issues.extend(_validate_expression(keyword.value, allow_tuple=False))
    return issues


def _validate_cast_call(call: ast.Call, name: str) -> list[str]:
    if len(call.args) != 1 or call.keywords:
        return [f"{name}() accepts exactly one positional value."]
    return _validate_expression(call.args[0], allow_tuple=False)


def _validate_fstring(expression: ast.JoinedStr) -> list[str]:
    issues: list[str] = []
    for value in expression.values:
        if isinstance(value, ast.Constant):
            if not isinstance(value.value, str):
                issues.append("F-string literal parts must be text.")
            continue
        if not isinstance(value, ast.FormattedValue):
            issues.append("F-strings may contain only text and formatted values.")
            continue
        issues.extend(_validate_expression(value.value, allow_tuple=False))
        if value.conversion not in {-1, ord("s")}:
            issues.append("Only no conversion or the safe !s conversion is allowed.")
        format_spec = value.format_spec
        if format_spec is not None and _format_spec_is_nonempty(format_spec):
            issues.append("F-string format specifications must be empty.")
            issues.extend(_validate_format_spec(format_spec))
    return issues


def _validate_format_spec(format_spec: ast.AST) -> list[str]:
    """Validate expressions hidden inside a nonempty format specification."""
    issues: list[str] = []
    if not isinstance(format_spec, ast.JoinedStr):
        return [_unsupported_expression_issue(format_spec)]
    for node in ast.walk(format_spec):
        if isinstance(node, ast.Call):
            issues.extend(_validate_value_call(node))
        elif isinstance(
            node,
            (ast.BoolOp, ast.Compare, ast.IfExp, ast.Subscript, ast.Attribute, ast.NamedExpr),
        ):
            issues.append(_unsupported_expression_issue(node))
    return issues


def _statement_issue(statement: ast.stmt) -> str:
    message = "Use only assignments and top-level print() expression statements."
    if isinstance(statement, (ast.If, ast.IfExp)):
        message = "Conditional control flow is not allowed."
    elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
        message = "Loops are not allowed in this sequence exercise."
    elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
        message = "Functions and classes are not allowed in this sequence exercise."
    elif isinstance(statement, (ast.Import, ast.ImportFrom)):
        message = "Imports are not allowed in this sequence exercise."
    elif isinstance(statement, ast.AugAssign):
        message = "Augmented assignments are not allowed; use one simple assignment."
    elif isinstance(statement, ast.NamedExpr):
        message = "Named expressions are not allowed in this sequence exercise."
    elif isinstance(statement, ast.Expr):
        message = "Only top-level print() expression statements are allowed."
    return message


def _unsupported_expression_issue(expression: ast.AST) -> str:
    rules = (
        (ast.BoolOp, "Boolean expressions are not allowed in this sequence exercise."),
        (ast.Compare, "Comparisons are not allowed in this sequence exercise."),
        (ast.IfExp, "Conditional expressions are not allowed in this sequence exercise."),
        (ast.Subscript, "Subscript lookups are not allowed in this sequence exercise."),
        (ast.Attribute, "Attribute access is not allowed in this sequence exercise."),
        (ast.NamedExpr, "Named expressions are not allowed in this sequence exercise."),
        ((ast.Dict, ast.List, ast.Set), "Lookup containers are not allowed in this sequence exercise."),
        ((ast.Lambda, ast.comprehension), "Functions and comprehensions are not allowed in this sequence exercise."),
    )
    message = "Use only constants, names, taught calls, and arithmetic expressions."
    for node_type, rule_message in rules:
        if isinstance(expression, node_type):
            message = rule_message
            break
    return message


def _format_spec_is_nonempty(format_spec: ast.AST | None) -> bool:
    if format_spec is None:
        return False
    if not isinstance(format_spec, ast.JoinedStr):
        return True
    return any(
        not (isinstance(value, ast.Constant) and value.value == "")
        for value in format_spec.values
    )


# ---------------------------------------------------------------------------
# Top-level bindings and symbolic flow tracing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Context:
    assignments: dict[str, list[_Binding]]
    before: int
    input_ids: dict[_Position, int]
    seen: frozenset[int]


def _assignments_by_name(tree: ast.Module) -> dict[str, list[_Binding]]:
    assignments: dict[str, list[_Binding]] = {}
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            _bind_target(statement.targets[0], statement.value, index, assignments)
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            _bind_target(statement.target, statement.value, index, assignments)
    return assignments


def _bind_target(
    target: ast.AST,
    value: ast.expr,
    index: int,
    assignments: dict[str, list[_Binding]],
) -> None:
    if isinstance(target, ast.Name):
        assignments.setdefault(target.id, []).append(_Binding(target.id, value, index))
    elif (
        isinstance(target, ast.Tuple)
        and isinstance(value, ast.Tuple)
        and len(target.elts) == len(value.elts)
    ):
        for target_element, value_element in zip(target.elts, value.elts, strict=True):
            _bind_target(target_element, value_element, index, assignments)


def _latest_binding(
    name: str,
    before: int,
    assignments: dict[str, list[_Binding]],
) -> _Binding | None:
    eligible = [binding for binding in assignments.get(name, ()) if binding.index < before]
    return eligible[-1] if eligible else None


def _input_positions(tree: ast.Module) -> list[_Position]:
    return sorted(
        _position(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) == "input"
    )


def _result_prints(
    tree: ast.Module,
    input_positions: list[_Position],
) -> list[tuple[ast.Call, int]]:
    prints = [
        (statement.value, index)
        for index, statement in enumerate(tree.body)
        if isinstance(statement, ast.Expr) and _is_print_call(statement.value)
    ]
    if not input_positions:
        return prints
    cutoff = max(input_positions)
    return [
        (call, index)
        for call, index in prints
        if _position(call) > cutoff or _print_contains_input(call, input_positions)
    ]


def _payload_flow(
    call: ast.Call,
    context: _Context,
    issues: list[str],
) -> _Flow:
    if not call.args:
        issues.append("Each result print() must have a positional f-string payload.")
        return _Flow()
    flows: list[_Flow] = []
    for argument in call.args:
        if not isinstance(argument, ast.JoinedStr):
            issues.append("Only positional f-strings count as printed result payload.")
            continue
        if not any(isinstance(value, ast.FormattedValue) for value in argument.values):
            issues.append("Each result f-string must contain at least one placeholder.")
        flows.append(_trace_fstring(argument, context))
    return _merge_flows(flows)


def _trace_fstring(expression: ast.JoinedStr, context: _Context) -> _Flow:
    flows: list[_Flow] = []
    direct_names: set[str] = set()
    for value in expression.values:
        if isinstance(value, ast.FormattedValue):
            if isinstance(value.value, ast.Name):
                direct_names.add(value.value.id)
            flows.append(_trace_expression(value.value, context))
    payload = _merge_flows(flows)
    return _Flow(
        names=payload.names,
        constants=payload.constants,
        input_ids=payload.input_ids,
        casts=payload.casts,
        operations=payload.operations,
        rounds=payload.rounds,
        formatted_names=frozenset(direct_names),
        has_fstring=True,
    )


def _trace_expression(expression: ast.AST, context: _Context) -> _Flow:
    if isinstance(expression, ast.Constant):
        return _flow_for_constant(expression)
    if isinstance(expression, ast.Name):
        return _trace_name(expression, context)
    if isinstance(expression, ast.BinOp):
        return _trace_binop(expression, context)
    return _trace_other_expression(expression, context)


def _trace_other_expression(expression: ast.AST, context: _Context) -> _Flow:
    if isinstance(expression, ast.UnaryOp):
        return _trace_expression(expression.operand, context)
    if isinstance(expression, ast.Call):
        return _trace_call(expression, context)
    if isinstance(expression, ast.JoinedStr):
        return _trace_fstring(expression, context)
    if isinstance(expression, ast.Tuple):
        return _merge_flows(_trace_expression(element, context) for element in expression.elts)
    return _Flow()


def _trace_name(expression: ast.Name, context: _Context) -> _Flow:
    base = _Flow(names=frozenset({expression.id}))
    if expression.id in _PROTECTED_NAMES:
        return base
    binding = _latest_binding(expression.id, context.before, context.assignments)
    if binding is None or binding.index in context.seen:
        return base
    nested = _trace_expression(
        binding.value,
        _Context(context.assignments, binding.index, context.input_ids, context.seen | {binding.index}),
    )
    return _merge_flows((base, nested))


def _trace_binop(expression: ast.BinOp, context: _Context) -> _Flow:
    left = _trace_expression(expression.left, context)
    right = _trace_expression(expression.right, context)
    operation = _Operation(type(expression.op), left, right, _position(expression))
    return _merge_flows((left, right, _Flow(operations=(operation,))))


def _trace_call(call: ast.Call, context: _Context) -> _Flow:
    name = _call_name(call)
    argument_flows = [_trace_expression(argument, context) for argument in call.args]
    keyword_flows = [_trace_expression(keyword.value, context) for keyword in call.keywords]
    flow = _merge_flows((*argument_flows, *keyword_flows))
    if name == "input":
        return replace(flow, input_ids=frozenset({context.input_ids[_position(call)]}))
    if name in {"int", "float", "str"}:
        return replace(
            flow,
            casts=frozenset((*flow.casts, *((source, name) for source in flow.input_ids))),
        )
    if name == "round":
        return replace(
            flow,
            rounds=(*flow.rounds, _RoundCall(_round_digits(call, argument_flows, keyword_flows), flow, _position(call))),
        )
    return flow


def _round_digits(
    call: ast.Call,
    argument_flows: list[_Flow],
    keyword_flows: list[_Flow],
) -> int | None:
    if len(call.args) >= _MAX_ROUND_ARGS:
        digits = _single_int_constant(argument_flows[1])
        if digits is not None:
            return digits
    for keyword, flow in zip(call.keywords, keyword_flows, strict=True):
        if keyword.arg == "ndigits":
            return _single_int_constant(flow)
    return None


def _single_int_constant(flow: _Flow) -> int | None:
    values = [value for value in flow.constants if type(value) is int]
    return values[0] if len(values) == 1 else None


def _flow_for_constant(expression: ast.Constant) -> _Flow:
    if isinstance(expression.value, bool) or not isinstance(expression.value, (str, int, float)):
        return _Flow()
    return _Flow(constants=frozenset({expression.value}))


def _merge_flows(flows: Iterable[_Flow]) -> _Flow:
    names: set[str] = set()
    constants: set[_Literal] = set()
    input_ids: set[int] = set()
    casts: set[tuple[int, str]] = set()
    operations: list[_Operation] = []
    rounds: list[_RoundCall] = []
    formatted_names: set[str] = set()
    has_fstring = False
    for flow in flows:
        names.update(flow.names)
        constants.update(flow.constants)
        input_ids.update(flow.input_ids)
        casts.update(flow.casts)
        operations.extend(flow.operations)
        rounds.extend(flow.rounds)
        formatted_names.update(flow.formatted_names)
        has_fstring = has_fstring or flow.has_fstring
    return _Flow(
        names=frozenset(names),
        constants=frozenset(constants),
        input_ids=frozenset(input_ids),
        casts=frozenset(casts),
        operations=tuple(operations),
        rounds=tuple(rounds),
        formatted_names=frozenset(formatted_names),
        has_fstring=has_fstring,
    )


def _dead_operation_issues(tree: ast.Module, flow: _Flow) -> list[str]:
    live_operations = {(operation.operator, operation.position) for operation in flow.operations}
    all_operations = {
        (type(node.op), _position(node))
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp)
    }
    issues: list[str] = []
    if all_operations - live_operations:
        issues.append("Every arithmetic operation must contribute to the positional printed payload.")
    live_rounds = {call.position for call in flow.rounds}
    all_rounds = {
        _position(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) == "round"
    }
    if all_rounds - live_rounds:
        issues.append("Every rounding operation must contribute to the positional printed payload.")
    return issues


# ---------------------------------------------------------------------------
# Task-specific semantic checks
# ---------------------------------------------------------------------------

_TaskChecker = Callable[[ast.Module, _Flow], list[str]]


def _task_flow_issues(tree: ast.Module, exercise_no: int, flow: _Flow) -> list[str]:
    checker = _TASK_CHECKERS.get(exercise_no)
    return [] if checker is None else checker(tree, flow)


def _pet_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return _require(
        _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _constant(7), allow_reversed=True)),
        "Multiply the entered age by the named or literal value 7.",
    )


def _pizza_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _constant(8), allow_reversed=True)),
            "Multiply the first input by 8 slices.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.FloorDiv, _source(1), _source(2))),
            "Divide total slices by the second input using floor division.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mod, _source(1), _source(2))),
            "Find leftover slices using the modulus operator.",
        ),
    ]


def _fuel_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _source(2), allow_reversed=True)),
            "Multiply both float inputs.",
        ),
        *_require(
            _has_round_around(flow, 2, ast.Mult),
            "Round the multiplied cost to 2 decimal places in the printed payload.",
        ),
    ]


def _temperature_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _constant(9), allow_reversed=True)),
            "Multiply Celsius by 9.",
        ),
        *_require(_has_operation(flow, _OperationPattern(ast.Div, None, _constant(5))), "Divide the temperature conversion by 5."),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Add, _source(1), _constant(32), allow_reversed=True)),
            "Add 32 to the converted temperature.",
        ),
        *_require(_has_round_around(flow, 1, ast.Add), "Round Fahrenheit to 1 decimal place in the printed payload."),
    ]


def _savings_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.FloorDiv, _source(1), _source(2))),
            "Divide the savings goal by weekly savings using floor division.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mod, _source(1), _source(2))),
            "Find the savings remainder using the modulus operator.",
        ),
    ]


def _garden_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _constant(2), allow_reversed=True)),
            "Double the garden area with multiplication by 2.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Pow, _source(1), _constant(2))),
            "Calculate the garden area with ** 2.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Pow, _source(1), _constant(0.5))),
            "Calculate the doubled-area side with ** 0.5.",
        ),
        *_require(_has_round_around(flow, 2, ast.Pow), "Round the doubled-area side to 2 decimal places in the printed payload."),
    ]


def _bill_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _source(2), allow_reversed=True)),
            "Multiply the bill by the tip percentage.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Add, _source(1), _source(2), allow_reversed=True)),
            "Add the tip to the bill.",
        ),
        *_require(_has_tip_division(flow), "Calculate the tip using bill * tip / 100."),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Div, _Pattern(source_ids=frozenset({1, 2})), _source(3))),
            "Divide the total by the third input.",
        ),
        *_require(
            _has_round_around(flow, 2, ast.Div, source_ids={3}),
            "Round the per-person result to 2 decimal places.",
        ),
    ]


def _supplies_issues(_tree: ast.Module, flow: _Flow) -> list[str]:
    return [
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _source(2), allow_reversed=True)),
            "Multiply students by pencils per student.",
        ),
        *_require(
            _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _source(3), allow_reversed=True)),
            "Multiply students by erasers per student.",
        ),
        *_require(_has_pack_add(flow, 1, 2, 24, "pencil_pack_size"), "Add the named or literal pencil pack size."),
        *_require(_has_pack_add(flow, 1, 3, 15, "eraser_pack_size"), "Add the named or literal eraser pack size."),
        *_require(_has_pack_division(flow, 1, 2, 24, "pencil_pack_size"), "Divide the pencil total by its pack size using ceiling division."),
        *_require(_has_pack_division(flow, 1, 3, 15, "eraser_pack_size"), "Divide the eraser total by its pack size using ceiling division."),
        *_require(_has_pack_leftover(flow, 1, 2, _PENCIL_PACK_SIZE, "pencil_pack_size"), "Calculate leftover pencil coverage."),
        *_require(_has_pack_leftover(flow, 1, 3, _ERASER_PACK_SIZE, "eraser_pack_size"), "Calculate leftover eraser coverage."),
        *_require(_PENCIL_PACK_SIZE in flow.constants, "Use the supplied pencil pack size 24."),
        *_require(_ERASER_PACK_SIZE in flow.constants, "Use the supplied eraser pack size 15."),
    ]


def _party_issues(tree: ast.Module, final_flow: _Flow) -> list[str]:
    issues = _ordered_assignment_issues(tree, _STATIC_ORDER[1], "party")
    assignments = _assignments_by_name(tree)
    full = _latest_binding("full_bags", len(tree.body), assignments)
    left = _latest_binding("sweets_left", len(tree.body), assignments)
    if full is None or not _has_operation(
        _binding_flow(full, tree),
        _OperationPattern(ast.FloorDiv, _name("total_sweets"), _name("sweets_per_bag")),
    ):
        issues.append("full_bags must use total_sweets // sweets_per_bag.")
    if left is None or not _has_operation(
        _binding_flow(left, tree),
        _OperationPattern(ast.Mod, _name("total_sweets"), _name("sweets_per_bag")),
    ):
        issues.append("sweets_left must use total_sweets % sweets_per_bag.")
    if not {"full_bags", "sweets_left"} <= final_flow.names:
        issues.append("The printed f-string must use full_bags and sweets_left.")
    return issues


def _paint_issues(tree: ast.Module, final_flow: _Flow) -> list[str]:
    issues = _ordered_assignment_issues(tree, _STATIC_ORDER[2], "paint")
    assignments = _assignments_by_name(tree)
    area = _binding_flow(_latest_binding("area", len(tree.body), assignments), tree)
    cans = _binding_flow(_latest_binding("cans_needed", len(tree.body), assignments), tree)
    left = _binding_flow(_latest_binding("paint_left", len(tree.body), assignments), tree)
    if not _has_operation(area, _OperationPattern(ast.Mult, _name("width"), _name("height"), allow_reversed=True)):
        issues.append("area must use width * height.")
    if not (
        _has_operation(cans, _OperationPattern(ast.FloorDiv, _name("area"), _name("coverage_per_can")))
        and _has_operation(cans, _OperationPattern(ast.Add, names=frozenset({"area", "coverage_per_can"})))
        and _has_operation(cans, _OperationPattern(ast.Sub, constants=frozenset({1})))
    ):
        issues.append("cans_needed must use the supplied ceiling-division formula.")
    if not (
        _has_operation(left, _OperationPattern(ast.Mult, _name("cans_needed"), _name("coverage_per_can"), allow_reversed=True))
        and _has_operation(left, _OperationPattern(ast.Sub, _name("cans_needed", "coverage_per_can"), _name("area")))
    ):
        issues.append("paint_left must subtract area from ordered-can coverage.")
    if not {"area", "cans_needed", "paint_left"} <= final_flow.names:
        issues.append("The printed f-strings must use area, cans_needed, and paint_left.")
    return issues


_TASK_CHECKERS: Final[dict[int, _TaskChecker]] = {
    1: _party_issues,
    2: _paint_issues,
    3: _pet_issues,
    4: _pizza_issues,
    5: _fuel_issues,
    6: _temperature_issues,
    7: _savings_issues,
    8: _garden_issues,
    9: _bill_issues,
    10: _supplies_issues,
}


def _ordered_assignment_issues(
    tree: ast.Module,
    expected: tuple[tuple[str, int | None], ...],
    label: str,
) -> list[str]:
    assignments = _assignments_by_name(tree)
    positions: list[int] = []
    for name, value in expected:
        bindings = assignments.get(name, ())
        if not bindings:
            return [f"Assign {name} before doing the calculation."]
        if value is not None and not _is_literal(bindings[0].value, value):
            return [f"The {label} variable {name} must first store {value}."]
        positions.append(bindings[0].index)
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        return [f"Create the {label} variables in the requested order."]
    return []


def _binding_flow(binding: _Binding | None, tree: ast.Module) -> _Flow:
    if binding is None:
        return _Flow()
    return _trace_expression(
        binding.value,
        _Context(_assignments_by_name(tree), binding.index, {}, frozenset()),
    )


def _require(condition: bool, message: str) -> list[str]:
    return [] if condition else [message]


def _has_operation(flow: _Flow, pattern: _OperationPattern) -> bool:
    for operation in flow.operations:
        if operation.operator is not pattern.operator:
            continue
        if pattern.names and not pattern.names <= (operation.left.names | operation.right.names):
            continue
        if pattern.constants and not pattern.constants <= (operation.left.constants | operation.right.constants):
            continue
        if _operand_matches(operation.left, pattern.left) and _operand_matches(operation.right, pattern.right):
            return True
        if pattern.allow_reversed and _operand_matches(operation.left, pattern.right) and _operand_matches(operation.right, pattern.left):
            return True
    return False


def _operand_matches(flow: _Flow, pattern: _Pattern | None) -> bool:
    return pattern is None or (
        pattern.source_ids <= flow.input_ids
        and pattern.names <= flow.names
        and pattern.constants <= flow.constants
    )


def _has_round(flow: _Flow, digits: int) -> bool:
    return any(call.digits == digits for call in flow.rounds)


def _has_round_around(
    flow: _Flow,
    digits: int,
    operator: _Operator,
    *,
    source_ids: set[int] | None = None,
) -> bool:
    for call in flow.rounds:
        if call.digits != digits:
            continue
        for operation in call.flow.operations:
            if operation.operator is not operator:
                continue
            if source_ids is None or source_ids <= (operation.left.input_ids | operation.right.input_ids):
                return True
    return False


def _has_tip_division(flow: _Flow) -> bool:
    direct = _OperationPattern(
        ast.Div,
        _Pattern(source_ids=frozenset({1, 2})),
        _constant(100),
    )
    grouped = _OperationPattern(ast.Div, _source(2), _constant(100))
    return _has_operation(flow, direct) or (
        _has_operation(flow, grouped)
        and _has_operation(flow, _OperationPattern(ast.Mult, _source(1), _source(2), allow_reversed=True))
    )


def _has_pack_add(flow: _Flow, source_id: int, item_id: int, value: int, name: str) -> bool:
    return _has_operation(
        flow,
        _OperationPattern(ast.Add, _Pattern(source_ids=frozenset({source_id, item_id})), _constant(value), allow_reversed=True),
    ) or _has_operation(
        flow,
        _OperationPattern(ast.Add, _Pattern(source_ids=frozenset({source_id, item_id})), _name(name), allow_reversed=True),
    )


def _has_pack_division(flow: _Flow, source_id: int, item_id: int, value: int, name: str) -> bool:
    numerator = _Pattern(source_ids=frozenset({source_id, item_id}))
    return _has_operation(flow, _OperationPattern(ast.FloorDiv, numerator, _constant(value))) or _has_operation(
        flow,
        _OperationPattern(ast.FloorDiv, numerator, _name(name)),
    )


def _has_pack_leftover(flow: _Flow, source_id: int, item_id: int, value: int, name: str) -> bool:
    sources = _Pattern(source_ids=frozenset({source_id, item_id}))
    return _has_operation(flow, _OperationPattern(ast.Sub, _Pattern(source_ids=sources.source_ids, constants=frozenset({value})), sources)) or _has_operation(
        flow,
        _OperationPattern(ast.Sub, _Pattern(source_ids=sources.source_ids, names=frozenset({name})), sources),
    )


def _source(source_id: int) -> _Pattern:
    return _Pattern(source_ids=frozenset({source_id}))


def _name(*names: str) -> _Pattern:
    return _Pattern(names=frozenset(names))


def _constant(*values: _Literal) -> _Pattern:
    return _Pattern(constants=frozenset(values))


def _position(node: ast.AST) -> _Position:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _is_print_call(expression: ast.AST) -> TypeGuard[ast.Call]:
    return isinstance(expression, ast.Call) and _call_name(expression) == "print"


def _print_contains_input(call: ast.Call, input_positions: list[_Position]) -> bool:
    start = _position(call)
    return any(position[0] == start[0] and start[1] <= position[1] for position in input_positions)


def _is_literal(expression: ast.AST, expected: object) -> bool:
    return (
        isinstance(expression, ast.Constant)
        and type(expression.value) is type(expected)
        and expression.value == expected
    )


def _public_analysis(issues: tuple[str, ...], flow: _Flow) -> SequenceAnalysis:
    return SequenceAnalysis(
        issues=issues,
        flow=flow,
        payload_names=flow.formatted_names,
        payload_operators=tuple(operation.operator for operation in flow.operations),
        payload_rounds=tuple(call.digits for call in flow.rounds),
        payload_constants=flow.constants,
        payload_input_ids=flow.input_ids,
        payload_casts=flow.casts,
    )


def _deduplicate(issues: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(issues))


def _operator_name(operator: _Operator) -> str:
    symbols = {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "Div": "/",
        "FloorDiv": "//",
        "Mod": "%",
        "Pow": "**",
    }
    return symbols.get(operator.__name__, operator.__name__)


__all__ = ["SequenceAnalysis", "analyze_sequence", "construct_issues", "data_flow_issues"]
