from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)

_EX008_EXERCISE_KEY = "ex008_sequence_make_consolidation"
ex008 = load_exercise_test_module(_EX008_EXERCISE_KEY, "expectations")
_CACHE = RuntimeCache()
_MIN_EXERCISE1_STRING_ASSIGNMENTS = 3
_MIN_EXERCISE2_NUMERIC_FACTORS = 2
_EXPECTED_INPUT_CALLS = 2


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run_static(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EX008_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _EX008_EXERCISE_KEY,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EX008_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _has_call(tree: ast.AST, func_name: str) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name
        for node in ast.walk(tree)
    )


def _has_binop(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    return any(
        isinstance(node, ast.BinOp) and isinstance(node.op, operator_type)
        for node in ast.walk(tree)
    )


def _string_assignment_count(tree: ast.AST) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _assigned_constant_names(tree: ast.AST, value_type: type[str | int | float]) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, value_type):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def _input_assigned_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "input":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def _input_call_count(tree: ast.AST) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
    )


def _print_uses_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "print":
            continue
        if any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node)):
            return True
    return False


def _printed_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "print":
            continue
        names.update(
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name)
        )
    return names


def _names_used_in_binop(tree: ast.AST, operator_type: type[ast.operator]) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, operator_type):
            continue
        names.update(
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name)
        )
    return names


def _assigned_names_from_binop(tree: ast.AST, operator_type: type[ast.operator]) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.BinOp) or not isinstance(node.value.op, operator_type):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def _assigned_names_using_names(tree: ast.AST, source_names: set[str], minimum_names: int) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        used_names = {
            child.id
            for child in ast.walk(node.value)
            if isinstance(child, ast.Name) and child.id in source_names
        }
        if len(used_names) < minimum_names:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _run_static(1) == ex008.EX008_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _string_assignment_count(tree) >= _MIN_EXERCISE1_STRING_ASSIGNMENTS
    string_names = _assigned_constant_names(tree, str)
    printed_names = _printed_names(tree)
    built_message_names = _assigned_names_using_names(
        tree,
        string_names,
        _MIN_EXERCISE1_STRING_ASSIGNMENTS,
    )
    assert len(string_names) >= _MIN_EXERCISE1_STRING_ASSIGNMENTS
    assert (
        len(printed_names & string_names) >= _MIN_EXERCISE1_STRING_ASSIGNMENTS
        or len(printed_names & built_message_names) >= 1
    )


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _run_static(2) == ex008.EX008_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _string_assignment_count(tree) >= 1
    assert _has_binop(tree, ast.Mult)
    assert _has_call(tree, "str")
    string_names = _assigned_constant_names(tree, str)
    numeric_names = _assigned_constant_names(tree, int) | _assigned_constant_names(tree, float)
    printed_names = _printed_names(tree)
    multiplied_names = _names_used_in_binop(tree, ast.Mult)
    total_names = _assigned_names_from_binop(tree, ast.Mult)
    assert len(printed_names & string_names) >= 1
    assert len(multiplied_names & numeric_names) >= _MIN_EXERCISE2_NUMERIC_FACTORS
    assert len(printed_names & total_names) >= 1


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[3])
def test_exercise3_logic(case: dict[str, object]) -> None:
    output = _run_with_inputs(3, list(case["inputs"]))
    assert output == case["expected_output"]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    input_names = _input_assigned_names(tree)
    assert len(input_names) == _EXPECTED_INPUT_CALLS
    assert all(_print_uses_name(tree, name) for name in input_names)


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[4])
def test_exercise4_logic(case: dict[str, object]) -> None:
    output = _run_with_inputs(4, list(case["inputs"]))
    assert output == case["expected_output"]


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    assert _input_call_count(tree) == _EXPECTED_INPUT_CALLS
    assert _has_call(tree, "int")
    assert _has_binop(tree, ast.Mult)


@pytest.mark.task(taskno=5)
@pytest.mark.parametrize("case", ex008.EX008_INTERACTIVE_CASES[5])
def test_exercise5_logic(case: dict[str, object]) -> None:
    output = _run_with_inputs(5, list(case["inputs"]))
    assert output == case["expected_output"]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    assert _input_call_count(tree) == _EXPECTED_INPUT_CALLS
    assert _has_call(tree, "float")
    assert _has_call(tree, "int")
    assert _has_binop(tree, ast.Mult)
