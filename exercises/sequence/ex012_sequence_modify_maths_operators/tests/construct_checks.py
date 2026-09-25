"""Straight-line AST and final-output flow checks for ex012."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Final, cast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex012_sequence_modify_maths_operators"
_ex = load_exercise_test_module(_EXERCISE_KEY, "expectations")

_ALLOWED_OPERATORS: Final[Any] = _ex.EX012_ALLOWED_OPERATORS
_ALLOWED_CALLS: Final[Any] = _ex.EX012_ALLOWED_CALLS
_REQUIRED_OPERATIONS: Final[Any] = _ex.EX012_REQUIRED_OPERATIONS
_EXPECTED_PRINT_TARGETS: Final[Any] = _ex.EX012_EXPECTED_PRINT_TARGETS
_REQUIRED_LITERALS: Final[Any] = _ex.EX012_REQUIRED_LITERALS
_OLD_ASSIGNMENTS: Final[Any] = _ex.EX012_OLD_ASSIGNMENTS
_OLD_EXPRESSIONS: Final[Any] = _ex.EX012_OLD_EXPRESSIONS

_OPERATOR_TYPES: Final[dict[str, type[ast.operator]]] = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mult,
    "/": ast.Div,
    "//": ast.FloorDiv,
    "%": ast.Mod,
}

_OPERATOR_SYMBOLS: Final[dict[type[ast.operator], str]] = {
    operator_type: symbol for symbol, operator_type in _OPERATOR_TYPES.items()
}

_ALLOWED_AST_NODES: Final[frozenset[type[ast.AST]]] = frozenset(
    {
        ast.Module,
        ast.Assign,
        ast.Expr,
        ast.Name,
        ast.Constant,
        ast.BinOp,
        ast.Call,
        ast.keyword,
        ast.Load,
        ast.Store,
        ast.JoinedStr,
        ast.FormattedValue,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
    }
)

_NODE_DESCRIPTIONS: Final[dict[type[ast.AST], str]] = {
    ast.BoolOp: "boolean operators",
    ast.Compare: "comparisons",
    ast.IfExp: "conditional expressions",
    ast.Subscript: "subscripts or lookup tables",
    ast.Attribute: "attributes or lookup methods",
    ast.FunctionDef: "functions",
    ast.AsyncFunctionDef: "functions",
    ast.Lambda: "lambda functions",
    ast.ClassDef: "classes",
    ast.Import: "imports",
    ast.ImportFrom: "imports",
    ast.AugAssign: "augmented assignments",
    ast.NamedExpr: "assignment expressions",
    ast.If: "if statements",
    ast.For: "loops",
    ast.AsyncFor: "loops",
    ast.While: "loops",
    ast.Try: "exception handling",
    ast.With: "context managers",
    ast.AsyncWith: "context managers",
    ast.Raise: "raises",
    ast.Assert: "assertions",
    ast.Delete: "deletions",
    ast.Global: "global declarations",
    ast.Nonlocal: "nonlocal declarations",
    ast.Return: "returns",
    ast.Yield: "yields",
    ast.YieldFrom: "yields",
    ast.Await: "await expressions",
    ast.List: "lists",
    ast.Tuple: "tuples",
    ast.Set: "sets",
    ast.Dict: "dictionaries",
    ast.ListComp: "comprehensions",
    ast.SetComp: "comprehensions",
    ast.DictComp: "comprehensions",
    ast.GeneratorExp: "generator expressions",
    ast.Match: "match statements",
}

_REBOUND_NAMES: Final[frozenset[str]] = frozenset({"print", "input"})
_ROUND_ARGUMENT_COUNT: Final[int] = 2
_MISSING: Final[object] = object()


@dataclass(frozen=True)
class _Assignment:
    """One simple top-level assignment in source order."""

    name: str
    value: ast.expr
    index: int


@dataclass(frozen=True)
class _Operation:
    """The expected live arithmetic operation for one target binding."""

    operator_type: type[ast.operator]
    operands: tuple[str | int | float, str | int | float]
    round_places: int | None


def straight_line_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return allowlist violations for one tagged exercise cell."""
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]

    allowed_operators = _operator_types_for_exercise(exercise_no)
    allowed_calls = cast(frozenset[str], _ALLOWED_CALLS.get(exercise_no, frozenset()))
    if not allowed_operators or not allowed_calls:
        return [f"No straight-line specification exists for exercise {exercise_no}."]

    issues = _node_issues(tree, exercise_no, allowed_operators, allowed_calls)
    issues.extend(_statement_issues(tree))
    return _deduplicate(issues)


def _node_issues(
    tree: ast.Module,
    exercise_no: int,
    allowed_operators: frozenset[type[ast.operator]],
    allowed_calls: frozenset[str],
) -> list[str]:
    issues: list[str] = []
    for node in ast.walk(tree):
        node_type = type(node)
        if node_type not in _ALLOWED_AST_NODES:
            description = _NODE_DESCRIPTIONS.get(node_type, node_type.__name__)
            issues.append(f"Use straight-line code without {description}.")
        if isinstance(node, ast.Constant) and type(node.value) not in (str, int, float):
            issues.append("Use only string, integer, and floating-point literals.")
        if isinstance(node, ast.BinOp) and type(node.op) not in allowed_operators:
            issues.append(f"Use only the operators required by exercise {exercise_no}.")
        if isinstance(node, ast.Call):
            issues.extend(_call_issues(node, allowed_calls))
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id in _REBOUND_NAMES
        ):
            issues.append(f"Do not rebind the built-in name {node.id!r}.")
    return issues


def _statement_issues(tree: ast.Module) -> list[str]:
    issues: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                issues.append("Assign one result variable at a time.")
        elif not isinstance(statement, ast.Expr):
            issues.append("Use only assignments and print() statements.")
        elif not _is_direct_print_call(statement.value):
            issues.append("Use print() only for the final output statement.")
    return issues


def retained_old_expression_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Reject conflicting starter placeholders/operators anywhere in the cell."""
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]

    issues: list[str] = []
    for old in _OLD_ASSIGNMENTS.get(exercise_no, ()):
        if _contains_literal(tree, old.value):
            issues.append(
                f"Remove the old placeholder value {old.value!r}; it conflicts with "
                f"the corrected {old.target!r} task."
            )

    for old in _OLD_EXPRESSIONS.get(exercise_no, ()):
        operator_type = _operator_type(old.operator)
        if operator_type is None:
            continue
        if any(
            isinstance(node, ast.BinOp)
            and _is_exact_operation(node, operator_type, old.operands)
            for node in ast.walk(tree)
        ):
            symbol = _operator_symbol(operator_type)
            issues.append(
                f"Remove the old {symbol!r} expression for {old.target!r}; it conflicts "
                "with the corrected task, even when wrapped or dead."
            )
    return _deduplicate(issues)


def required_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return all straight-line, old-code, and final-output flow problems."""
    issues = straight_line_issues(tree, exercise_no)
    if not isinstance(tree, ast.Module):
        return issues

    issues.extend(retained_old_expression_issues(tree, exercise_no))
    prints = _collect_top_level_prints(tree)
    issues.extend(_print_issues(tree, prints, exercise_no))
    if not prints:
        return _deduplicate(issues)

    assignments = _collect_assignments(tree)
    issues.extend(_literal_issues(assignments, prints[0][0], exercise_no))
    issues.extend(_operation_issues(assignments, prints, exercise_no))
    return _deduplicate(issues)


def sequence_only_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Compatibility name for the notebook's straight-line restriction."""
    return straight_line_issues(tree, exercise_no)


def _call_issues(call: ast.Call, allowed_calls: frozenset[str]) -> list[str]:
    name = _call_name(call)
    if name not in allowed_calls:
        return [f"Do not use an unlisted function call in this exercise: {name or 'attribute call'}."]

    if name == "print":
        if call.keywords:
            return ["print() must not use flush, end, file, or sep keyword arguments."]
    elif name == "str":
        if len(call.args) != 1 or call.keywords:
            return ["str() must receive exactly one positional value."]
    elif name == "round" and not _valid_round_call(call):
        return ["round() must receive one value and an exact decimal-place argument."]
    return []


def _valid_round_call(call: ast.Call) -> bool:
    if len(call.args) == 1:
        return len(call.keywords) == 1 and call.keywords[0].arg == "ndigits"
    if len(call.args) == _ROUND_ARGUMENT_COUNT:
        return not call.keywords
    return False


def _print_issues(
    tree: ast.Module,
    prints: list[tuple[int, ast.Call]],
    exercise_no: int,
) -> list[str]:
    expected_targets = cast(
        tuple[tuple[str, ...], ...] | None,
        _EXPECTED_PRINT_TARGETS.get(exercise_no),
    )
    if expected_targets is None:
        return [f"No print-flow expectation is defined for exercise {exercise_no}."]

    issues: list[str] = []
    if len(prints) != len(expected_targets):
        issues.append(
            f"Use exactly {len(expected_targets)} top-level print() call(s); found {len(prints)}."
        )
    if prints and prints[-1][0] != len(tree.body) - 1:
        issues.append("The final print() must be the last live statement in the cell.")

    for index, targets in enumerate(expected_targets):
        if index >= len(prints):
            continue
        for target in targets:
            if not _print_uses_name(prints[index][1], target):
                issues.append(
                    f"Print line {index + 1} must use {target!r} in a positional payload."
                )
    return issues


def _operation_issues(
    assignments: dict[str, list[_Assignment]],
    prints: list[tuple[int, ast.Call]],
    exercise_no: int,
) -> list[str]:
    requirements_by_target = _operation_requirements(exercise_no)
    issues: list[str] = []
    for requirement in _REQUIRED_OPERATIONS.get(exercise_no, ()):
        target = cast(str, requirement.target)
        operation = requirements_by_target.get(target)
        if operation is None:
            issues.append(
                f"Exercise {exercise_no}: unsupported expected operator {requirement.operator!r}."
            )
            continue

        print_index = _print_index_for_target(prints, exercise_no, target)
        if print_index is None:
            continue
        assignment = _latest_assignment(target, print_index, assignments)
        if assignment is None:
            issues.append(f"Assign {target!r} before its print() call.")
            continue

        issues.extend(_literal_issues(assignments, assignment.index, exercise_no))
        if _binding_matches(operation, assignment, assignments):
            issues.extend(
                _dependency_issues(
                    _binding_value(assignment, operation),
                    assignment.index,
                    target,
                    requirements_by_target,
                    assignments,
                )
            )
            continue

        symbol = _operator_symbol(operation.operator_type)
        operands = " and ".join(str(operand) for operand in operation.operands)
        if operation.round_places is None:
            issues.append(f"{target} must be assigned from {operands} with {symbol}.")
        else:
            issues.append(
                f"{target} must be assigned from {operands} with {symbol}, then rounded "
                f"to {operation.round_places} place(s)."
            )
    return issues


def _operation_requirements(exercise_no: int) -> dict[str, _Operation]:
    requirements: dict[str, _Operation] = {}
    for requirement in _REQUIRED_OPERATIONS.get(exercise_no, ()):
        operator = _operator_type(cast(str, requirement.operator))
        if operator is None:
            continue
        requirements[cast(str, requirement.target)] = _Operation(
            operator_type=operator,
            operands=cast(tuple[str | int | float, str | int | float], requirement.operands),
            round_places=cast(int | None, requirement.round_places),
        )
    return requirements


def _binding_matches(
    operation: _Operation,
    assignment: _Assignment,
    assignments: dict[str, list[_Assignment]],
) -> bool:
    if operation.round_places is None:
        return _resolves_to_operation(
            assignment.value,
            operation,
            assignments,
            assignment.index,
            frozenset(),
        )
    return _is_rounded_operation(
        assignment.value,
        operation,
        assignments,
        assignment.index,
    )


def _binding_value(assignment: _Assignment, operation: _Operation) -> ast.expr:
    if operation.round_places is None:
        return assignment.value
    if not isinstance(assignment.value, ast.Call):
        return assignment.value
    argument = _round_argument(assignment.value, operation.round_places)
    return argument if argument is not None else assignment.value


def _dependency_issues(
    expression: ast.expr,
    before: int,
    owner: str,
    requirements_by_target: dict[str, _Operation],
    assignments: dict[str, list[_Assignment]],
) -> list[str]:
    issues: list[str] = []
    pending: list[tuple[ast.expr, int, str]] = [(expression, before, owner)]
    seen: set[tuple[str, int]] = set()
    while pending:
        current, current_before, current_owner = pending.pop()
        if isinstance(current, ast.Name):
            if current.id == current_owner:
                continue
            assignment = _latest_assignment(current.id, current_before, assignments)
            if assignment is None:
                continue
            marker = (current.id, assignment.index)
            if marker in seen:
                continue
            seen.add(marker)
            operation = requirements_by_target.get(current.id)
            if operation is not None and not _binding_matches(operation, assignment, assignments):
                issues.append(f"{current.id} must be the corrected value used by {current_owner!r}.")
                continue
            pending.append((assignment.value, assignment.index, current.id))
            continue
        pending.extend(
            (child, current_before, current_owner)
            for child in ast.iter_child_nodes(current)
            if isinstance(child, ast.expr)
        )
    return issues


def _print_index_for_target(
    prints: list[tuple[int, ast.Call]],
    exercise_no: int,
    target: str,
) -> int | None:
    expected_targets = cast(
        tuple[tuple[str, ...], ...],
        _EXPECTED_PRINT_TARGETS.get(exercise_no, ()),
    )
    for target_index, targets in enumerate(expected_targets):
        if target not in targets:
            continue
        if target_index < len(prints):
            return prints[target_index][0]
        return prints[-1][0] if prints else None
    return None


def _is_rounded_operation(
    expression: ast.expr,
    operation: _Operation,
    assignments: dict[str, list[_Assignment]],
    before: int,
    seen_assignments: frozenset[int] = frozenset(),
) -> bool:
    if operation.round_places is None:
        return False
    if not (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "round"
    ):
        return False
    argument = _round_argument(expression, operation.round_places)
    if argument is None:
        return False
    return _resolves_to_operation(
        argument,
        operation,
        assignments,
        before,
        seen_assignments,
    )


def _round_argument(expression: ast.Call, precision: int) -> ast.expr | None:
    if len(expression.args) == _ROUND_ARGUMENT_COUNT and not expression.keywords:
        precision_node = expression.args[1]
    elif len(expression.args) == 1 and len(expression.keywords) == 1:
        if expression.keywords[0].arg != "ndigits":
            return None
        precision_node = expression.keywords[0].value
    else:
        return None
    if not (
        isinstance(precision_node, ast.Constant)
        and type(precision_node.value) is int
        and precision_node.value == precision
    ):
        return None
    return expression.args[0]


def _resolves_to_operation(
    expression: ast.expr,
    operation: _Operation,
    assignments: dict[str, list[_Assignment]],
    before: int,
    seen_assignments: frozenset[int],
) -> bool:
    if _is_exact_operation(expression, operation.operator_type, operation.operands):
        return True
    if not isinstance(expression, ast.Name):
        return False
    assignment = _latest_assignment(expression.id, before, assignments)
    if assignment is None or assignment.index in seen_assignments:
        return False
    return _resolves_to_operation(
        assignment.value,
        operation,
        assignments,
        assignment.index,
        seen_assignments | {assignment.index},
    )


def _is_exact_operation(
    expression: ast.expr,
    operator_type: type[ast.operator],
    operands: tuple[str | int | float, str | int | float],
) -> bool:
    if not isinstance(expression, ast.BinOp) or type(expression.op) is not operator_type:
        return False
    if _operand_matches(expression.left, operands[0]) and _operand_matches(
        expression.right, operands[1]
    ):
        return True
    return (
        operator_type is ast.Mult
        and _operand_matches(expression.left, operands[1])
        and _operand_matches(expression.right, operands[0])
    )


def _operand_matches(expression: ast.expr, expected: str | int | float) -> bool:
    if isinstance(expected, str):
        return isinstance(expression, ast.Name) and expression.id == expected
    actual = _literal_value(expression)
    return type(actual) is type(expected) and actual == expected


def _literal_value(expression: ast.expr) -> object:
    if isinstance(expression, ast.Constant) and type(expression.value) in (str, int, float):
        return expression.value
    return _MISSING


def _same_literal(actual: object, expected: str | int | float) -> bool:
    return type(actual) is type(expected) and actual == expected


def _contains_literal(tree: ast.Module, expected: object) -> bool:
    if isinstance(expected, str):
        return any(
            isinstance(node, ast.Constant)
            and type(node.value) is str
            and node.value == expected
            for node in ast.walk(tree)
        )
    return any(
        isinstance(node, ast.Constant)
        and type(node.value) in (int, float)
        and not isinstance(node.value, bool)
        and node.value == expected
        for node in ast.walk(tree)
    )


def _literal_issues(
    assignments: dict[str, list[_Assignment]],
    before: int,
    exercise_no: int,
) -> list[str]:
    issues: list[str] = []
    for name, expected in _REQUIRED_LITERALS.get(exercise_no, {}).items():
        assignment = _latest_assignment(cast(str, name), before, assignments)
        if assignment is None:
            issues.append(f"Keep the supplied {name!r} value before the output.")
            continue
        actual = _literal_value(assignment.value)
        if not _same_literal(actual, cast(int | float, expected)):
            issues.append(f"{name} must keep the supplied value {expected!r}; found {actual!r}.")
    return issues


def _collect_assignments(tree: ast.Module) -> dict[str, list[_Assignment]]:
    assignments: dict[str, list[_Assignment]] = {}
    for index, statement in enumerate(tree.body):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name):
            assignments.setdefault(target.id, []).append(
                _Assignment(target.id, statement.value, index)
            )
    return assignments


def _collect_top_level_prints(tree: ast.Module) -> list[tuple[int, ast.Call]]:
    prints: list[tuple[int, ast.Call]] = []
    for index, statement in enumerate(tree.body):
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _call_name(statement.value) == "print"
        ):
            prints.append((index, statement.value))
    return prints


def _print_uses_name(call: ast.Call, name: str) -> bool:
    return any(_payload_expression_uses_name(argument, name) for argument in call.args)


def _payload_expression_uses_name(expression: ast.AST, name: str) -> bool:
    if isinstance(expression, ast.Name):
        return expression.id == name
    if isinstance(expression, ast.BinOp | ast.UnaryOp):
        operands = (
            (expression.left, expression.right)
            if isinstance(expression, ast.BinOp)
            else (expression.operand,)
        )
        return any(_payload_expression_uses_name(operand, name) for operand in operands)
    if isinstance(expression, ast.JoinedStr):
        return any(_payload_expression_uses_name(value, name) for value in expression.values)
    if isinstance(expression, ast.FormattedValue):
        return _payload_expression_uses_name(expression.value, name) or (
            expression.format_spec is not None
            and _payload_expression_uses_name(expression.format_spec, name)
        )
    if isinstance(expression, ast.Call):
        call_name = _call_name(expression)
        if call_name in {"str", "round"} and expression.args:
            return _payload_expression_uses_name(expression.args[0], name)
    return False


def _latest_assignment(
    name: str,
    before: int,
    assignments: dict[str, list[_Assignment]],
) -> _Assignment | None:
    eligible = [assignment for assignment in assignments.get(name, ()) if assignment.index < before]
    return eligible[-1] if eligible else None


def _is_direct_print_call(expression: ast.AST) -> bool:
    return isinstance(expression, ast.Call) and _call_name(expression) == "print"


def _call_name(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


def _operator_types_for_exercise(exercise_no: int) -> frozenset[type[ast.operator]]:
    symbols = cast(frozenset[str], _ALLOWED_OPERATORS.get(exercise_no, frozenset()))
    return frozenset(
        operator_type
        for symbol in symbols
        if (operator_type := _operator_type(symbol)) is not None
    )


def _operator_type(symbol: str) -> type[ast.operator] | None:
    return _OPERATOR_TYPES.get(symbol)


def _operator_symbol(operator_type: type[ast.operator]) -> str:
    return _OPERATOR_SYMBOLS.get(operator_type, operator_type.__name__)


def _deduplicate(issues: list[str]) -> list[str]:
    return list(dict.fromkeys(issues))


__all__ = [
    "required_flow_issues",
    "retained_old_expression_issues",
    "sequence_only_issues",
    "straight_line_issues",
]
