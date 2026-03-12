"""Shared AST helpers for ex007 construct checks."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputFlowAnalysis:
    """Describe how a printed expression depends on entered values."""

    input_names: frozenset[str]
    call_names: frozenset[str]
    op_types: frozenset[type[ast.operator]]


def has_call(tree: ast.AST, func_name: str) -> bool:
    """Return True when the tree contains a call to the named function."""

    return any(
        isinstance(node, ast.Call) and _call_name(node) == func_name
        for node in ast.walk(tree)
    )


def has_binop(tree: ast.AST, op_type: type[ast.operator]) -> bool:
    """Return True when the tree contains the requested binary operator."""

    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, op_type)
        for node in ast.walk(tree)
    )


def input_assigned_names(tree: ast.AST) -> set[str]:
    """Return variable names that are assigned directly from input()."""

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call) or _call_name(node.value) != "input":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def interactive_construct_issues(
    tree: ast.AST,
    *,
    expected_input_count: int,
    required_calls: tuple[str, ...] = (),
    required_ops: tuple[type[ast.operator], ...] = (),
    forbidden_ops: tuple[type[ast.operator], ...] = (),
) -> list[str]:
    """Return student-friendly construct issues for ex007 interactive tasks."""

    input_names = input_assigned_names(tree)
    if len(input_names) != expected_input_count:
        return [
            "Use a variable for each entered value before doing the calculation."
        ]

    analyses = _print_output_analyses(tree, input_names)
    if not analyses:
        return ["Print the final answer from the calculation."]

    expected_inputs = frozenset(input_names)
    relevant_analyses = [
        analysis for analysis in analyses if expected_inputs.issubset(analysis.input_names)
    ]
    if not relevant_analyses:
        return ["Printed output must use all entered value variables."]

    required_call_set = set(required_calls)
    required_op_set = set(required_ops)

    if any(
        required_call_set.issubset(analysis.call_names)
        and required_op_set.issubset(analysis.op_types)
        and not any(op in analysis.op_types for op in forbidden_ops)
        for analysis in relevant_analyses
    ):
        return []

    issues: list[str] = []
    if required_calls and not any(
        required_call_set.issubset(analysis.call_names)
        for analysis in relevant_analyses
    ):
        formatted_calls = ", ".join(f"{name}()" for name in required_calls)
        issues.append(
            f"Printed result must come from calculations that use {formatted_calls}."
        )

    if required_ops and not any(
        required_op_set.issubset(analysis.op_types)
        for analysis in relevant_analyses
    ):
        formatted_ops = ", ".join(_operator_token(op) for op in required_ops)
        issues.append(
            f"Printed result must come from calculations that use {formatted_ops}."
        )

    used_forbidden_ops = [
        op for op in forbidden_ops if any(op in analysis.op_types for analysis in relevant_analyses)
    ]
    if used_forbidden_ops:
        formatted_ops = ", ".join(_operator_token(op)
                                  for op in used_forbidden_ops)
        issues.append(f"Printed result must not use {formatted_ops}.")

    if not issues:
        issues.append(
            "Print the final answer from one calculation that uses the entered values."
        )
    return issues


def _print_output_analyses(
    tree: ast.AST,
    input_names: set[str],
) -> list[OutputFlowAnalysis]:
    assignments = _collect_assignments(tree)
    analyses: list[OutputFlowAnalysis] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node) != "print":
            continue
        for arg in node.args:
            analyses.append(
                _analyse_expression(
                    arg,
                    before_line=getattr(node, "lineno", 10**9),
                    assignments=assignments,
                    input_names=input_names,
                    seen_names=frozenset(),
                )
            )

    return analyses


def _collect_assignments(tree: ast.AST) -> dict[str, list[ast.Assign]]:
    collector = _AssignmentCollector()
    collector.visit(tree)
    for nodes in collector.assignments.values():
        nodes.sort(key=lambda node: getattr(node, "lineno", 0))
    return collector.assignments


def _analyse_expression(
    expr: ast.AST,
    *,
    before_line: int,
    assignments: dict[str, list[ast.Assign]],
    input_names: set[str],
    seen_names: frozenset[str],
) -> OutputFlowAnalysis:
    direct_input_names: set[str] = set()
    call_names: set[str] = set()
    op_types: set[type[ast.operator]] = set()

    for node in ast.walk(expr):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in input_names:
            direct_input_names.add(node.id)
        if isinstance(node, ast.Call):
            call_name = _call_name(node)
            if call_name is not None:
                call_names.add(call_name)
        if isinstance(node, ast.BinOp):
            op_types.add(type(node.op))

    transitive_input_names = set(direct_input_names)
    for node in ast.walk(expr):
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            continue
        if node.id in input_names or node.id in seen_names:
            continue
        assignment = _last_assignment_before(
            assignments,
            node.id,
            getattr(node, "lineno", before_line),
        )
        if assignment is None:
            continue
        nested = _analyse_expression(
            assignment.value,
            before_line=getattr(assignment, "lineno", before_line),
            assignments=assignments,
            input_names=input_names,
            seen_names=seen_names | {node.id},
        )
        transitive_input_names.update(nested.input_names)
        call_names.update(nested.call_names)
        op_types.update(nested.op_types)

    return OutputFlowAnalysis(
        input_names=frozenset(transitive_input_names),
        call_names=frozenset(call_names),
        op_types=frozenset(op_types),
    )


def _last_assignment_before(
    assignments: dict[str, list[ast.Assign]],
    name: str,
    before_line: int,
) -> ast.Assign | None:
    for assignment in reversed(assignments.get(name, [])):
        if getattr(assignment, "lineno", 0) < before_line:
            return assignment
    return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "builtins":
            return node.func.attr
    return None


def _operator_token(op_type: type[ast.operator]) -> str:
    mapping = {
        ast.Add: "+",
        ast.Div: "/",
        ast.FloorDiv: "//",
        ast.Mult: "*",
    }
    return mapping.get(op_type, op_type.__name__)


class _AssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assignments: dict[str, list[ast.Assign]] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assignments.setdefault(target.id, []).append(node)
        self.generic_visit(node)


__all__ = [
    "OutputFlowAnalysis",
    "has_binop",
    "has_call",
    "input_assigned_names",
    "interactive_construct_issues",
]
