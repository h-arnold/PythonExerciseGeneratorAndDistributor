"""Shared task-completion checks for ex008."""

from __future__ import annotations

import ast
import builtins
from collections.abc import Iterator
from pathlib import Path
from typing import TypeAlias, TypeGuard

from exercise_runtime_support.exercise_framework import exec_tagged_code
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import NotebookGradingError

expectations = load_exercise_test_module("ex008_sequence_make_consolidation", "expectations")
Symbol: TypeAlias = tuple[object, ...]


def _is_symbol(value: object) -> TypeGuard[Symbol]:
    return isinstance(value, tuple)


def _is_sequence(value: object) -> TypeGuard[tuple[str, tuple[Symbol, ...]]]:
    """Narrow a ``("sequence", children)`` snapshot to its typed children."""
    return _is_symbol(value) and value[:1] == ("sequence",)


def _is_variable(value: object) -> TypeGuard[tuple[str, str, Symbol]]:
    """Narrow a ``("variable", name, value)`` snapshot to its stored value."""
    return _is_symbol(value) and value[:1] == ("variable",)


def _clean(text: str) -> str:
    return " ".join(text.split())


def output_errors(
    exercise_no: int,
    output: str,
    inputs: list[str] | None = None,
    prompts: list[str] | None = None,
) -> list[str]:
    """Check complete required output while permitting harmless whitespace."""
    if exercise_no in expectations.EX008_EXPECTED_STATIC_OUTPUTS:
        expected_lines = expectations.EX008_EXPECTED_STATIC_OUTPUTS[exercise_no].splitlines()
        actual_lines = output.splitlines()
        if len(actual_lines) != len(expected_lines) or any(
            _clean(actual) != _clean(expected)
            for actual, expected in zip(actual_lines, expected_lines, strict=True)
        ):
            return [
                f"Print exactly {len(expected_lines)} required line(s), with the required content."
            ]
        return []

    assert inputs is not None
    if exercise_no == 3:
        expected = f"Hello {inputs[0]}! Your hobby is {inputs[1]}."
    elif exercise_no == 4:
        expected = f"Books read altogether: {int(inputs[0]) * int(inputs[1])}"
    else:
        expected = f"Total distance: {float(inputs[0]) * int(inputs[1]):g} km"
    normalized = _clean(output)
    wanted = _clean(expected)
    # Remove only prompts proved by the parsed, ordered input flow. Everything
    # else must be the single required answer, regardless of line wrapping.
    prompt_residue = normalized
    for prompt in prompts or []:
        prompt_text = _clean(prompt)
        if prompt_text:
            prompt_residue = prompt_residue.replace(prompt_text, "", 1)
    if _clean(prompt_residue) != wanted:
        return [f"Print one complete result, and no other answer: {expected!r}."]
    return []


def capture_interactive_events(
    notebook_path: str | Path, exercise_no: int, inputs: list[str]
) -> list[tuple[str, str]]:
    """Execute one tagged cell while recording actual print/input prompt events.

    When a cell consumes fewer inputs than the tests supply, an ``error`` event is
    appended instead of raising so callers can report an ordinary failing check
    rather than aborting the whole self-check table.
    """
    events: list[tuple[str, str]] = []
    supplied = iter(inputs)

    def capture_print(
        *values: object, sep: str | None = " ", end: str | None = "\n", **_: object
    ) -> None:
        rendered = (sep or "").join(str(value) for value in values) + (end or "")
        events.append(("print", rendered))

    def capture_input(prompt: str = "") -> str:
        events.append(("input", prompt))
        try:
            return next(supplied)
        except StopIteration as exc:
            raise NotebookGradingError(
                "The code calls input() more times than the tests supply values."
            ) from exc

    original_print, original_input = builtins.print, builtins.input
    builtins.print, builtins.input = capture_print, capture_input
    try:
        exec_tagged_code(notebook_path, tag=f"exercise{exercise_no}")
        if next(supplied, None) is not None:
            events.append(("error", "Read exactly the two required answers with input()."))
    finally:
        builtins.print, builtins.input = original_print, original_input
    return events


def interactive_event_errors(
    exercise_no: int, events: list[tuple[str, str]], inputs: list[str]
) -> list[str]:
    """Check dynamic prompt events and the sole remaining printed result."""
    expected = (
        f"Hello {inputs[0]}! Your hobby is {inputs[1]}."
        if exercise_no == 3
        else f"Books read altogether: {int(inputs[0]) * int(inputs[1])}"
        if exercise_no == 4
        else f"Total distance: {float(inputs[0]) * int(inputs[1]):g} km"
    )
    residual = ""
    pending_print = ""
    input_count = 0

    def meaningful(text: str) -> bool:
        return len(text.strip()) >= 3 and any(char.isalpha() for char in text)

    for kind, text in events:
        if kind == "error":
            return [text]
        if kind == "print":
            pending_print += text
            continue
        input_count += 1
        prompt_line = pending_print.rstrip("\n").rsplit("\n", 1)[-1]
        printed_prompt = meaningful(prompt_line)
        inline_prompt = meaningful(text)
        prompt_ok = printed_prompt if exercise_no == 3 else printed_prompt or inline_prompt
        if not prompt_ok:
            return [
                "Print a meaningful prompt before each input()."
                if exercise_no == 3
                else "Give each input a meaningful prompt."
            ]
        if printed_prompt and prompt_line:
            residual += pending_print[: pending_print.rfind(prompt_line)]
        else:
            residual += pending_print
        pending_print = ""
    if input_count != 2:
        return ["Read exactly the two required answers with input()."]
    residual += pending_print
    if _clean(residual) != _clean(expected):
        return [f"Print one complete result, and no other answer: {expected!r}."]
    return []


def _symbolic(tree: ast.AST) -> tuple[dict[str, Symbol], list[tuple[str, Symbol, ast.Call | None]]]:
    """Resolve simple sequential assignments into immutable expression snapshots."""
    env: dict[str, Symbol] = {}
    outputs: list[tuple[str, Symbol, ast.Call | None]] = []
    input_number = 0

    def resolve(node: ast.AST) -> Symbol:
        nonlocal input_number
        if isinstance(node, ast.Name):
            return env.get(node.id, ("name", node.id))
        if isinstance(node, ast.Constant):
            return ("constant", node.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "input":
                input_number += 1
                return ("input", input_number)
            return ("call", node.func.id, tuple(resolve(arg) for arg in node.args))
        if isinstance(node, ast.BinOp):
            return ("binop", type(node.op).__name__, resolve(node.left), resolve(node.right))
        if isinstance(node, (ast.Tuple, ast.List)):
            return ("sequence", tuple(resolve(item) for item in node.elts))
        if isinstance(node, ast.JoinedStr):
            return ("joined", tuple(resolve(item) for item in node.values))
        if isinstance(node, ast.FormattedValue):
            return ("formatted", resolve(node.value))
        return ("node", ast.dump(node, include_attributes=False))

    def bind(target: ast.AST, value: Symbol) -> None:
        if isinstance(target, ast.Name):
            env[target.id] = ("variable", target.id, value)
        elif isinstance(target, (ast.Tuple, ast.List)) and _is_sequence(value):
            for child, child_value in zip(target.elts, value[1], strict=False):
                bind(child, child_value)

    body = tree.body if isinstance(tree, ast.Module) else []
    for statement in body:
        if isinstance(statement, ast.Assign):
            value = resolve(statement.value)
            for target in statement.targets:
                bind(target, value)
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            bind(statement.target, resolve(statement.value))
        elif isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            previous = env.get(statement.target.id, ("name", statement.target.id))
            updated = ("binop", type(statement.op).__name__, previous, resolve(statement.value))
            bind(statement.target, updated)
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
            if isinstance(call.func, ast.Name) and call.func.id == "print":
                value = tuple(resolve(arg) for arg in call.args)
                inputs = [
                    arg
                    for arg in call.args
                    if isinstance(arg, ast.Call)
                    and isinstance(arg.func, ast.Name)
                    and arg.func.id == "input"
                ]
                outputs.append(("print", value, inputs[0] if inputs else None))
    return env, outputs


def _walk(value: object) -> Iterator[Symbol]:
    if _is_symbol(value):
        yield value
        for child in value:
            yield from _walk(child)


def _contains(value: object, expected: Symbol) -> bool:
    return any(item == expected for item in _walk(value))


def _has_origin(value: object, name: str) -> bool:
    return any(item[:2] == ("variable", name) for item in _walk(value))


def _unwrapped(value: Symbol) -> Symbol:
    while _is_variable(value):
        value = value[2]
    return value


def _effective_origins(value: object) -> set[str]:
    """Return variable origins that can affect this straight-line expression."""
    if not _is_symbol(value):
        return set()
    if _is_variable(value):
        return {value[1]} | _effective_origins(value[2])
    if value[:1] == ("binop",):
        assert len(value) >= 4
        _, operator, left, right = value[:4]
        if operator == "Mult":
            if left == ("constant", 0):
                return _effective_origins(left)
            if right == ("constant", 0):
                return _effective_origins(right)
        if operator == "Sub" and left == right:
            return set()
        return _effective_origins(left) | _effective_origins(right)
    result: set[str] = set()
    for child in value:
        result.update(_effective_origins(child))
    return result


def _printed_values(outputs: list[tuple[str, Symbol, ast.Call | None]]) -> list[Symbol]:
    return [value for kind, value, _ in outputs if kind == "print"]


def construct_errors(exercise_no: int, tree: ast.AST) -> list[str]:
    """Check that required stored values and operations reach printed results."""
    env, outputs = _symbolic(tree)
    printed = _printed_values(outputs)
    errors: list[str] = []
    if exercise_no == 1:
        for word in ("Oakwood", "Coding", "Club"):
            token = ("constant", word)
            source_names = {name for name, value in env.items() if _unwrapped(value) == token}
            if not source_names or not any(
                _effective_origins(value) & source_names for value in printed
            ):
                errors.append(f"Use the stored word {word!r} in the printed message.")
        assigned_words = {
            name
            for name, value in env.items()
            if _unwrapped(value)
            in {("constant", "Oakwood"), ("constant", "Coding"), ("constant", "Club")}
        }
        if len(assigned_words) < 3:
            errors.append("Keep Oakwood, Coding, and Club in three separate variables.")
    elif exercise_no == 2:
        assignments = env
        snack_names = {
            name
            for name, value in assignments.items()
            if _unwrapped(value) == ("constant", "muffins")
        }
        qty_names = {
            name for name, value in assignments.items() if _unwrapped(value) == ("constant", 4)
        }
        price_names = {
            name for name, value in assignments.items() if _unwrapped(value) == ("constant", 2)
        }
        if not snack_names or not any(
            _contains(value, ("constant", "muffins"))
            and any(_has_origin(value, name) for name in snack_names)
            for value in printed
        ):
            errors.append("Store and print the snack name.")
        if not qty_names or not price_names:
            errors.append("Store quantity 4 and price 2 in variables.")
        if not any(
            _effective_origins(value) & qty_names and _effective_origins(value) & price_names
            for value in printed
            if any(node[:1] == ("binop",) and node[1] == "Mult" for node in _walk(value))
        ):
            errors.append(
                "Use multiplication of the stored quantity and price in the printed result."
            )
    else:
        # Input expressions may be consumed inline and therefore absent from env.
        input_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ]
        if len(input_calls) != 2:
            errors.append("Read both answers with input().")
        result_values = [
            value
            for value in printed
            if _contains(value, ("input", 1)) or _contains(value, ("input", 2))
        ]
        if not result_values:
            errors.append("Use the entered answers in the printed result.")
        if exercise_no == 3:
            if not all(
                any(_contains(value, ("input", index)) for value in printed) for index in (1, 2)
            ):
                errors.append("Use both entered text answers in the printed greeting.")
            events = _prompt_events(tree, require_print=True)
            if len(events) != 2 or any(not prompted for prompted in events):
                errors.append("Print a meaningful prompt before each input().")
        else:
            products = [
                node
                for value in result_values
                for node in _walk(value)
                if node[:1] == ("binop",) and node[1] == "Mult"
            ]
            required_casts = (
                ((1, "int"), (2, "int")) if exercise_no == 4 else ((1, "float"), (2, "int"))
            )

            def operand_has_cast(operand: object, input_no: int, cast_name: str) -> bool:
                return any(
                    node[:2] == ("call", cast_name) and _contains(node, ("input", input_no))
                    for node in _walk(operand)
                )

            def operands_have_required_casts(product: Symbol) -> bool:
                assert len(product) >= 4
                operands = (product[2], product[3])
                used: set[int] = set()
                for input_no, cast_name in required_casts:
                    match = next(
                        (
                            index
                            for index, operand in enumerate(operands)
                            if index not in used
                            and _contains(operand, ("input", input_no))
                            and operand_has_cast(operand, input_no, cast_name)
                        ),
                        None,
                    )
                    if match is None:
                        return False
                    used.add(match)
                return True

            if not any(operands_have_required_casts(product) for product in products):
                errors.append(
                    "Convert each input to the required type on its multiplication operand."
                )
            if not products or not any(
                _contains(product, ("input", 1)) and _contains(product, ("input", 2))
                for product in products
            ):
                errors.append("Multiply both entered values in the printed result.")
            events = _prompt_events(tree)
            if len(events) != 2 or any(not prompted for prompted in events):
                errors.append(
                    "Give each input a meaningful prompt, either with print() or input()."
                )
    return errors


def _prompt_events(tree: ast.AST, *, require_print: bool = False) -> list[bool]:
    """Return whether each sequential input has a meaningful preceding/inline prompt."""
    events: list[bool] = []
    pending_prompt = False
    env: dict[str, ast.AST] = {}

    def meaningful(node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id in env:
            return meaningful(env[node.id])
        if isinstance(node, ast.JoinedStr):
            return any(meaningful(part) for part in node.values)
        if isinstance(node, ast.FormattedValue):
            return meaningful(node.value)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return meaningful(node.left) or meaningful(node.right)
        else:
            text = " ".join(
                n.value
                for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            )
        return len(text.strip()) >= 3 and any(char.isalpha() for char in text)

    def visit(node: ast.AST) -> None:
        nonlocal pending_prompt
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "print":
                pending_prompt = any(meaningful(arg) for arg in node.args)
                return
            elif node.func.id == "input":
                inline = any(meaningful(arg) for arg in node.args)
                events.append(pending_prompt if require_print else pending_prompt or inline)
                pending_prompt = False
                return
        if isinstance(node, ast.Assign):
            visit(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env[target.id] = node.value
            return
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            visit(node.value)
            if isinstance(node.target, ast.Name):
                env[node.target.id] = node.value
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in tree.body if isinstance(tree, ast.Module) else []:
        visit(statement)
    return events


def input_prompts(tree: ast.AST) -> list[str]:
    """Extract ordered prompts associated with input calls for transcript checks."""
    prompts: list[str] = []
    env: dict[str, ast.AST] = {}
    pending = ""

    def text(node: ast.AST) -> str:
        if isinstance(node, ast.Name) and node.id in env:
            return text(env[node.id])
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return "".join(text(part) for part in node.values)
        if isinstance(node, ast.FormattedValue):
            return text(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return text(node.left) + text(node.right)
        return ""

    def input_nodes(node: ast.AST) -> list[ast.Call]:
        return [
            n
            for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input"
        ]

    for statement in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
            if isinstance(call.func, ast.Name) and call.func.id == "print":
                pending = " ".join(text(arg) for arg in call.args).strip()
            else:
                for call_input in input_nodes(call):
                    prompts.append(text(call_input.args[0]) if call_input.args else pending)
                    pending = ""
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            if value is None:
                continue
            calls = input_nodes(value)
            for call_input in calls:
                prompts.append(text(call_input.args[0]) if call_input.args else pending)
                pending = ""
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    env[target.id] = value
    return prompts
