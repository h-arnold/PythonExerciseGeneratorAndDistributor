"""Conservative semantic checks for ex014 advanced arithmetic gap-fill cells."""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class _Binding:
    """One single-assignment binding in a validated straight-line cell."""

    name: str
    value: ast.expr
    key: tuple[int, int]


@dataclass(frozen=True)
class _FlowSpec:
    """Task-specific input, cast, calculation, and transcript requirements."""

    input_count: int
    cast_name: str | None
    target_name: str
    operation: str
    exponent: int | float | None
    print_names: tuple[str, ...]
    fixed_values: tuple[tuple[str, int | float], ...] = ()


_FLOW_SPECS: Final[dict[int, _FlowSpec]] = {
    1: _FlowSpec(0, None, "result", "power", 2, ("number", "result"), (("number", 8),)),
    2: _FlowSpec(0, None, "result", "power", 3, ("number", "result"), (("number", 6),)),
    3: _FlowSpec(1, "int", "result", "power", 0.5, ("number_input", "result")),
    4: _FlowSpec(
        2,
        "int",
        "result",
        "power",
        None,
        ("base_input", "exponent_input", "result"),
    ),
    5: _FlowSpec(1, "float", "area", "power", 2, ("side_input", "area")),
    6: _FlowSpec(2, "float", "area", "multiply", None, ("area",)),
    7: _FlowSpec(1, "float", "volume", "power", 3, ("volume",)),
    8: _FlowSpec(1, "int", "result", "power", 0.5, ("number_input", "result")),
    9: _FlowSpec(
        1,
        "float",
        "area",
        "circle",
        None,
        ("area",),
        (("pi", 3.14159),),
    ),
    10: _FlowSpec(
        2,
        "int",
        "result",
        "power",
        None,
        ("base_input", "exponent_input", "result"),
    ),
}

_ALLOWED_BINARY_OPERATORS: Final[tuple[type[ast.operator], ...]] = (ast.Mult, ast.Pow)
_ALLOWED_CASTS: Final[frozenset[str]] = frozenset({"float", "int"})
_ALLOWED_CALLS: Final[frozenset[str]] = frozenset({"float", "input", "int"})
_FORBIDDEN_REBINDINGS: Final[frozenset[str]] = frozenset(dir(builtins)) | frozenset(
    {"__builtins__"}
)


def required_flow_issues(tree: ast.AST, exercise_no: int) -> list[str]:
    """Return grammar or task-specific data-flow problems for one exercise cell."""
    spec = _FLOW_SPECS.get(exercise_no)
    if spec is None:
        return [f"Exercise {exercise_no}: no semantic flow is defined."]
    if not isinstance(tree, ast.Module):
        return ["The exercise code must be a top-level Python module."]

    bindings, grammar_issues = _validate_grammar(tree)
    if grammar_issues:
        return grammar_issues
    return _semantic_issues(spec, bindings, _final_print(tree))


def _validate_grammar(module: ast.Module) -> tuple[list[_Binding], list[str]]:
    """Validate one assignment per name, safe RHS expressions, and one final print."""
    issues: list[str] = []
    bindings: list[_Binding] = []
    seen: set[str] = set()
    print_count = 0

    for statement in module.body:
        if isinstance(statement, ast.Assign):
            binding, statement_issues = _validate_assignment(statement, seen)
            issues.extend(statement_issues)
            if binding is not None:
                bindings.append(binding)
                seen.add(binding.name)
            continue
        if isinstance(statement, ast.Expr):
            if not isinstance(statement.value, ast.Call) or not _is_direct_call(
                statement.value,
                "print",
            ):
                issues.append("Only a direct top-level print() expression is allowed.")
                continue
            print_count += 1
            issues.extend(_print_issues(statement.value, seen))
            continue
        issues.append(
            f"{type(statement).__name__} statements are not allowed; "
            "use only simple assignments followed by print()."
        )

    if print_count != 1:
        issues.append("The cell must contain exactly one top-level print() call.")
    if not module.body or not (
        isinstance(module.body[-1], ast.Expr) and _is_direct_call(module.body[-1].value, "print")
    ):
        issues.append("The final statement must be the top-level print() call.")
    return bindings, issues


def _validate_assignment(
    statement: ast.Assign,
    seen: set[str],
) -> tuple[_Binding | None, list[str]]:
    """Validate one plain-name assignment and its allowlisted right-hand side."""
    if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
        return None, ["Each assignment must target exactly one plain variable name."]

    target = statement.targets[0]
    issues: list[str] = []
    if _is_forbidden_name(target.id):
        issues.append(f"Do not rebind the builtin or special name {target.id!r}.")
    if target.id in seen:
        issues.append(f"Assign {target.id!r} only once; later reassignment is not allowed.")
    issues.extend(_expression_issues(statement.value, seen))
    if issues:
        return None, issues
    return _Binding(target.id, statement.value, _node_key(statement)), []


def _expression_issues(expression: ast.AST, seen: set[str]) -> list[str]:
    """Validate an expression against the conservative assignment-RHS allowlist."""
    if isinstance(expression, ast.Constant):
        return _constant_issues(expression)
    if isinstance(expression, ast.Name):
        return _name_issues(expression, seen)
    if isinstance(expression, ast.BinOp):
        return _binary_issues(expression, seen)
    if isinstance(expression, ast.JoinedStr):
        return _joined_string_issues(expression, seen)
    if isinstance(expression, ast.Call):
        return _call_issues(expression, seen)
    return [
        f"{type(expression).__name__} expressions are not allowed; "
        "use only constants, names, required arithmetic, direct casts/input, and safe f-strings."
    ]


def _constant_issues(expression: ast.Constant) -> list[str]:
    """Allow only ordinary string, integer, and float literals."""
    value = expression.value
    if isinstance(value, str):
        return []
    if isinstance(value, bool):
        return ["Boolean literals are not used in this exercise."]
    if isinstance(value, (int, float)):
        return []
    return ["Only ordinary text and numeric constants are allowed."]


def _name_issues(expression: ast.Name, seen: set[str]) -> list[str]:
    """Require a previously assigned, non-special loaded name."""
    if not isinstance(expression.ctx, ast.Load):
        return ["Only loaded variable names are allowed in expressions."]
    if _is_forbidden_name(expression.id):
        return [f"The name {expression.id!r} is not allowed in this cell."]
    if expression.id not in seen:
        return [f"Assign {expression.id!r} before using it."]
    return []


def _binary_issues(expression: ast.BinOp, seen: set[str]) -> list[str]:
    """Allow only multiplication and exponentiation."""
    if not isinstance(expression.op, _ALLOWED_BINARY_OPERATORS):
        return ["Only multiplication (*) and exponentiation (**) are allowed here."]
    return _expression_issues(expression.left, seen) + _expression_issues(expression.right, seen)


def _joined_string_issues(expression: ast.JoinedStr, seen: set[str]) -> list[str]:
    """Allow f-strings made only from literal text and direct formatted names."""
    issues: list[str] = []
    for value in expression.values:
        if isinstance(value, ast.FormattedValue):
            issues.extend(_formatted_value_issues(value, seen))
        else:
            issues.extend(_expression_issues(value, seen))
    return issues


def _formatted_value_issues(expression: ast.FormattedValue, seen: set[str]) -> list[str]:
    """Require a plain name with no conversion or nested format expression."""
    if (
        expression.conversion != -1
        or expression.format_spec is not None
        or not isinstance(expression.value, ast.Name)
    ):
        return ["Each f-string field must be a plain variable name without conversion or format spec."]
    return _name_issues(expression.value, seen)


def _call_issues(expression: ast.Call, seen: set[str]) -> list[str]:
    """Allow only direct input(), int(), and float() calls with conservative arguments."""
    if not isinstance(expression.func, ast.Name):
        return ["Only direct input(), int(), and float() calls are allowed."]
    if expression.func.id not in _ALLOWED_CALLS:
        return [f"The function {expression.func.id!r} is not allowed in this cell."]

    if expression.func.id == "input":
        return _input_call_issues(expression)
    return _cast_call_issues(expression, expression.func.id, seen)


def _input_call_issues(expression: ast.Call) -> list[str]:
    """Allow input() with at most one literal text prompt."""
    if expression.keywords or len(expression.args) > 1:
        return ["input() accepts at most one literal prompt and no keywords."]
    if not expression.args:
        return []
    prompt = expression.args[0]
    if not isinstance(prompt, ast.Constant) or type(prompt.value) is not str:
        return ["The input() prompt must be a literal string."]
    return []


def _cast_call_issues(expression: ast.Call, cast_name: str, seen: set[str]) -> list[str]:
    """Allow only a one-name int() or float() cast of an existing variable."""
    if expression.keywords or len(expression.args) != 1:
        return [f"{cast_name}() must cast exactly one existing variable without keywords."]
    argument = expression.args[0]
    if not isinstance(argument, ast.Name):
        return [f"{cast_name}() must cast a previously assigned plain variable name."]
    return _name_issues(argument, seen)


def _print_issues(expression: ast.Call, seen: set[str]) -> list[str]:
    """Require one safe f-string argument to the direct print() call."""
    if expression.keywords or len(expression.args) != 1:
        return ["The final print() call must contain exactly one f-string argument."]
    return _expression_issues(expression.args[0], seen)


def _semantic_issues(
    spec: _FlowSpec,
    bindings: list[_Binding],
    final_print: ast.Call,
) -> list[str]:
    """Check the task-specific input-to-cast-to-calculation-to-transcript flow."""
    by_name = {binding.name: binding for binding in bindings}
    target = by_name.get(spec.target_name)
    if target is None:
        return [f"Assign {spec.target_name!r} before the final print() call."]

    issues = _fixed_value_issues(spec, by_name)
    inputs = [binding for binding in bindings if _is_direct_call(binding.value, "input")]
    cast_names, cast_issues = _cast_names(spec, inputs, by_name)
    issues.extend(cast_issues)
    issues.extend(_calculation_issues(spec, target, inputs, cast_names))
    issues.extend(_order_issues(spec, target, inputs, cast_names, by_name))
    issues.extend(_transcript_issues(spec, final_print))
    return issues


def _fixed_value_issues(spec: _FlowSpec, by_name: dict[str, _Binding]) -> list[str]:
    """Check supplied constants such as the original number and pi."""
    issues: list[str] = []
    for name, expected in spec.fixed_values:
        binding = by_name.get(name)
        if binding is None:
            issues.append(f"Assign the supplied value {name!r} before calculating.")
        elif _numeric_constant(binding.value) != expected:
            issues.append(f"{name} must be assigned the value {expected!r}.")
    return issues


def _cast_names(
    spec: _FlowSpec,
    inputs: list[_Binding],
    by_name: dict[str, _Binding],
) -> tuple[list[str], list[str]]:
    """Map every input binding to one distinct live cast binding of the required type."""
    if len(inputs) != spec.input_count:
        return [], [f"Read exactly {spec.input_count} value(s) directly with input()."]
    if spec.cast_name is None:
        return [], []

    cast_bindings = [
        binding
        for binding in by_name.values()
        if _is_cast_of(binding.value, spec.cast_name)
    ]
    if len(cast_bindings) != len(inputs):
        return [], [
            f"Create exactly one {spec.cast_name}() cast binding for each input binding."
        ]
    return _matched_cast_names(spec.cast_name, inputs, cast_bindings)


def _matched_cast_names(
    cast_name: str,
    inputs: list[_Binding],
    cast_bindings: list[_Binding],
) -> tuple[list[str], list[str]]:
    """Match each input to one distinct cast binding in source order."""
    issues: list[str] = []
    cast_names: list[str] = []
    for input_binding in inputs:
        matches = [
            binding
            for binding in cast_bindings
            if _cast_source(binding.value) == input_binding.name
        ]
        if len(matches) != 1:
            issues.append(
                f"Cast {input_binding.name!r} exactly once with {cast_name}() before calculating."
            )
            continue
        cast_binding = matches[0]
        if cast_binding.name == input_binding.name:
            issues.append(
                f"Use a distinct variable name for the {cast_name}() cast of "
                f"{input_binding.name!r}."
            )
            continue
        if cast_binding.key < input_binding.key:
            issues.append(f"Cast {input_binding.name!r} after reading it with input().")
        cast_names.append(cast_binding.name)
    return cast_names, issues


def _calculation_issues(
    spec: _FlowSpec,
    target: _Binding,
    inputs: list[_Binding],
    cast_names: list[str],
) -> list[str]:
    """Dispatch the task-specific live calculation check."""
    if len(cast_names) != spec.input_count:
        return [f"Calculate {spec.target_name!r} from the correctly cast inputs."]
    if spec.operation == "multiply":
        if _is_product_of(target.value, set(cast_names)):
            return []
        return ["Calculate area by multiplying both distinct float-cast inputs."]
    if spec.operation == "circle":
        if _is_circle_area(target.value, cast_names[0]):
            return []
        return ["Calculate area as pi multiplied by the float-cast radius squared."]
    return _power_calculation_issues(spec, target, inputs, cast_names)


def _power_calculation_issues(
    spec: _FlowSpec,
    target: _Binding,
    inputs: list[_Binding],
    cast_names: list[str],
) -> list[str]:
    """Check constant or input-driven power operands and exponents."""
    left_name = cast_names[0] if inputs else spec.fixed_values[0][0]
    if spec.exponent is not None:
        if _is_power_of(target.value, left_name, spec.exponent):
            return []
        return [f"Calculate {spec.target_name!r} as {left_name} ** {spec.exponent!r}."]
    if _is_dynamic_power(target.value, left_name, cast_names[1]):
        return []
    return ["Calculate the result as the first cast input ** the second cast input."]


def _order_issues(
    spec: _FlowSpec,
    target: _Binding,
    inputs: list[_Binding],
    cast_names: list[str],
    by_name: dict[str, _Binding],
) -> list[str]:
    """Require input, cast, calculation, and print to occur in that source order."""
    prerequisites = [*inputs, *(by_name[name] for name in cast_names)]
    if any(binding.key > target.key for binding in prerequisites):
        return [f"Calculate {spec.target_name!r} only after reading and casting all inputs."]
    return []


def _transcript_issues(spec: _FlowSpec, final_print: ast.Call) -> list[str]:
    """Require the final safe f-string to preserve the supplied transcript values."""
    argument = final_print.args[0]
    if not isinstance(argument, ast.JoinedStr):
        return ["The final output must use a safe f-string."]
    printed_names = {
        value.value.id
        for value in argument.values
        if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name)
    }
    if printed_names != set(spec.print_names):
        return [
            "The final f-string must print exactly these live values: "
            + ", ".join(spec.print_names)
            + "."
        ]
    return []


def _is_direct_call(expression: ast.AST, function_name: str) -> bool:
    """Return whether an expression directly calls one named function."""
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == function_name
    )


def _is_cast_of(expression: ast.AST, cast_name: str) -> bool:
    """Return whether an expression is a one-name direct cast."""
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == cast_name
        and not expression.keywords
        and len(expression.args) == 1
        and isinstance(expression.args[0], ast.Name)
    )


def _cast_source(expression: ast.AST) -> str | None:
    """Return the plain variable name cast by a direct cast expression."""
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in _ALLOWED_CASTS
        and not expression.keywords
        and len(expression.args) == 1
        and isinstance(expression.args[0], ast.Name)
    ):
        return expression.args[0].id
    return None


def _numeric_constant(expression: ast.AST) -> int | float | None:
    """Return an integer or float AST constant, excluding booleans."""
    if not isinstance(expression, ast.Constant) or isinstance(expression.value, bool):
        return None
    value = expression.value
    if isinstance(value, (int, float)):
        return value
    return None


def _is_power_of(expression: ast.AST, base_name: str, exponent: int | float) -> bool:
    """Return whether an expression directly raises a named value to an exponent."""
    return (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Pow)
        and _is_named(expression.left, base_name)
        and _numeric_constant(expression.right) == exponent
    )


def _is_dynamic_power(expression: ast.AST, base_name: str, exponent_name: str) -> bool:
    """Return whether an expression raises one named value to another."""
    return (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Pow)
        and _is_named(expression.left, base_name)
        and _is_named(expression.right, exponent_name)
    )


def _is_product_of(expression: ast.AST, names: set[str]) -> bool:
    """Return whether an expression directly multiplies exactly the supplied names."""
    return (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Mult)
        and isinstance(expression.left, ast.Name)
        and isinstance(expression.right, ast.Name)
        and {expression.left.id, expression.right.id} == names
    )


def _is_circle_area(expression: ast.AST, radius_name: str) -> bool:
    """Return whether an expression is pi times a named radius squared."""
    if not isinstance(expression, ast.BinOp) or not isinstance(expression.op, ast.Mult):
        return False
    return (
        _is_named(expression.left, "pi") and _is_power_of(expression.right, radius_name, 2)
    ) or (
        _is_named(expression.right, "pi") and _is_power_of(expression.left, radius_name, 2)
    )


def _is_named(expression: ast.AST, name: str) -> bool:
    """Return whether an expression is exactly one named value."""
    return isinstance(expression, ast.Name) and expression.id == name


def _final_print(module: ast.Module) -> ast.Call:
    """Return the validated final print call."""
    statement = module.body[-1]
    assert isinstance(statement, ast.Expr)
    assert isinstance(statement.value, ast.Call)
    return statement.value


def _is_forbidden_name(name: str) -> bool:
    """Reject builtin and dunder rebinding or access."""
    return name in _FORBIDDEN_REBINDINGS or (name.startswith("__") and name.endswith("__"))


def _node_key(node: ast.AST) -> tuple[int, int]:
    """Return a stable source-order key for an AST node."""
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


__all__ = ["required_flow_issues"]
