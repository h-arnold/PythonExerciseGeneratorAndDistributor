"""Exercise-local AST helpers for ex007 construct checks."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputFlowAnalysis:
    """Describe how a printed expression depends on entered values."""

    input_names: frozenset[str]
    call_names: frozenset[str]
    op_types: frozenset[type[ast.operator]]


@dataclass(frozen=True)
class _ExpressionAnalysisContext:
    before_line: int
    assignments: dict[str, list[ast.Assign]]
    input_names: set[str]
    seen_names: frozenset[str]


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
    input_count_issue = _input_count_issue(
        input_names,
        expected_input_count=expected_input_count,
    )
    if input_count_issue is not None:
        return input_count_issue

    relevant_analyses, print_issue = _relevant_print_analyses(tree, input_names)
    if print_issue is not None:
        return print_issue

    return _construct_requirement_issues(
        relevant_analyses,
        required_calls=required_calls,
        required_ops=required_ops,
        forbidden_ops=forbidden_ops,
    )


def _input_count_issue(
    input_names: set[str],
    *,
    expected_input_count: int,
) -> list[str] | None:
    if len(input_names) == expected_input_count:
        return None
    return ["Use a variable for each entered value before doing the calculation."]


def _relevant_print_analyses(
    tree: ast.AST,
    input_names: set[str],
) -> tuple[list[OutputFlowAnalysis], list[str] | None]:
    analyses = _print_output_analyses(tree, input_names)
    if not analyses:
        return [], ["Print the final answer from the calculation."]

    expected_inputs = frozenset(input_names)
    relevant_analyses = [
        analysis for analysis in analyses if expected_inputs.issubset(analysis.input_names)
    ]
    if relevant_analyses:
        return relevant_analyses, None
    return [], ["Printed output must use all entered value variables."]


def _construct_requirement_issues(
    relevant_analyses: list[OutputFlowAnalysis],
    *,
    required_calls: tuple[str, ...],
    required_ops: tuple[type[ast.operator], ...],
    forbidden_ops: tuple[type[ast.operator], ...],
) -> list[str]:
    required_call_set = set(required_calls)
    required_op_set = set(required_ops)

    if any(
        _analysis_satisfies_requirements(
            analysis,
            required_call_set=required_call_set,
            required_op_set=required_op_set,
            forbidden_ops=forbidden_ops,
        )
        for analysis in relevant_analyses
    ):
        return []

    issues: list[str] = []
    _append_required_call_issue(issues, relevant_analyses, required_calls, required_call_set)
    _append_required_op_issue(issues, relevant_analyses, required_ops, required_op_set)
    _append_forbidden_op_issue(issues, relevant_analyses, forbidden_ops)

    if not issues:
        issues.append(
            "Print the final answer from one calculation that uses the entered values."
        )
    return issues


def _analysis_satisfies_requirements(
    analysis: OutputFlowAnalysis,
    *,
    required_call_set: set[str],
    required_op_set: set[type[ast.operator]],
    forbidden_ops: tuple[type[ast.operator], ...],
) -> bool:
    return (
        required_call_set.issubset(analysis.call_names)
        and required_op_set.issubset(analysis.op_types)
        and not any(op in analysis.op_types for op in forbidden_ops)
    )


def _append_required_call_issue(
    issues: list[str],
    relevant_analyses: list[OutputFlowAnalysis],
    required_calls: tuple[str, ...],
    required_call_set: set[str],
) -> None:
    if not required_calls:
        return
    if any(required_call_set.issubset(analysis.call_names) for analysis in relevant_analyses):
        return
    formatted_calls = ", ".join(f"{name}()" for name in required_calls)
    issues.append(
        f"Printed result must come from calculations that use {formatted_calls}."
    )


def _append_required_op_issue(
    issues: list[str],
    relevant_analyses: list[OutputFlowAnalysis],
    required_ops: tuple[type[ast.operator], ...],
    required_op_set: set[type[ast.operator]],
) -> None:
    if not required_ops:
        return
    if any(required_op_set.issubset(analysis.op_types) for analysis in relevant_analyses):
        return
    formatted_ops = ", ".join(_operator_token(op) for op in required_ops)
    issues.append(
        f"Printed result must come from calculations that use {formatted_ops}."
    )


def _append_forbidden_op_issue(
    issues: list[str],
    relevant_analyses: list[OutputFlowAnalysis],
    forbidden_ops: tuple[type[ast.operator], ...],
) -> None:
    used_forbidden_ops = [
        op for op in forbidden_ops if any(op in analysis.op_types for analysis in relevant_analyses)
    ]
    if not used_forbidden_ops:
        return
    formatted_ops = ", ".join(_operator_token(op) for op in used_forbidden_ops)
    issues.append(f"Printed result must not use {formatted_ops}.")


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
    direct_input_names, call_names, op_types = _collect_direct_expression_details(
        expr,
        input_names=input_names,
    )
    transitive_input_names = set(direct_input_names)
    context = _ExpressionAnalysisContext(
        before_line=before_line,
        assignments=assignments,
        input_names=input_names,
        seen_names=seen_names,
    )
    _merge_transitive_expression_details(
        expr,
        context=context,
        transitive_input_names=transitive_input_names,
        call_names=call_names,
        op_types=op_types,
    )
    return OutputFlowAnalysis(
        input_names=frozenset(transitive_input_names),
        call_names=frozenset(call_names),
        op_types=frozenset(op_types),
    )


def _collect_direct_expression_details(
    expr: ast.AST,
    *,
    input_names: set[str],
) -> tuple[set[str], set[str], set[type[ast.operator]]]:
    direct_input_names: set[str] = set()
    call_names: set[str] = set()
    op_types: set[type[ast.operator]] = set()

    for node in ast.walk(expr):
        if isinstance(node, ast.Name) and node.id in input_names:
            direct_input_names.add(node.id)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node)
            if call_name is not None:
                call_names.add(call_name)
        elif isinstance(node, ast.BinOp):
            op_types.add(type(node.op))

    return direct_input_names, call_names, op_types


def _merge_transitive_expression_details(
    expr: ast.AST,
    *,
    context: _ExpressionAnalysisContext,
    transitive_input_names: set[str],
    call_names: set[str],
    op_types: set[type[ast.operator]],
) -> None:
    for node in ast.walk(expr):
        if not isinstance(node, ast.Name):
            continue
        assignment = _latest_assignment_before_line(
            context.assignments,
            node.id,
            before_line=context.before_line,
        )
        if assignment is None or node.id in context.seen_names:
            continue
        nested = _analyse_expression(
            assignment.value,
            before_line=getattr(assignment, "lineno", context.before_line),
            assignments=context.assignments,
            input_names=context.input_names,
            seen_names=context.seen_names | {node.id},
        )
        transitive_input_names.update(nested.input_names)
        call_names.update(nested.call_names)
        op_types.update(nested.op_types)


def _latest_assignment_before_line(
    assignments: dict[str, list[ast.Assign]],
    name: str,
    *,
    before_line: int,
) -> ast.Assign | None:
    candidates = assignments.get(name)
    if not candidates:
        return None
    eligible = [node for node in candidates if getattr(node, "lineno", 0) < before_line]
    if not eligible:
        return None
    return eligible[-1]


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _operator_token(operator_type: type[ast.operator]) -> str:
    mapping: dict[type[ast.operator], str] = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "//",
    }
    return mapping.get(operator_type, operator_type.__name__)


class _AssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assignments: dict[str, list[ast.Assign]] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assignments.setdefault(target.id, []).append(node)
        self.generic_visit(node)
