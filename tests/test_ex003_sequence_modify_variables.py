from __future__ import annotations

import ast
from collections.abc import Callable

import pytest

from tests.exercise_expectations import ex003_sequence_modify_variables as ex003
from tests.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


_NOTEBOOK_PATH = resolve_notebook_path(ex003.EX003_NOTEBOOK_PATH)
_CACHE = RuntimeCache()
_EXPECTED_INPUT_CALLS = 2


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _assert_strict_output(exercise_no: int, output: str, expected: str) -> None:
    assert output.strip() == expected, (
        f"Exercise {exercise_no}: expected exact text '{expected}' but got '{output.strip()}'."
    )
    assert output == f"{expected}\n", (
        f"Exercise {exercise_no}: output must end with a single newline."
    )


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _assignment_matches(
    tree: ast.AST,
    name: str,
    predicate: Callable[[str], bool],
) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and predicate(node.value.value)
        ):
            return True
    return False


def _print_uses_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))
        ):
            return True
    return False


def _input_assigned_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "input":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    _assert_strict_output(1, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[1])
    assert "Hello from Python" not in output


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_STATIC_OUTPUT[1] in constants
    assert _assignment_matches(
        tree,
        "greeting",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[1]["greeting"],
    )


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    _assert_strict_output(2, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[2])
    assert "math" not in output.lower()


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _assignment_matches(
        tree,
        "subject",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[2]["subject"],
    )
    assert _print_uses_name(tree, "subject")


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    _assert_strict_output(3, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[3])
    assert "pasta" not in output.lower()


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    assert _assignment_matches(
        tree,
        "food",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[3]["food"],
    )
    assert _print_uses_name(tree, "food")


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    fruit = "dragonfruit"
    descriptor = "sweet"
    output = _exercise_output_with_inputs(4, [fruit, descriptor])
    lines = output.strip().splitlines()
    assert lines == [
        ex003.EX003_EXPECTED_PROMPTS[4][0],
        ex003.EX003_EXPECTED_PROMPTS[4][1],
        ex003.EX003_EXPECTED_INPUT_MESSAGES[4].format(value1=fruit, value2=descriptor),
    ]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output_with_inputs(4, ["mango", "tropical"])
    expected = (
        f"{ex003.EX003_EXPECTED_PROMPTS[4][0]}\n"
        f"{ex003.EX003_EXPECTED_PROMPTS[4][1]}\n"
        f"{ex003.EX003_EXPECTED_INPUT_MESSAGES[4].format(value1='mango', value2='tropical')}\n"
    )
    assert output == expected


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_PROMPTS[4][0] in constants
    assert ex003.EX003_EXPECTED_PROMPTS[4][1] in constants
    assert ex003.EX003_ORIGINAL_PROMPTS[4] not in constants

    input_names = _input_assigned_names(tree)
    assert len(input_names) == _EXPECTED_INPUT_CALLS
    assert all(_print_uses_name(tree, name) for name in input_names)


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    town = "Newport"
    country = "Wales"
    output = _exercise_output_with_inputs(5, [town, country])
    lines = output.strip().splitlines()
    assert lines == [
        ex003.EX003_EXPECTED_PROMPTS[5][0],
        ex003.EX003_EXPECTED_PROMPTS[5][1],
        ex003.EX003_EXPECTED_INPUT_MESSAGES[5].format(town=town, country=country),
    ]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output_with_inputs(5, ["Cardiff", "Wales"])
    expected = (
        f"{ex003.EX003_EXPECTED_PROMPTS[5][0]}\n"
        f"{ex003.EX003_EXPECTED_PROMPTS[5][1]}\n"
        f"{ex003.EX003_EXPECTED_INPUT_MESSAGES[5].format(town='Cardiff', country='Wales')}\n"
    )
    assert output == expected


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_PROMPTS[5][0] in constants
    assert ex003.EX003_EXPECTED_PROMPTS[5][1] in constants
    assert ex003.EX003_ORIGINAL_PROMPTS[5] not in constants

    input_names = _input_assigned_names(tree)
    assert len(input_names) == _EXPECTED_INPUT_CALLS
    assert all(_print_uses_name(tree, name) for name in input_names)


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    first = "Jess"
    last = "Jones"
    output = _exercise_output_with_inputs(6, [first, last])
    lines = output.strip().splitlines()
    assert lines == [
        ex003.EX003_EXPECTED_PROMPTS[6][0],
        ex003.EX003_EXPECTED_PROMPTS[6][1],
        ex003.EX003_EXPECTED_INPUT_MESSAGES[6].format(first=first, last=last),
    ]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output_with_inputs(6, ["Alex", "Morgan"])
    expected = (
        f"{ex003.EX003_EXPECTED_PROMPTS[6][0]}\n"
        f"{ex003.EX003_EXPECTED_PROMPTS[6][1]}\n"
        f"{ex003.EX003_EXPECTED_INPUT_MESSAGES[6].format(first='Alex', last='Morgan')}\n"
    )
    assert output == expected


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_PROMPTS[6][0] in constants
    assert ex003.EX003_EXPECTED_PROMPTS[6][1] in constants
    assert ex003.EX003_ORIGINAL_PROMPTS[6] not in constants

    input_names = _input_assigned_names(tree)
    assert len(input_names) == _EXPECTED_INPUT_CALLS
    assert all(_print_uses_name(tree, name) for name in input_names)
    assert any("!" in value for value in constants)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    _assert_strict_output(7, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[7])
    assert "Learning" not in output
    assert "Python" not in output


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _assignment_matches(
        tree,
        "first_word",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[7]["first_word"],
    )
    assert _assignment_matches(
        tree,
        "second_word",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[7]["second_word"],
    )
    assert _print_uses_name(tree, "first_word")
    assert _print_uses_name(tree, "second_word")


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    _assert_strict_output(8, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[8])
    assert "coding" not in output.lower()


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _assignment_matches(
        tree,
        "part1",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[8]["part1"],
    )
    assert _assignment_matches(
        tree,
        "part2",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[8]["part2"],
    )
    assert _print_uses_name(tree, "part1")
    assert _print_uses_name(tree, "part2")


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    _assert_strict_output(9, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[9])
    assert "morning" not in output.lower()


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _assignment_matches(
        tree,
        "greeting",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[9]["greeting"],
    )
    assert _assignment_matches(
        tree,
        "time_of_day",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[9]["time_of_day"],
    )
    assert _assignment_matches(
        tree,
        "audience",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[9]["audience"],
    )
    assert _print_uses_name(tree, "greeting")
    assert _print_uses_name(tree, "time_of_day")
    assert _print_uses_name(tree, "audience")


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    _assert_strict_output(10, output, ex003.EX003_EXPECTED_STATIC_OUTPUT[10])
    assert "Python" not in output
    assert "matter" not in output


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    assert _assignment_matches(
        tree,
        "part_one",
        lambda value: ex003.EX003_EXERCISE10_REQUIRED_PHRASES["part_one"] in value,
    )
    assert _assignment_matches(
        tree,
        "part_two",
        lambda value: ex003.EX003_EXERCISE10_REQUIRED_PHRASES["part_two"] in value,
    )
    assert _assignment_matches(
        tree,
        "part_three",
        lambda value: ex003.EX003_EXERCISE10_REQUIRED_PHRASES["part_three"] in value,
    )
    assert _print_uses_name(tree, "part_one")
    assert _print_uses_name(tree, "part_two")
    assert _print_uses_name(tree, "part_three")
