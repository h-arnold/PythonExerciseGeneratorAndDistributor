from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Final

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EX003_EXERCISE_KEY = "ex003_sequence_modify_variables"
_EXERCISE10: Final = 10
ex003 = load_exercise_test_module(_EX003_EXERCISE_KEY, "expectations")
_checker = load_exercise_test_module(_EX003_EXERCISE_KEY, "student_checker_support")
_construct_checks = load_exercise_test_module(_EX003_EXERCISE_KEY, "construct_checks")


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


_CACHE = RuntimeCache()


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _EX003_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        _EX003_EXERCISE_KEY,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _EX003_EXERCISE_KEY,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _assert_strict_output(exercise_no: int, output: str, expected: str) -> None:
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact text '{expected}' but got '{output}'."
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


def _has_string_concatenation_in_print(tree: ast.AST) -> bool:
    """Check if print() statement uses string concatenation (+)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "print":
            continue
        for arg in node.args:
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                return True
    return False


def _assert_interactive_construct(exercise_no: int) -> None:
    """Require the complete ordered input-to-output data flow."""
    issues = _checker.check_interactive_construct(exercise_no)
    assert not issues, (
        f"Exercise {exercise_no}: " + "; ".join(issues)
    )


def _assert_static_construct(exercise_no: int) -> None:
    """Require a live top-level assignment-to-print data flow."""
    issues = _construct_checks.static_construct_issues(
        _exercise_ast(exercise_no),
        exercise_no,
        required_values=ex003.EX003_EXPECTED_ASSIGNMENTS.get(exercise_no),
        required_fragments=(
            ex003.EX003_EXERCISE10_REQUIRED_PHRASES if exercise_no == _EXERCISE10 else None
        ),
    )
    assert not issues, (
        f"Exercise {exercise_no}: " + "; ".join(issues)
    )


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    _assert_strict_output(1, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[1])
    assert "Hello from Python" not in output


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_static_construct(1)
    tree = _exercise_ast(1)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_STATIC_OUTPUTS[1] in constants
    assert "Hello from Python!" not in constants, "Old greeting value should be removed"
    assert _assignment_matches(
        tree,
        "greeting",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[1]["greeting"],
    )
    assert _print_uses_name(
        tree, "greeting"), "Must use greeting variable in print"


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    _assert_strict_output(2, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[2])
    assert "math" not in output.lower()


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_static_construct(2)
    tree = _exercise_ast(2)
    constants = _string_constants(tree)
    assert "math" not in constants, "Old subject value should be removed"
    assert _assignment_matches(
        tree,
        "subject",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[2]["subject"],
    )
    assert _print_uses_name(
        tree, "subject"), "Must use subject variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    _assert_strict_output(3, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[3])
    assert "pasta" not in output.lower()


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_static_construct(3)
    tree = _exercise_ast(3)
    constants = _string_constants(tree)
    assert "pasta" not in constants, "Old food value should be removed"
    assert _assignment_matches(
        tree,
        "food",
        lambda value: value == ex003.EX003_EXPECTED_ASSIGNMENTS[3]["food"],
    )
    assert _print_uses_name(tree, "food"), "Must use food variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    case = ex003.EX003_INPUT_EDGE_CASES[4]
    output = _exercise_output_with_inputs(4, list(case["inputs"]))
    _assert_strict_output(4, output, case["expected_output"])


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    case = ex003.EX003_INPUT_CASES[4]
    output = _exercise_output_with_inputs(4, list(case["inputs"]))
    _assert_strict_output(4, output, case["expected_output"])


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    _assert_interactive_construct(4)


@pytest.mark.task(taskno=4)
def test_exercise4_semantic_sensitivity() -> None:
    case = ex003.EX003_INPUT_SEMANTIC_CASES[4]
    output = _exercise_output_with_inputs(4, list(case["inputs"]))
    _assert_strict_output(4, output, case["expected_output"])


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    case = ex003.EX003_INPUT_EDGE_CASES[5]
    output = _exercise_output_with_inputs(5, list(case["inputs"]))
    _assert_strict_output(5, output, case["expected_output"])


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    case = ex003.EX003_INPUT_CASES[5]
    output = _exercise_output_with_inputs(5, list(case["inputs"]))
    _assert_strict_output(5, output, case["expected_output"])


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_interactive_construct(5)


@pytest.mark.task(taskno=5)
def test_exercise5_semantic_sensitivity() -> None:
    case = ex003.EX003_INPUT_SEMANTIC_CASES[5]
    output = _exercise_output_with_inputs(5, list(case["inputs"]))
    _assert_strict_output(5, output, case["expected_output"])


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    case = ex003.EX003_INPUT_EDGE_CASES[6]
    output = _exercise_output_with_inputs(6, list(case["inputs"]))
    _assert_strict_output(6, output, case["expected_output"])


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    case = ex003.EX003_INPUT_CASES[6]
    output = _exercise_output_with_inputs(6, list(case["inputs"]))
    _assert_strict_output(6, output, case["expected_output"])


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    _assert_interactive_construct(6)


@pytest.mark.task(taskno=6)
def test_exercise6_semantic_sensitivity() -> None:
    case = ex003.EX003_INPUT_SEMANTIC_CASES[6]
    output = _exercise_output_with_inputs(6, list(case["inputs"]))
    _assert_strict_output(6, output, case["expected_output"])


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    _assert_strict_output(7, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[7])
    assert "Learning" not in output
    assert "Python" not in output


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    _assert_static_construct(7)
    tree = _exercise_ast(7)
    constants = _string_constants(tree)
    assert "Learning" not in constants, "Old first_word value should be removed"
    assert "Python" not in constants, "Old second_word value should be removed"
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
    assert _print_uses_name(
        tree, "first_word"), "Must use first_word variable in print"
    assert _print_uses_name(
        tree, "second_word"), "Must use second_word variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    _assert_strict_output(8, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[8])
    assert "coding" not in output.lower()


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    _assert_static_construct(8)
    tree = _exercise_ast(8)
    constants = _string_constants(tree)
    assert "coding" not in constants, "Old part2 value should be removed"
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
    assert _print_uses_name(tree, "part1"), "Must use part1 variable in print"
    assert _print_uses_name(tree, "part2"), "Must use part2 variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    _assert_strict_output(9, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[9])
    assert "morning" not in output.lower()


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    _assert_static_construct(9)
    tree = _exercise_ast(9)
    constants = _string_constants(tree)
    assert "morning" not in constants, "Old time_of_day value should be removed"
    assert "students" not in constants, "Old audience value should be removed"
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
    assert _print_uses_name(
        tree, "greeting"), "Must use greeting variable in print"
    assert _print_uses_name(
        tree, "time_of_day"), "Must use time_of_day variable in print"
    assert _print_uses_name(
        tree, "audience"), "Must use audience variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    _assert_strict_output(10, output, ex003.EX003_EXPECTED_STATIC_OUTPUTS[10])
    assert "Python" not in output
    assert "matter" not in output


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    _assert_static_construct(10)
    tree = _exercise_ast(10)
    constants = _string_constants(tree)
    assert "Python" not in constants, "Old part_one value should be removed"
    assert "matter" not in constants, "Old part_three value should be removed"
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
    assert _print_uses_name(
        tree, "part_one"), "Must use part_one variable in print"
    assert _print_uses_name(
        tree, "part_two"), "Must use part_two variable in print"
    assert _print_uses_name(
        tree, "part_three"), "Must use part_three variable in print"
    assert _has_string_concatenation_in_print(
        tree), "Must use + to concatenate strings"


def _static_issues(code: str, exercise_no: int) -> list[str]:
    """Return construct issues for a synthetic static example."""
    return _construct_checks.static_construct_issues(ast.parse(code), exercise_no)


def _interactive_issues(code: str, exercise_no: int) -> list[str]:
    """Return construct issues for a synthetic interactive example."""
    return _construct_checks.interactive_construct_issues(
        ast.parse(code),
        expected_input_count=2,
        message_template=ex003.EX003_EXPECTED_INPUT_MESSAGES[exercise_no],
    )


@pytest.mark.task(taskno=1)
def test_static_adversarial_constructs_reject_dead_and_neutral_flows() -> None:
    """Keep the real cell valid and reject bypasses of its data flow."""
    _assert_static_construct(1)
    assert ex003.EX003_EXPECTED_STATIC_OUTPUTS[1] in _string_constants(_exercise_ast(1))
    assert not _static_issues(
        'greeting = "Hi there!"\nmessage = greeting\nprint(message)\n',
        1,
    )
    for code in (
        'print("Hi there!")\ngreeting = "Hi there!"\nif False:\n    print(greeting)\n',
        'greeting = "Hi there!"\nprint("Hi there!")\nif False:\n    print(greeting)\n',
        'greeting = "Hi there!"\nprint("Hi there!" * 0)\n',
        'import builtins\ngreeting = "Hi there!"\nprint(greeting)\n',
        'for word in ["Hi there!"]:\n    print(word)\n',
        'while False:\n    print("Hi there!")\n',
        'def helper():\n    return "Hi there!"\nprint(helper())\n',
        'greeting = "Hi there!"\ngreeting += " again"\nprint(greeting)\n',
        'greeting = (value := "Hi there!")\nprint(greeting)\n',
        'greeting = value.text\nprint(greeting)\n',
        'print = print\ngreeting = "Hi there!"\nprint(greeting)\n',
        'input = input\ngreeting = "Hi there!"\nprint(greeting)\n',
        'greeting = "Hi there!" or "Goodbye"\nprint(greeting)\n',
        'greeting = "Hi there!" if True else "Goodbye"\nprint(greeting)\n',
        'greeting = "Hi there!" == "Hi there!"\nprint(greeting)\n',
    ):
        assert _static_issues(code, 1), code


@pytest.mark.task(taskno=4)
def test_interactive_adversarial_constructs_reject_lookup_and_accept_aliases() -> None:
    """Exercise valid aliases/separators and reject fixture-specific lookups."""
    _assert_interactive_construct(4)
    assert not _interactive_issues(
        'print("Type the name of your favourite fruit:")\n'
        'fruit = input()\n'
        'print("Type one word to describe it:")\n'
        'descriptor = input()\n'
        'message = "I like " + fruit + " because it is " + descriptor\n'
        'print(message)\n',
        4,
    )
    assert not _interactive_issues(
        'print("Type the name of your favourite fruit:")\n'
        'fruit = input()\n'
        'print("Type one word to describe it:")\n'
        'descriptor = input()\n'
        'print("I like ", fruit, " because it is ", descriptor, sep="")\n',
        4,
    )
    for code in (
        'fruit = input()\ndescriptor = input()\n'
        'lookup = {("mango", "tropical"): "I like mango because it is tropical"}\n'
        'print(lookup[(fruit, descriptor)])\n',
        'fruit = input()\ndescriptor = input()\n'
        'message = "I like mango because it is tropical" if fruit == "mango" else "wrong"\n'
        'print(message)\n',
        'fruit = input()\ndescriptor = input()\n'
        'print("I like " + (fruit * 0) + " because it is " + descriptor)\n',
        'fruit = input()\ndescriptor = input()\n'
        'print("I like mango because it is tropical")\n',
    ):
        assert _interactive_issues(code, 4), code
