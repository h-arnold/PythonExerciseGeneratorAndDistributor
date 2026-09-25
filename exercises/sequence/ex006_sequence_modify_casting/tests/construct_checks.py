"""Task-specific straight-line data-flow checks for ex006 casting tasks.

The checker accepts only simple assignments and top-level ``print`` expressions,
then follows aliases, tuple bindings, casts, and required operations through
positional print payloads.
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

_CAST_NAMES: Final[frozenset[str]] = frozenset({"int", "float", "str"})
_ALLOWED_CALL_NAMES: Final[frozenset[str]] = frozenset(
    {"print", "input", "int", "float", "str", "round"}
)
_PROTECTED_NAMES: Final[frozenset[str]] = frozenset(
    {"print", "input", "int", "float", "str", "round"}
)
_ALLOWED_PRINT_KEYWORDS: Final[frozenset[str]] = frozenset({"sep", "flush", "end", "file"})
_EMPTY_KEY: Final[tuple[int, int]] = (0, 0)


class _DisallowedCode(ValueError):
    """Raised when a cell leaves the exercise's straight-line subset."""


@dataclass(frozen=True)
class Operation:
    """A binary operation and the flows of its two operands."""

    operator: type[ast.operator]
    left: ExpressionFlow
    right: ExpressionFlow


@dataclass(frozen=True)
class ExpressionFlow:
    """Names, sources, conversions, and operations contributing to a value."""

    names: frozenset[str] = frozenset()
    direct_names: frozenset[str] = frozenset()
    sources: frozenset[str] = frozenset()
    input_names: frozenset[str] = frozenset()
    casts: frozenset[tuple[str, str]] = frozenset()
    operations: tuple[Operation, ...] = ()


@dataclass(frozen=True)
class _Assignment:
    """One top-level name binding used by the data-flow analysis."""

    name: str
    value: ast.expr
    key: tuple[int, int]


@dataclass(frozen=True)
class _Requirement:
    """The task-specific value flow required by one exercise."""

    sources: frozenset[str]
    input_names: frozenset[str] = frozenset()
    operator: type[ast.operator] | None = None
    left_sources: frozenset[str] = frozenset()
    right_sources: frozenset[str] = frozenset()
    left_casts: frozenset[tuple[str, str]] = frozenset()
    right_casts: frozenset[tuple[str, str]] = frozenset()
    cast_operand: str | None = None
    assignment_cast: tuple[str, str] | None = None


_REQUIREMENTS: Final[dict[int, _Requirement]] = {
    1: _Requirement(
        sources=frozenset({"a", "b"}),
        operator=ast.Add,
        left_sources=frozenset({"a"}),
        right_sources=frozenset({"b"}),
        left_casts=frozenset({("a", "int")}),
        right_casts=frozenset({("b", "int")}),
    ),
    2: _Requirement(
        sources=frozenset({"price_1", "price_2"}),
        operator=ast.Add,
        left_sources=frozenset({"price_1"}),
        right_sources=frozenset({"price_2"}),
        left_casts=frozenset({("price_1", "float")}),
        right_casts=frozenset({("price_2", "float")}),
    ),
    3: _Requirement(
        sources=frozenset({"days", "weeks"}),
        operator=ast.Mult,
        left_sources=frozenset({"days"}),
        right_sources=frozenset({"weeks"}),
        left_casts=frozenset({("days", "int")}),
    ),
    4: _Requirement(
        sources=frozenset({"score"}),
        operator=ast.Add,
        cast_operand="score",
    ),
    5: _Requirement(
        sources=frozenset({"temperature"}),
        assignment_cast=("temperature", "int"),
    ),
    6: _Requirement(
        sources=frozenset({"num"}),
        input_names=frozenset({"num"}),
        operator=ast.Add,
        left_sources=frozenset({"num"}),
        right_sources=frozenset({"num"}),
        left_casts=frozenset({("num", "int")}),
        right_casts=frozenset({("num", "int")}),
    ),
    7: _Requirement(
        sources=frozenset({"price"}),
        input_names=frozenset({"price"}),
        operator=ast.Add,
        left_sources=frozenset({"price"}),
        right_sources=frozenset({"price"}),
        left_casts=frozenset({("price", "float")}),
        right_casts=frozenset({("price", "float")}),
    ),
    8: _Requirement(
        sources=frozenset({"width", "height"}),
        operator=ast.Mult,
        left_sources=frozenset({"width"}),
        right_sources=frozenset({"height"}),
        left_casts=frozenset({("width", "int")}),
        right_casts=frozenset({("height", "int")}),
    ),
    9: _Requirement(
        sources=frozenset({"item", "cost"}),
        operator=ast.Add,
        cast_operand="cost",
    ),
    10: _Requirement(
        sources=frozenset({"p1", "p2"}),
        input_names=frozenset({"p1", "p2"}),
        operator=ast.Add,
        left_sources=frozenset({"p1"}),
        right_sources=frozenset({"p2"}),
        left_casts=frozenset({("p1", "float")}),
        right_casts=frozenset({("p2", "float")}),
    ),
}


def required_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return task-specific data-flow problems for one exercise cell."""

    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]
    requirement = _REQUIREMENTS.get(exercise_no)
    if requirement is None:
        return [f"Exercise {exercise_no}: no data-flow requirement is defined."]

    try:
        assignments = _collect_assignments(tree)
        print_flows = _collect_print_flows(tree, assignments)
    except _DisallowedCode as exc:
        return [f"Exercise {exercise_no}: {exc}"]

    issues: list[str] = []
    if not print_flows:
        issues.append(f"Exercise {exercise_no}: print the answer with a top-level print call.")
    elif requirement.assignment_cast is not None and not _has_cast_assignment(
        assignments, requirement.assignment_cast
    ):
        name, cast_name = requirement.assignment_cast
        issues.append(
            f"Exercise {exercise_no}: assign {name} = {cast_name}({name}) before printing it."
        )
    if issues:
        return issues
    if _flow_matches(print_flows[-1], requirement):
        return []
    return [f"Exercise {exercise_no}: {_flow_issue(requirement)}"]


def _flow_matches(flow: ExpressionFlow, requirement: _Requirement) -> bool:
    """Return whether the final positional print payload has required flow."""

    if not requirement.sources.issubset(flow.sources):
        return False
    if not requirement.input_names.issubset(flow.input_names):
        return False
    if requirement.assignment_cast is not None:
        return requirement.assignment_cast in flow.casts
    if requirement.operator is None:
        return True
    if requirement.cast_operand is not None:
        return _has_cast_in_operation(flow, requirement)
    return any(_is_required_pair(operation, requirement) for operation in flow.operations)


def _flow_issue(requirement: _Requirement) -> str:
    """Return a concise explanation for a failed printed-value flow."""

    parts: list[str] = []
    if requirement.sources:
        parts.append(f"the answer must come from {', '.join(sorted(requirement.sources))}")
    if requirement.input_names:
        parts.append("the entered value(s) must reach the answer")
    if requirement.operator is not None:
        parts.append("the required operands and conversions must be in the printed calculation")
    return "The final printed value is incorrect: " + "; ".join(parts) + "."


def _is_required_pair(operation: Operation, requirement: _Requirement) -> bool:
    """Return whether an operation uses the required sources and casts."""

    if operation.operator is not requirement.operator:
        return False
    if not _unordered_sources_match(
        operation.left.sources,
        operation.right.sources,
        requirement.left_sources,
        requirement.right_sources,
    ):
        return False
    return requirement.left_casts.issubset(
        operation.left.casts
    ) and requirement.right_casts.issubset(operation.right.casts)


def _has_cast_in_operation(flow: ExpressionFlow, requirement: _Requirement) -> bool:
    """Return whether the required cast is inside a required operation."""

    name = requirement.cast_operand
    if name is None:
        return False
    for operation in flow.operations:
        if operation.operator is not requirement.operator:
            continue
        for operand in (operation.left, operation.right):
            if name in operand.sources and (name, "str") in operand.casts:
                return True
    return False


def _unordered_sources_match(
    left: frozenset[str],
    right: frozenset[str],
    required_left: frozenset[str],
    required_right: frozenset[str],
) -> bool:
    """Return whether two operand source sets match in either order."""

    return (left == required_left and right == required_right) or (
        left == required_right and right == required_left
    )


def _has_cast_assignment(
    assignments: dict[str, list[_Assignment]],
    assignment_cast: tuple[str, str],
) -> bool:
    """Return whether the exact documented cast assignment exists."""

    name, cast_name = assignment_cast
    for assignment in assignments.get(name, ()):
        value = assignment.value
        if not isinstance(value, ast.Call) or _call_name(value) != cast_name:
            continue
        if len(value.args) != 1 or value.keywords:
            continue
        argument = value.args[0]
        if isinstance(argument, ast.Name) and argument.id == name:
            return True
    return False


def _collect_assignments(module: ast.Module) -> dict[str, list[_Assignment]]:
    """Validate straight-line code and collect name bindings in source order."""

    assignments: dict[str, list[_Assignment]] = {}
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            value = statement.value
            _validate_expression(value)
            key = _node_key(statement)
            for target in statement.targets:
                _record_target(target, value, key, assignments)
        elif isinstance(statement, ast.AnnAssign):
            if statement.value is None:
                raise _DisallowedCode("annotated assignments need a value")
            _validate_expression(statement.annotation)
            _validate_expression(statement.value)
            _record_target(statement.target, statement.value, _node_key(statement), assignments)
        elif isinstance(statement, ast.Expr):
            call = statement.value
            if not isinstance(call, ast.Call) or _call_name(call) != "print":
                raise _DisallowedCode(
                    "only straight-line assignments and top-level print() calls are allowed"
                )
            _validate_print_call(call)
        else:
            raise _DisallowedCode(
                f"{type(statement).__name__} is not allowed; use straight-line assignments and print()"
            )
    return assignments


def _record_target(
    target: ast.expr,
    value: ast.expr,
    key: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
) -> None:
    """Validate an assignment target and record each simple name binding."""

    if isinstance(target, ast.Name):
        if target.id in _PROTECTED_NAMES:
            raise _DisallowedCode(f"do not rebind built-in name {target.id!r}")
        assignments.setdefault(target.id, []).append(_Assignment(target.id, value, key))
        return
    if isinstance(target, ast.Tuple):
        if not isinstance(value, ast.Tuple) or len(target.elts) != len(value.elts):
            raise _DisallowedCode("tuple unpacking must match its tuple value")
        for target_element, value_element in zip(target.elts, value.elts, strict=True):
            _record_target(target_element, value_element, key, assignments)
        return
    raise _DisallowedCode("assignment targets must be names or tuples of names")


def _validate_print_call(call: ast.Call) -> None:
    """Validate a direct print call and its allowed keyword arguments."""

    for keyword in call.keywords:
        if keyword.arg not in _ALLOWED_PRINT_KEYWORDS:
            raise _DisallowedCode("print() keywords must be sep, flush, end, or file")
        _validate_expression(keyword.value)
    for argument in call.args:
        _validate_expression(argument)


def _validate_expression(expression: ast.AST) -> None:
    """Reject expressions outside the exercise's straight-line subset."""

    if isinstance(expression, (ast.Constant, ast.Name)):
        return
    if isinstance(expression, ast.BinOp):
        _validate_expression(expression.left)
        _validate_expression(expression.right)
        return
    if isinstance(expression, ast.Tuple):
        for element in expression.elts:
            _validate_expression(element)
        return
    if isinstance(expression, ast.Call):
        _validate_call_expression(expression)
        return
    _reject_unsupported_expression(expression)


def _validate_call_expression(call: ast.Call) -> None:
    """Validate one allowed call expression."""

    call_name = _call_name(call)
    if call_name is None or call_name not in _ALLOWED_CALL_NAMES:
        raise _DisallowedCode("only print, input, int, float, str, and round calls are allowed")
    if call_name == "print":
        raise _DisallowedCode("print() may only be used as a top-level expression")
    _validate_call_arguments(call, call_name)


def _reject_unsupported_expression(expression: ast.AST) -> None:
    """Raise a specific error for a rejected expression node."""

    if isinstance(expression, ast.BoolOp):
        raise _DisallowedCode("and/or expressions are not allowed")
    if isinstance(expression, ast.Compare):
        raise _DisallowedCode("comparisons are not allowed")
    if isinstance(expression, ast.IfExp):
        raise _DisallowedCode("conditional/fallback expressions are not allowed")
    if isinstance(expression, ast.NamedExpr):
        raise _DisallowedCode("assignment expressions are not allowed")
    raise _DisallowedCode(f"{type(expression).__name__} expressions are not allowed")


def _validate_call_arguments(call: ast.Call, call_name: str) -> None:
    """Validate positional and keyword arguments for an allowed call."""

    if call_name in _CAST_NAMES:
        _validate_cast_arguments(call, call_name)
    elif call_name == "input":
        _validate_input_arguments(call)
    elif call_name == "round":
        _validate_round_arguments(call)
    for argument in call.args:
        _validate_expression(argument)


def _validate_cast_arguments(call: ast.Call, call_name: str) -> None:
    """Validate an int, float, or str call."""

    if len(call.args) != 1 or call.keywords:
        raise _DisallowedCode(f"{call_name}() takes one positional value")


def _validate_input_arguments(call: ast.Call) -> None:
    """Validate an input call and its optional prompt."""

    if len(call.args) > 1 or any(keyword.arg != "prompt" for keyword in call.keywords):
        raise _DisallowedCode("input() accepts only an optional prompt")
    for keyword in call.keywords:
        _validate_expression(keyword.value)


def _validate_round_arguments(call: ast.Call) -> None:
    """Validate a round call."""

    if len(call.args) not in {1, 2} or call.keywords:
        raise _DisallowedCode("round() takes one or two positional values")


def _collect_print_flows(
    module: ast.Module,
    assignments: dict[str, list[_Assignment]],
) -> list[ExpressionFlow]:
    """Return flows for positional print payloads only, in source order."""

    flows: list[ExpressionFlow] = []
    for statement in module.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if _call_name(call) != "print":
            continue
        before = _node_key(call)
        flows.append(
            _merge_flows(
                [_analyze_expression(argument, before, assignments) for argument in call.args]
            )
        )
    return flows


def _analyze_expression(
    expression: ast.AST,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]] = frozenset(),
) -> ExpressionFlow:
    """Analyze names, casts, and operations in one expression."""

    if isinstance(expression, ast.Name):
        return _analyze_name(expression, before, assignments, seen_assignments)
    if isinstance(expression, ast.BinOp):
        return _analyze_binop(expression, before, assignments, seen_assignments)
    if isinstance(expression, ast.Call):
        return _analyze_call(expression, before, assignments, seen_assignments)
    if isinstance(expression, ast.Tuple):
        return _analyze_tuple(expression, before, assignments, seen_assignments)
    return ExpressionFlow()


def _analyze_name(
    expression: ast.Name,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]],
) -> ExpressionFlow:
    """Analyze a name and the value bound to it at this location."""

    base = ExpressionFlow(
        names=frozenset({expression.id}),
        direct_names=frozenset({expression.id}),
    )
    assignment = _latest_assignment(expression.id, before, assignments)
    if assignment is None or assignment.key in seen_assignments:
        return ExpressionFlow(
            names=base.names,
            direct_names=base.direct_names,
            sources=frozenset({expression.id}),
        )
    nested = _analyze_assignment(assignment, assignments, seen_assignments | {assignment.key})
    return ExpressionFlow(
        names=base.names | nested.names,
        direct_names=base.direct_names,
        sources=nested.sources or frozenset({expression.id}),
        input_names=nested.input_names,
        casts=nested.casts,
        operations=nested.operations,
    )


def _analyze_binop(
    expression: ast.BinOp,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]],
) -> ExpressionFlow:
    """Analyze a binary operation and both operand flows."""

    left = _analyze_expression(expression.left, before, assignments, seen_assignments)
    right = _analyze_expression(expression.right, before, assignments, seen_assignments)
    operation = Operation(type(expression.op), left, right)
    return _merge_flows((left, right, ExpressionFlow(operations=(operation,))))


def _analyze_call(
    expression: ast.Call,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]],
) -> ExpressionFlow:
    """Analyze an allowed call, treating input() as an external value."""

    call_name = _call_name(expression)
    if call_name == "input":
        return ExpressionFlow()
    child_flows = [
        _analyze_expression(argument, before, assignments, seen_assignments)
        for argument in expression.args
    ]
    cast_flow = ExpressionFlow()
    if call_name in _CAST_NAMES and child_flows:
        argument_flow = child_flows[0]
        cast_flow = ExpressionFlow(
            casts=frozenset((source, call_name) for source in argument_flow.sources)
        )
    return _merge_flows((*child_flows, cast_flow))


def _analyze_tuple(
    expression: ast.Tuple,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]],
) -> ExpressionFlow:
    """Analyze each element of a tuple value."""

    return _merge_flows(
        [
            _analyze_expression(element, before, assignments, seen_assignments)
            for element in expression.elts
        ]
    )


def _analyze_assignment(
    assignment: _Assignment,
    assignments: dict[str, list[_Assignment]],
    seen_assignments: frozenset[tuple[int, int]],
) -> ExpressionFlow:
    """Analyze an assignment value and record direct input provenance."""

    flow = _analyze_expression(assignment.value, assignment.key, assignments, seen_assignments)
    if _contains_input(assignment.value) and not flow.sources:
        flow = _merge_flows(
            (
                flow,
                ExpressionFlow(
                    names=frozenset({assignment.name}),
                    sources=frozenset({assignment.name}),
                    input_names=frozenset({assignment.name}),
                ),
            )
        )
    call_name = _call_name(assignment.value) if isinstance(assignment.value, ast.Call) else None
    if (
        call_name is not None
        and call_name in _CAST_NAMES
        and isinstance(assignment.value, ast.Call)
        and assignment.value.args
        and _contains_input(assignment.value.args[0])
        and not flow.casts
    ):
        flow = _merge_flows(
            (
                flow,
                ExpressionFlow(
                    names=frozenset({assignment.name}),
                    sources=frozenset({assignment.name}),
                    input_names=frozenset({assignment.name}),
                    casts=frozenset({(assignment.name, call_name)}),
                ),
            )
        )
    return flow


def _latest_assignment(
    name: str,
    before: tuple[int, int],
    assignments: dict[str, list[_Assignment]],
) -> _Assignment | None:
    """Return the most recent assignment to *name* before a source location."""

    candidates = assignments.get(name, ())
    eligible = [assignment for assignment in candidates if assignment.key < before]
    return eligible[-1] if eligible else None


def _contains_input(expression: ast.AST) -> bool:
    """Return whether an expression contains an input call."""

    return any(
        isinstance(node, ast.Call) and _call_name(node) == "input" for node in ast.walk(expression)
    )


def _call_name(call: ast.Call) -> str | None:
    """Return a simple call name, if the call has one."""

    return call.func.id if isinstance(call.func, ast.Name) else None


def _node_key(node: ast.AST) -> tuple[int, int]:
    """Return a stable source-order key for an AST node."""

    return (
        getattr(node, "lineno", _EMPTY_KEY[0]),
        getattr(node, "col_offset", _EMPTY_KEY[1]),
    )


def _merge_flows(flows: Sequence[ExpressionFlow]) -> ExpressionFlow:
    """Merge flow summaries collected from sibling expressions."""

    names: set[str] = set()
    direct_names: set[str] = set()
    sources: set[str] = set()
    input_names: set[str] = set()
    casts: set[tuple[str, str]] = set()
    operations: list[Operation] = []
    for flow in flows:
        names.update(flow.names)
        direct_names.update(flow.direct_names)
        sources.update(flow.sources)
        input_names.update(flow.input_names)
        casts.update(flow.casts)
        operations.extend(flow.operations)
    return ExpressionFlow(
        names=frozenset(names),
        direct_names=frozenset(direct_names),
        sources=frozenset(sources),
        input_names=frozenset(input_names),
        casts=frozenset(casts),
        operations=tuple(operations),
    )


__all__ = ["required_flow_issues"]
