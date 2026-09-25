"""Tests for ex006 sequence modify casting."""

from __future__ import annotations

import ast
from typing import Final

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex006_sequence_modify_casting"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()
_MIN_INTERACTIVE_CASES: Final[int] = 2

_ADVERSARIAL_FLOW_CASES: Final[dict[int, tuple[str, ...]]] = {
    1: (
        'a = "5"\nb = "10"\na = int(a)\nb = int(b)\nprint(a + b if False else 15)',
        'a = "5"\nb = "10"\na = int(a)\nb = int(b)\nprint(15)',
        'a = "5"\nb = "10"\na = int(a)\nb = int(b)\nprint("15", sep=str(a) + str(b))',
        'print = print\nprint("15")',
    ),
    2: (
        'price_1 = "2.5"\nprice_2 = "3.5"\nprice_1 = float(price_1)\n'
        'price_2 = float(price_2)\nprint(price_1 + (price_2 and ""))',
        'price_1 = "2.5"\nprice_2 = "3.5"\nprint(float(2.5) + float(3.5))',
        'price_1 = "2.5"\nprice_2 = "3.5"\nprice_1 = float(price_1)\n'
        "price_2 = float(price_2)\nprint(6.0)",
    ),
    3: (
        'days = "7"\nweeks = 4\ndays = int(days)\nprint(int(7) * weeks)',
        'days = "7"\nweeks = 4\ndays = int(days)\nprint(days * weeks if False else 28)',
        'days = "7"\nweeks = 4\ndays = int(days)\nprint(28)',
    ),
    4: (
        'score = 500\nprint("Your score is " + str(500))',
        'score = 500\nprint("Your score is 500", end="")',
        'print = print\nprint("Your score is " + str(500))',
    ),
    5: (
        "temperature = 25.9\ntemperature = int(temperature)\nprint(25)",
        "temperature = 25.9\nprint(int(temperature) if False else 25)",
        "temperature = 25.9\ntemperature = int(25.9)\nprint(temperature)",
        "temperature = 25.9\nprint(int(temperature))",
    ),
    6: (
        'print("Enter number:")\nnum = input()\nnum = int(num)\nprint(12, end="")',
        'print("Enter number:")\nnum = input()\nnum = int(num)\nprint(num and 12)',
        'print("Enter number:")\nnum = input()\nnum = int(num)\nprint = print\nprint(num + num)',
    ),
    7: (
        'print("Enter price:")\nprice = input()\nprice = float(price)\nprint("Two items cost:", 3.0)',
        'print("Enter price:")\nprice = input()\nprice = float(price)\n'
        'print("Two items cost:", price and price * 2)',
        'print("Enter price:")\nprice = input()\nprice = float(price)\n'
        'print("Two items cost:", float(1.5) + float(1.5), file=None)',
    ),
    8: (
        'width = "10"\nheight = "5"\nwidth = int(width)\nheight = int(height)\nprint("Area: 50")',
        'width = "10"\nheight = "5"\nwidth = int(width)\nheight = int(height)\n'
        'print("Area: " + str(int(5) * int(2)))',
        'width = "10"\nheight = "5"\nwidth = int(width)\nheight = int(height)\n'
        'print("Area: " + str(width * height) if False else "Area: 50")',
    ),
    9: (
        'item = "Burger"\ncost = 5.50\nprint("The " + item + " costs \\u00a3" + str(5.5))',
        'item = "Burger"\ncost = 5.50\nprint("The " + item + " costs \\u00a3" + '
        '(str(cost) if False else "5.5"))',
        'item = "Burger"\ncost = 5.50\ncost = str(cost)\n'
        'print("The " + item + " costs \\u00a3" + cost and "")',
        'item = "Burger"\ncost = 5.50\ncost = str(cost)\nprint("The Burger costs \\u00a35.5")',
    ),
    10: (
        'print("Enter item 1:")\np1 = input()\nprint("Enter item 2:")\np2 = input()\n'
        'p1 = float(p1)\np2 = float(p2)\nprint("Total: 30.0")',
        'print("Enter item 1:")\np1 = input()\nprint("Enter item 2:")\np2 = input()\n'
        'p1 = float(p1)\np2 = float(p2)\nprint("Total:", p1 + p2 if False else 30.0)',
        'print("Enter item 1:")\np1 = input()\nprint("Enter item 2:")\np2 = input()\n'
        'p1 = float(p1)\np2 = float(p2)\nprint("Total:", p1 and p2)',
    ),
}

_COMMON_DISALLOWED_FLOW_CASES: Final[tuple[str, ...]] = (
    "if True:\n    print(15)",
    "from builtins import print\nprint(15)",
    "def fake():\n    return 15\nprint(fake())",
    "a = 15\na += 1\nprint(a)",
    "print(15 == 15)",
    "print((value := 15))",
    "values = (15,)\nprint(values[0])",
    "print((15).real)",
    "print = print\nprint(15)",
    "input = input\nprint(15)",
    "int = int\nprint(15)",
    "float = float\nprint(15)",
    "str = str\nprint(15)",
    "round = round\nprint(15)",
)

_POSITIVE_FLOW_CASES: Final[dict[int, tuple[str, ...]]] = {
    1: (
        'a = "5"\nb = "10"\na_value = int(a)\nb_value = int(b)\nprint(a_value + b_value)',
        'a = "5"\nb = "10"\na_value = int(a)\nb_value = int(b)\nprint(a_value + b_value, flush=True)',
    ),
    2: (
        'price_1 = "2.5"\nprice_2 = "3.5"\np1, p2 = float(price_1), float(price_2)\nprint(p1 + p2)',
    ),
    3: ('days = "7"\nweeks = 4\nconverted = int(days)\nprint(converted * weeks)',),
    4: ('score = 500\nscore_text = str(score)\nprint("Your score is " + score_text)',),
    5: ("temperature = 25.9\ntemperature = int(temperature)\nprint(temperature)",),
    6: (
        'print("Enter number:")\nnum, = (input(),)\nnum_value = int(num)\n'
        "print(num_value + num_value)",
    ),
    7: (
        'print("Enter price:")\nprice = input()\nprice_value = float(price)\n'
        'print("Two items cost:", price_value + price_value)',
    ),
    8: (
        'width = "10"\nheight = "5"\nw, h = int(width), int(height)\nprint("Area: " + str(w * h))',
    ),
    9: (
        'item = "Burger"\ncost = 5.50\ncost_text = str(cost)\n'
        'print("The " + item + " costs \\u00a3" + cost_text)',
    ),
    10: (
        'print("Enter item 1:")\np1, p2 = input(), input()\n'
        'p1, p2 = float(p1), float(p2)\nprint("Total:", p1 + p2)',
    ),
}


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
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


def _assert_required_flow(exercise_no: int) -> None:
    issues = _construct_checks.required_flow_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


def _assert_interactive_cases(exercise_no: int) -> None:
    cases = _ex.EX006_INPUT_CASES[exercise_no]
    assert len(cases) >= _MIN_INTERACTIVE_CASES, (
        f"Exercise {exercise_no} needs at least {_MIN_INTERACTIVE_CASES} input cases."
    )
    for case in cases:
        inputs = list(case["inputs"])
        output = _run_with_inputs(exercise_no, inputs)
        assert output == case["expected_output"], (
            f"Exercise {exercise_no} with inputs {inputs!r}: "
            f"expected {case['expected_output']!r}, got {output!r}."
        )


def _assert_flow_regressions(exercise_no: int) -> None:
    """Reject adversarial forms and accept documented equivalent forms."""

    adversarial_cases = (*_ADVERSARIAL_FLOW_CASES[exercise_no], *_COMMON_DISALLOWED_FLOW_CASES)
    for source in adversarial_cases:
        issues = _construct_checks.required_flow_issues(ast.parse(source), exercise_no)
        assert issues, f"Exercise {exercise_no} accepted adversarial flow: {source!r}"
    for source in _POSITIVE_FLOW_CASES[exercise_no]:
        issues = _construct_checks.required_flow_issues(ast.parse(source), exercise_no)
        assert not issues, f"Exercise {exercise_no} rejected valid flow: {source!r}; {issues}"
    _assert_required_flow(exercise_no)


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    assert _run(1) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    _assert_required_flow(1)


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    assert _run(2) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_construct() -> None:
    _assert_required_flow(2)


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    assert _run(3) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[3]


@pytest.mark.task(taskno=3)
def test_exercise3_construct() -> None:
    _assert_required_flow(3)


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    assert _run(4) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[4]
    _assert_required_flow(4)


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    assert _run(5) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[5]


@pytest.mark.task(taskno=5)
def test_exercise5_construct() -> None:
    _assert_required_flow(5)


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    _assert_interactive_cases(6)


@pytest.mark.task(taskno=6)
def test_exercise6_construct() -> None:
    _assert_required_flow(6)


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    _assert_interactive_cases(7)


@pytest.mark.task(taskno=7)
def test_exercise7_construct() -> None:
    _assert_required_flow(7)


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    assert _run(8) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[8]


@pytest.mark.task(taskno=8)
def test_exercise8_construct() -> None:
    _assert_required_flow(8)


@pytest.mark.task(taskno=8)
def test_exercise8_negative() -> None:
    assert "Dimensions:" not in _run(8)


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    assert _run(9) == _ex.EX006_EXPECTED_STATIC_OUTPUTS[9]


@pytest.mark.task(taskno=9)
def test_exercise9_construct() -> None:
    _assert_required_flow(9)


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    _assert_interactive_cases(10)


@pytest.mark.task(taskno=10)
def test_exercise10_construct() -> None:
    _assert_required_flow(10)


@pytest.mark.task(taskno=1)
def test_exercise1_flow_regressions() -> None:
    _assert_flow_regressions(1)


@pytest.mark.task(taskno=2)
def test_exercise2_flow_regressions() -> None:
    _assert_flow_regressions(2)


@pytest.mark.task(taskno=3)
def test_exercise3_flow_regressions() -> None:
    _assert_flow_regressions(3)


@pytest.mark.task(taskno=4)
def test_exercise4_flow_regressions() -> None:
    _assert_flow_regressions(4)


@pytest.mark.task(taskno=5)
def test_exercise5_flow_regressions() -> None:
    _assert_flow_regressions(5)


@pytest.mark.task(taskno=6)
def test_exercise6_flow_regressions() -> None:
    _assert_flow_regressions(6)


@pytest.mark.task(taskno=7)
def test_exercise7_flow_regressions() -> None:
    _assert_flow_regressions(7)


@pytest.mark.task(taskno=8)
def test_exercise8_flow_regressions() -> None:
    _assert_flow_regressions(8)


@pytest.mark.task(taskno=9)
def test_exercise9_flow_regressions() -> None:
    _assert_flow_regressions(9)


@pytest.mark.task(taskno=10)
def test_exercise10_flow_regressions() -> None:
    _assert_flow_regressions(10)
