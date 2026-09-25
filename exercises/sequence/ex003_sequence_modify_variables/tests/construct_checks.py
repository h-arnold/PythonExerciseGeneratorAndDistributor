"""Straight-line AST validation for ex003 sequence modify variables."""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from string import Formatter
from typing import Final, TypeGuard

_STATIC_REQUIREMENTS: Final[dict[int, tuple[tuple[str, ...], bool]]] = {
    1: (("greeting",), False),
    2: (("subject",), True),
    3: (("food",), True),
    7: (("first_word", "second_word"), True),
    8: (("part1", "part2"), True),
    9: (("greeting", "time_of_day", "audience"), True),
    10: (("part_one", "part_two", "part_three"), True),
}

_DISALLOWED_STATEMENTS: Final[tuple[type[ast.stmt], ...]] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Break,
    ast.Continue,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Import,
    ast.ImportFrom,
    ast.AugAssign,
    ast.Pass,
    ast.Try,
    ast.Raise,
    ast.Assert,
    ast.Delete,
    ast.Global,
    ast.Nonlocal,
    ast.Match,
    ast.With,
    ast.AsyncWith,
)

_DISALLOWED_EXPRESSIONS: Final[tuple[type[ast.AST], ...]] = (
    ast.Attribute,
    ast.Subscript,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Lambda,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Dict,
    ast.JoinedStr,
    ast.Starred,
    ast.NamedExpr,
    ast.UnaryOp,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


@dataclass(frozen=True)
class ExpressionFacts:
    """Names, input provenance, literals, and operators in one expression."""

    names: frozenset[str] = frozenset()
    input_names: frozenset[str] = frozenset()
    literals: frozenset[str] = frozenset()
    has_addition: bool = False


@dataclass(frozen=True)
class _Assignment:
    """A top-level name assignment and its source-order index."""

    name: str
    value: ast.expr
    index: int


@dataclass(frozen=True)
class _PrintCall:
    """A top-level print call and its source-order index."""

    index: int
    call: ast.Call


def _is_call_to(node: ast.AST, name: str) -> TypeGuard[ast.Call]:
    """Return whether *node* is a direct call to *name*."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    )


def _is_disallowed_expression(node: ast.AST) -> bool:
    """Return whether *node* is outside the novice straight-line grammar."""
    return isinstance(node, _DISALLOWED_EXPRESSIONS)


def _input_call_issues(call: ast.Call, *, allow_input: bool) -> list[str]:
    """Return issues for an input() call in the current expression context."""
    if not allow_input:
        return ["Store each input() result in a variable before using it."]
    if len(call.args) > 1 or call.keywords:
        return ["input() accepts at most one simple prompt argument."]
    if not call.args:
        return []
    return _expression_issues(call.args[0], allow_input=False)


def _addition_issues(expression: ast.BinOp) -> list[str]:
    """Return issues for one top-level string concatenation expression."""
    if not isinstance(expression.op, ast.Add):
        return ["Use + for string concatenation in a straight-line sequence."]
    return [
        *_expression_issues(expression.left, allow_input=False),
        *_expression_issues(expression.right, allow_input=False),
    ]


def _expression_issues(expression: ast.AST, *, allow_input: bool) -> list[str]:
    """Return issues for one assignment or print-payload expression."""
    if isinstance(expression, (ast.Constant, ast.Name)):
        return []
    if isinstance(expression, ast.BinOp):
        return _addition_issues(expression)
    if _is_call_to(expression, "input"):
        return _input_call_issues(expression, allow_input=allow_input)
    if _is_disallowed_expression(expression):
        return ["Use only simple assignments, names, strings, and + concatenation."]
    if isinstance(expression, ast.Call):
        return ["Use only print() and input() in a straight-line sequence."]
    return ["Use only simple expressions in a straight-line sequence."]


def _print_call_issues(call: ast.Call) -> list[str]:
    """Validate one direct top-level print call and its payload arguments."""
    issues: list[str] = []
    for argument in call.args:
        issues.extend(_expression_issues(argument, allow_input=False))
    for keyword in call.keywords:
        if keyword.arg not in {"sep", "end"}:
            issues.append("print() may only use the sep or end keyword.")
            continue
        if not isinstance(keyword.value, ast.Constant) or not isinstance(
            keyword.value.value, str
        ):
            issues.append("print() sep and end must be simple string literals.")
    return issues


def _assignment_issues(statement: ast.stmt) -> list[str]:
    """Validate one top-level assignment statement."""
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1:
            return ["Assign one value to one name at a time."]
        target = statement.targets[0]
        value = statement.value
    elif isinstance(statement, ast.AnnAssign):
        target = statement.target
        value = statement.value
    else:
        return ["Use only simple assignments and print() calls in a straight-line sequence."]

    issues: list[str] = []
    if not isinstance(target, ast.Name):
        return ["Assign to a simple variable name, not an attribute or subscript."]
    if target.id in {"print", "input"}:
        issues.append("Do not rebind print or input.")
    if value is None:
        issues.append("Give every annotated variable a starting value.")
    else:
        issues.extend(_expression_issues(value, allow_input=True))
    return issues


def structure_issues(tree: ast.AST) -> list[str]:
    """Return issues for anything outside the allowed top-level grammar."""
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a straight-line top-level sequence."]

    issues: list[str] = []
    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            issues.extend(_assignment_issues(statement))
        elif isinstance(statement, ast.Expr):
            value = statement.value
            if not _is_call_to(value, "print"):
                issues.append("Top-level expressions must be print() calls.")
            else:
                issues.extend(_print_call_issues(value))
        elif isinstance(statement, _DISALLOWED_STATEMENTS):
            issues.append("Use only straight-line assignments and print() calls.")
        else:
            issues.append("Use only straight-line assignments and print() calls.")
    return issues


def _collect_assignments(tree: ast.Module) -> dict[str, list[_Assignment]]:
    """Collect top-level name assignments in source order."""
    assignments: dict[str, list[_Assignment]] = {}
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Assign):
            target = statement.targets[0] if len(statement.targets) == 1 else None
            value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
            value = statement.value
        else:
            continue
        if isinstance(target, ast.Name) and value is not None:
            assignments.setdefault(target.id, []).append(
                _Assignment(name=target.id, value=value, index=index)
            )
    return assignments


def _collect_print_calls(tree: ast.Module) -> list[_PrintCall]:
    """Collect direct top-level print calls in source order."""
    calls: list[_PrintCall] = []
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Expr) and _is_call_to(statement.value, "print"):
            calls.append(_PrintCall(index=index, call=statement.value))
    return calls


def _latest_assignment(
    name: str,
    before: int,
    assignments: dict[str, list[_Assignment]],
) -> _Assignment | None:
    """Return the latest assignment to *name* before a top-level index."""
    eligible = [item for item in assignments.get(name, ()) if item.index < before]
    return eligible[-1] if eligible else None


def _contains_input_call(expression: ast.AST) -> bool:
    """Return whether an expression contains a direct input() call."""
    return any(_is_call_to(node, "input") for node in ast.walk(expression))


def _merge_facts(facts: Sequence[ExpressionFacts]) -> ExpressionFacts:
    """Merge expression summaries."""
    names: set[str] = set()
    input_names: set[str] = set()
    literals: set[str] = set()
    return ExpressionFacts(
        names=frozenset(names.union(*(item.names for item in facts))),
        input_names=frozenset(input_names.union(*(item.input_names for item in facts))),
        literals=frozenset(literals.union(*(item.literals for item in facts))),
        has_addition=any(item.has_addition for item in facts),
    )


def _analyze_name(
    name: ast.Name,
    before: int,
    assignments: dict[str, list[_Assignment]],
    seen_names: frozenset[str],
) -> ExpressionFacts:
    """Trace one name and the simple assignment that supplies its value."""
    direct = ExpressionFacts(names=frozenset({name.id}))
    if name.id in seen_names:
        return direct
    assignment = _latest_assignment(name.id, before, assignments)
    if assignment is None:
        return direct
    nested = _analyze_expression(
        assignment.value,
        assignment.index,
        assignments,
        seen_names | {name.id},
    )
    if _contains_input_call(assignment.value) or nested.input_names:
        nested = _merge_facts(
            (nested, ExpressionFacts(input_names=frozenset({assignment.name})))
        )
    return _merge_facts((direct, nested))


def _analyze_addition(
    expression: ast.BinOp,
    before: int,
    assignments: dict[str, list[_Assignment]],
    seen_names: frozenset[str],
) -> ExpressionFacts:
    """Trace both operands of one concatenation expression."""
    left = _analyze_expression(expression.left, before, assignments, seen_names)
    right = _analyze_expression(expression.right, before, assignments, seen_names)
    return _merge_facts((left, right, ExpressionFacts(has_addition=True)))


def _analyze_expression(
    expression: ast.AST,
    before: int,
    assignments: dict[str, list[_Assignment]],
    seen_names: frozenset[str] = frozenset(),
) -> ExpressionFacts:
    """Trace simple aliases and provenance into one expression."""
    if isinstance(expression, ast.Constant):
        if isinstance(expression.value, str):
            return ExpressionFacts(literals=frozenset({expression.value}))
        return ExpressionFacts()
    if isinstance(expression, ast.Name):
        return _analyze_name(expression, before, assignments, seen_names)
    if isinstance(expression, ast.BinOp):
        return _analyze_addition(expression, before, assignments, seen_names)
    if isinstance(expression, ast.Call):
        return ExpressionFacts()
    return ExpressionFacts()


def _print_facts(
    print_call: _PrintCall,
    assignments: dict[str, list[_Assignment]],
) -> ExpressionFacts:
    """Analyze every positional argument in a print payload."""
    return _merge_facts(
        tuple(
            _analyze_expression(argument, print_call.index, assignments)
            for argument in print_call.call.args
        )
    )


def _has_addition_or_empty_separator(print_call: _PrintCall) -> bool:
    """Return whether a print uses + or an explicitly empty separator."""
    for keyword in print_call.call.keywords:
        if (
            keyword.arg == "sep"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == ""
        ):
            return True
    return False


def _message_fragments(template: str) -> tuple[str, ...]:
    """Return non-empty literal fragments from a message template."""
    return tuple(
        literal
        for literal, _, _, _ in Formatter().parse(template)
        if literal and literal.strip()
    )


def _assignment_value_issues(
    assignment: _Assignment,
    required_values: Mapping[str, str] | None,
    required_fragments: Mapping[str, str] | None,
) -> list[str]:
    """Check that a live assignment carries the required string value."""
    issues: list[str] = []
    if required_values and assignment.name in required_values:
        expected = required_values[assignment.name]
        actual = assignment.value.value if isinstance(assignment.value, ast.Constant) else None
        if not isinstance(actual, str) or actual != expected:
            issues.append(f"Set {assignment.name!r} to {expected!r} before the final print().")
    if required_fragments and assignment.name in required_fragments:
        fragment = required_fragments[assignment.name]
        actual = assignment.value.value if isinstance(assignment.value, ast.Constant) else None
        if not isinstance(actual, str) or fragment not in actual:
            issues.append(f"{assignment.name!r} must contain {fragment!r}.")
    return issues


def static_construct_issues(
    tree: ast.AST,
    exercise_no: int,
    *,
    required_values: Mapping[str, str] | None = None,
    required_fragments: Mapping[str, str] | None = None,
) -> list[str]:
    """Return straight-line data-flow issues for a static exercise cell."""
    issues = structure_issues(tree)
    if issues:
        return issues
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a straight-line top-level sequence."]

    required_names, require_addition = _STATIC_REQUIREMENTS[exercise_no]
    assignments = _collect_assignments(tree)
    print_calls = _collect_print_calls(tree)
    if not print_calls:
        return ["Print the final message from the assigned variables."]
    final_print = print_calls[-1]
    facts = _print_facts(final_print, assignments)
    for name in required_names:
        assignment = _latest_assignment(name, final_print.index, assignments)
        if assignment is None:
            issues.append(f"Assign {name!r} before the final print().")
        else:
            issues.extend(
                _assignment_value_issues(assignment, required_values, required_fragments)
            )
            if name not in facts.names:
                issues.append(f"The final print() must use {name!r}.")
    if require_addition and not facts.has_addition:
        issues.append("Build the final message with + concatenation.")
    return issues


def _input_assignments(
    assignments: dict[str, list[_Assignment]],
) -> list[_Assignment]:
    """Return top-level assignments whose value is a direct input() call."""
    return [
        item
        for candidates in assignments.values()
        for item in candidates
        if _contains_input_call(item.value)
    ]


def _interactive_flow_issues(
    input_assignments: list[_Assignment],
    assignments: dict[str, list[_Assignment]],
    final_print: _PrintCall,
    message_template: str,
) -> list[str]:
    """Return issues for the final live interactive print payload."""
    issues: list[str] = []
    facts = _print_facts(final_print, assignments)
    for item in input_assignments:
        if item.index >= final_print.index:
            issues.append("Read both input values before the final print().")
        if item.name not in facts.input_names:
            issues.append(f"The final print() must use the entered value {item.name!r}.")
    if not facts.has_addition and not _has_addition_or_empty_separator(final_print):
        issues.append("Build the final message with + concatenation or sep=''.")
    for fragment in _message_fragments(message_template):
        if fragment not in facts.literals:
            issues.append(f"Keep the final message fragment {fragment!r}.")
    return issues


def interactive_construct_issues(
    tree: ast.AST,
    *,
    expected_input_count: int,
    message_template: str,
) -> list[str]:
    """Return straight-line data-flow issues for an interactive cell."""
    issues = structure_issues(tree)
    if issues:
        return issues
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a straight-line top-level sequence."]

    assignments = _collect_assignments(tree)
    inputs = _input_assignments(assignments)
    if len(inputs) != expected_input_count:
        return [
            *issues,
            f"Use exactly {expected_input_count} top-level input() assignments; "
            f"found {len(inputs)}.",
        ]

    print_calls = _collect_print_calls(tree)
    if not print_calls:
        return [*issues, "Print the final message from the entered values."]
    issues.extend(
        _interactive_flow_issues(inputs, assignments, print_calls[-1], message_template)
    )
    return issues


def obsolete_text_issues(tree: ast.AST, obsolete_text: Sequence[str]) -> list[str]:
    """Reject obsolete starter prompts and messages from string literals."""
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    return [
        f"Remove the old text {obsolete!r}."
        for obsolete in obsolete_text
        if any(obsolete in literal for literal in literals)
    ]


__all__ = [
    "ExpressionFacts",
    "interactive_construct_issues",
    "obsolete_text_issues",
    "static_construct_issues",
    "structure_issues",
]
