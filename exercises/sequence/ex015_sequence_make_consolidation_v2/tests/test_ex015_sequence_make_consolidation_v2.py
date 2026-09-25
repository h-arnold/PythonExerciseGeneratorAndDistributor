"""Canonical output, construct, and data-flow tests for ex015."""

from __future__ import annotations

import ast
from textwrap import dedent
from typing import cast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex015_sequence_make_consolidation_v2"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_checks = load_exercise_test_module(EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()


def _tag(exercise_no: int) -> str:
    """Return the tagged-cell name for an exercise part."""
    return f"exercise{exercise_no}"


def _run_static(exercise_no: int) -> str:
    """Execute a non-interactive exercise cell."""
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _run_with_inputs(exercise_no: int, inputs: list[str]) -> str:
    """Execute an interactive exercise cell with deterministic input."""
    return run_cell_with_input(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        inputs=inputs,
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    """Parse the active notebook's tagged cell."""
    return ast.parse(
        extract_tagged_code(
            _NOTEBOOK_PATH,
            tag=_tag(exercise_no),
            cache=_CACHE,
        )
    )


def _input_case_params(exercise_no: int) -> list[object]:
    """Return concise stable pytest IDs from the canonical case catalog."""
    cases = cast(dict[int, tuple[dict[str, object], ...]], _ex.EX015_INPUT_CASES)
    return [pytest.param(case, id=cast(str, case["id"])) for case in cases[exercise_no]]


def _assert_construct(exercise_no: int) -> None:
    """Assert the conservative printed-payload construct contract."""
    issues = _checks.construct_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


def _assert_data_flow(exercise_no: int) -> None:
    """Assert input provenance, casts, and calculated-flow requirements."""
    issues = _checks.data_flow_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


def _assert_rejects(source: str, exercise_no: int, fragment: str) -> None:
    """Assert that a synthetic shortcut is rejected by the analyzer."""
    issues = _checks.construct_issues(ast.parse(dedent(source).strip()), exercise_no)
    issues += _checks.data_flow_issues(ast.parse(dedent(source).strip()), exercise_no)
    assert any(fragment.lower() in issue.lower() for issue in issues), (
        f"Exercise {exercise_no}: expected an issue containing {fragment!r}; got {issues!r}."
    )


def _assert_accepts(source: str, exercise_no: int) -> None:
    """Assert that a valid equivalent passes both semantic checks."""
    tree = ast.parse(dedent(source).strip())
    issues = _checks.construct_issues(tree, exercise_no)
    issues += _checks.data_flow_issues(tree, exercise_no)
    assert not issues, f"Exercise {exercise_no}: {' '.join(issues)}"


# ---------------------------------------------------------------------------
# Static parts
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_output() -> None:
    assert _run_static(1) == _ex.EX015_EXPECTED_STATIC_OUTPUTS[1]


@pytest.mark.task(taskno=1)
def test_exercise1_constructs() -> None:
    _assert_construct(1)


@pytest.mark.task(taskno=1)
def test_exercise1_assignment_order_and_flow() -> None:
    _assert_data_flow(1)


@pytest.mark.task(taskno=2)
def test_exercise2_output() -> None:
    assert _run_static(2) == _ex.EX015_EXPECTED_STATIC_OUTPUTS[2]


@pytest.mark.task(taskno=2)
def test_exercise2_constructs() -> None:
    _assert_construct(2)


@pytest.mark.task(taskno=2)
def test_exercise2_assignment_order_and_flow() -> None:
    _assert_data_flow(2)


# ---------------------------------------------------------------------------
# Interactive parts
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=3)
@pytest.mark.parametrize("case", _input_case_params(3))
def test_exercise3_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(3, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=3)
def test_exercise3_constructs() -> None:
    _assert_construct(3)


@pytest.mark.task(taskno=3)
def test_exercise3_int_cast_and_multiply_flow() -> None:
    _assert_data_flow(3)


@pytest.mark.task(taskno=4)
@pytest.mark.parametrize("case", _input_case_params(4))
def test_exercise4_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(4, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=4)
def test_exercise4_constructs() -> None:
    _assert_construct(4)


@pytest.mark.task(taskno=4)
def test_exercise4_two_int_inputs_and_remainder_flow() -> None:
    _assert_data_flow(4)


@pytest.mark.task(taskno=5)
@pytest.mark.parametrize("case", _input_case_params(5))
def test_exercise5_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(5, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=5)
def test_exercise5_constructs() -> None:
    _assert_construct(5)


@pytest.mark.task(taskno=5)
def test_exercise5_float_casts_and_rounding_flow() -> None:
    _assert_data_flow(5)


@pytest.mark.task(taskno=6)
@pytest.mark.parametrize("case", _input_case_params(6))
def test_exercise6_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(6, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=6)
def test_exercise6_constructs() -> None:
    _assert_construct(6)


@pytest.mark.task(taskno=6)
def test_exercise6_formula_and_rounding_flow() -> None:
    _assert_data_flow(6)


@pytest.mark.task(taskno=7)
@pytest.mark.parametrize("case", _input_case_params(7))
def test_exercise7_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(7, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=7)
def test_exercise7_constructs() -> None:
    _assert_construct(7)


@pytest.mark.task(taskno=7)
def test_exercise7_two_int_inputs_and_remainder_flow() -> None:
    _assert_data_flow(7)


@pytest.mark.task(taskno=8)
@pytest.mark.parametrize("case", _input_case_params(8))
def test_exercise8_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(8, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=8)
def test_exercise8_constructs() -> None:
    _assert_construct(8)


@pytest.mark.task(taskno=8)
def test_exercise8_power_and_rounding_flow() -> None:
    _assert_data_flow(8)


@pytest.mark.task(taskno=9)
@pytest.mark.parametrize("case", _input_case_params(9))
def test_exercise9_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(9, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=9)
def test_exercise9_constructs() -> None:
    _assert_construct(9)


@pytest.mark.task(taskno=9)
def test_exercise9_casts_and_bill_flow() -> None:
    _assert_data_flow(9)


@pytest.mark.task(taskno=10)
@pytest.mark.parametrize("case", _input_case_params(10))
def test_exercise10_output(case: dict[str, object]) -> None:
    assert _run_with_inputs(10, cast(list[str], case["inputs"])) == cast(
        str,
        case["expected_output"],
    )


@pytest.mark.task(taskno=10)
def test_exercise10_constructs() -> None:
    _assert_construct(10)


@pytest.mark.task(taskno=10)
def test_exercise10_three_int_inputs_and_pack_flow() -> None:
    _assert_data_flow(10)


# ---------------------------------------------------------------------------
# Canonical adversarial regressions. Each first checks the active notebook,
# so these cases also fail for an untouched student notebook.
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_rejects_reordered_assignments() -> None:
    _assert_construct(1)
    _assert_data_flow(1)
    _assert_rejects(
        """
        sweets_per_bag = 7
        total_sweets = 50
        full_bags = total_sweets // sweets_per_bag
        sweets_left = total_sweets % sweets_per_bag
        print(f"You can make {full_bags} full bags with {sweets_left} sweets left over.")
        """,
        1,
        "requested order",
    )


@pytest.mark.task(taskno=3)
def test_exercise3_rejects_hardcoded_answer() -> None:
    _assert_construct(3)
    _assert_data_flow(3)
    _assert_rejects(
        """
        age = int(input())
        print(f"If you were a dog, you would be {28} years old.")
        """,
        3,
        "must reach",
    )


@pytest.mark.task(taskno=4)
def test_exercise4_rejects_lookup_table() -> None:
    _assert_construct(4)
    _assert_data_flow(4)
    _assert_rejects(
        """
        pizzas = int(input())
        people = int(input())
        answers = {(3, 5): "canned"}
        print(f"{answers[(pizzas, people)]}")
        """,
        4,
        "lookup",
    )


@pytest.mark.task(taskno=5)
def test_exercise5_rejects_dead_operation() -> None:
    _assert_construct(5)
    _assert_data_flow(5)
    source = extract_tagged_code(_NOTEBOOK_PATH, tag=_tag(5), cache=_CACHE)
    _assert_rejects(f"{source}\nunused_cost = 2 * 3\n", 5, "every arithmetic operation")


@pytest.mark.task(taskno=6)
def test_exercise6_rejects_missing_input() -> None:
    _assert_construct(6)
    _assert_data_flow(6)
    _assert_rejects(
        """
        celsius = 25
        fahrenheit = celsius * 9 / 5 + 32
        print(f"{celsius}°C is {round(fahrenheit, 1)}°F")
        """,
        6,
        "exactly 1 input",
    )


@pytest.mark.task(taskno=8)
def test_exercise8_rejects_dead_rounding() -> None:
    _assert_construct(8)
    _assert_data_flow(8)
    source = extract_tagged_code(_NOTEBOOK_PATH, tag=_tag(8), cache=_CACHE)
    _assert_rejects(f"{source}\nunused_rounded = round(7, 2)\n", 8, "rounding operation")


@pytest.mark.task(taskno=9)
def test_exercise9_rejects_wrong_flow() -> None:
    _assert_construct(9)
    _assert_data_flow(9)
    _assert_rejects(
        """
        bill = float(input())
        tip_percent = int(input())
        people = int(input())
        tip_amount = bill * tip_percent / 100
        total = round(50.0 + tip_amount, 2)
        per_person = round(total / 4, 2)
        print(f"Total bill: £{round(50.0, 2)}")
        print(f"Tip ({tip_percent}%): £{round(tip_amount, 2)}")
        print(f"Total with tip: £{total}")
        print(f"Each of {people} people pays: £{per_person}")
        """,
        9,
        "divide the total",
    )


@pytest.mark.task(taskno=3)
def test_exercise3_accepts_named_constant_alias() -> None:
    _assert_construct(3)
    _assert_data_flow(3)
    _assert_accepts(
        """
        age = int(input())
        factor = 7
        answer = age * factor
        print(f"If you were a dog, you would be {answer} years old.")
        """,
        3,
    )


@pytest.mark.task(taskno=10)
def test_exercise10_accepts_literal_pack_sizes() -> None:
    _assert_construct(10)
    _assert_data_flow(10)
    _assert_accepts(
        """
        students = int(input())
        pencils = int(input())
        erasers = int(input())
        total_pencils = students * pencils
        total_erasers = students * erasers
        pencil_packs = (total_pencils + 24 - 1) // 24
        eraser_packs = (total_erasers + 15 - 1) // 15
        leftover_pencils = pencil_packs * 24 - total_pencils
        leftover_erasers = eraser_packs * 15 - total_erasers
        print(f"For {students} students:")
        print(f"Each student needs {pencils} pencils and {erasers} erasers.")
        print(f"Order {pencil_packs} packs of pencils (24 per pack) — {leftover_pencils} pencils will be left over.")
        print(f"Order {eraser_packs} packs of erasers (15 per pack) — {leftover_erasers} erasers will be left over.")
        """,
        10,
    )


@pytest.mark.task(taskno=3)
def test_exercise3_accepts_tuple_and_annotated_bindings() -> None:
    _assert_construct(3)
    _assert_data_flow(3)
    _assert_accepts(
        """
        age, factor = int(input()), 7
        answer: int = age * factor
        print(f"If you were a dog, you would be {answer} years old.")
        """,
        3,
    )


__all__ = ["EXERCISE_KEY"]
