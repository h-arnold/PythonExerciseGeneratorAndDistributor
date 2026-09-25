"""Conservative AST/data-flow checks for ex010 sequence debug f-strings."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Final

_RESERVED_TARGET_NAMES: Final[frozenset[str]] = frozenset(
    {
        "print",
        "input",
        "int",
        "float",
        "round",
        "str",
        "builtins",
        "__builtins__",
    }
)
_ALLOWED_BINARY_OPERATORS: Final[tuple[type[ast.operator], ...]] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
)
_ALLOWED_UNARY_OPERATORS: Final[tuple[type[ast.unaryop], ...]] = (
    ast.UAdd,
    ast.USub,
)
_ALLOWED_PRINT_KEYWORDS: Final[frozenset[str]] = frozenset(
    {"sep", "end", "file", "flush"}
)
_EXPECTED_OPERAND_COUNT: Final[int] = 2

_REQUIRED_PLACEHOLDERS: Final[dict[int, frozenset[str]]] = {
    1: frozenset({"name"}),
    2: frozenset({"pet"}),
    3: frozenset({"person", "hobby"}),
    4: frozenset({"lesson"}),
    5: frozenset({"snack"}),
    6: frozenset({"name", "town"}),
    7: frozenset({"goals"}),
    8: frozenset({"total_tickets"}),
    9: frozenset({"total_pages"}),
    10: frozenset({"amount", "total_cost"}),
}

_REQUIRED_LITERALS: Final[dict[int, dict[str, str | int | float]]] = {
    1: {"name": "Sam"},
    2: {"pet": "rabbit"},
    3: {"person": "Mia", "hobby": "drawing"},
    4: {"lesson": "computing"},
    7: {"goals": 4},
    8: {"adult_tickets": 4, "child_tickets": 3},
    9: {"pages_today": 12, "pages_tomorrow": 8},
    10: {"price": 0.5, "amount": 6},
}

_REQUIRED_INPUTS: Final[dict[int, tuple[tuple[str, str], ...]]] = {
    5: (("snack", "Type your favourite snack: "),),
    6: (
        ("name", "Enter your first name: "),
        ("town", "Enter your town: "),
    ),
}

_REQUIRED_FSTRING_LITERALS: Final[dict[int, str]] = {7: "goals"}
_FORBIDDEN_NAMES: Final[dict[int, frozenset[str]]] = {2: frozenset({"animal"})}

_ARITHMETIC: Final[dict[int, tuple[str, type[ast.operator], frozenset[str]]]] = {
    8: ("total_tickets", ast.Add, frozenset({"adult_tickets", "child_tickets"})),
    9: ("total_pages", ast.Add, frozenset({"pages_today", "pages_tomorrow"})),
    10: ("total_cost", ast.Mult, frozenset({"price", "amount"})),
}


@dataclass(frozen=True)
class AssignmentRecord:
    """One simple top-level assignment in source order."""

    name: str
    value: ast.expr
    index: int


@dataclass(frozen=True)
class PrintRecord:
    """One top-level print expression in source order."""

    index: int
    call: ast.Call


@dataclass(frozen=True)
class InputCallRecord:
    """One direct input call and the top-level statement that contains it."""

    index: int
    call: ast.Call


@dataclass(frozen=True)
class SequenceAnalysis:
    """The allowlisted top-level sequence facts collected from a cell."""

    assignments: tuple[AssignmentRecord, ...]
    prints: tuple[PrintRecord, ...]
    input_calls: tuple[InputCallRecord, ...]
    issues: tuple[str, ...]

    @property
    def final_print(self) -> PrintRecord | None:
        """Return the last top-level print expression, if one exists."""
        return self.prints[-1] if self.prints else None

    @property
    def final_payload(self) -> tuple[ast.expr, ...]:
        """Return only positional arguments from the final print call."""
        final_print = self.final_print
        return tuple(final_print.call.args) if final_print is not None else ()

    def final_payload_fstrings(self) -> tuple[ast.JoinedStr, ...]:
        """Return f-strings found only in positional final-print arguments."""
        return tuple(
            node
            for argument in self.final_payload
            for node in _fstrings_in_payload(argument)
        )

    def final_payload_formatted_names(self) -> frozenset[str]:
        """Return direct names interpolated by positional final-print f-strings."""
        return frozenset(
            value.value.id
            for joined in self.final_payload_fstrings()
            for value in joined.values
            if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name)
        )

    def latest_assignment(self, name: str, before: int | None = None) -> AssignmentRecord | None:
        """Return the last assignment to *name* before a top-level statement."""
        candidates = [
            assignment
            for assignment in self.assignments
            if assignment.name == name
            and (before is None or assignment.index < before)
        ]
        return candidates[-1] if candidates else None


@dataclass
class _AnalysisState:
    """Mutable state used while walking one module."""

    assignments: list[AssignmentRecord]
    prints: list[PrintRecord]
    input_calls: list[InputCallRecord]
    issues: list[str]


def analyze_sequence(tree: ast.AST) -> SequenceAnalysis:
    """Validate the conservative top-level sequence surface and collect facts."""
    if not isinstance(tree, ast.Module):
        return SequenceAnalysis((), (), (), ("The exercise code must be a top-level Python module.",))

    state = _AnalysisState([], [], [], [])
    for index, statement in enumerate(tree.body):
        _analyze_statement(statement, index, state)
    _validate_all_format_specs(tree, state.issues)

    return SequenceAnalysis(
        tuple(state.assignments),
        tuple(state.prints),
        tuple(state.input_calls),
        tuple(state.issues),
    )


def _analyze_statement(statement: ast.stmt, index: int, state: _AnalysisState) -> None:
    if isinstance(statement, ast.Assign):
        _analyze_assign(statement, index, state)
    elif isinstance(statement, ast.AnnAssign):
        _analyze_annassign(statement, index, state)
    elif isinstance(statement, ast.Expr):
        _analyze_print_expression(statement, index, state)
    else:
        state.issues.append(_statement_issue(statement))


def _analyze_assign(statement: ast.Assign, index: int, state: _AnalysisState) -> None:
    for target in statement.targets:
        _validate_target(target, state.issues)
        state.assignments.extend(
            _assignment_records_for_target(target, statement.value, index)
        )
    _validate_expression(statement.value, index, state.input_calls, state.issues)


def _analyze_annassign(
    statement: ast.AnnAssign,
    index: int,
    state: _AnalysisState,
) -> None:
    names = list(_validate_annassign_target(statement.target, state.issues))
    state.assignments.extend(
        AssignmentRecord(name, statement.value, index)
        for name in names
        if statement.value is not None
    )
    _validate_expression(statement.annotation, index, state.input_calls, state.issues)
    if statement.value is None:
        state.issues.append("An annotated assignment must have a value.")
    else:
        _validate_expression(statement.value, index, state.input_calls, state.issues)


def _analyze_print_expression(
    statement: ast.Expr,
    index: int,
    state: _AnalysisState,
) -> None:
    if isinstance(statement.value, ast.Call) and _is_print_call(statement.value):
        state.prints.append(PrintRecord(index, statement.value))
        _validate_print_call(statement.value, index, state.input_calls, state.issues)
        return
    state.issues.append("Only a top-level print() expression is allowed.")


def construct_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return all allowlist and task-specific issues for one exercise cell."""
    analysis = analyze_sequence(tree)
    issues = list(analysis.issues)
    if exercise_no not in _REQUIRED_PLACEHOLDERS:
        return [*issues, f"No construct requirement is defined for exercise {exercise_no}."]

    final_print = analysis.final_print
    if final_print is None:
        return [*issues, "Finish with a top-level print() call."]

    issues.extend(_final_print_task_issues(tree, analysis, final_print, exercise_no))
    issues.extend(_required_binding_issues(analysis, exercise_no, final_print.index))
    issues.extend(_literal_issues(analysis, exercise_no, final_print.index))
    issues.extend(_input_issues(analysis, exercise_no, final_print.index))
    issues.extend(_arithmetic_issues(analysis, exercise_no, final_print.index))
    issues.extend(_forbidden_name_issues(tree, exercise_no))
    return issues


def _final_print_task_issues(
    tree: ast.AST,
    analysis: SequenceAnalysis,
    final_print: PrintRecord,
    exercise_no: int,
) -> list[str]:
    issues: list[str] = []
    required_names = _REQUIRED_PLACEHOLDERS[exercise_no]
    final_fstrings = analysis.final_payload_fstrings()
    formatted_names = analysis.final_payload_formatted_names()
    if not final_fstrings:
        issues.append("The final print() must use an f-string in a positional payload.")
    missing_names = required_names - formatted_names
    if missing_names:
        issues.append(
            "The final positional f-string must interpolate: "
            + ", ".join(sorted(missing_names))
            + "."
        )
    for value in final_fstrings:
        for part in value.values:
            if isinstance(part, ast.FormattedValue) and not isinstance(part.value, ast.Name):
                issues.append("Each f-string placeholder must refer to a variable directly.")
    if isinstance(tree, ast.Module) and final_print.index != len(tree.body) - 1:
        issues.append("The final print() must be the last live statement in the cell.")
    issues.extend(_fstring_literal_issues(final_fstrings, required_names, exercise_no))
    return issues


def _required_binding_issues(
    analysis: SequenceAnalysis,
    exercise_no: int,
    before: int,
) -> list[str]:
    return [
        f"Assign {name} before the final print()."
        for name in _REQUIRED_PLACEHOLDERS[exercise_no]
        if analysis.latest_assignment(name, before=before) is None
    ]


def name_ids(tree: ast.AST) -> set[str]:
    """Return every variable name in the tagged code."""
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def has_operator(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    """Return whether the code contains a binary operator of the given type."""
    return any(
        isinstance(node, ast.BinOp) and type(node.op) is operator_type
        for node in ast.walk(tree)
    )


def final_fstring_contains(tree: ast.AST, literal: str) -> bool:
    """Return whether a positional final-print f-string contains a literal."""
    analysis = analyze_sequence(tree)
    return any(
        literal in fragment
        for joined in analysis.final_payload_fstrings()
        for fragment in _fstring_fragments(joined)
    )


def _validate_target(target: ast.expr, issues: list[str]) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        if target.id in _RESERVED_TARGET_NAMES:
            issues.append(f"Do not rebind the protected name {target.id!r}.")
        return (target.id,)
    if isinstance(target, ast.Tuple):
        names: list[str] = []
        for element in target.elts:
            names.extend(_validate_target(element, issues))
        return tuple(names)
    if isinstance(target, ast.Starred):
        return _validate_target(target.value, issues)
    target_type = type(target).__name__
    issues.append(f"Reject {target_type} assignment targets; use names or tuple targets.")
    return ()


def _assignment_records_for_target(
    target: ast.expr,
    value: ast.expr,
    index: int,
) -> tuple[AssignmentRecord, ...]:
    """Associate tuple-target names with their corresponding values."""
    if isinstance(target, ast.Name):
        return (AssignmentRecord(target.id, value, index),)
    if isinstance(target, ast.Starred):
        return _assignment_records_for_target(target.value, value, index)
    if isinstance(target, ast.Tuple):
        if isinstance(value, ast.Tuple):
            records: list[AssignmentRecord] = []
            for target_element, value_element in zip(target.elts, value.elts, strict=False):
                records.extend(
                    _assignment_records_for_target(target_element, value_element, index)
                )
            return tuple(records)
        return tuple(
            record
            for element in target.elts
            for record in _assignment_records_for_target(element, value, index)
        )
    return ()


def _validate_annassign_target(target: ast.expr, issues: list[str]) -> tuple[str, ...]:
    if not isinstance(target, ast.Name):
        issues.append("Annotated assignment targets must be simple names.")
        return ()
    if target.id in _RESERVED_TARGET_NAMES:
        issues.append(f"Do not rebind the protected name {target.id!r}.")
    return (target.id,)


def _validate_expression(
    expression: ast.expr,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    if _is_leaf_expression(expression):
        return
    _validate_non_leaf_expression(expression, statement_index, input_calls, issues)


def _is_leaf_expression(expression: ast.expr) -> bool:
    return isinstance(expression, (ast.Constant, ast.Name))


def _validate_non_leaf_expression(
    expression: ast.expr,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    if isinstance(expression, ast.IfExp):
        _validate_expression(expression.test, statement_index, input_calls, issues)
        _validate_expression(expression.body, statement_index, input_calls, issues)
        _validate_expression(expression.orelse, statement_index, input_calls, issues)
        issues.append(_expression_issue(expression))
    elif isinstance(expression, ast.Tuple):
        for element in expression.elts:
            _validate_expression(element, statement_index, input_calls, issues)
    elif isinstance(expression, ast.BinOp):
        _validate_binop(expression, statement_index, input_calls, issues)
    elif isinstance(expression, ast.UnaryOp):
        _validate_unaryop(expression, statement_index, input_calls, issues)
    elif isinstance(expression, ast.JoinedStr):
        _validate_fstring(expression, statement_index, input_calls, issues)
    elif isinstance(expression, ast.Call):
        _validate_call(expression, statement_index, input_calls, issues)
    else:
        issues.append(_expression_issue(expression))


def _validate_binop(
    expression: ast.BinOp,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    if type(expression.op) not in _ALLOWED_BINARY_OPERATORS:
        issues.append("Use only the taught +, -, or * arithmetic operators.")
    _validate_expression(expression.left, statement_index, input_calls, issues)
    _validate_expression(expression.right, statement_index, input_calls, issues)


def _validate_unaryop(
    expression: ast.UnaryOp,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    if type(expression.op) not in _ALLOWED_UNARY_OPERATORS:
        issues.append("Use only unary + or unary - in sequence expressions.")
    _validate_expression(expression.operand, statement_index, input_calls, issues)


def _validate_fstring(
    joined: ast.JoinedStr,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    for value in joined.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            continue
        if not isinstance(value, ast.FormattedValue):
            issues.append("F-strings may contain only literal text and variable placeholders.")
            continue
        if _has_nonempty_format_spec(value.format_spec):
            issues.append("F-string format specifications must be empty.")
        if not isinstance(value.value, ast.Name):
            issues.append("Each f-string placeholder must refer to a variable directly.")
            issues.append(_expression_issue(value.value))
        else:
            _validate_expression(value.value, statement_index, input_calls, issues)


def _validate_call(
    call: ast.Call,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    if not isinstance(call.func, ast.Name):
        _validate_expression(call.func, statement_index, input_calls, issues)
        _validate_call_arguments(call, statement_index, input_calls, issues)
        issues.append("Arbitrary calls are not allowed for sequence expressions.")
        if isinstance(call.func, ast.Lambda):
            issues.append("Reject Lambda; do not wrap the output in a helper expression.")
        return
    if call.func.id == "print":
        issues.append("print() may only be used as a top-level expression.")
        _validate_print_arguments(call, statement_index, input_calls, issues)
        return
    if call.func.id == "input":
        input_calls.append(InputCallRecord(statement_index, call))
        _validate_input_call(call, statement_index, input_calls, issues)
        return
    _validate_call_arguments(call, statement_index, input_calls, issues)
    issues.append(f"Arbitrary call to {call.func.id}() is not allowed.")


def _validate_print_call(
    call: ast.Call,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    _validate_print_arguments(call, statement_index, input_calls, issues)


def _validate_call_arguments(
    call: ast.Call,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    for argument in call.args:
        _validate_expression(argument, statement_index, input_calls, issues)
    for keyword in call.keywords:
        _validate_expression(keyword.value, statement_index, input_calls, issues)


def _validate_print_arguments(
    call: ast.Call,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    for argument in call.args:
        _validate_expression(argument, statement_index, input_calls, issues)
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in _ALLOWED_PRINT_KEYWORDS:
            issues.append("print() accepts only sep, end, file, and flush keywords.")
        _validate_expression(keyword.value, statement_index, input_calls, issues)


def _validate_input_call(
    call: ast.Call,
    statement_index: int,
    input_calls: list[InputCallRecord],
    issues: list[str],
) -> None:
    positional_prompt = call.args[0] if len(call.args) == 1 else None
    keyword_prompt = next(
        (keyword.value for keyword in call.keywords if keyword.arg == "prompt"),
        None,
    )
    if len(call.args) > 1 or (positional_prompt is not None and keyword_prompt is not None):
        issues.append("input() accepts at most one prompt value.")
    for keyword in call.keywords:
        if keyword.arg != "prompt":
            issues.append("input() does not accept arbitrary keyword arguments.")
        _validate_expression(keyword.value, statement_index, input_calls, issues)
    if positional_prompt is not None:
        _validate_expression(positional_prompt, statement_index, input_calls, issues)


def _is_print_call(expression: ast.expr) -> bool:
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "print"
    )


def _statement_issue(statement: ast.stmt) -> str:
    statement_type = type(statement).__name__
    if statement_type in {"Import", "ImportFrom"}:
        return "Imports are not allowed in a sequence cell."
    if statement_type in {"FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda"}:
        return f"Reject {statement_type}; use straight-line assignments and print()."
    if statement_type in {
        "If",
        "IfExp",
        "For",
        "AsyncFor",
        "While",
        "Try",
        "TryStar",
        "With",
        "AsyncWith",
        "Match",
    }:
        return f"Reject {statement_type}; sequence cells must not use control flow."
    if statement_type in {"AugAssign", "NamedExpr"}:
        return f"Reject {statement_type}; use a simple assignment instead."
    if statement_type in {"Break", "Continue", "Return", "Raise", "Assert", "Delete"}:
        return f"Reject {statement_type}; sequence cells must remain straight-line."
    return f"Only Assign, AnnAssign, and top-level print() Expr are allowed; reject {statement_type}."


def _expression_issue(expression: ast.expr) -> str:
    expression_type = type(expression).__name__
    if expression_type in {"BoolOp", "Compare"}:
        return f"Reject {expression_type}; use a simple sequence expression."
    if expression_type == "NamedExpr":
        return "Reject NamedExpr; use a simple assignment."
    if expression_type in {"Attribute", "Subscript"}:
        return f"Reject {expression_type}; use the named variable directly."
    if expression_type == "Lambda":
        return "Reject Lambda; do not wrap the output in a helper expression."
    if expression_type in {
        "ListComp",
        "SetComp",
        "DictComp",
        "GeneratorExp",
        "Await",
        "Yield",
        "YieldFrom",
    }:
        return f"Reject {expression_type}; sequence expressions must remain simple."
    return f"Reject unsupported expression {expression_type}; use literals, names, arithmetic, input(), or f-strings."


def _validate_all_format_specs(tree: ast.AST, issues: list[str]) -> None:
    issue = "F-string format specifications must be empty."
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.JoinedStr)
            and any(
                _has_nonempty_format_spec(value.format_spec)
                for value in node.values
                if isinstance(value, ast.FormattedValue)
            )
            and issue not in issues
        ):
            issues.append(issue)


def _has_nonempty_format_spec(format_spec: ast.AST | None) -> bool:
    if not isinstance(format_spec, ast.JoinedStr):
        return False
    return any(
        not (isinstance(value, ast.Constant) and value.value == "")
        for value in format_spec.values
    )


def _fstrings_in_payload(expression: ast.expr) -> tuple[ast.JoinedStr, ...]:
    """Find f-strings that are actual payload, not nested helper code."""
    if isinstance(expression, ast.JoinedStr):
        return (expression,)
    if isinstance(expression, ast.Tuple):
        return tuple(
            node
            for element in expression.elts
            for node in _fstrings_in_payload(element)
        )
    if isinstance(expression, ast.BinOp):
        return _fstrings_in_payload(expression.left) + _fstrings_in_payload(expression.right)
    if isinstance(expression, ast.UnaryOp):
        return _fstrings_in_payload(expression.operand)
    return ()


def _fstring_fragments(joined: ast.JoinedStr) -> list[str]:
    return [
        value.value
        for value in joined.values
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    ]


def _literal_issues(
    analysis: SequenceAnalysis,
    exercise_no: int,
    before: int,
) -> list[str]:
    issues: list[str] = []
    for name, expected in _REQUIRED_LITERALS.get(exercise_no, {}).items():
        assignment = analysis.latest_assignment(name, before=before)
        if assignment is None:
            issues.append(f"Assign {name} before the final print().")
            continue
        actual = _constant_value(assignment.value)
        if not _same_literal(actual, expected):
            issues.append(f"{name} must keep the supplied value {expected!r}.")
    return issues


def _input_issues(
    analysis: SequenceAnalysis,
    exercise_no: int,
    before: int,
) -> list[str]:
    requirements = _REQUIRED_INPUTS.get(exercise_no)
    if requirements is None:
        return []
    if len(analysis.input_calls) != len(requirements):
        return [
            f"Use exactly {len(requirements)} input() call(s); found {len(analysis.input_calls)}."
        ]

    issues: list[str] = []
    for name, prompt in requirements:
        record = _input_record_for_name(analysis, name, before)
        if record is None or not _input_prompt_matches(record, prompt, analysis):
            issues.append(f"Assign {name} directly from input({prompt!r}) before printing.")
    return issues


def _input_record_for_name(
    analysis: SequenceAnalysis,
    name: str,
    before: int,
    seen: frozenset[str] = frozenset(),
) -> InputCallRecord | None:
    if name in seen:
        return None
    assignment = analysis.latest_assignment(name, before=before)
    if assignment is None:
        return None
    if _is_input_call(assignment.value):
        return next(
            (
                record
                for record in analysis.input_calls
                if record.call is assignment.value
            ),
            None,
        )
    if isinstance(assignment.value, ast.Name):
        return _input_record_for_name(
            analysis,
            assignment.value.id,
            assignment.index,
            seen | {name},
        )
    return None


def _input_prompt_matches(
    record: InputCallRecord,
    prompt: str,
    analysis: SequenceAnalysis,
) -> bool:
    expression = _input_prompt_expression(record.call)
    if expression is None:
        return False
    if isinstance(expression, ast.Constant):
        return expression.value == prompt
    if isinstance(expression, ast.Name):
        binding = analysis.latest_assignment(expression.id, before=record.index)
        return binding is not None and _constant_value(binding.value) == prompt
    return False


def _input_prompt_expression(call: ast.Call) -> ast.expr | None:
    if len(call.args) == 1:
        return call.args[0]
    for keyword in call.keywords:
        if keyword.arg == "prompt":
            return keyword.value
    return None


def _is_input_call(expression: ast.expr) -> bool:
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "input"
    )


def _arithmetic_issues(
    analysis: SequenceAnalysis,
    exercise_no: int,
    before: int,
) -> list[str]:
    requirement = _ARITHMETIC.get(exercise_no)
    if requirement is None:
        return []
    target, operator_type, operand_names = requirement
    assignment = analysis.latest_assignment(target, before=before)
    if assignment is None or not isinstance(assignment.value, ast.BinOp):
        return [f"{target} must be calculated before the final print()."]
    if type(assignment.value.op) is not operator_type:
        return [f"{target} must use the required arithmetic operator."]

    operands = (assignment.value.left, assignment.value.right)
    actual_names = {
        operand.id for operand in operands if isinstance(operand, ast.Name)
    }
    if len(actual_names) != _EXPECTED_OPERAND_COUNT or actual_names != set(operand_names):
        return [
            f"{target} must use exactly these operands: "
            + ", ".join(sorted(operand_names))
            + "."
        ]
    return []


def _forbidden_name_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    forbidden = _FORBIDDEN_NAMES.get(exercise_no, frozenset())
    present = forbidden & name_ids(tree)
    if not present:
        return []
    return ["Remove the old variable name(s): " + ", ".join(sorted(present)) + "."]


def _fstring_literal_issues(
    fstrings: tuple[ast.JoinedStr, ...],
    required_names: frozenset[str],
    exercise_no: int,
) -> list[str]:
    literal = _REQUIRED_FSTRING_LITERALS.get(exercise_no)
    if literal is None:
        return []
    if any(
        required_names
        & {
            value.value.id
            for value in joined.values
            if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name)
        }
        and any(literal in fragment for fragment in _fstring_fragments(joined))
        for joined in fstrings
    ):
        return []
    return [f"The final f-string must contain the corrected text {literal!r}."]


def _constant_value(expression: ast.AST) -> str | int | float | None:
    if not isinstance(expression, ast.Constant):
        return None
    value = expression.value
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    return value


def _same_literal(actual: str | int | float | None, expected: str | int | float) -> bool:
    return type(actual) is type(expected) and actual == expected


__all__ = [
    "SequenceAnalysis",
    "analyze_sequence",
    "construct_issues",
    "final_fstring_contains",
    "has_operator",
    "name_ids",
]
