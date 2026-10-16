"""Repository-only regressions for shared notebook/checker task validation."""

from __future__ import annotations

import builtins
import contextlib
import io
from collections.abc import Callable

import pytest

from exercises.sequence.ex005_sequence_debug_logic.tests.task_checks import validate_task

_FULL_NAME_PART = 5


def _run(code: str, inputs: list[str] | None = None) -> str:
    output = io.StringIO()
    supplied = iter(inputs or [])
    original_input = builtins.input
    builtins.input = lambda prompt="": (print(prompt, end=""), next(supplied))[1]
    try:
        with contextlib.redirect_stdout(output):
            exec(compile(code, "<regression>", "exec"), {})
    finally:
        builtins.input = original_input
    return output.getvalue().rstrip("\n")


@pytest.mark.parametrize(
    ("n", "code", "expected"),
    [
        pytest.param(
            1,
            "price=10\nquantity=5\nprint(price * quantity)",
            "50",
            id="inline-product",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            1,
            "price=10\nquantity=5\nsubtotal=price*quantity\ntotal=subtotal\nprint(total)",
            "50",
            id="intermediate-product",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            1,
            "price, quantity = 10, 5\nprint(price * quantity)",
            "50",
            id="tuple-initialization",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            7,
            "score1=20\nscore2=30\naverage=(score1 + score2) / 2\nprint(average)",
            "25.0",
            id="inline-average",
            marks=pytest.mark.task(taskno=7),
        ),
        pytest.param(
            9,
            "length=10\nwidth=5\nperimeter=2*(length+width)\nprint(perimeter)",
            "30",
            id="factored-perimeter",
            marks=pytest.mark.task(taskno=9),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nmessage=f'{word1} {word2}'\nprint(message)",
            "Hello World",
            id="f-string",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            4,
            "word1='Hello '\nword2='World'\nmessage=word1+word2\nprint(message)",
            "Hello World",
            id="separator-in-initial-data",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nword1=word1+' '\nprint(word1+word2)",
            "Hello World",
            id="separator-transformation",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nprint(word1 +\n' ' + word2)",
            "Hello World",
            id="multiline-expression",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nprint(word1+' '+word2)",
            "Hello\nWorld",
            id="output-linebreak",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            8,
            "word1='I'\nword2='love'\nword3='learning'\nword4='Python'\nprint(f'{word1} {word2} {word3} {word4}')",
            "I love learning Python",
            id="f-string-sentence",
            marks=pytest.mark.task(taskno=8),
        ),
        pytest.param(
            8,
            "word1='I '\nword2='love '\nword3='learning '\nword4='Python'\nprint(word1+word2+word3+word4)",
            "I love learning Python",
            id="separators-in-initial-data",
            marks=pytest.mark.task(taskno=8),
        ),
        pytest.param(
            5,
            "print('Enter first name: ', end='')\nfirst=input()\nprint('Enter last name: ', end='')\nlast=input()\nprint(first+' '+last)",
            "Enter first name: Enter last name: Maria Jones",
            id="separate-prompt-prints",
            marks=pytest.mark.task(taskno=5),
        ),
    ],
)
def test_accepts_sound_alternatives(n: int, code: str, expected: str) -> None:
    def observe(values: list[str] | None) -> str:
        if n == _FULL_NAME_PART:
            return _run(code, values or ["Maria", "Jones"])
        return expected

    assert not validate_task(n, code, observe)


@pytest.mark.parametrize(
    ("n", "code", "observed"),
    [
        pytest.param(
            1,
            "price=10\nquantity=5\ntotal=price*5\nprint(total)",
            "50",
            id="fixed-quantity",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            1,
            "price=10\nquantity=5\ntotal=price*0+50\nprint(total)",
            "50",
            id="constant-correction",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            1,
            "price=10\nquantity=5\ntotal=price*quantity\ntotal=50\nprint(total)",
            "50",
            id="overwritten-result",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            9,
            "length=10\nwidth=5\nperimeter=length*width-length-width-width\nprint(perimeter)",
            "30",
            id="coincidental-perimeter",
            marks=pytest.mark.task(taskno=9),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nmessage=word1+' '+ 'World'\nprint(message)",
            "Hello World",
            id="hardcoded-second-word",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            4,
            "word1='Hello'\nword2='World'\nprint(word1+'World')",
            "HelloWorld",
            id="missing-separator",
            marks=pytest.mark.task(taskno=4),
        ),
    ],
)
def test_rejects_hardcoding_or_incorrect_calculations(n: int, code: str, observed: str) -> None:
    errors = validate_task(n, code, lambda _: observed)
    assert errors


@pytest.mark.parametrize(
    ("code", "inputs"),
    [
        pytest.param(
            "first=input('Enter first name: ')\nlast=input('Enter last name: ')\nfirst='Maria'\nlast='Jones'\nprint(first+' '+last)",
            ["Zara", "Khan"],
            id="discarded-name-input",
            marks=pytest.mark.task(taskno=5),
        ),
        pytest.param(
            "age=input('Enter your age: ')\ncity=input('Enter your city: ')\nage='16'\ncity='Birmingham'\nprint('You are '+age+' years old and live in '+city)",
            ["42", "Cardiff"],
            id="discarded-profile-input",
            marks=pytest.mark.task(taskno=10),
        ),
    ],
)
def test_rejects_discarded_input(code: str, inputs: list[str]) -> None:
    defaults = ["Maria", "Jones"] if inputs[0] == "Zara" else ["16", "Birmingham"]

    def observe(values: list[str] | None) -> str:
        return _run(code, values or defaults)

    exercise_no = _FULL_NAME_PART if inputs[0] == "Zara" else 10
    check: Callable[[int, str, Callable[[list[str] | None], str]], list[str]] = validate_task
    assert check(exercise_no, code, observe)
