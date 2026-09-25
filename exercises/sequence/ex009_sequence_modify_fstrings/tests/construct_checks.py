"""Conservative AST and provenance checks for ex009 sequence modify f-strings."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, TypeAlias, TypeGuard

_Literal: TypeAlias = str | int | float
_Position: TypeAlias = tuple[int, int]
_CastMap: TypeAlias = tuple[tuple[_Position, frozenset[str]], ...]


@dataclass(frozen=True)
class _Operation:
    """One allowed binary operation and its operand provenance."""

    operator: type[ast.operator]
    left: _Provenance
    right: _Provenance


@dataclass(frozen=True)
class _Provenance:
    """Simple value provenance used by the final f-string checks."""

    roots: frozenset[str] = frozenset()
    calculations: frozenset[str] = frozenset()
    literals: frozenset[_Literal] = frozenset()
    input_casts: _CastMap = ()
    operations: tuple[_Operation, ...] = ()


@dataclass(frozen=True)
class _Assignment:
    """One simple top-level assignment in execution order."""

    name: str
    value: ast.expr
    index: int


_EXPECTED_PAGES_TOMORROW: Final[int] = 8
_EXERCISE_8: Final[int] = 8
_EXERCISE_9: Final[int] = 9

_REQUIRED_PLACEHOLDER_ROOTS: Final[dict[int, frozenset[str]]] = {
    1: frozenset({"name"}),
    2: frozenset({"pet"}),
    3: frozenset({"first_name", "hobby"}),
    4: frozenset({"subject"}),
    7: frozenset({"goal_count"}),
}

_REQUIRED_LITERALS: Final[dict[int, dict[str, _Literal]]] = {
    1: {"name": "Sam"},
    2: {"pet": "rabbit"},
    3: {"first_name": "Mia", "hobby": "drawing"},
    4: {"subject": "computing"},
    7: {"goal_count": 4},
    8: {"tickets_sold": 5, "extra_tickets": 2},
    9: {"pages_tomorrow": 8},
}

_OLD_LITERALS: Final[dict[int, dict[str, _Literal]]] = {
    2: {"pet": "cat"},
    4: {"subject": "science"},
    9: {"pages_tomorrow": 3},
}

_INPUT_SPECS: Final[dict[int, tuple[str | None, ...]]] = {
    5: (None,),
    6: (None, None),
    9: ("int",),
    10: ("float", "int"),
}

_ARITHMETIC: Final[dict[int, tuple[str, type[ast.operator], frozenset[str]]]] = {
    8: ("total_tickets", ast.Add, frozenset({"tickets_sold", "extra_tickets"})),
    9: ("total_pages", ast.Add, frozenset({"pages_today", "pages_tomorrow"})),
    10: ("total", ast.Mult, frozenset()),
}

_ALLOWED_CALLS: Final[dict[int, frozenset[str]]] = {
    1: frozenset({"print"}),
    2: frozenset({"print"}),
    3: frozenset({"print"}),
    4: frozenset({"print"}),
    5: frozenset({"input", "print"}),
    6: frozenset({"input", "print"}),
    7: frozenset({"print"}),
    8: frozenset({"print"}),
    9: frozenset({"input", "int", "print"}),
    10: frozenset({"float", "input", "int", "print"}),
}

_ALLOWED_OPERATORS: Final[dict[int, frozenset[type[ast.operator]]]] = {
    1: frozenset(),
    2: frozenset(),
    3: frozenset(),
    4: frozenset(),
    5: frozenset(),
    6: frozenset(),
    7: frozenset(),
    8: frozenset({ast.Add}),
    9: frozenset({ast.Add}),
    10: frozenset({ast.Mult}),
}

_REQUIRED_CALL_COUNTS: Final[dict[int, dict[str, int]]] = {
    5: {"input": 1},
    6: {"input": 2},
    9: {"input": 1, "int": 1},
    10: {"input": 2, "float": 1, "int": 1},
}

_RESERVED_NAMES: Final[frozenset[str]] = frozenset(
    {"float", "input", "int", "print", "str"}
)

_UNSUPPORTED_EXPRESSION_RULES: Final[tuple[tuple[type[ast.AST], str], ...]] = (
    (ast.BoolOp, "Boolean expressions are not allowed in this sequence exercise."),
    (ast.Compare, "Comparisons are not allowed in this sequence exercise."),
    (ast.IfExp, "Conditional expressions are not allowed in this sequence exercise."),
    (ast.Subscript, "Subscript lookups are not allowed in this sequence exercise."),
    (ast.Attribute, "Attribute access is not allowed in this sequence exercise."),
    (ast.NamedExpr, "Named expressions are not allowed in this sequence exercise."),
    (
        ast.Dict,
        "Finite-case mappings and containers are not allowed in this sequence exercise.",
    ),
    (
        ast.List,
        "Finite-case mappings and containers are not allowed in this sequence exercise.",
    ),
    (
        ast.Set,
        "Finite-case mappings and containers are not allowed in this sequence exercise.",
    ),
    (
        ast.Tuple,
        "Finite-case mappings and containers are not allowed in this sequence exercise.",
    ),
    (
        ast.Lambda,
        "Functions and loop comprehensions are not allowed in this sequence exercise.",
    ),
    (
        ast.comprehension,
        "Functions and loop comprehensions are not allowed in this sequence exercise.",
    ),
)


def construct_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return grammar and provenance problems for one exercise cell."""

    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]
    if exercise_no not in _ALLOWED_CALLS:
        return [f"No construct requirement is defined for exercise {exercise_no}."]

    grammar_issues = _grammar_issues(tree, exercise_no)
    if grammar_issues:
        return grammar_issues

    final = _find_final_print(tree)
    if final is None:
        return ["Finish with a top-level print() call."]
    final_index, final_call = final
    assignments = _collect_assignments(tree)
    provenance, provenance_issues = _final_fstring_provenance(
        final_call,
        final_index,
        assignments,
    )
    issues = [*provenance_issues]
    issues.extend(_assignment_provenance_issues(assignments))
    issues.extend(_assignment_issues(tree, assignments, exercise_no, final_index))
    issues.extend(_calculation_assignment_issues(assignments, exercise_no, final_index))
    issues.extend(_global_operator_issues(tree, exercise_no))
    issues.extend(_input_issues(tree, provenance, exercise_no))
    issues.extend(_arithmetic_issues(provenance, exercise_no))
    issues.extend(_required_root_issues(provenance, exercise_no))
    return issues


def assignment_literal_values(tree: ast.AST, name: str) -> set[_Literal]:
    """Return literal values assigned to *name* in a top-level cell."""

    if not isinstance(tree, ast.Module):
        return set()
    values: set[_Literal] = set()
    for assignment in _collect_assignments(tree).get(name, ()):
        value = _constant_value(assignment.value)
        if value is not None:
            values.add(value)
    return values


def string_literal_values(tree: ast.AST) -> set[str]:
    """Return executable string literals contained in *tree*."""

    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def has_call(tree: ast.AST, name: str) -> bool:
    """Return whether a direct call to the named function occurs in *tree*."""

    return any(_call_name(node) == name for node in ast.walk(tree))


def has_addition_in_print(tree: ast.AST) -> bool:
    """Return whether any print argument contains a ``+`` expression."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node) != "print":
            continue
        if any(
            isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add)
            for argument in (*node.args, *(keyword.value for keyword in node.keywords))
            for child in ast.walk(argument)
        ):
            return True
    return False


def required_placeholder_names(tree: ast.AST) -> frozenset[str]:
    """Return direct names used by the final f-string."""

    if not isinstance(tree, ast.Module):
        return frozenset()
    final = _find_final_print(tree)
    if final is None or not final[1].args:
        return frozenset()
    expression = final[1].args[0]
    if not isinstance(expression, ast.JoinedStr):
        return frozenset()
    return frozenset(
        value.value.id
        for value in expression.values
        if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name)
    )


def _grammar_issues(tree: ast.Module, exercise_no: int) -> list[str]:
    issues: list[str] = []
    final = _find_final_print(tree)
    final_index = final[0] if final is not None else -1
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Assign):
            issues.extend(_validate_assignment(statement, exercise_no))
        elif isinstance(statement, ast.Expr) and _is_print_call(statement.value):
            issues.extend(
                _validate_print_call(
                    statement.value,
                    exercise_no,
                    is_final=index == final_index,
                )
            )
        else:
            issues.append(_statement_issue(statement))
    if final is None:
        issues.append("Finish with a top-level print() call.")
    elif final_index != len(tree.body) - 1:
        issues.append("The final print() must be the last live statement in the cell.")
    return _deduplicate(issues)


def _validate_assignment(statement: ast.Assign, exercise_no: int) -> list[str]:
    issues: list[str] = []
    if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
        return ["Use one simple name on the left side of each assignment."]
    target = statement.targets[0]
    if target.id in _RESERVED_NAMES:
        issues.append(f"Do not rebind the built-in name {target.id!r}.")
    if isinstance(statement.value, ast.JoinedStr):
        issues.append("Build the final message directly in the final print() f-string.")
    issues.extend(_validate_expression(statement.value, exercise_no))
    return issues


def _validate_print_call(
    call: ast.Call,
    exercise_no: int,
    *,
    is_final: bool,
) -> list[str]:
    issues: list[str] = []
    if call.keywords or len(call.args) != 1:
        return ["Each print() must receive exactly one positional message."]
    argument = call.args[0]
    if is_final:
        if not isinstance(argument, ast.JoinedStr):
            issues.append("The final print() must use an f-string.")
        else:
            issues.extend(_validate_fstring(argument))
    elif not isinstance(argument, ast.Constant) or not isinstance(argument.value, str):
        issues.append("Non-final print() calls must use literal prompt strings.")
    return issues


def _validate_expression(expression: ast.AST, exercise_no: int) -> list[str]:
    issues: list[str] = []
    if isinstance(expression, ast.Constant):
        if isinstance(expression.value, bool) or not isinstance(
            expression.value, (str, int, float)
        ):
            issues.append("Use only text or numeric constants in the sequence.")
    elif isinstance(expression, ast.Name):
        if expression.id in _RESERVED_NAMES:
            issues.append(f"Do not use or rebind the built-in name {expression.id!r}.")
    elif isinstance(expression, ast.BinOp):
        if type(expression.op) not in _ALLOWED_OPERATORS[exercise_no]:
            issues.append("Use only the arithmetic operator required by this exercise.")
        issues.extend(_validate_expression(expression.left, exercise_no))
        issues.extend(_validate_expression(expression.right, exercise_no))
    elif isinstance(expression, ast.Call):
        issues.extend(_validate_value_call(expression, exercise_no))
    else:
        issues.extend(_unsupported_expression_issues(expression))
    return issues


def _validate_value_call(call: ast.Call, exercise_no: int) -> list[str]:
    issues: list[str] = []
    if not isinstance(call.func, ast.Name):
        return ["Calls in assignments must be direct input() or cast calls."]
    name = call.func.id
    allowed = _ALLOWED_CALLS[exercise_no]
    if name == "print":
        issues.append("print() may only be a top-level expression statement.")
    elif name not in allowed:
        issues.append(f"The call to {name}() is not part of this exercise's sequence.")
    elif call.keywords:
        issues.append("Calls in this sequence do not use keyword arguments.")
    elif name == "input":
        if len(call.args) > 1:
            issues.append("input() accepts at most one literal prompt.")
        elif call.args:
            prompt = call.args[0]
            if not isinstance(prompt, ast.Constant) or not isinstance(
                prompt.value, str
            ):
                issues.append("input() prompts must be literal text.")
    elif len(call.args) != 1:
        issues.append(f"{name}() must receive exactly one value.")
    else:
        issues.extend(_validate_expression(call.args[0], exercise_no))
    return issues


def _validate_fstring(expression: ast.JoinedStr) -> list[str]:
    issues: list[str] = []
    placeholder_count = 0
    for value in expression.values:
        if isinstance(value, ast.Constant):
            if not isinstance(value.value, str):
                issues.append("F-string literal parts must be text.")
            continue
        if not isinstance(value, ast.FormattedValue):
            issues.append(
                "F-strings may contain only literal text and simple placeholders."
            )
            continue
        placeholder_count += 1
        if not isinstance(value.value, ast.Name):
            issues.append("Each f-string placeholder must be a direct simple name.")
            issues.extend(_unsupported_expression_issues(value.value))
        elif value.value.id in _RESERVED_NAMES:
            issues.append("F-string placeholders may not use built-in names.")
        if value.format_spec is not None:
            issues.append("F-string placeholders may not use a format specifier.")
        if value.conversion not in {-1, ord("s")}:
            issues.append("Only no conversion or the safe !s conversion is allowed.")
    if placeholder_count == 0:
        issues.append("The final f-string must contain at least one placeholder.")
    return issues


def _statement_issue(statement: ast.stmt) -> str:
    message = "Use only simple assignments and top-level print() calls."
    if isinstance(statement, ast.If):
        message = "Use sequence-only code without if/else branches."
    elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
        message = "Use sequence-only code without loops."
    elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        message = "Use sequence-only code without functions."
    elif isinstance(statement, (ast.Import, ast.ImportFrom)):
        message = "Imports are not allowed in this sequence exercise."
    elif isinstance(statement, ast.AugAssign):
        message = "Augmented assignments are not allowed; use one simple assignment."
    elif isinstance(statement, ast.NamedExpr):
        message = "Named expressions are not allowed in this sequence exercise."
    elif isinstance(statement, ast.Subscript):
        message = "Subscript lookups are not allowed in this sequence exercise."
    elif isinstance(statement, ast.Attribute):
        message = "Attribute access is not allowed in this sequence exercise."
    elif isinstance(statement, ast.Expr):
        message = _unsupported_expression_issue(statement.value)
    return message


def _unsupported_expression_issue(expression: ast.AST) -> str:
    message = (
        "Use only constants, simple names, allowed calls, and required arithmetic."
    )
    if isinstance(expression, ast.BoolOp):
        message = "Boolean expressions are not allowed in this sequence exercise."
    elif isinstance(expression, ast.Compare):
        message = "Comparisons are not allowed in this sequence exercise."
    elif isinstance(expression, ast.IfExp):
        message = "Conditional expressions are not allowed in this sequence exercise."
    elif isinstance(expression, ast.Subscript):
        message = "Subscript lookups are not allowed in this sequence exercise."
    elif isinstance(expression, ast.Attribute):
        message = "Attribute access is not allowed in this sequence exercise."
    elif isinstance(expression, ast.NamedExpr):
        message = "Named expressions are not allowed in this sequence exercise."
    elif isinstance(expression, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        message = "Finite-case mappings and containers are not allowed in this sequence exercise."
    elif isinstance(expression, (ast.Lambda, ast.comprehension)):
        message = "Functions and loop comprehensions are not allowed in this sequence exercise."
    return message


def _unsupported_expression_issues(expression: ast.AST) -> list[str]:
    issues: list[str] = []
    for node in ast.walk(expression):
        for node_type, message in _UNSUPPORTED_EXPRESSION_RULES:
            if isinstance(node, node_type):
                issues.append(message)
                break
    if not issues:
        issues.append(_unsupported_expression_issue(expression))
    return _deduplicate(issues)


def _find_final_print(tree: ast.Module) -> tuple[int, ast.Call] | None:
    prints: list[tuple[int, ast.Call]] = []
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Expr) and _is_print_call(statement.value):
            prints.append((index, statement.value))
    return prints[-1] if prints else None


def _is_print_call(expression: ast.expr) -> TypeGuard[ast.Call]:
    return isinstance(expression, ast.Call) and _call_name(expression) == "print"


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


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


def _final_fstring_provenance(
    call: ast.Call,
    before: int,
    assignments: dict[str, list[_Assignment]],
) -> tuple[_Provenance, list[str]]:
    if len(call.args) != 1 or not isinstance(call.args[0], ast.JoinedStr):
        return _Provenance(), ["The final print() must use one positional f-string."]
    flows: list[_Provenance] = []
    issues: list[str] = []
    for value in call.args[0].values:
        if not isinstance(value, ast.FormattedValue) or not isinstance(
            value.value, ast.Name
        ):
            continue
        provenance = _resolve_name(value.value.id, before, assignments)
        if provenance is None:
            issues.append(
                f"Could not trace the f-string placeholder {value.value.id!r}."
            )
        else:
            flows.append(provenance)
    if not flows:
        issues.append("The final f-string must use at least one traceable variable.")
    return _merge_provenance(flows), issues


def _assignment_provenance_issues(
    assignments: dict[str, list[_Assignment]],
) -> list[str]:
    issues: list[str] = []
    for values in assignments.values():
        for assignment in values:
            if (
                _analyze_expression(
                    assignment.value,
                    assignment.index,
                    assignments,
                    frozenset({assignment.index}),
                )
                is None
            ):
                issues.append(
                    f"Could not trace the simple assignment to {assignment.name!r}."
                )
    return issues


def _calculation_assignment_issues(
    assignments: dict[str, list[_Assignment]],
    exercise_no: int,
    before: int,
) -> list[str]:
    requirement = _ARITHMETIC.get(exercise_no)
    if requirement is None:
        return []
    target, _operator_type, _operand_roots = requirement
    values = assignments.get(target, ())
    if len(values) != 1:
        return [f"Assign {target} exactly once as the live calculation."]
    latest = _latest_assignment(values, before)
    if latest is None or not isinstance(latest.value, ast.BinOp):
        return [f"{target} must be assigned from the required arithmetic expression."]
    return []


def _assignment_issues(
    tree: ast.Module,
    assignments: dict[str, list[_Assignment]],
    exercise_no: int,
    before: int,
) -> list[str]:
    issues: list[str] = []
    for name, expected in _REQUIRED_LITERALS.get(exercise_no, {}).items():
        values = assignments.get(name, ())
        if len(values) != 1:
            issues.append(f"Assign {name} exactly once before the final print().")
        latest = _latest_assignment(values, before)
        if latest is None or not _same_literal(latest.value, expected):
            issues.append(f"{name} must be assigned the required value {expected!r}.")
    string_literals = string_literal_values(tree)
    for name, old_value in _OLD_LITERALS.get(exercise_no, {}).items():
        if isinstance(old_value, str):
            old_value_present = any(old_value in value for value in string_literals)
        else:
            old_value_present = any(
                _same_literal(node, old_value) for node in ast.walk(tree)
            )
        if old_value_present:
            issues.append(
                f"Remove the old value {old_value!r} from the {name} assignment."
            )
    return issues


def _global_operator_issues(tree: ast.Module, exercise_no: int) -> list[str]:
    if exercise_no not in _ARITHMETIC:
        return []
    count = sum(isinstance(node, ast.BinOp) for node in ast.walk(tree))
    if count != 1:
        return ["Use one live arithmetic expression for the calculated result."]
    return []


def _required_root_issues(provenance: _Provenance, exercise_no: int) -> list[str]:
    required = _REQUIRED_PLACEHOLDER_ROOTS.get(exercise_no, frozenset())
    missing = required - provenance.roots
    if missing:
        return [
            "The final f-string must trace these variables: "
            + ", ".join(sorted(missing))
            + "."
        ]
    return []


def _input_issues(
    tree: ast.Module,
    provenance: _Provenance,
    exercise_no: int,
) -> list[str]:
    expected_specs = _INPUT_SPECS.get(exercise_no)
    input_positions = tuple(
        sorted(
            _node_position(node)
            for node in ast.walk(tree)
            if _call_name(node) == "input"
        )
    )
    if expected_specs is None:
        if input_positions:
            return ["This exercise must not call input()."]
        return []

    issues: list[str] = []
    if len(input_positions) != len(expected_specs):
        return [
            f"Use exactly {len(expected_specs)} live input() call(s); "
            f"found {len(input_positions)}."
        ]
    actual_casts = dict(provenance.input_casts)
    for position, expected_cast in zip(input_positions, expected_specs, strict=True):
        actual = actual_casts.get(position)
        if actual is None:
            issues.append("Every entered value must flow into the final f-string.")
        elif expected_cast is None and actual:
            issues.append("Text input must not be converted before it is printed.")
        elif expected_cast is not None and actual != frozenset({expected_cast}):
            issues.append(f"Use {expected_cast}() for this entered value.")
    return issues


def _arithmetic_issues(provenance: _Provenance, exercise_no: int) -> list[str]:
    requirement = _ARITHMETIC.get(exercise_no)
    if requirement is None:
        return []
    target, operator_type, operand_roots = requirement
    issues: list[str] = []
    if target not in provenance.calculations:
        issues.append(f"The final f-string must use the calculated {target} variable.")
    if len(provenance.operations) != 1:
        issues.append(
            "Use one live arithmetic operation in the final f-string provenance."
        )
        return issues
    operation = provenance.operations[0]
    if operation.operator is not operator_type:
        issues.append(f"{target} must use the required arithmetic operator.")
        return issues
    if exercise_no == _EXERCISE_8:
        if not _operation_has_root_pair(operation, operand_roots):
            issues.append("The total must add tickets_sold and extra_tickets.")
    elif exercise_no == _EXERCISE_9:
        if not (
            _has_input_cast(operation.left, "int")
            or _has_input_cast(operation.right, "int")
        ) or not (
            _has_root_and_literal(
                operation.left,
                "pages_tomorrow",
                _EXPECTED_PAGES_TOMORROW,
            )
            or _has_root_and_literal(
                operation.right,
                "pages_tomorrow",
                _EXPECTED_PAGES_TOMORROW,
            )
        ):
            issues.append("total_pages must add int input to the named value 8.")
    elif not (
        (
            _has_input_cast(operation.left, "float")
            and _has_input_cast(operation.right, "int")
        )
        or (
            _has_input_cast(operation.left, "int")
            and _has_input_cast(operation.right, "float")
        )
    ):
        issues.append("total must multiply float price by int amount.")
    return issues


def _operation_has_root_pair(operation: _Operation, expected: frozenset[str]) -> bool:
    tickets = frozenset({"tickets_sold"})
    extra = frozenset({"extra_tickets"})
    if expected != frozenset({"tickets_sold", "extra_tickets"}):
        return False
    return (operation.left.roots == tickets and operation.right.roots == extra) or (
        operation.left.roots == extra and operation.right.roots == tickets
    )


def _has_input_cast(provenance: _Provenance, cast_name: str) -> bool:
    return any(
        casts == frozenset({cast_name}) for _position, casts in provenance.input_casts
    )


def _has_root_and_literal(
    provenance: _Provenance,
    root: str,
    literal: _Literal,
) -> bool:
    return root in provenance.roots and literal in provenance.literals


def _resolve_name(
    name: str,
    before: int,
    assignments: dict[str, list[_Assignment]],
    seen: frozenset[int] = frozenset(),
) -> _Provenance | None:
    assignment = _latest_assignment(assignments.get(name, ()), before)
    if assignment is None or assignment.index in seen:
        return None
    value = _analyze_expression(
        assignment.value,
        assignment.index,
        assignments,
        seen | {assignment.index},
    )
    if value is None:
        return None
    if isinstance(assignment.value, ast.BinOp):
        return _merge_provenance((value, _Provenance(calculations=frozenset({name}))))
    if (
        not value.roots
        and not value.calculations
        and not value.operations
        and not value.input_casts
    ):
        return _merge_provenance((value, _Provenance(roots=frozenset({name}))))
    return value


def _analyze_expression(
    expression: ast.AST,
    before: int,
    assignments: dict[str, list[_Assignment]],
    seen: frozenset[int],
) -> _Provenance | None:
    provenance: _Provenance | None = None
    if isinstance(expression, ast.Constant):
        value = _constant_value(expression)
        if value is not None:
            provenance = _Provenance(literals=frozenset({value}))
    elif isinstance(expression, ast.Name):
        provenance = _resolve_name(expression.id, before, assignments, seen)
    elif isinstance(expression, ast.BinOp):
        left = _analyze_expression(expression.left, before, assignments, seen)
        right = _analyze_expression(expression.right, before, assignments, seen)
        if left is not None and right is not None:
            operation = _Operation(type(expression.op), left, right)
            provenance = _merge_provenance(
                (left, right, _Provenance(operations=(operation,)))
            )
    elif isinstance(expression, ast.Call):
        name = _call_name(expression)
        if name == "input":
            provenance = _Provenance(
                input_casts=((_node_position(expression), frozenset()),)
            )
        elif name in {"float", "int"} and len(expression.args) == 1:
            child = _analyze_expression(expression.args[0], before, assignments, seen)
            if child is not None:
                provenance = _add_cast(child, name)
    return provenance


def _add_cast(provenance: _Provenance, cast_name: str) -> _Provenance:
    casts = tuple(
        (position, existing | frozenset({cast_name}))
        for position, existing in provenance.input_casts
    )
    return _Provenance(
        roots=provenance.roots,
        calculations=provenance.calculations,
        literals=provenance.literals,
        input_casts=casts,
        operations=provenance.operations,
    )


def _merge_provenance(flows: Sequence[_Provenance]) -> _Provenance:
    roots: set[str] = set()
    calculations: set[str] = set()
    literals: set[_Literal] = set()
    operations: list[_Operation] = []
    cast_map: dict[_Position, set[str]] = {}
    for flow in flows:
        roots.update(flow.roots)
        calculations.update(flow.calculations)
        literals.update(flow.literals)
        operations.extend(flow.operations)
        for position, casts in flow.input_casts:
            cast_map.setdefault(position, set()).update(casts)
    return _Provenance(
        roots=frozenset(roots),
        calculations=frozenset(calculations),
        literals=frozenset(literals),
        input_casts=tuple(
            (position, frozenset(casts)) for position, casts in sorted(cast_map.items())
        ),
        operations=tuple(operations),
    )


def _latest_assignment(
    assignments: Sequence[_Assignment],
    before: int,
) -> _Assignment | None:
    eligible = [assignment for assignment in assignments if assignment.index < before]
    return eligible[-1] if eligible else None


def _constant_value(expression: ast.AST) -> _Literal | None:
    if not isinstance(expression, ast.Constant):
        return None
    value = expression.value
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    return value


def _same_literal(expression: ast.AST, expected: _Literal) -> bool:
    value = _constant_value(expression)
    return value == expected and type(value) is type(expected)


def _node_position(node: ast.AST) -> _Position:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


def _deduplicate(issues: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(issues))


__all__ = [
    "assignment_literal_values",
    "construct_issues",
    "has_addition_in_print",
    "has_call",
    "required_placeholder_names",
    "string_literal_values",
]
