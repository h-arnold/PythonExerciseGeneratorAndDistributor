"""Conservative straight-line AST and data-flow checks for ex013."""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Final

Position = tuple[int, int]
Numeric = int | float

_PROTECTED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "abs",
        "bool",
        "compile",
        "eval",
        "exec",
        "float",
        "input",
        "int",
        "len",
        "max",
        "min",
        "open",
        "pow",
        "print",
        "round",
        "str",
        "sum",
        "type",
        "__builtins__",
    }
)
_ALLOWED_CALLS: Final[frozenset[str]] = frozenset(
    {"float", "input", "int", "print", "round", "str"}
)
_ALLOWED_OPERATORS: Final[frozenset[type[ast.operator]]] = frozenset(
    {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow}
)
_ALLOWED_UNARY_OPERATORS: Final[frozenset[type[ast.unaryop]]] = frozenset({ast.UAdd, ast.USub})
_NODE_DESCRIPTIONS: Final[dict[str, str]] = {
    "Assert": "assertions",
    "Assign": "assignments",
    "AsyncFor": "loops",
    "AsyncFunctionDef": "functions",
    "AsyncWith": "context managers",
    "Attribute": "attributes",
    "Await": "await expressions",
    "BoolOp": "boolean operators",
    "Break": "loop control",
    "Call": "calls",
    "ClassDef": "classes",
    "Compare": "comparisons",
    "Continue": "loop control",
    "Delete": "deletions",
    "Dict": "lookup tables",
    "DictComp": "comprehensions",
    "For": "loops",
    "FunctionDef": "functions",
    "GeneratorExp": "comprehensions",
    "Global": "global declarations",
    "If": "control flow",
    "IfExp": "conditional expressions",
    "Import": "imports",
    "ImportFrom": "imports",
    "Lambda": "functions",
    "List": "list expressions",
    "ListComp": "comprehensions",
    "Match": "control flow",
    "NamedExpr": "assignment expressions",
    "Nonlocal": "nonlocal declarations",
    "Raise": "raises",
    "Return": "returns",
    "Set": "set expressions",
    "SetComp": "comprehensions",
    "Subscript": "subscripts or lookup tables",
    "Try": "exception handling",
    "TryStar": "exception handling",
    "While": "loops",
    "With": "context managers",
    "Yield": "yield expressions",
    "YieldFrom": "yield expressions",
}
_EMPTY_POSITION: Final[Position] = (0, 0)
_ROUND_ARGUMENT_COUNT: Final[int] = 2
_EXPONENT: Final[int] = 2
_BINARY_OPERATIONS: Final[dict[type[ast.operator], Callable[[Numeric, Numeric], Numeric]]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


@dataclass(frozen=True)
class _Binding:
    """One named top-level assignment in source order."""

    name: str
    value: ast.expr
    position: Position


@dataclass(frozen=True)
class _Print:
    """One top-level print expression in source order."""

    index: int
    call: ast.Call
    position: Position


@dataclass(frozen=True)
class SequenceAnalysis:
    """Facts collected by the conservative top-level grammar."""

    bindings: tuple[_Binding, ...]
    prints: tuple[_Print, ...]
    issues: tuple[str, ...]

    def latest_binding(self, name: str, before: Position | None = None) -> _Binding | None:
        """Return the last binding for *name* before a source position."""
        candidates = [
            binding
            for binding in self.bindings
            if binding.name == name and (before is None or binding.position < before)
        ]
        return candidates[-1] if candidates else None


@dataclass(frozen=True)
class _InputFact:
    """Prompt, source label, and cast history for one input value."""

    prompt: str
    source: str
    casts: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Operation:
    """A binary operation and the analyzed values of its operands."""

    operator: type[ast.operator]
    left: _Value
    right: _Value


@dataclass(frozen=True)
class _Round:
    """A round call, its exact precision, and its input value."""

    precision: int | None
    value: _Value


@dataclass(frozen=True)
class _Value:
    """Symbolic value facts resolved through simple top-level aliases."""

    numeric: Numeric | None = None
    text: str | None = None
    roots: frozenset[str] = frozenset()
    input_facts: tuple[_InputFact, ...] = ()
    operations: tuple[_Operation, ...] = ()
    rounds: tuple[_Round, ...] = ()
    has_fstring: bool = False


@dataclass(frozen=True)
class _OperandPattern:
    """Expected source roots, numeric value, or nested formula for an operand."""

    roots: frozenset[str] = frozenset()
    number: Numeric | None = None
    formula: _Formula | None = None


@dataclass(frozen=True)
class _Formula:
    """One arithmetic operation required in a live output payload."""

    operator: type[ast.operator]
    operands: tuple[_OperandPattern, _OperandPattern]
    allow_reversed: bool = False


@dataclass(frozen=True)
class _Slot:
    """One required result or source value in a positional print payload."""

    name: str
    formula: _Formula | None = None
    roots: frozenset[str] = frozenset()
    round_digits: int | None = None
    alternatives: tuple[_Formula, ...] = ()


@dataclass(frozen=True)
class _PrintSpec:
    """Required slots and formatting for one top-level print line."""

    slots: tuple[_Slot, ...]
    fstring_required: bool = False


@dataclass(frozen=True)
class _InputSpec:
    """Prompt and required cast for one input value."""

    name: str
    prompt: str
    cast: str


@dataclass(frozen=True)
class _TaskSpec:
    """Canonical scenario and output-flow contract for one exercise."""

    source_names: frozenset[str]
    static_values: dict[str, Numeric]
    inputs: tuple[_InputSpec, ...]
    prints: tuple[_PrintSpec, ...]
    forbidden_output_names: frozenset[str] = frozenset()


def _formula(
    operator: type[ast.operator],
    left: _OperandPattern,
    right: _OperandPattern,
    *,
    allow_reversed: bool = False,
) -> _Formula:
    return _Formula(operator, (left, right), allow_reversed)


def _roots(*names: str) -> _OperandPattern:
    return _OperandPattern(roots=frozenset(names))


def _number(value: Numeric) -> _OperandPattern:
    return _OperandPattern(number=value)


def _nested(formula: _Formula) -> _OperandPattern:
    return _OperandPattern(formula=formula)


_FULL_GROUPS: Final[_Formula] = _formula(ast.FloorDiv, _roots("students"), _roots("group_size"))
_LEFTOVER: Final[_Formula] = _formula(ast.Mod, _roots("sweets"), _roots("per_bag"))
_AVERAGE: Final[_Formula] = _formula(ast.Div, _roots("total"), _roots("count"))
_TEAMS: Final[_Formula] = _formula(ast.FloorDiv, _roots("players"), _number(5))
_TOTAL: Final[_Formula] = _formula(ast.Mult, _roots("price"), _roots("qty"), allow_reversed=True)
_HOURS: Final[_Formula] = _formula(ast.FloorDiv, _roots("minutes"), _number(60))
_MINUTES_LEFT: Final[_Formula] = _formula(ast.Mod, _roots("minutes"), _number(60))
_PENCE_POUNDS: Final[_Formula] = _formula(ast.FloorDiv, _roots("pence"), _number(100))
_PENCE_LEFT: Final[_Formula] = _formula(ast.Mod, _roots("pence"), _number(100))
_AREA_MULTIPLICATION: Final[_Formula] = _formula(
    ast.Mult, _roots("length"), _roots("length"), allow_reversed=True
)
_AREA_POWER: Final[_Formula] = _formula(ast.Pow, _roots("length"), _number(_EXPONENT))
_APPLES_BAGS: Final[_Formula] = _formula(ast.FloorDiv, _roots("apples"), _roots("per_bag"))
_APPLES_LEFT: Final[_Formula] = _formula(ast.Mod, _roots("apples"), _roots("per_bag"))
_BOXES: Final[_Formula] = _formula(ast.FloorDiv, _roots("items"), _roots("box_size"))
_ITEMS_LEFT: Final[_Formula] = _formula(ast.Mod, _roots("items"), _roots("box_size"))
_COST_PER_BOX: Final[_Formula] = _formula(ast.Div, _roots("total_cost"), _nested(_BOXES))


_TASKS: Final[dict[int, _TaskSpec]] = {
    1: _TaskSpec(
        source_names=frozenset({"students", "group_size"}),
        static_values={"students": 25, "group_size": 4},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(_Slot("full_groups", formula=_FULL_GROUPS),),
                fstring_required=True,
            ),
        ),
    ),
    2: _TaskSpec(
        source_names=frozenset({"sweets", "per_bag"}),
        static_values={"sweets": 25, "per_bag": 4},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(_Slot("leftover", formula=_LEFTOVER),),
                fstring_required=True,
            ),
        ),
    ),
    3: _TaskSpec(
        source_names=frozenset({"total", "count"}),
        static_values={"total": 20, "count": 3},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(_Slot("average", formula=_AVERAGE, round_digits=1),),
            ),
        ),
    ),
    4: _TaskSpec(
        source_names=frozenset({"players"}),
        static_values={},
        inputs=(_InputSpec("players", "How many players? ", "int"),),
        prints=(_PrintSpec(slots=(_Slot("teams", formula=_TEAMS),)),),
    ),
    5: _TaskSpec(
        source_names=frozenset({"price", "qty"}),
        static_values={"price": 1.257, "qty": 3},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(_Slot("total", formula=_TOTAL, round_digits=2),),
            ),
        ),
        forbidden_output_names=frozenset({"price"}),
    ),
    6: _TaskSpec(
        source_names=frozenset({"minutes"}),
        static_values={"minutes": 200},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(
                    _Slot("hours", formula=_HOURS),
                    _Slot("minutes_left", formula=_MINUTES_LEFT),
                    _Slot("minutes", roots=frozenset({"minutes"})),
                ),
            ),
        ),
    ),
    7: _TaskSpec(
        source_names=frozenset({"pence"}),
        static_values={},
        inputs=(_InputSpec("pence", "Enter pence: ", "int"),),
        prints=(
            _PrintSpec(
                slots=(
                    _Slot("pounds", formula=_PENCE_POUNDS),
                    _Slot("leftover", formula=_PENCE_LEFT),
                    _Slot("pence", roots=frozenset({"pence"})),
                ),
            ),
        ),
    ),
    8: _TaskSpec(
        source_names=frozenset({"length"}),
        static_values={"length": 2.345},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(
                    _Slot(
                        "rounded",
                        formula=_AREA_MULTIPLICATION,
                        round_digits=2,
                        alternatives=(_AREA_POWER,),
                    ),
                ),
            ),
        ),
        forbidden_output_names=frozenset({"area"}),
    ),
    9: _TaskSpec(
        source_names=frozenset({"apples", "per_bag"}),
        static_values={"apples": 47, "per_bag": 5},
        inputs=(),
        prints=(
            _PrintSpec(
                slots=(
                    _Slot("bags", formula=_APPLES_BAGS),
                    _Slot("left", formula=_APPLES_LEFT),
                ),
                fstring_required=True,
            ),
        ),
    ),
    10: _TaskSpec(
        source_names=frozenset({"items", "box_size", "total_cost"}),
        static_values={},
        inputs=(
            _InputSpec("items", "How many items? ", "int"),
            _InputSpec("box_size", "How many per box? ", "int"),
            _InputSpec("total_cost", "Total cost? £", "float"),
        ),
        prints=(
            _PrintSpec(slots=(_Slot("boxes", formula=_BOXES),)),
            _PrintSpec(slots=(_Slot("leftover", formula=_ITEMS_LEFT),)),
            _PrintSpec(
                slots=(_Slot("cost_per_box", formula=_COST_PER_BOX, round_digits=2),),
            ),
        ),
    ),
}


def analyze_sequence(tree: ast.AST) -> SequenceAnalysis:
    """Validate the conservative top-level grammar and collect source facts."""
    if not isinstance(tree, ast.Module):
        return SequenceAnalysis((), (), ("The exercise code must be a top-level Python module.",))

    issues: list[str] = []
    bindings: list[_Binding] = []
    prints: list[_Print] = []
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.Assign):
            _collect_assignment(statement, index, bindings, issues)
        elif isinstance(statement, ast.AnnAssign):
            _collect_annassign(statement, index, bindings, issues)
        elif isinstance(statement, ast.Expr):
            _collect_print(statement, index, prints, issues)
        else:
            issues.append(_statement_issue(statement))

    return SequenceAnalysis(tuple(bindings), tuple(prints), tuple(dict.fromkeys(issues)))


def construct_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return grammar, provenance, and task-specific issues for one cell."""
    spec = _TASKS.get(exercise_no)
    if spec is None:
        return [f"No construct requirement is defined for exercise {exercise_no}."]
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]

    analysis = analyze_sequence(tree)
    issues = list(analysis.issues)
    if not analysis.prints:
        return _deduplicate([*issues, "Finish with a top-level print() expression."])

    if len(analysis.prints) != len(spec.prints):
        issues.append(
            f"Use exactly {len(spec.prints)} top-level print() expression(s); "
            f"found {len(analysis.prints)}."
        )
    if analysis.prints[-1].index != len(tree.body) - 1:
        issues.append("The final print() expression must be the last live statement.")

    issues.extend(_static_value_issues(analysis, spec))
    issues.extend(_input_issues(tree, analysis, spec))
    issues.extend(_print_flow_issues(tree, analysis, spec))
    return _deduplicate(issues)


def required_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Compatibility alias for the complete construct/data-flow check."""
    return construct_issues(tree, exercise_no)


def straight_line_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return only top-level grammar issues for compatibility callers."""
    del exercise_no
    return list(analyze_sequence(tree).issues)


def name_ids(tree: ast.AST) -> set[str]:
    """Return every variable name in the tagged code."""
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def has_operator(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    """Return whether the code contains a binary operator of the given type."""
    return any(
        isinstance(node, ast.BinOp) and type(node.op) is operator_type for node in ast.walk(tree)
    )


def _collect_assignment(
    statement: ast.Assign,
    index: int,
    bindings: list[_Binding],
    issues: list[str],
) -> None:
    for target in statement.targets:
        _validate_target(target, issues)
        if not _target_shape_matches(target, statement.value):
            issues.append("Tuple assignment targets must match the number of values.")
        for name, value in _target_bindings(target, statement.value):
            bindings.append(_Binding(name, value, _position(statement)))
    _validate_expression(statement.value, issues, allow_print=False)


def _collect_annassign(
    statement: ast.AnnAssign,
    index: int,
    bindings: list[_Binding],
    issues: list[str],
) -> None:
    del index
    if statement.value is None:
        issues.append("An annotated assignment must have a value.")
        return
    _validate_target(statement.target, issues)
    _validate_annotation(statement.annotation, issues)
    if isinstance(statement.target, ast.Name):
        bindings.append(_Binding(statement.target.id, statement.value, _position(statement)))
    _validate_expression(statement.value, issues, allow_print=False)


def _collect_print(
    statement: ast.Expr,
    index: int,
    prints: list[_Print],
    issues: list[str],
) -> None:
    if not _is_direct_call(statement.value, "print"):
        issues.append("Only a top-level print() expression is allowed.")
        return
    call = statement.value
    assert isinstance(call, ast.Call)
    prints.append(_Print(index, call, _position(call)))
    if not call.args:
        issues.append("print() must receive a positional payload.")
    if call.keywords:
        issues.append("print() payload arguments must be positional.")
    for argument in call.args:
        _validate_expression(argument, issues, allow_print=False)


def _validate_annotation(annotation: ast.expr, issues: list[str]) -> None:
    if isinstance(annotation, ast.Name):
        return
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        return
    issues.append("Use a simple name or string annotation.")


def _validate_target(target: ast.AST, issues: list[str]) -> None:
    if isinstance(target, ast.Name):
        if target.id in _PROTECTED_NAMES:
            issues.append(f"Do not rebind the protected name {target.id!r}.")
        return
    if isinstance(target, ast.Tuple):
        for element in target.elts:
            _validate_target(element, issues)
        return
    if isinstance(target, ast.List):
        issues.append("Use tuple targets rather than list targets.")
        return
    if isinstance(target, ast.Starred):
        issues.append("Reject starred assignment targets.")
        return
    issues.append(f"Reject {type(target).__name__} assignment targets; use names or tuples.")


def _target_shape_matches(target: ast.AST, value: ast.expr) -> bool:
    if isinstance(target, ast.Name):
        return True
    if not isinstance(target, ast.Tuple):
        return False
    if not isinstance(value, ast.Tuple) or len(target.elts) != len(value.elts):
        return False
    return all(
        _target_shape_matches(target_element, value_element)
        for target_element, value_element in zip(target.elts, value.elts, strict=True)
    )


def _target_bindings(target: ast.AST, value: ast.expr) -> tuple[tuple[str, ast.expr], ...]:
    if isinstance(target, ast.Name):
        return ((target.id, value),)
    if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple):
        if len(target.elts) != len(value.elts):
            return ()
        records: list[tuple[str, ast.expr]] = []
        for target_element, value_element in zip(target.elts, value.elts, strict=True):
            records.extend(_target_bindings(target_element, value_element))
        return tuple(records)
    if isinstance(target, ast.Tuple):
        records = []
        for element in target.elts:
            records.extend(_target_bindings(element, value))
        return tuple(records)
    return ()


def _validate_expression(
    expression: ast.AST,
    issues: list[str],
    *,
    allow_print: bool,
) -> None:
    if isinstance(expression, (ast.Constant, ast.Name)):
        _validate_leaf_expression(expression, issues)
    elif isinstance(expression, ast.UnaryOp):
        _validate_unary_expression(expression, issues)
    elif isinstance(expression, ast.BinOp):
        _validate_binary_expression(expression, issues)
    elif isinstance(expression, ast.JoinedStr):
        _validate_fstring(expression, issues)
    elif isinstance(expression, ast.FormattedValue):
        _validate_formatted_value(expression, issues)
    elif isinstance(expression, ast.Call):
        _validate_call(expression, issues, allow_print=allow_print)
    elif isinstance(expression, (ast.Tuple, ast.Starred)):
        _validate_sequence_expression(expression, issues)
    else:
        issues.append(_expression_issue(expression))


def _validate_leaf_expression(expression: ast.Constant | ast.Name, issues: list[str]) -> None:
    if isinstance(expression, ast.Constant):
        if isinstance(expression.value, bool) or not isinstance(
            expression.value, (str, int, float)
        ):
            issues.append("Use only string, integer, and floating-point literals.")
    elif expression.id in _PROTECTED_NAMES:
        issues.append(f"Do not use the protected name {expression.id!r} as a value.")


def _validate_unary_expression(expression: ast.UnaryOp, issues: list[str]) -> None:
    if type(expression.op) not in _ALLOWED_UNARY_OPERATORS:
        issues.append("Use only unary + or unary - in sequence expressions.")
    _validate_expression(expression.operand, issues, allow_print=False)


def _validate_binary_expression(expression: ast.BinOp, issues: list[str]) -> None:
    if type(expression.op) not in _ALLOWED_OPERATORS:
        issues.append("Use only the taught arithmetic operators.")
    _validate_expression(expression.left, issues, allow_print=False)
    _validate_expression(expression.right, issues, allow_print=False)


def _validate_formatted_value(expression: ast.FormattedValue, issues: list[str]) -> None:
    if expression.conversion not in (-1, 115):
        issues.append("Use only the safe !s f-string conversion.")
    if expression.format_spec is not None and not _empty_format_spec(expression.format_spec):
        issues.append("F-string format specifications must be empty.")
    _validate_expression(expression.value, issues, allow_print=False)
    if expression.format_spec is not None:
        _validate_expression(expression.format_spec, issues, allow_print=False)


def _validate_sequence_expression(
    expression: ast.Tuple | ast.Starred,
    issues: list[str],
) -> None:
    if isinstance(expression, ast.Starred):
        issues.append("Reject starred expressions.")
        return
    for element in expression.elts:
        _validate_expression(element, issues, allow_print=False)


def _validate_fstring(expression: ast.JoinedStr, issues: list[str]) -> None:
    for value in expression.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            continue
        if not isinstance(value, ast.FormattedValue):
            issues.append("F-strings may contain only literal text and placeholders.")
            continue
        _validate_expression(value, issues, allow_print=False)


def _validate_call(expression: ast.Call, issues: list[str], *, allow_print: bool) -> None:
    name = _call_name(expression)
    if name is None:
        _reject_call(expression, issues, "Reject attribute and arbitrary side-effect calls.")
    elif name == "print":
        _validate_print_call(expression, issues, allow_print=allow_print)
    elif name not in _ALLOWED_CALLS:
        _reject_call(expression, issues, f"Reject arbitrary side-effect call {name}().")
    elif name == "input":
        _validate_input_call(expression, issues)
    else:
        _validate_allowed_call(expression, name, issues)


def _validate_print_call(
    expression: ast.Call,
    issues: list[str],
    *,
    allow_print: bool,
) -> None:
    if not allow_print:
        issues.append("print() may only be used as a top-level expression.")
    if expression.keywords:
        issues.append("print() payload arguments must be positional.")
    if not expression.args:
        issues.append("print() must receive a positional payload.")
    _validate_call_arguments(expression, issues)


def _validate_allowed_call(expression: ast.Call, name: str, issues: list[str]) -> None:
    if name in {"int", "float", "str"}:
        if len(expression.args) != 1 or expression.keywords:
            issues.append(f"{name}() must receive one positional value.")
    elif name == "round" and not _valid_round_shape(expression):
        issues.append("round() must receive one value and an exact precision argument.")
    _validate_call_arguments(expression, issues)


def _reject_call(expression: ast.Call, issues: list[str], message: str) -> None:
    issues.append(message)
    _validate_call_arguments(expression, issues)


def _validate_call_arguments(expression: ast.Call, issues: list[str]) -> None:
    for argument in expression.args:
        _validate_expression(argument, issues, allow_print=False)
    for keyword in expression.keywords:
        _validate_expression(keyword.value, issues, allow_print=False)


def _validate_input_call(expression: ast.Call, issues: list[str]) -> None:
    positional = expression.args[0] if len(expression.args) == 1 else None
    prompt_keywords = [keyword for keyword in expression.keywords if keyword.arg == "prompt"]
    if len(expression.args) > 1 or (positional is not None and prompt_keywords):
        issues.append("input() accepts at most one prompt value.")
    for keyword in expression.keywords:
        if keyword.arg != "prompt":
            issues.append("input() does not accept arbitrary keyword arguments.")
        _validate_expression(keyword.value, issues, allow_print=False)
    if positional is not None:
        _validate_expression(positional, issues, allow_print=False)


def _valid_round_shape(expression: ast.Call) -> bool:
    if len(expression.args) == _ROUND_ARGUMENT_COUNT and not expression.keywords:
        return True
    return (
        len(expression.args) == 1
        and len(expression.keywords) == 1
        and expression.keywords[0].arg == "ndigits"
    )


def _empty_format_spec(expression: ast.AST) -> bool:
    return isinstance(expression, ast.JoinedStr) and all(
        isinstance(value, ast.Constant) and value.value == "" for value in expression.values
    )


def _statement_issue(statement: ast.stmt) -> str:
    name = type(statement).__name__
    description = _NODE_DESCRIPTIONS.get(name, name)
    if name == "AugAssign":
        return "Reject AugAssign; use a simple assignment."
    if name in {"Import", "ImportFrom"}:
        return "Imports are not allowed in a sequence cell."
    return f"Only Assign, AnnAssign, and top-level print() Expr are allowed; reject {description}."


def _expression_issue(expression: ast.AST) -> str:
    name = type(expression).__name__
    description = _NODE_DESCRIPTIONS.get(name, name)
    return f"Reject {description}; use straight-line assignments, arithmetic, and f-strings."


def _is_direct_call(expression: ast.AST, name: str) -> bool:
    return isinstance(expression, ast.Call) and _call_name(expression) == name


def _call_name(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


def _position(node: ast.AST) -> Position:
    return (
        getattr(node, "lineno", _EMPTY_POSITION[0]),
        getattr(node, "col_offset", _EMPTY_POSITION[1]),
    )


def _deduplicate(issues: list[str]) -> list[str]:
    return list(dict.fromkeys(issues))


def _static_value_issues(analysis: SequenceAnalysis, spec: _TaskSpec) -> list[str]:
    issues: list[str] = []
    if not spec.static_values:
        return issues
    final_position = analysis.prints[-1].position
    for name, expected in spec.static_values.items():
        binding = analysis.latest_binding(name, before=final_position)
        if binding is None:
            issues.append(f"Keep the supplied value for {name!r} before the final print().")
            continue
        value = _binding_value(binding, analysis.bindings, spec.source_names)
        if value.numeric != expected or name not in value.roots:
            issues.append(f"{name} must keep the supplied value {expected!r}.")
    return issues


def _input_issues(
    tree: ast.Module,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> list[str]:
    if not spec.inputs:
        return []
    expected_prompts = tuple(item.prompt for item in spec.inputs)
    actual_prompts = tuple(_all_input_prompts(tree, analysis, spec.source_names))
    issues: list[str] = []
    if actual_prompts != expected_prompts:
        issues.append(
            "Use the exact input prompts in order: "
            + ", ".join(repr(prompt) for prompt in expected_prompts)
            + "."
        )
    if len(actual_prompts) != len(expected_prompts):
        issues.append(
            f"Use exactly {len(expected_prompts)} input() call(s); found {len(actual_prompts)}."
        )

    live_facts = _live_input_facts(analysis, spec)
    for item in spec.inputs:
        matching = [fact for fact in live_facts if fact.prompt == item.prompt]
        if not _input_binding_reaches_print(analysis, spec, item):
            issues.append(
                f"Assign the value entered for {item.name!r} to a variable used in the printed result."
            )
        if not matching:
            issues.append(f"The value entered for {item.name!r} must reach the printed result.")
            continue
        if not any(fact.casts and fact.casts[-1] == item.cast for fact in matching):
            issues.append(f"{item.name!r} must be cast with {item.cast}() before arithmetic.")
    return issues


def _all_input_prompts(
    tree: ast.Module,
    analysis: SequenceAnalysis,
    source_names: frozenset[str],
) -> list[str]:
    prompts: list[tuple[Position, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node) != "input":
            continue
        expression = _input_prompt_expression(node)
        if expression is None:
            prompts.append((_position(node), ""))
            continue
        value = _analyze_value(expression, _position(node), analysis.bindings, source_names)
        prompts.append((_position(node), value.text or ""))
    return [prompt for _, prompt in sorted(prompts)]


def _live_input_facts(analysis: SequenceAnalysis, spec: _TaskSpec) -> tuple[_InputFact, ...]:
    facts: list[_InputFact] = []
    for record in analysis.prints:
        for argument in record.call.args:
            for value in _payload_values(
                argument, record.position, analysis.bindings, spec.source_names
            ):
                facts.extend(value.input_facts)
    return tuple(dict.fromkeys(facts))


def _input_binding_reaches_print(
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
    item: _InputSpec,
) -> bool:
    if not analysis.prints:
        return False
    binding = analysis.latest_binding(item.name, before=analysis.prints[-1].position)
    if binding is None:
        return False
    value = _binding_value(binding, analysis.bindings, spec.source_names)
    has_matching_fact = any(fact.prompt == item.prompt for fact in value.input_facts)
    if not has_matching_fact:
        return False
    return any(
        _name_reaches_target(
            name,
            item.name,
            record.position,
            analysis.bindings,
            frozenset(),
        )
        for record in analysis.prints
        for argument in record.call.args
        for name in _names_in_expression(argument)
    )


def _name_reaches_target(
    name: str,
    target: str,
    before: Position,
    bindings: tuple[_Binding, ...],
    seen: frozenset[Position],
) -> bool:
    if name == target:
        return True
    binding = _latest_binding(name, before, bindings)
    if binding is None or binding.position in seen:
        return False
    return any(
        _name_reaches_target(
            child.id,
            target,
            binding.position,
            bindings,
            seen | {binding.position},
        )
        for child in ast.walk(binding.value)
        if isinstance(child, ast.Name)
    )


def _names_in_expression(expression: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(expression) if isinstance(node, ast.Name)}


def _print_flow_issues(
    tree: ast.Module,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> list[str]:
    issues: list[str] = []
    for index, record in enumerate(analysis.prints):
        if index < len(spec.prints):
            issues.extend(_print_line_issues(index, record, analysis, spec))
    if len(analysis.prints) > len(spec.prints):
        issues.append("Remove extra top-level print() expressions.")
    if analysis.prints and analysis.prints[-1].index != len(tree.body) - 1:
        issues.append("The final print() expression must be the last live statement.")
    return issues


def _fstring_line_issues(
    index: int,
    record: _Print,
    print_spec: _PrintSpec,
) -> list[str]:
    if not print_spec.fstring_required:
        return []
    issues: list[str] = []
    if not _contains_fstring(record.call):
        issues.append(f"Print line {index + 1} must use an f-string in its positional payload.")
    if len(record.call.args) != 1 or not isinstance(record.call.args[0], ast.JoinedStr):
        issues.append(f"Print line {index + 1} must put the complete result in one f-string.")
    if _contains_addition(record.call):
        issues.append(f"Print line {index + 1} must not use + concatenation.")
    return issues


def _print_line_issues(
    index: int,
    record: _Print,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> list[str]:
    print_spec = spec.prints[index]
    issues = _fstring_line_issues(index, record, print_spec)
    values = _record_payload_values(record, analysis, spec)
    for slot in print_spec.slots:
        if not any(_slot_matches(value, slot) for value in values):
            issues.append(f"Print line {index + 1} must carry the live {slot.name!r} calculation.")
        if slot.formula is not None and slot.name in _names_in_expression(record.call):
            issues.extend(
                f"Print line {index + 1}: {issue}"
                for issue in _binding_flow_issues(analysis, record.position, spec, slot)
            )
    if print_spec.fstring_required:
        issues.extend(_literal_fstring_issues(record.call, record.position, analysis, spec))
    issues.extend(_forbidden_output_issues(record, analysis, spec))
    return issues


def _record_payload_values(
    record: _Print,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> tuple[_Value, ...]:
    return tuple(
        value
        for argument in record.call.args
        for value in _payload_values(
            argument, record.position, analysis.bindings, spec.source_names
        )
    )


def _payload_values(
    expression: ast.AST,
    position: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
) -> tuple[_Value, ...]:
    if isinstance(expression, ast.JoinedStr):
        return _joined_payload_values(expression, position, bindings, source_names)
    if isinstance(expression, ast.Tuple):
        return _tuple_payload_values(expression, position, bindings, source_names)
    if isinstance(expression, ast.BinOp):
        return _binary_payload_values(expression, position, bindings, source_names)
    if isinstance(expression, (ast.UnaryOp, ast.Call, ast.Name, ast.Constant)):
        return (_analyze_value(expression, position, bindings, source_names),)
    return ()


def _joined_payload_values(
    expression: ast.JoinedStr,
    position: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
) -> tuple[_Value, ...]:
    return tuple(
        _analyze_value(value.value, position, bindings, source_names)
        for value in expression.values
        if isinstance(value, ast.FormattedValue)
    )


def _tuple_payload_values(
    expression: ast.Tuple,
    position: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
) -> tuple[_Value, ...]:
    values: list[_Value] = []
    for element in expression.elts:
        values.extend(_payload_values(element, position, bindings, source_names))
    return tuple(values)


def _binary_payload_values(
    expression: ast.BinOp,
    position: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
) -> tuple[_Value, ...]:
    return (
        _analyze_value(expression, position, bindings, source_names),
        *_payload_values(expression.left, position, bindings, source_names),
        *_payload_values(expression.right, position, bindings, source_names),
    )


def _slot_formulas(slot: _Slot) -> tuple[_Formula, ...]:
    return (slot.formula, *slot.alternatives) if slot.formula is not None else ()


def _slot_matches(value: _Value, slot: _Slot) -> bool:
    formulas = _slot_formulas(slot)
    if not formulas:
        return value.roots == slot.roots
    if not any(_contains_formula(value, formula) for formula in formulas):
        return False
    if slot.round_digits is not None:
        return any(_has_correct_round(value, formula, slot.round_digits) for formula in formulas)
    return True


def _binding_flow_issues(
    analysis: SequenceAnalysis,
    before: Position,
    spec: _TaskSpec,
    slot: _Slot,
) -> list[str]:
    binding = analysis.latest_binding(slot.name, before=before)
    formulas = _slot_formulas(slot)
    if binding is None or not formulas:
        return ["The result must be assigned before it is printed."] if binding is None else []
    value = _binding_value(binding, analysis.bindings, spec.source_names)
    if not any(_contains_formula(value, formula) for formula in formulas):
        return [f"{slot.name!r} must be assigned from the corrected live calculation."]
    if slot.round_digits is not None and not any(
        _has_correct_round(value, formula, slot.round_digits) for formula in formulas
    ):
        return [f"{slot.name!r} must be rounded to {slot.round_digits} decimal place(s)."]
    return []


def _forbidden_output_issues(
    record: _Print,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> list[str]:
    if not spec.forbidden_output_names:
        return []
    used: set[str] = set()
    for argument in record.call.args:
        used.update(_direct_result_names(argument))
    old_names: set[str] = set()
    for name in used:
        old_names.update(
            old_name
            for old_name in spec.forbidden_output_names
            if _is_pure_alias(name, old_name, record.position, analysis.bindings, frozenset())
        )
    if not old_names:
        return []
    return ["Do not print the old result variable(s): " + ", ".join(sorted(old_names)) + "."]


def _is_pure_alias(
    name: str,
    target: str,
    before: Position,
    bindings: tuple[_Binding, ...],
    seen: frozenset[Position],
) -> bool:
    if name == target:
        return True
    binding = _latest_binding(name, before, bindings)
    if binding is None or binding.position in seen or not isinstance(binding.value, ast.Name):
        return False
    return _is_pure_alias(
        binding.value.id,
        target,
        binding.position,
        bindings,
        seen | {binding.position},
    )


def _literal_fstring_issues(
    call: ast.Call,
    position: Position,
    analysis: SequenceAnalysis,
    spec: _TaskSpec,
) -> list[str]:
    issues: list[str] = []
    for formatted in _formatted_values(call):
        value = _analyze_value(formatted, position, analysis.bindings, spec.source_names)
        if not value.roots and not value.operations and not value.input_facts:
            issues.append("Do not hard-code a formatted result value.")
    return issues


def _has_correct_round(value: _Value, formula: _Formula, digits: int) -> bool:
    matching = any(
        round_value.precision == digits and _contains_formula(round_value.value, formula)
        for round_value in value.rounds
    )
    wrong_precision = any(round_value.precision != digits for round_value in value.rounds)
    return matching and not wrong_precision


def _contains_formula(value: _Value, formula: _Formula) -> bool:
    """Match the live result's primary arithmetic operation, not dead inner work."""
    return bool(value.operations) and _operation_matches(value.operations[-1], formula)


def _operation_matches(operation: _Operation, formula: _Formula) -> bool:
    if operation.operator is not formula.operator:
        return False
    left, right = formula.operands
    if _operand_matches(operation.left, left) and _operand_matches(operation.right, right):
        return True
    return (
        formula.allow_reversed
        and _operand_matches(operation.right, left)
        and _operand_matches(operation.left, right)
    )


def _operand_matches(value: _Value, pattern: _OperandPattern) -> bool:
    if pattern.formula is not None:
        return _contains_formula(value, pattern.formula)
    if pattern.number is not None:
        return value.numeric == pattern.number and not value.roots
    return value.roots == pattern.roots and (not value.operations or _numeric_factorization(value))


def _binding_value(
    binding: _Binding,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
) -> _Value:
    value = _analyze_value(binding.value, binding.position, bindings, source_names)
    if binding.name in source_names:
        value = replace(value, roots=value.roots | {binding.name})
    if value.input_facts:
        value = replace(
            value,
            input_facts=tuple(replace(fact, source=binding.name) for fact in value.input_facts),
        )
    return value


def _numeric_factorization(value: _Value) -> bool:
    return value.numeric is not None and all(
        not operation.left.roots and not operation.right.roots for operation in value.operations
    )


def _analyze_value(
    expression: ast.AST,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position] = frozenset(),
) -> _Value:
    if isinstance(expression, (ast.Constant, ast.Name, ast.Call)):
        return _analyze_term_value(expression, before, bindings, source_names, seen)
    if isinstance(expression, (ast.UnaryOp, ast.BinOp)):
        return _analyze_operator_value(expression, before, bindings, source_names, seen)
    if isinstance(expression, (ast.JoinedStr, ast.FormattedValue)):
        return _analyze_string_value(expression, before, bindings, source_names, seen)
    if isinstance(expression, ast.Tuple):
        return _analyze_tuple_value(expression, before, bindings, source_names, seen)
    return _analyze_child_values(expression, before, bindings, source_names, seen)


def _analyze_term_value(
    expression: ast.Constant | ast.Name | ast.Call,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    if isinstance(expression, ast.Constant):
        if isinstance(expression.value, str):
            return _Value(text=expression.value)
        if isinstance(expression.value, (int, float)) and not isinstance(expression.value, bool):
            return _Value(numeric=expression.value)
        return _Value()
    if isinstance(expression, ast.Name):
        return _analyze_name(expression, before, bindings, source_names, seen)
    return _analyze_call_value(expression, before, bindings, source_names, seen)


def _analyze_operator_value(
    expression: ast.UnaryOp | ast.BinOp,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    if isinstance(expression, ast.UnaryOp):
        operand = _analyze_value(expression.operand, before, bindings, source_names, seen)
        return replace(operand, numeric=_unary_value(expression.op, operand.numeric))
    left = _analyze_value(expression.left, before, bindings, source_names, seen)
    right = _analyze_value(expression.right, before, bindings, source_names, seen)
    operation = _Operation(type(expression.op), left, right)
    merged = _merge_values((left, right, _Value(operations=(operation,))))
    return replace(merged, numeric=_binary_value(expression.op, left.numeric, right.numeric))


def _analyze_string_value(
    expression: ast.JoinedStr | ast.FormattedValue,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    if isinstance(expression, ast.JoinedStr):
        values = tuple(
            _analyze_value(value.value, before, bindings, source_names, seen)
            for value in expression.values
            if isinstance(value, ast.FormattedValue)
        )
        return _merge_values((*values, _Value(has_fstring=True)))
    value = _analyze_value(expression.value, before, bindings, source_names, seen)
    if expression.format_spec is None:
        return value
    format_value = _analyze_value(expression.format_spec, before, bindings, source_names, seen)
    return _merge_values((value, format_value))


def _analyze_tuple_value(
    expression: ast.Tuple,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    return _merge_values(
        tuple(
            _analyze_value(element, before, bindings, source_names, seen)
            for element in expression.elts
        )
    )


def _analyze_child_values(
    expression: ast.AST,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    children = tuple(
        _analyze_value(child, before, bindings, source_names, seen)
        for child in ast.iter_child_nodes(expression)
    )
    return _merge_values(children)


def _analyze_name(
    expression: ast.Name,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    binding = _latest_binding(expression.id, before, bindings)
    if binding is None or binding.position in seen:
        return _Value(roots=frozenset({expression.id}))
    nested = _analyze_value(
        binding.value,
        binding.position,
        bindings,
        source_names,
        seen | {binding.position},
    )
    value = nested
    if expression.id in source_names:
        value = replace(value, roots=value.roots | {expression.id})
    if nested.input_facts:
        value = replace(
            value,
            input_facts=tuple(replace(fact, source=expression.id) for fact in nested.input_facts),
        )
    return value


def _analyze_call_value(
    expression: ast.Call,
    before: Position,
    bindings: tuple[_Binding, ...],
    source_names: frozenset[str],
    seen: frozenset[Position],
) -> _Value:
    name = _call_name(expression)
    arguments = tuple(
        _analyze_value(argument, before, bindings, source_names, seen)
        for argument in expression.args
    )
    keywords = tuple(
        _analyze_value(keyword.value, before, bindings, source_names, seen)
        for keyword in expression.keywords
    )
    value = _merge_values((*arguments, *keywords))
    if name == "input":
        prompt_expression = _input_prompt_expression(expression)
        prompt_value = (
            _analyze_value(prompt_expression, before, bindings, source_names, seen)
            if prompt_expression is not None
            else _Value()
        )
        fact = _InputFact(prompt_value.text or "", f"input@{_position(expression)}")
        return _Value(text=prompt_value.text, input_facts=(fact,))
    if name in {"int", "float", "str"} and value.input_facts:
        facts = tuple(replace(fact, casts=(*fact.casts, name)) for fact in value.input_facts)
        return replace(value, input_facts=facts)
    if name == "round":
        precision_expression = _round_precision_expression(expression)
        precision_value = (
            _analyze_value(precision_expression, before, bindings, source_names, seen)
            if precision_expression is not None
            else _Value()
        )
        precision = precision_value.numeric if type(precision_value.numeric) is int else None
        round_value = arguments[0] if arguments else _Value()
        return _merge_values((value, _Value(rounds=(_Round(precision, round_value),))))
    return value


def _merge_values(values: tuple[_Value, ...]) -> _Value:
    if not values:
        return _Value()
    roots: set[str] = set()
    facts: list[_InputFact] = []
    operations: list[_Operation] = []
    rounds: list[_Round] = []
    has_fstring = False
    numeric_values = [value.numeric for value in values]
    text_values = [value.text for value in values if value.text is not None]
    for value in values:
        roots.update(value.roots)
        facts.extend(value.input_facts)
        operations.extend(value.operations)
        rounds.extend(value.rounds)
        has_fstring = has_fstring or value.has_fstring
    if numeric_values and (
        len(numeric_values) == 1 or all(value == numeric_values[0] for value in numeric_values)
    ):
        numeric = numeric_values[0]
    else:
        numeric = None
    text = (
        text_values[0]
        if text_values and all(value == text_values[0] for value in text_values)
        else None
    )
    return _Value(
        numeric=numeric,
        text=text,
        roots=frozenset(roots),
        input_facts=tuple(dict.fromkeys(facts)),
        operations=tuple(operations),
        rounds=tuple(rounds),
        has_fstring=has_fstring,
    )


def _latest_binding(
    name: str,
    before: Position,
    bindings: tuple[_Binding, ...],
) -> _Binding | None:
    candidates = [
        binding for binding in bindings if binding.name == name and binding.position < before
    ]
    return candidates[-1] if candidates else None


def _binary_value(
    operator_type: ast.operator,
    left: Numeric | None,
    right: Numeric | None,
) -> Numeric | None:
    if left is None or right is None:
        return None
    operation = _BINARY_OPERATIONS.get(type(operator_type))
    if operation is None:
        return None
    try:
        return operation(left, right)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def _unary_value(operator: ast.unaryop, value: Numeric | None) -> Numeric | None:
    if value is None:
        return None
    if isinstance(operator, ast.UAdd):
        return value
    if isinstance(operator, ast.USub):
        return -value
    return None


def _input_prompt_expression(call: ast.Call) -> ast.expr | None:
    if len(call.args) == 1 and not call.keywords:
        return call.args[0]
    if not call.args and len(call.keywords) == 1 and call.keywords[0].arg == "prompt":
        return call.keywords[0].value
    return None


def _round_precision_expression(call: ast.Call) -> ast.expr | None:
    if len(call.args) == _ROUND_ARGUMENT_COUNT and not call.keywords:
        return call.args[1]
    if len(call.args) == 1 and len(call.keywords) == 1 and call.keywords[0].arg == "ndigits":
        return call.keywords[0].value
    return None


def _contains_fstring(expression: ast.AST) -> bool:
    return any(isinstance(node, ast.JoinedStr) for node in ast.walk(expression))


def _contains_addition(expression: ast.AST) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
        for node in ast.walk(expression)
    )


def _formatted_values(expression: ast.AST) -> tuple[ast.AST, ...]:
    return tuple(
        value.value
        for node in ast.walk(expression)
        if isinstance(node, ast.JoinedStr)
        for value in node.values
        if isinstance(value, ast.FormattedValue)
    )


def _direct_result_names(expression: ast.AST) -> set[str]:
    if isinstance(expression, ast.Name):
        return {expression.id}
    if isinstance(expression, ast.JoinedStr):
        names: set[str] = set()
        for value in expression.values:
            if isinstance(value, ast.FormattedValue):
                names.update(_direct_result_names(value.value))
        return names
    if isinstance(expression, ast.Call) and _call_name(expression) == "str" and expression.args:
        return _direct_result_names(expression.args[0])
    return set()


__all__ = [
    "SequenceAnalysis",
    "analyze_sequence",
    "construct_issues",
    "has_operator",
    "name_ids",
    "required_flow_issues",
    "straight_line_issues",
]
