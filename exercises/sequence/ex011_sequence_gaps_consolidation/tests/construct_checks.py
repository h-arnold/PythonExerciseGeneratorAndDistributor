"""Semantic sensitivity and safety checks for ex011 sequence gaps consolidation."""

from __future__ import annotations

import ast
import builtins
import copy
import io
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Final

_ALLOWED_FUNCTIONS: Final[frozenset[str]] = frozenset(
    {"float", "format", "input", "int", "print", "str"}
)
# These are the only attribute-based methods needed for equivalent string
# formatting; arbitrary attribute access remains forbidden below.
_ALLOWED_METHODS: Final[frozenset[str]] = frozenset({"format", "join"})
_ALLOWED_BINARY_OPERATORS: Final[tuple[type[ast.operator], ...]] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)
_ALLOWED_UNARY_OPERATORS: Final[tuple[type[ast.unaryop], ...]] = (
    ast.UAdd,
    ast.USub,
    ast.Invert,
)
_ALLOWED_CONSTANT_TYPES: Final[tuple[type[object], ...]] = (str, int, float, bool, type(None))
_FORBIDDEN_REBINDINGS: Final[frozenset[str]] = frozenset(dir(builtins)) | frozenset(
    {"__builtins__"}
)
_FORBIDDEN_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__builtins__",
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "eval",
        "exec",
        "exit",
        "getattr",
        "globals",
        "locals",
        "open",
        "quit",
        "setattr",
        "vars",
    }
)

# These values are only perturbation inputs for static sensitivity checks.  The
# semantic decision is made by executing the student's source and comparing
# outputs; the names are not used as a direct-use allowlist.
_STATIC_ALTERNATES: Final[dict[int, dict[str, str | int | float]]] = {
    1: {
        "word_one": "Changed",
        "word_two": "updated",
        "word_three": "value",
    },
    2: {"greeting": "Hi", "name": "Ravi"},
    4: {"first_number": 13, "second_number": 17},
    5: {"price": 4.5, "item_count": 5},
    6: {"total_distance": 19, "days": 4},
    7: {"first_name": "Noor", "hobby": "cycling"},
}
_INTERACTIVE_EXERCISES: Final[frozenset[int]] = frozenset({3, 8, 9, 10})
_INTERACTIVE_STATIC_ALTERNATES: Final[dict[int, dict[str, str | int | float]]] = {
    10: {
        "shop_name": "Other Shop",
        "notebook_price": 5.0,
        "notebook_count": 5,
    },
}
_FSTRING_EXERCISE_NO: Final[int] = 7
_EXECUTION_EXCEPTIONS: Final[tuple[type[BaseException], ...]] = (
    ArithmeticError,
    AttributeError,
    IndexError,
    KeyError,
    NameError,
    RecursionError,
    RuntimeError,
    TypeError,
    UnicodeError,
    ValueError,
)

_STATEMENT_MESSAGES: Final[dict[type[ast.stmt], str]] = {
    ast.Assert: "assertions are not allowed in this straight-line sequence cell",
    ast.AsyncFor: "for loops are not allowed in this straight-line sequence cell",
    ast.AsyncFunctionDef: "function definitions are not allowed in this cell",
    ast.AsyncWith: "with statements are not allowed in this straight-line sequence cell",
    ast.Break: "break statements are not allowed in this straight-line sequence cell",
    ast.ClassDef: "class definitions are not allowed in this cell",
    ast.Continue: "continue statements are not allowed in this straight-line sequence cell",
    ast.Delete: "delete statements are not allowed in this cell",
    ast.For: "for loops are not allowed in this straight-line sequence cell",
    ast.FunctionDef: "function definitions are not allowed in this cell",
    ast.Global: "global declarations are not allowed in this cell",
    ast.If: "if/else control flow is not allowed in this straight-line sequence cell",
    ast.Import: "imports are not allowed in this cell",
    ast.ImportFrom: "imports are not allowed in this cell",
    ast.Match: "match statements are not allowed in this straight-line sequence cell",
    ast.Nonlocal: "nonlocal declarations are not allowed in this cell",
    ast.Pass: "pass statements are not allowed in this cell",
    ast.Raise: "raise statements are not allowed in this cell",
    ast.Return: "return statements are not allowed in this cell",
    ast.Try: "try statements are not allowed in this cell",
    ast.While: "while loops are not allowed in this straight-line sequence cell",
    ast.With: "with statements are not allowed in this straight-line sequence cell",
}


@dataclass(frozen=True)
class _Execution:
    """Captured output and the portion produced after the final input."""

    output: str
    final_output: str
    input_count: int


def required_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return safety and semantic-sensitivity issues for one exercise cell."""

    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]

    issues = _statement_issues(tree)
    if issues:
        return issues
    if _final_print(tree) is None:
        return ["Finish with a top-level print() call."]

    if exercise_no in _STATIC_ALTERNATES:
        issues.extend(_static_sensitivity_issues(tree, exercise_no))
    elif exercise_no in _INTERACTIVE_EXERCISES:
        issues.extend(_interactive_sensitivity_issues(tree, exercise_no))
    else:
        issues.append(f"Exercise {exercise_no}: no semantic requirement is defined.")

    if exercise_no == _FSTRING_EXERCISE_NO and not _has_final_fstring(tree):
        issues.append("The final message must be built with an f-string.")
    return issues


def _statement_issues(tree: ast.Module) -> list[str]:
    """Validate the conservative straight-line statement allowlist."""

    issues: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            issues.extend(_assignment_issues(statement))
        elif isinstance(statement, ast.Expr):
            if not _is_print_call(statement.value):
                issues.append("Only print() expression statements are allowed.")
            else:
                issues.extend(_expression_issues(statement.value))
        else:
            message = _STATEMENT_MESSAGES.get(
                type(statement),
                f"{type(statement).__name__} statements are not allowed in this cell.",
            )
            issues.append(message)
    return issues


def _assignment_issues(statement: ast.Assign) -> list[str]:
    """Validate assignment targets and their right-hand side."""

    issues: list[str] = []
    if not statement.targets:
        return ["An assignment must have at least one target."]
    for target in statement.targets:
        if not isinstance(target, ast.Name):
            issues.append("Assignment targets must be plain names.")
        elif target.id in _FORBIDDEN_REBINDINGS:
            issues.append(f"Do not rebind the builtin or special name {target.id!r}.")
    issues.extend(_expression_issues(statement.value))
    return issues


def _is_print_call(expression: ast.AST) -> bool:
    """Return whether an expression is a direct print call."""

    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "print"
    )


def _expression_issues(expression: ast.AST) -> list[str]:
    """Validate expressions without rejecting ordinary formatting equivalents."""

    if isinstance(expression, ast.Constant):
        issues = _constant_issues(expression)
    elif isinstance(expression, ast.Name):
        issues = _name_issues(expression)
    elif isinstance(expression, ast.BinOp):
        issues = _binary_issues(expression)
    elif isinstance(expression, ast.UnaryOp):
        issues = _unary_issues(expression)
    elif isinstance(expression, (ast.List, ast.Tuple)):
        issues = _sequence_issues(expression)
    elif isinstance(expression, ast.JoinedStr):
        issues = _joined_string_issues(expression)
    elif isinstance(expression, ast.FormattedValue):
        issues = _formatted_value_issues(expression)
    elif isinstance(expression, ast.Call):
        issues = _call_issues(expression)
    else:
        issues = _special_expression_issues(expression)
    return issues


def _constant_issues(expression: ast.Constant) -> list[str]:
    """Validate literal values used by an expression."""

    if not isinstance(expression.value, _ALLOWED_CONSTANT_TYPES):
        return ["Only ordinary text and numeric literals are allowed."]
    return []


def _name_issues(expression: ast.Name) -> list[str]:
    """Validate a loaded name."""

    if expression.id in _FORBIDDEN_NAMES:
        return [f"The name {expression.id!r} is not allowed in this cell."]
    return []


def _binary_issues(expression: ast.BinOp) -> list[str]:
    """Validate arithmetic and string-formatting expressions."""

    if not isinstance(expression.op, _ALLOWED_BINARY_OPERATORS):
        return ["Only ordinary arithmetic and string-formatting operators are allowed."]
    return _expression_issues(expression.left) + _expression_issues(expression.right)


def _unary_issues(expression: ast.UnaryOp) -> list[str]:
    """Validate a unary expression."""

    if not isinstance(expression.op, _ALLOWED_UNARY_OPERATORS):
        return ["This unary operator is not allowed in the sequence cell."]
    return _expression_issues(expression.operand)


def _sequence_issues(expression: ast.List | ast.Tuple) -> list[str]:
    """Validate list/tuple literals used by join or percent formatting."""

    issues: list[str] = []
    for element in expression.elts:
        issues.extend(_expression_issues(element))
    return issues


def _joined_string_issues(expression: ast.JoinedStr) -> list[str]:
    """Validate the literal and formatted parts of an f-string."""

    issues: list[str] = []
    for value in expression.values:
        issues.extend(_expression_issues(value))
    return issues


def _formatted_value_issues(expression: ast.FormattedValue) -> list[str]:
    """Validate a formatted expression and its optional format spec."""

    issues = _expression_issues(expression.value)
    if expression.format_spec is not None:
        issues.extend(_expression_issues(expression.format_spec))
    return issues


def _special_expression_issues(expression: ast.AST) -> list[str]:
    """Reject expressions outside the conservative straight-line allowlist."""

    if isinstance(expression, ast.Attribute):
        return ["Attributes are only allowed as the receiver of join() or format()."]
    if isinstance(expression, ast.Subscript):
        return ["Subscripts are not allowed in this sequence cell."]
    if isinstance(expression, ast.NamedExpr):
        return ["Named expressions are not allowed in this sequence cell."]
    if isinstance(expression, ast.Starred):
        return ["Starred arguments are not allowed in this sequence cell."]
    return [f"{type(expression).__name__} expressions are not allowed in this cell."]


def _call_issues(expression: ast.Call) -> list[str]:
    """Validate direct builtin calls and the two safe string methods."""

    target_issues = _call_target_issues(expression)
    if target_issues:
        return target_issues
    issues: list[str] = []
    for argument in expression.args:
        issues.extend(_expression_issues(argument))
    for keyword in expression.keywords:
        issues.extend(_expression_issues(keyword.value))
    return issues


def _call_target_issues(expression: ast.Call) -> list[str]:
    """Validate the callable portion of a call expression."""

    if isinstance(expression.func, ast.Name):
        issues = _direct_call_target_issues(expression.func.id, expression)
    elif isinstance(expression.func, ast.Attribute):
        if expression.func.attr not in _ALLOWED_METHODS:
            issues = [f"The method {expression.func.attr!r} is not allowed in this cell."]
        else:
            issues = _expression_issues(expression.func.value)
    else:
        issues = ["Only direct builtin calls and safe string methods are allowed."]
    return issues


def _direct_call_target_issues(name: str, expression: ast.Call) -> list[str]:
    """Validate a direct builtin call and its limited argument forms."""

    if name not in _ALLOWED_FUNCTIONS:
        return [f"The function {name!r} is not allowed in this cell."]
    if name == "input" and (len(expression.args) > 1 or expression.keywords):
        return ["input() accepts at most one prompt argument."]
    if name in {"float", "format", "int", "str"} and expression.keywords:
        return [f"{name}() does not accept keyword arguments here."]
    return []


def _final_print(module: ast.Module) -> ast.Call | None:
    """Return the last top-level print call in a cell."""

    prints: list[ast.Call] = []
    for statement in module.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if isinstance(call.func, ast.Name) and call.func.id == "print":
            prints.append(call)
    return prints[-1] if prints else None


def _static_sensitivity_issues(tree: ast.Module, exercise_no: int) -> list[str]:
    """Execute static code after changing each supplied value separately."""

    return _replacement_sensitivity_issues(
        tree,
        _STATIC_ALTERNATES[exercise_no],
        (),
        "Static",
    )


def _replacement_sensitivity_issues(
    tree: ast.Module,
    alternates: dict[str, str | int | float],
    inputs: tuple[str, ...],
    label: str,
) -> list[str]:
    """Require every perturbed supplied value to change the final output."""

    baseline, error = _execute_tree(tree, inputs)
    if error is not None:
        return [f"{label} semantic execution failed: {error}"]
    assert baseline is not None
    if not baseline.final_output:
        return ["The program must print a final result."]

    issues: list[str] = []
    for name, alternate in alternates.items():
        changed_tree, found = _replace_assignment_value(tree, name, alternate)
        if not found:
            issues.append(f"The supplied value {name!r} must be assigned in the cell.")
            continue
        changed, error = _execute_tree(changed_tree, inputs)
        if error is not None:
            issues.append(f"Changing {name!r} caused an execution error: {error}")
            continue
        assert changed is not None
        if changed.final_output == baseline.final_output:
            issues.append(
                f"The final output must change when the supplied value {name!r} changes; "
                "neutral expressions such as name * 0 do not count as use."
            )
    return issues


def _interactive_sensitivity_issues(tree: ast.Module, exercise_no: int) -> list[str]:
    """Run unseen deterministic input cases and require each input to matter."""

    input_names = _input_assignment_names(tree)
    if not input_names:
        return ["Assign each input() result to a variable before printing it."]
    input_call_count = sum(
        1 for node in ast.walk(tree) if isinstance(node, ast.Call) and _call_name(node) == "input"
    )
    if input_call_count != len(input_names):
        return ["Each input() call must assign to a different plain-name variable."]

    cases = _sensitivity_cases(len(input_names))
    results: list[_Execution] = []
    for values in cases:
        result, error = _execute_tree(tree, values)
        if error is not None:
            return [f"Interactive semantic execution failed for {values!r}: {error}"]
        assert result is not None
        results.append(result)
    if not results[0].final_output:
        return ["The program must print a result after reading its input values."]

    issues: list[str] = []
    baseline_output = results[0].final_output
    for index, name in enumerate(input_names):
        affected = any(
            values[index] != cases[0][index] and result.final_output != baseline_output
            for values, result in zip(cases, results, strict=True)
        )
        if not affected:
            issues.append(
                f"The value entered for {name!r} must affect the final output; "
                "input used only in a neutral expression does not count."
            )

    static_alternates = _INTERACTIVE_STATIC_ALTERNATES.get(exercise_no)
    if static_alternates:
        issues.extend(
            _replacement_sensitivity_issues(
                tree,
                static_alternates,
                cases[0],
                "Interactive",
            )
        )
    return issues


def _input_assignment_names(module: ast.Module) -> list[str]:
    """Find variables assigned from input() calls in source order."""

    names: list[str] = []
    for statement in module.body:
        if not isinstance(statement, ast.Assign) or not _contains_input(statement.value):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id not in names:
                names.append(target.id)
    return names


def _sensitivity_cases(input_count: int) -> tuple[tuple[str, ...], ...]:
    """Create multiple deterministic cases that are not notebook transcripts."""

    base = tuple(f"semantic_base_{index}" for index in range(input_count))
    cases = [base]
    for index in range(input_count):
        values = list(base)
        values[index] = f"semantic_alternate_{index}"
        cases.append(tuple(values))
    cases.append(tuple(f"semantic_combined_{index}" for index in range(input_count)))
    return tuple(cases)


def _replace_assignment_value(
    tree: ast.Module,
    name: str,
    value: str | int | float,
) -> tuple[ast.Module, bool]:
    """Return a copy with every assignment to *name* replaced by a literal."""

    changed = copy.deepcopy(tree)
    found = False
    for statement in changed.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
            continue
        constant = ast.Constant(value=value)
        ast.copy_location(constant, statement.value)
        statement.value = constant
        found = True
    ast.fix_missing_locations(changed)
    return changed, found


def _execute_tree(
    tree: ast.Module,
    inputs: tuple[str, ...],
) -> tuple[_Execution | None, str | None]:
    """Execute validated straight-line code with restricted builtins."""

    buffer = io.StringIO()
    input_marks: list[int] = []
    input_values = iter(inputs)

    def fake_input(prompt: str = "") -> str:
        if prompt:
            print(prompt, end="")
        input_marks.append(len(buffer.getvalue()))
        try:
            return next(input_values)
        except StopIteration as exc:
            raise RuntimeError("semantic test supplied too few input values") from exc

    safe_builtins = {
        "float": float,
        "format": format,
        "input": fake_input,
        "int": int,
        "print": print,
        "str": str,
    }
    namespace = {
        "__builtins__": safe_builtins,
        "__name__": "__ex011_semantic_check__",
    }
    try:
        with redirect_stdout(buffer):
            exec(compile(tree, "<ex011-semantic-check>", "exec"), namespace, namespace)
    except _EXECUTION_EXCEPTIONS as exc:
        return None, f"{type(exc).__name__}: {exc}"

    raw_output = buffer.getvalue()
    final_start = input_marks[-1] if input_marks else 0
    return (
        _Execution(
            output=raw_output.removesuffix("\n"),
            final_output=raw_output[final_start:].removesuffix("\n"),
            input_count=len(input_marks),
        ),
        None,
    )


def _has_final_fstring(module: ast.Module) -> bool:
    """Return whether the final print argument depends on an f-string."""

    final_print = _final_print(module)
    if final_print is None:
        return False
    return any(
        _contains_fstring(argument, module, _node_key(final_print), frozenset())
        for argument in final_print.args
    ) or any(
        _contains_fstring(keyword.value, module, _node_key(final_print), frozenset())
        for keyword in final_print.keywords
    )


def _contains_fstring(
    expression: ast.AST,
    module: ast.Module,
    before: tuple[int, int],
    seen: frozenset[tuple[int, int]],
) -> bool:
    """Find an f-string in the final expression, following plain assignments."""

    if isinstance(expression, ast.JoinedStr):
        found = True
    elif isinstance(expression, ast.Name):
        assignment = _latest_assignment(expression.id, before, module)
        found = (
            assignment is not None
            and assignment.key not in seen
            and _contains_fstring(
                assignment.value,
                module,
                assignment.key,
                seen | {assignment.key},
            )
        )
    elif isinstance(expression, ast.FormattedValue):
        found = _contains_fstring(expression.value, module, before, seen)
    elif isinstance(expression, ast.BinOp):
        found = _contains_fstring(expression.left, module, before, seen) or _contains_fstring(
            expression.right,
            module,
            before,
            seen,
        )
    elif isinstance(expression, ast.Call):
        found = any(_contains_fstring(argument, module, before, seen) for argument in expression.args)
        if not found and isinstance(expression.func, ast.Attribute):
            found = _contains_fstring(expression.func.value, module, before, seen)
    elif isinstance(expression, (ast.List, ast.Tuple)):
        found = any(_contains_fstring(element, module, before, seen) for element in expression.elts)
    else:
        found = False
    return found


def _latest_assignment(name: str, before: tuple[int, int], module: ast.Module) -> _Assignment | None:
    """Return the latest simple assignment before a source location."""

    assignments = [
        statement
        for statement in module.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
        and _node_key(statement) < before
    ]
    if not assignments:
        return None
    statement = assignments[-1]
    return _Assignment(statement.value, _node_key(statement))


@dataclass(frozen=True)
class _Assignment:
    """The value and source position of a plain assignment."""

    value: ast.expr
    key: tuple[int, int]


def _contains_input(expression: ast.AST) -> bool:
    """Return whether an expression contains an input call."""

    return any(
        isinstance(node, ast.Call) and _call_name(node) == "input" for node in ast.walk(expression)
    )


def _call_name(call: ast.Call) -> str | None:
    """Return a direct builtin name for a call node."""

    return call.func.id if isinstance(call.func, ast.Name) else None


def _node_key(node: ast.AST) -> tuple[int, int]:
    """Return a stable source-order key for an AST node."""

    return (
        getattr(node, "lineno", 0),
        getattr(node, "col_offset", 0),
    )


__all__ = ["required_flow_issues"]
