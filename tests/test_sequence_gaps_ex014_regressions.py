"""Repository-only regressions for the ex014 conservative semantic analyzer."""

from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_ANALYZER = load_exercise_test_module(
    "ex014_sequence_gaps_advanced_arithmetic",
    "construct_checks",
)

_VALID_SOURCES: dict[int, str] = {
    1: 'number = 8\nresult = number ** 2\nprint(f"The square of {number} is {result}")\n',
    2: 'number = 6\nresult = number ** 3\nprint(f"The cube of {number} is {result}")\n',
    3: (
        'number_input = input("Enter a number: ")\n'
        "number_int = int(number_input)\n"
        "result = number_int ** 0.5\n"
        'print(f"The square root of {number_input} is {result}")\n'
    ),
    4: (
        'base_input = input("Enter the base: ")\n'
        'exponent_input = input("Enter the exponent: ")\n'
        "base_int = int(base_input)\n"
        "exponent_int = int(exponent_input)\n"
        "result = base_int ** exponent_int\n"
        'print(f"{base_input} to the power of {exponent_input} is {result}")\n'
    ),
    5: (
        'side_input = input("Enter the side length: ")\n'
        "side_float = float(side_input)\n"
        "area = side_float ** 2\n"
        'print(f"A square with side {side_input} has area {area}")\n'
    ),
    6: (
        'width_input = input("Enter the width: ")\n'
        'length_input = input("Enter the length: ")\n'
        "width_float = float(width_input)\n"
        "length_float = float(length_input)\n"
        "area = width_float * length_float\n"
        'print(f"The area of the rectangle is {area}")\n'
    ),
    7: (
        'side_input = input("Enter the side length: ")\n'
        "side_float = float(side_input)\n"
        "volume = side_float ** 3\n"
        'print(f"The volume of the cube is {volume}")\n'
    ),
    8: (
        'number_input = input("Enter a whole number: ")\n'
        "number_int = int(number_input)\n"
        "result = number_int ** 0.5\n"
        'print(f"The square root of {number_input} is {result}")\n'
    ),
    9: (
        "pi = 3.14159\n"
        'radius_input = input("Enter the radius: ")\n'
        "radius_float = float(radius_input)\n"
        "area = pi * radius_float ** 2\n"
        'print(f"The area of the circle is {area}")\n'
    ),
    10: (
        'base_input = input("Enter the base: ")\n'
        'exponent_input = input("Enter the exponent: ")\n'
        "base_int = int(base_input)\n"
        "exponent_int = int(exponent_input)\n"
        "result = base_int ** exponent_int\n"
        'print(f"{base_input} to the power of {exponent_input} is {result}")\n'
    ),
}


def _issues(source: str, exercise_no: int) -> list[str]:
    """Run the exercise-local analyzer against one synthetic source string."""
    return _ANALYZER.required_flow_issues(ast.parse(source), exercise_no)


def _dynamic_power_source(middle: str = "") -> str:
    """Return valid Ex4 flow with optional statements inserted before calculation."""
    return (
        'base_input = input("Enter the base: ")\n'
        'exponent_input = input("Enter the exponent: ")\n'
        "base_int = int(base_input)\n"
        "exponent_int = int(exponent_input)\n"
        f"{middle}"
        "result = base_int ** exponent_int\n"
        'print(f"{base_input} to the power of {exponent_input} is {result}")\n'
    )


@pytest.mark.parametrize("exercise_no", range(1, 11))
def test_accepts_each_solution_data_flow(exercise_no: int) -> None:
    assert _issues(_VALID_SOURCES[exercise_no], exercise_no) == []


@pytest.mark.parametrize(
    ("case_id", "source"),
    [
        pytest.param(
            "named-expression",
            _dynamic_power_source("decoy = (captured := base_int) ** exponent_int\n"),
            id="named-expression",
        ),
        pytest.param(
            "globals-call",
            _dynamic_power_source("scope = globals()\n"),
            id="globals-call",
        ),
        pytest.param(
            "globals-mutation",
            _dynamic_power_source('globals()["result"] = base_int ** exponent_int\n'),
            id="globals-mutation",
        ),
        pytest.param(
            "locals-call",
            _dynamic_power_source("scope = locals()\n"),
            id="locals-call",
        ),
        pytest.param(
            "locals-mutation",
            _dynamic_power_source('locals()["result"] = base_int ** exponent_int\n'),
            id="locals-mutation",
        ),
        pytest.param(
            "exec",
            _dynamic_power_source('exec("result = 2 ** 10")\n'),
            id="exec",
        ),
        pytest.param(
            "lambda",
            _dynamic_power_source("decoy = lambda value: value ** exponent_int\n"),
            id="lambda",
        ),
        pytest.param(
            "builtins-mutation",
            _dynamic_power_source('__builtins__["print"] = lambda *args: None\n'),
            id="builtins-mutation",
        ),
        pytest.param(
            "print-mutation",
            _dynamic_power_source("print = lambda *args, **kwargs: None\n"),
            id="print-mutation",
        ),
        pytest.param(
            "side-effect-call",
            _dynamic_power_source('open("side-effect.txt", "w")\n'),
            id="side-effect-call",
        ),
        pytest.param(
            "attribute-access",
            _dynamic_power_source("decoy = base_int.real\n"),
            id="attribute-access",
        ),
        pytest.param(
            "subscript-lookup",
            _dynamic_power_source("answers = {(2, 10): 1024}\ndecoy = answers[(base_int, exponent_int)]\n"),
            id="subscript-lookup",
        ),
        pytest.param(
            "control-flow",
            _dynamic_power_source("if base_int > 0:\n    decoy = exponent_int\n"),
            id="control-flow",
        ),
        pytest.param(
            "augmented-assignment",
            _dynamic_power_source("base_int += 1\n"),
            id="augmented-assignment",
        ),
        pytest.param(
            "import",
            _dynamic_power_source("import math\n"),
            id="import",
        ),
        pytest.param(
            "builtin-rebinding",
            _dynamic_power_source("int = lambda value: value\n"),
            id="builtin-rebinding",
        ),
        pytest.param(
            "dunder-rebinding",
            _dynamic_power_source("__builtins__ = {}\n"),
            id="dunder-rebinding",
        ),
    ],
)
def test_rejects_second_pass_side_effect_bypasses(case_id: str, source: str) -> None:
    assert _issues(source, 4), case_id


def test_rejects_same_name_input_cast_reassignment_and_lost_transcript_input() -> None:
    source = (
        'number_input = input("Enter a number: ")\n'
        "number_input = int(number_input)\n"
        "result = number_input ** 0.5\n"
        'print(f"The square root of {number_input} is {result}")\n'
    )
    issues = _issues(source, 3)
    assert issues
    assert any("only once" in issue or "distinct" in issue for issue in issues)


def test_rejects_transcript_hardcode_without_input() -> None:
    source = (
        'number_input = "144"\n'
        "number_int = int(number_input)\n"
        "result = number_int ** 0.5\n"
        'print(f"The square root of {number_input} is {result}")\n'
    )
    assert _issues(source, 3)


def test_rejects_decoy_exponent_and_xor() -> None:
    source = (
        "number = 6\n"
        "decoy = number ** 2\n"
        "result = number ^ 3\n"
        'print(f"The cube of {number} is {result}")\n'
    )
    assert _issues(source, 2)


def test_rejects_reversed_power_operands() -> None:
    source = (
        'base_input = input("Enter the base: ")\n'
        'exponent_input = input("Enter the exponent: ")\n'
        "base_int = int(base_input)\n"
        "exponent_int = int(exponent_input)\n"
        "result = exponent_int ** base_int\n"
        'print(f"{base_input} to the power of {exponent_input} is {result}")\n'
    )
    assert _issues(source, 4)


def test_rejects_missing_rectangle_multiplication() -> None:
    source = (
        'width_input = input("Enter the width: ")\n'
        'length_input = input("Enter the length: ")\n'
        "width_float = float(width_input)\n"
        "length_float = float(length_input)\n"
        "decoy = width_float * length_float\n"
        "area = width_float + length_float\n"
        'print(f"The area of the rectangle is {area}")\n'
    )
    assert _issues(source, 6)


def test_rejects_unsquared_circle_radius() -> None:
    source = (
        "pi = 3.14159\n"
        'radius_input = input("Enter the radius: ")\n'
        "radius_float = float(radius_input)\n"
        "area = pi * radius_float\n"
        'print(f"The area of the circle is {area}")\n'
    )
    assert _issues(source, 9)


def test_rejects_unsafe_fstring_conversion() -> None:
    source = _dynamic_power_source().replace(
        "{result}",
        "{result!r}",
    )
    assert _issues(source, 4)
