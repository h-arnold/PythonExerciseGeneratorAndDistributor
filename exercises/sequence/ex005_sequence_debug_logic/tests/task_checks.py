"""Shared task-completion checks used by pytest and the notebook self-check."""

from __future__ import annotations

import ast
import contextlib
import io
import re
from collections.abc import Callable

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_ex = load_exercise_test_module("ex005_sequence_debug_logic", "expectations")
_NUMERIC_SOURCES = {
    1: {"price", "quantity"},
    3: {"width", "height"},
    6: {"paid", "cost"},
    7: {"score1", "score2"},
    9: {"length", "width"},
}
_TEXT_SOURCES = {
    2: {"name"},
    4: {"word1", "word2"},
    5: {"first_name", "last_name"},
    8: {"word1", "word2", "word3", "word4"},
    10: {"age", "city"},
}
_INTERACTIVE_PARTS = {5, 10}


def semantic(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _updated_string(original: str, replacement: str) -> str:
    leading = original[: len(original) - len(original.lstrip())]
    trailing = original[len(original.rstrip()) :]
    return f"{leading}{replacement.strip()}{trailing}"


class _SourceInitializerProbe(ast.NodeTransformer):
    def __init__(self, probes: dict[str, int | str]) -> None:
        self.probes = probes
        self.initialized: set[str] = set()

    def _updated_value(self, target: ast.expr, value: ast.expr) -> ast.expr:
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
            if len(target.elts) == len(value.elts):
                value.elts = [
                    self._updated_value(item_target, item_value)
                    for item_target, item_value in zip(target.elts, value.elts, strict=True)
                ]
            return value
        if not isinstance(target, ast.Name) or target.id not in self.probes:
            return value
        if target.id in self.initialized:
            return value
        self.initialized.add(target.id)
        replacement = self.probes[target.id]
        if (
            isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and isinstance(replacement, str)
        ):
            return ast.Constant(_updated_string(value.value, replacement))
        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
            return ast.Constant(replacement)
        return value

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        if len(node.targets) == 1:
            node.value = self._updated_value(node.targets[0], node.value)
        return self.generic_visit(node)


def _changed_code(code: str, values: dict[str, int | str]) -> str:
    tree = _SourceInitializerProbe(values).visit(ast.parse(code))
    return ast.unparse(ast.fix_missing_locations(tree))


def _run_source(code: str) -> str:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(code, "<exercise-probe>", "exec"), {})
    return output.getvalue().rstrip("\n")


def _input_result(n: int, values: list[str]) -> str:
    prompts = _ex.EX005_INPUT_PROMPTS[n]
    ending = (
        f"{values[0]} {values[1]}"
        if n == _ex.EX005_FULL_NAME_EXERCISE
        else f"You are {values[0]} years old and live in {values[1]}"
    )
    return prompts[0] + prompts[1] + ending


def _check_expected_output(n: int, output: Callable[[list[str] | None], str]) -> list[str]:
    errors: list[str] = []
    expected = _ex.EX005_EXPECTED_SINGLE_LINE.get(n)
    if expected is not None:
        if semantic(output(None)) != semantic(expected):
            errors.append("output does not match the expected result")
    elif n in _INTERACTIVE_PARTS:
        inputs = _ex.EX005_EXERCISE_INPUTS[n]
        if semantic(output(None)) != semantic(_input_result(n, inputs)):
            errors.append("output does not match the expected prompt flow")
    return errors


def _check_source_probe(n: int, code: str) -> list[str]:
    if n in _NUMERIC_SOURCES:
        actual = semantic(_run_source(_changed_code(code, _ex.EX005_NUMERIC_PROBES[n])))
        if actual != _ex.EX005_EXPECTED_PROBE_OUTPUTS[n]:
            return ["calculation does not use the supplied source values correctly"]
    if n in _TEXT_SOURCES and n in _ex.EX005_TEXT_PROBES:
        actual = semantic(_run_source(_changed_code(code, _ex.EX005_TEXT_PROBES[n])))
        if actual != _ex.EX005_EXPECTED_PROBE_OUTPUTS[n]:
            return ["printed text does not use all supplied source values"]
    return []


def _check_alternate_inputs(n: int, output: Callable[[list[str] | None], str]) -> list[str]:
    if n not in _INTERACTIVE_PARTS:
        return []
    alternate = _ex.EX005_ALTERNATE_INPUTS[n]
    if semantic(output(alternate)) != semantic(_input_result(n, alternate)):
        return ["output does not use both supplied inputs"]
    return []


def validate_task(n: int, code: str, output: Callable[[list[str] | None], str]) -> list[str]:
    """Check expected behavior and probe source-data flow without prescribing syntax."""
    try:
        errors = _check_expected_output(n, output)
        ast.parse(code)
        errors.extend(_check_source_probe(n, code))
        errors.extend(_check_alternate_inputs(n, output))
    except (SyntaxError, NameError, TypeError, ValueError, ZeroDivisionError, RuntimeError) as exc:
        return [str(exc)]
    return errors
