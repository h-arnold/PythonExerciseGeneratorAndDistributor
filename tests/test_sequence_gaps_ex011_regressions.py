"""Repository-only regressions for the ex011 semantic sensitivity checker."""

from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_ANALYZER = load_exercise_test_module(
    "ex011_sequence_gaps_consolidation",
    "construct_checks",
)


def _issues(source: str, exercise_no: int) -> list[str]:
    return _ANALYZER.required_flow_issues(ast.parse(source), exercise_no)


@pytest.mark.parametrize(
    ("exercise_no", "source"),
    [
        (
            1,
            "word_one = 'A'\n"
            "word_two = 'B'\n"
            "word_three = 'C'\n"
            "message = str.join(', ', [word_one, word_two, word_three])\n"
            "print(message)\n",
        ),
        (
            2,
            "greeting = 'Hello'\n"
            "name = 'Amina'\n"
            "message = '{} {}'.format(greeting, name)\n"
            "print(message)\n",
        ),
        (
            2,
            "greeting = 'Hello'\n"
            "name = 'Amina'\n"
            "message = 'Hello %s %s' % (greeting, name)\n"
            "print(message)\n",
        ),
        (
            4,
            "first_number = 4\n"
            "second_number = 6\n"
            "print(f'The total is {first_number + second_number}')\n",
        ),
        (
            5,
            "price = 2.5\n"
            "item_count = 3\n"
            "print(f'Total cost: {price * item_count}')\n",
        ),
        (
            6,
            "total_distance = 7\n"
            "days = 2\n"
            "print(f'Average distance: {total_distance / days} km')\n",
        ),
        (
            8,
            "print('Enter your first name:')\n"
            "first_name = input()\n"
            "print('Enter your town:')\n"
            "town = input()\n"
            "print('Hello {} from {}.'.format(first_name, town))\n",
        ),
        (
            9,
            "print('Enter your favourite colour:')\n"
            "colour = input()\n"
            "print('Enter your favourite animal:')\n"
            "animal = input()\n"
            "print('My favourite colour is %s and my favourite animal is %s.' % (colour, animal))\n",
        ),
        (
            10,
            "shop_name = 'Sequence Supplies'\n"
            "print('Enter your name:')\n"
            "customer_name = input()\n"
            "notebook_price = 3.5\n"
            "notebook_count = 4\n"
            "print(f'Welcome to {shop_name}, {customer_name}. Your total is £{notebook_price * notebook_count}.')\n",
        ),
    ],
)
def test_allows_ordinary_formatting_and_inline_arithmetic(
    exercise_no: int,
    source: str,
) -> None:
    assert _issues(source, exercise_no) == []


def test_rejects_neutralized_supplied_value() -> None:
    source = (
        "first_number = 4\n"
        "second_number = 6\n"
        "print(f'The total is {first_number * 0}')\n"
    )
    issues = _issues(source, 4)
    assert issues
    assert any("neutral expressions" in issue for issue in issues)


def test_rejects_hardcoded_interactive_output() -> None:
    source = (
        "print('What is your favourite word?')\n"
        "word = input()\n"
        "print('You chose coding')\n"
    )
    issues = _issues(source, 3)
    assert issues
    assert any("must affect the final output" in issue for issue in issues)


def test_requires_final_fstring_and_sensitivity_for_exercise7() -> None:
    concatenation = (
        "first_name = 'Aisha'\n"
        "hobby = 'drawing'\n"
        "message = first_name + ' enjoys ' + hobby + ' after school.'\n"
        "print(message)\n"
    )
    fstring = (
        "first_name = 'Aisha'\n"
        "hobby = 'drawing'\n"
        "print(f'{first_name} enjoys {hobby} after school.')\n"
    )
    assert any("f-string" in issue for issue in _issues(concatenation, 7))
    assert _issues(fstring, 7) == []


_BASE_STATIC_SOURCE = "first_number = 4\nsecond_number = 6\n"
@pytest.mark.parametrize(
    "source",
    [
        _BASE_STATIC_SOURCE + "if first_number > 0:\n    print(10)\n",
        _BASE_STATIC_SOURCE + "import math\n",
        _BASE_STATIC_SOURCE + "def helper():\n    return 10\n",
        _BASE_STATIC_SOURCE + "total = (10).real\nprint(total)\n",
        _BASE_STATIC_SOURCE + "total = first_number[0]\nprint(total)\n",
        _BASE_STATIC_SOURCE + "first_number += 1\n",
        _BASE_STATIC_SOURCE + "print((value := 10))\n",
        _BASE_STATIC_SOURCE + "print = 10\n",
        _BASE_STATIC_SOURCE + "print(open('side-effect.txt'))\n",
    ],
)
def test_rejects_non_allowlisted_statements_and_expressions(source: str) -> None:
    assert _issues(source, 4)
