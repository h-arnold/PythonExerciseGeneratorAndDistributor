from __future__ import annotations

import ast

import pytest

from tests.notebook_grader import (
    extract_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

NOTEBOOK_PATH = "notebooks/ex005_sequence_debug_logic.ipynb"
MIN_EXPLANATION_LENGTH = 50

# Placeholder phrases that indicate incomplete student work
PLACEHOLDER_PHRASES = (
    "describe what",
    "your explanation",
    "explain here",
    "write your",
    "todo",
    "...",
)


def _is_valid_explanation(text: str) -> bool:
    """Check explanation is long enough and doesn't contain placeholder phrases."""
    stripped = text.strip().lower()
    if len(stripped) < MIN_EXPLANATION_LENGTH:
        return False
    return not any(phrase in stripped for phrase in PLACEHOLDER_PHRASES)


FULL_NAME_EXERCISE = 5
PROFILE_EXERCISE = 10
AVERAGE_DIVISOR = 2

EXPECTED_SINGLE_LINE = {
    1: "50",
    2: "Alice",
    3: "24",
    4: "Hello World",
    6: "5",
    7: "25.0",
    8: "I love learning Python",
    9: "30",
}

EXERCISE_INPUTS = {
    FULL_NAME_EXERCISE: ["Maria", "Jones"],
    PROFILE_EXERCISE: ["16", "Birmingham"],
}

INPUT_PROMPTS = {
    FULL_NAME_EXERCISE: ("Enter first name: ", "Enter last name: "),
    PROFILE_EXERCISE: ("Enter your age: ", "Enter your city: "),
}


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _explanation_tag(exercise_no: int) -> str:
    return f"explanation{exercise_no}"


def _exercise_output(exercise_no: int) -> str:
    inputs = EXERCISE_INPUTS.get(exercise_no)
    if inputs is None:
        return run_cell_and_capture_output(NOTEBOOK_PATH, tag=_tag(exercise_no))
    return run_cell_with_input(NOTEBOOK_PATH, tag=_tag(exercise_no), inputs=inputs)


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(NOTEBOOK_PATH, tag=_tag(exercise_no))
    return ast.parse(code)


def _assignment_value(tree: ast.AST, target_name: str) -> ast.AST | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == target_name for t in node.targets):
            return node.value
    return None


def _names_in_node(node: ast.AST) -> list[str]:
    return [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]


def _string_constants(node: ast.AST) -> list[str]:
    return [
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def _number_constants(node: ast.AST) -> list[int | float]:
    return [
        n.value
        for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
    ]


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


def _input_prompts(tree: ast.AST) -> list[str]:
    prompts: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) for t in node.targets):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        if not (isinstance(func, ast.Name) and func.id == "input"):
            continue
        if (
            value.args
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)
        ):
            prompts.append(value.args[0].value)
    return prompts


def _expected_io_output(exercise_no: int, inputs: list[str]) -> str:
    prompt_first, prompt_second = INPUT_PROMPTS[exercise_no]
    if exercise_no == FULL_NAME_EXERCISE:
        first, last = inputs
        return f"{prompt_first}{prompt_second}{first} {last}\n"
    if exercise_no == PROFILE_EXERCISE:
        age, city = inputs
        return f"{prompt_first}{prompt_second}You are {age} years old and live in {city}\n"
    raise ValueError(f"Unexpected interactive exercise: {exercise_no}")


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert output.strip() == EXPECTED_SINGLE_LINE[1]


@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{EXPECTED_SINGLE_LINE[1]}\n"


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    value = _assignment_value(tree, "total")
    assert isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mult)
    assert {"price", "quantity"} <= set(_names_in_node(value))
    assert _print_uses_name(tree, "total")


@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(1))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    output = _exercise_output(2)
    assert output.strip() == EXPECTED_SINGLE_LINE[2]


@pytest.mark.task(taskno=2)
def test_exercise2_formatting() -> None:
    output = _exercise_output(2)
    assert output == f"{EXPECTED_SINGLE_LINE[2]}\n"


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    tree = _exercise_ast(2)
    value = _assignment_value(tree, "name")
    assert isinstance(value, ast.Constant) and value.value == "Alice"
    assert _print_uses_name(tree, "name")
    assert not _print_uses_name(tree, "username")


@pytest.mark.task(taskno=2)
def test_exercise2_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(2))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    output = _exercise_output(3)
    assert output.strip() == EXPECTED_SINGLE_LINE[3]


@pytest.mark.task(taskno=3)
def test_exercise3_formatting() -> None:
    output = _exercise_output(3)
    assert output == f"{EXPECTED_SINGLE_LINE[3]}\n"


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    tree = _exercise_ast(3)
    value = _assignment_value(tree, "area")
    assert isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mult)
    assert {"width", "height"} <= set(_names_in_node(value))
    assert _print_uses_name(tree, "area")


@pytest.mark.task(taskno=3)
def test_exercise3_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(3))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    output = _exercise_output(4)
    assert output.strip() == EXPECTED_SINGLE_LINE[4]


@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output(4)
    assert output == f"{EXPECTED_SINGLE_LINE[4]}\n"


@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    value = _assignment_value(tree, "message")
    assert isinstance(value, (ast.BinOp, ast.JoinedStr))
    if isinstance(value, ast.BinOp):
        assert isinstance(value.op, ast.Add)
    assert {"word1", "word2"} <= set(_names_in_node(value))
    assert " " in _string_constants(value)
    assert _print_uses_name(tree, "message")


@pytest.mark.task(taskno=4)
def test_exercise4_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(4))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    output = _exercise_output(FULL_NAME_EXERCISE)
    first, last = EXERCISE_INPUTS[FULL_NAME_EXERCISE]
    expected_name = f"{first} {last}"
    assert expected_name in output


@pytest.mark.task(taskno=5)
def test_exercise5_formatting() -> None:
    inputs = EXERCISE_INPUTS[FULL_NAME_EXERCISE]
    output = _exercise_output(FULL_NAME_EXERCISE)
    assert output == _expected_io_output(FULL_NAME_EXERCISE, inputs)


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    tree = _exercise_ast(FULL_NAME_EXERCISE)
    prompts = _input_prompts(tree)
    assert set(INPUT_PROMPTS[FULL_NAME_EXERCISE]).issubset(prompts)
    value = _assignment_value(tree, "full_name")
    assert isinstance(value, (ast.BinOp, ast.JoinedStr))
    if isinstance(value, ast.BinOp):
        assert isinstance(value.op, ast.Add)
    assert {"first_name", "last_name"} <= set(_names_in_node(value))
    assert " " in _string_constants(value)
    assert _print_uses_name(tree, "full_name")


@pytest.mark.task(taskno=5)
def test_exercise5_explanation() -> None:
    explanation = get_explanation_cell(
        NOTEBOOK_PATH, tag=_explanation_tag(FULL_NAME_EXERCISE))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    output = _exercise_output(6)
    assert output.strip() == EXPECTED_SINGLE_LINE[6]


@pytest.mark.task(taskno=6)
def test_exercise6_formatting() -> None:
    output = _exercise_output(6)
    assert output == f"{EXPECTED_SINGLE_LINE[6]}\n"


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    tree = _exercise_ast(6)
    value = _assignment_value(tree, "change")
    assert isinstance(value, ast.BinOp) and isinstance(value.op, ast.Sub)
    assert isinstance(value.left, ast.Name) and value.left.id == "paid"
    assert isinstance(value.right, ast.Name) and value.right.id == "cost"
    assert _print_uses_name(tree, "change")


@pytest.mark.task(taskno=6)
def test_exercise6_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(6))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _exercise_output(7)
    assert output.strip() == EXPECTED_SINGLE_LINE[7]


@pytest.mark.task(taskno=7)
def test_exercise7_formatting() -> None:
    output = _exercise_output(7)
    assert output == f"{EXPECTED_SINGLE_LINE[7]}\n"


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    tree = _exercise_ast(7)
    total_value = _assignment_value(tree, "total")
    assert isinstance(total_value, ast.BinOp) and isinstance(
        total_value.op, ast.Add)
    assert {"score1", "score2"} <= set(_names_in_node(total_value))
    average_value = _assignment_value(tree, "average")
    assert isinstance(average_value, ast.BinOp) and isinstance(
        average_value.op, ast.Div)
    assert "total" in _names_in_node(average_value)
    assert AVERAGE_DIVISOR in _number_constants(average_value)
    assert _print_uses_name(tree, "average")


@pytest.mark.task(taskno=7)
def test_exercise7_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(7))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    output = _exercise_output(8)
    assert output.strip() == EXPECTED_SINGLE_LINE[8]


@pytest.mark.task(taskno=8)
def test_exercise8_formatting() -> None:
    output = _exercise_output(8)
    assert output == f"{EXPECTED_SINGLE_LINE[8]}\n"


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    tree = _exercise_ast(8)
    value = _assignment_value(tree, "sentence")
    assert isinstance(value, (ast.BinOp, ast.JoinedStr))
    if isinstance(value, ast.BinOp):
        assert isinstance(value.op, ast.Add)
    assert {"word1", "word2", "word3", "word4"} <= set(_names_in_node(value))
    assert " " in _string_constants(value)
    assert _print_uses_name(tree, "sentence")


@pytest.mark.task(taskno=8)
def test_exercise8_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(8))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    output = _exercise_output(9)
    assert output.strip() == EXPECTED_SINGLE_LINE[9]


@pytest.mark.task(taskno=9)
def test_exercise9_formatting() -> None:
    output = _exercise_output(9)
    assert output == f"{EXPECTED_SINGLE_LINE[9]}\n"


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    tree = _exercise_ast(9)
    value = _assignment_value(tree, "perimeter")
    assert value is not None
    assert {"length", "width"} <= set(_names_in_node(value))
    assert any(isinstance(node, (ast.Add, ast.Mult))
               for node in ast.walk(value))
    assert _print_uses_name(tree, "perimeter")


@pytest.mark.task(taskno=9)
def test_exercise9_explanation() -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=_explanation_tag(9))
    assert _is_valid_explanation(explanation)


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    output = _exercise_output(PROFILE_EXERCISE)
    age, city = EXERCISE_INPUTS[PROFILE_EXERCISE]
    expected_message = f"You are {age} years old and live in {city}"
    assert expected_message in output


@pytest.mark.task(taskno=10)
def test_exercise10_formatting() -> None:
    inputs = EXERCISE_INPUTS[PROFILE_EXERCISE]
    output = _exercise_output(PROFILE_EXERCISE)
    assert output == _expected_io_output(PROFILE_EXERCISE, inputs)


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    tree = _exercise_ast(PROFILE_EXERCISE)
    prompts = _input_prompts(tree)
    assert set(INPUT_PROMPTS[PROFILE_EXERCISE]).issubset(prompts)
    value = _assignment_value(tree, "message")
    assert isinstance(value, (ast.BinOp, ast.JoinedStr))
    if isinstance(value, ast.BinOp):
        assert isinstance(value.op, ast.Add)
    assert {"age", "city"} <= set(_names_in_node(value))
    assert any(" live in " in constant for constant in _string_constants(value))
    assert _print_uses_name(tree, "message")


@pytest.mark.task(taskno=10)
def test_exercise10_explanation() -> None:
    explanation = get_explanation_cell(
        NOTEBOOK_PATH, tag=_explanation_tag(PROFILE_EXERCISE))
    assert _is_valid_explanation(explanation)
