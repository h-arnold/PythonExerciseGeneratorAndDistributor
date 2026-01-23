from __future__ import annotations

import ast
from collections.abc import Callable

import pytest

from tests.notebook_grader import (
    extract_tagged_code,
    run_cell_and_capture_output,
    run_cell_with_input,
)

NOTEBOOK_PATH = "notebooks/ex003_sequence_modify_variables.ipynb"

EXPECTED_STATIC_OUTPUT = {
    1: "Hi there!",
    2: "I enjoy coding lessons.",
    3: "My favourite food is sushi",
    7: "Variables matter",
    8: "Keep experimenting",
    9: "Good evening everyone!",
    10: "Variables and strings make a message!",
}

EXPECTED_PROMPTS = {
    4: "Type the name of your favourite fruit:",
    5: "Which town do you like the most?",
    6: "Please enter your name:",
}

EXPECTED_INPUT_MESSAGES = {
    4: "I like {value}",
    5: "I would visit {value}",
    6: "Welcome, {value}!",
}

ORIGINAL_PROMPTS = {
    4: "What is your favourite fruit?",
    5: "Tell me your favourite place:",
    6: "Enter your name:",
}


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    return run_cell_and_capture_output(NOTEBOOK_PATH, tag=_tag(exercise_no))


def _exercise_output_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    return run_cell_with_input(
        NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(NOTEBOOK_PATH, tag=_tag(exercise_no))
    return ast.parse(code)


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


def _has_input_assignment(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "input"
        ):
            return True
    return False


@pytest.mark.parametrize("exercise_no", range(1, 11))
@pytest.mark.task(taskno=0)
def test_exercise_cells_execute(exercise_no: int) -> None:
    if exercise_no in (4, 5, 6):
        output = _exercise_output_with_inputs(exercise_no, ["check"])
    else:
        output = _exercise_output(exercise_no)
    assert output is not None


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[1]
    assert "Hello from Python" not in output


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{EXPECTED_STATIC_OUTPUT[1]}\n"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    constants = _string_constants(tree)
    assert EXPECTED_STATIC_OUTPUT[1] in constants
    assert _assignment_matches(
        tree, "greeting", lambda value: value == EXPECTED_STATIC_OUTPUT[1])


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[2]
    assert "math" not in output.lower()


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == f"{EXPECTED_STATIC_OUTPUT[2]}\n"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    assert _assignment_matches(
        tree, "subject", lambda value: value == "coding")
    assert _print_uses_name(tree, "subject")


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[3]
    assert "pasta" not in output.lower()


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == f"{EXPECTED_STATIC_OUTPUT[3]}\n"


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    assert _assignment_matches(tree, "food", lambda value: value == "sushi")
    assert _print_uses_name(tree, "food")


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    fruit = "dragonfruit"
    output = _exercise_output_with_inputs(4, [fruit])
    lines = output.strip().splitlines()
    assert lines == [EXPECTED_PROMPTS[4],
                     EXPECTED_INPUT_MESSAGES[4].format(value=fruit)]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output_with_inputs(4, ["mango"])
    expected = f"{EXPECTED_PROMPTS[4]}\n{EXPECTED_INPUT_MESSAGES[4].format(value='mango')}\n"
    assert output == expected


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    constants = _string_constants(tree)
    assert EXPECTED_PROMPTS[4] in constants
    assert ORIGINAL_PROMPTS[4] not in constants
    assert _has_input_assignment(tree, "fruit")
    assert _print_uses_name(tree, "fruit")


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    place = "Newport"
    output = _exercise_output_with_inputs(5, [place])
    lines = output.strip().splitlines()
    assert lines == [EXPECTED_PROMPTS[5],
                     EXPECTED_INPUT_MESSAGES[5].format(value=place)]


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    output = _exercise_output_with_inputs(5, ["Cardiff"])
    expected = f"{EXPECTED_PROMPTS[5]}\n{EXPECTED_INPUT_MESSAGES[5].format(value='Cardiff')}\n"
    assert output == expected


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(5)
    constants = _string_constants(tree)
    assert EXPECTED_PROMPTS[5] in constants
    assert ORIGINAL_PROMPTS[5] not in constants
    assert _has_input_assignment(tree, "place")
    assert _print_uses_name(tree, "place")


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    name = "Jess"
    output = _exercise_output_with_inputs(6, [name])
    lines = output.strip().splitlines()
    assert lines == [EXPECTED_PROMPTS[6],
                     EXPECTED_INPUT_MESSAGES[6].format(value=name)]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output_with_inputs(6, ["Alex"])
    expected = f"{EXPECTED_PROMPTS[6]}\n{EXPECTED_INPUT_MESSAGES[6].format(value='Alex')}\n"
    assert output == expected


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    constants = _string_constants(tree)
    assert EXPECTED_PROMPTS[6] in constants
    assert ORIGINAL_PROMPTS[6] not in constants
    assert _has_input_assignment(tree, "name")
    assert _print_uses_name(tree, "name")
    assert any("!" in value for value in constants)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[7]
    assert "Learning" not in output
    assert "Python" not in output


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output(7)
    assert output == f"{EXPECTED_STATIC_OUTPUT[7]}\n"


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    assert _assignment_matches(
        tree, "first_word", lambda value: value == "Variables")
    assert _assignment_matches(
        tree, "second_word", lambda value: value == "matter")
    assert _print_uses_name(tree, "first_word")
    assert _print_uses_name(tree, "second_word")


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[8]
    assert "coding" not in output.lower()


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    output = _exercise_output(8)
    assert output == f"{EXPECTED_STATIC_OUTPUT[8]}\n"


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    assert _assignment_matches(tree, "part1", lambda value: value == "Keep")
    assert _assignment_matches(
        tree, "part2", lambda value: value == "experimenting")
    assert _print_uses_name(tree, "part1")
    assert _print_uses_name(tree, "part2")


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[9]
    assert "morning" not in output.lower()


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    assert output == f"{EXPECTED_STATIC_OUTPUT[9]}\n"


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    assert _assignment_matches(tree, "greeting", lambda value: value == "Good")
    assert _assignment_matches(
        tree, "time_of_day", lambda value: value == "evening")
    assert _assignment_matches(
        tree, "audience", lambda value: value == "everyone!")
    assert _print_uses_name(tree, "greeting")
    assert _print_uses_name(tree, "time_of_day")
    assert _print_uses_name(tree, "audience")


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(10)
    assert output.strip() == EXPECTED_STATIC_OUTPUT[10]
    assert "Python" not in output
    assert "matter" not in output


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    output = _exercise_output(10)
    assert output == f"{EXPECTED_STATIC_OUTPUT[10]}\n"


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(10)
    assert _assignment_matches(
        tree, "part_one", lambda value: "Variables" in value)
    assert _assignment_matches(
        tree, "part_two", lambda value: "strings" in value)
    assert _assignment_matches(
        tree, "part_three", lambda value: "message" in value)
    assert _print_uses_name(tree, "part_one")
    assert _print_uses_name(tree, "part_two")
    assert _print_uses_name(tree, "part_three")
