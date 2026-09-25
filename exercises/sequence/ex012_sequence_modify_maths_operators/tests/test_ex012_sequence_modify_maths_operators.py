"""Tests for ex012 sequence modify maths operators."""

from __future__ import annotations

import ast
import json
from collections import Counter
from typing import Any, Final, Literal, cast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex012_sequence_modify_maths_operators"
_ex = load_exercise_test_module(EXERCISE_KEY, "expectations")
_construct_checks = load_exercise_test_module(EXERCISE_KEY, "construct_checks")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()
_WRAPPED_OLD_ISSUE_COUNT: Final[int] = 2


def _tag(exercise_no: int) -> str:
    return f"exercise{exercise_no}"


def _run(exercise_no: int) -> str:
    return run_cell_and_capture_output(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )


def _exercise_ast(exercise_no: int) -> ast.Module:
    code = extract_tagged_code(
        _NOTEBOOK_PATH,
        tag=_tag(exercise_no),
        cache=_CACHE,
    )
    return ast.parse(code)


def _assert_exact_output(exercise_no: int, output: str) -> None:
    expected = _ex.EX012_EXPECTED_OUTPUTS[exercise_no]
    assert output == expected, (
        f"Exercise {exercise_no}: expected exact output {expected!r} but got {output!r}."
    )


def _assert_required_flow(exercise_no: int) -> None:
    issues = _construct_checks.required_flow_issues(_exercise_ast(exercise_no), exercise_no)
    assert not issues, f"Exercise {exercise_no}: {'; '.join(issues)}"


def _adversarial_issues(exercise_no: int, code: str) -> list[str]:
    return _construct_checks.required_flow_issues(ast.parse(code), exercise_no)


def _code_cells(variant: Literal["student", "solution"]) -> list[dict[str, Any]]:
    path = resolve_exercise_notebook_path(EXERCISE_KEY, variant=variant)
    notebook = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    cells = cast(list[object], notebook.get("cells"))
    return [
        cast(dict[str, Any], cell)
        for cell in cells
        if isinstance(cell, dict)
        and cast(dict[str, Any], cell).get("cell_type") == "code"
    ]


def _cell_tags(cell: dict[str, Any]) -> list[str]:
    metadata = cast(dict[str, Any], cell.get("metadata"))
    raw_tags = metadata.get("tags", [])
    if not isinstance(raw_tags, list):
        return []
    return [tag for tag in cast(list[object], raw_tags) if isinstance(tag, str)]


def _assert_one_code_cell_per_exercise_tag() -> None:
    expected_tags = {f"exercise{number}" for number in range(1, 11)}
    variants = (
        ("student", _code_cells("student")),
        ("solution", _code_cells("solution")),
    )
    for variant, cells in variants:
        counts = Counter(
            tag
            for cell in cells
            for tag in _cell_tags(cell)
            if tag.startswith("exercise") and tag[8:].isdigit()
        )
        for tag in expected_tags:
            assert counts[tag] == 1, f"{variant} notebook must have one code cell tagged {tag}."
        assert set(counts) == expected_tags, f"{variant} notebook has unexpected exercise tags."
        for cell in cells:
            exercise_tags = [
                tag
                for tag in _cell_tags(cell)
                if tag.startswith("exercise") and tag[8:].isdigit()
            ]
            assert len(exercise_tags) <= 1, f"{variant} notebook has a multi-exercise code cell."


# ---------------------------------------------------------------------------
# Exact output checks
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    _assert_exact_output(1, _run(1))


@pytest.mark.task(taskno=2)
def test_exercise2_logic() -> None:
    _assert_exact_output(2, _run(2))


@pytest.mark.task(taskno=3)
def test_exercise3_logic() -> None:
    _assert_exact_output(3, _run(3))


@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    _assert_exact_output(4, _run(4))


@pytest.mark.task(taskno=5)
def test_exercise5_logic() -> None:
    _assert_exact_output(5, _run(5))


@pytest.mark.task(taskno=6)
def test_exercise6_logic() -> None:
    _assert_exact_output(6, _run(6))


@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    _assert_exact_output(7, _run(7))


@pytest.mark.task(taskno=8)
def test_exercise8_logic() -> None:
    _assert_exact_output(8, _run(8))


@pytest.mark.task(taskno=9)
def test_exercise9_logic() -> None:
    _assert_exact_output(9, _run(9))


@pytest.mark.task(taskno=10)
def test_exercise10_logic() -> None:
    _assert_exact_output(10, _run(10))


# ---------------------------------------------------------------------------
# Final-binding, arithmetic, precision, and positional output-flow checks
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_final_floor_division_flow() -> None:
    _assert_required_flow(1)


@pytest.mark.task(taskno=2)
def test_exercise2_final_modulus_flow() -> None:
    _assert_required_flow(2)


@pytest.mark.task(taskno=3)
def test_exercise3_final_floor_division_flow() -> None:
    _assert_required_flow(3)


@pytest.mark.task(taskno=4)
def test_exercise4_final_modulus_flow() -> None:
    _assert_required_flow(4)


@pytest.mark.task(taskno=5)
def test_exercise5_final_division_and_round_precision_flow() -> None:
    _assert_required_flow(5)


@pytest.mark.task(taskno=6)
def test_exercise6_final_multiplication_and_round_precision_flow() -> None:
    _assert_required_flow(6)


@pytest.mark.task(taskno=7)
def test_exercise7_mixed_floor_division_and_modulus_flow() -> None:
    _assert_required_flow(7)


@pytest.mark.task(taskno=8)
def test_exercise8_mixed_floor_division_and_modulus_flow() -> None:
    _assert_required_flow(8)


@pytest.mark.task(taskno=9)
def test_exercise9_final_division_and_round_precision_flow() -> None:
    _assert_required_flow(9)


@pytest.mark.task(taskno=10)
def test_exercise10_mixed_arithmetic_flow() -> None:
    _assert_required_flow(10)


# ---------------------------------------------------------------------------
# Old starter code must be removed recursively, not only from a final binding
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_exercise1_rejects_wrapped_old_expression() -> None:
    code = """
students = 29
group_size = 4
decoy = str(students / group_size)
full_groups = students // group_size
print("Full groups: " + str(full_groups))
"""
    issues = _adversarial_issues(1, code)
    assert any("old" in issue.lower() for issue in issues)
    _assert_required_flow(1)


@pytest.mark.task(taskno=2)
def test_exercise2_rejects_wrapped_placeholder() -> None:
    code = """
cupcakes = 29
per_box = 4
decoy = str(0)
leftover = cupcakes % per_box
print("Leftover cupcakes: " + str(leftover))
"""
    issues = _adversarial_issues(2, code)
    assert any("old" in issue.lower() for issue in issues)
    _assert_required_flow(2)


@pytest.mark.task(taskno=3)
def test_exercise3_rejects_wrapped_old_expression() -> None:
    code = """
players = 23
team_size = 5
decoy = str(players / team_size)
complete_teams = players // team_size
print("Complete teams: " + str(complete_teams))
"""
    issues = _adversarial_issues(3, code)
    assert any("old" in issue.lower() for issue in issues)
    _assert_required_flow(3)


@pytest.mark.task(taskno=4)
def test_exercise4_rejects_wrapped_placeholder() -> None:
    code = """
stickers = 23
stickers_per_sheet = 6
decoy = str(0)
leftover = stickers % stickers_per_sheet
print("Leftover stickers: " + str(leftover))
"""
    issues = _adversarial_issues(4, code)
    assert any("old" in issue.lower() for issue in issues)
    _assert_required_flow(4)


@pytest.mark.task(taskno=7)
def test_exercise7_rejects_wrapped_old_expressions() -> None:
    code = """
minutes = 125
decoy_hours = str(minutes / 60)
decoy_left = str(minutes - 60)
hours = minutes // 60
minutes_left = minutes % 60
print(str(minutes) + " minutes is " + str(hours) + " hours and " + str(minutes_left) + " minutes")
"""
    issues = _adversarial_issues(7, code)
    assert sum("old" in issue.lower() for issue in issues) >= _WRAPPED_OLD_ISSUE_COUNT
    _assert_required_flow(7)


@pytest.mark.task(taskno=8)
def test_exercise8_rejects_wrapped_old_expression_and_placeholder() -> None:
    code = """
pence = 389
decoy_pounds = str(pence / 100)
decoy_left = str(0)
pounds = pence // 100
leftover_pence = pence % 100
print(str(pence) + "p is £" + str(pounds) + " and " + str(leftover_pence) + "p")
"""
    issues = _adversarial_issues(8, code)
    assert any("old" in issue.lower() for issue in issues)
    _assert_required_flow(8)


@pytest.mark.task(taskno=10)
def test_exercise10_rejects_wrapped_old_expressions() -> None:
    code = """
crayons = 26
per_box = 4
total_price = 10.99
decoy_boxes = str(crayons / per_box)
decoy_left = str(crayons - per_box)
full_boxes = crayons // per_box
leftover = crayons % per_box
price_per_box = total_price / full_boxes
price_per_box = round(price_per_box, 2)
print("Full boxes: " + str(full_boxes))
print("Leftover crayons: " + str(leftover))
print("Price per box: £" + str(price_per_box))
"""
    issues = _adversarial_issues(10, code)
    assert sum("old" in issue.lower() for issue in issues) >= _WRAPPED_OLD_ISSUE_COUNT
    _assert_required_flow(10)


# ---------------------------------------------------------------------------
# The required target must occur in a positional print payload, never in a
# control keyword or a lookup fallback.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("exercise_no", "code"),
    [
        pytest.param(
            1,
            """
students = 29
group_size = 4
full_groups = students // group_size
print("Full groups: 7", flush=full_groups)
""",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            2,
            """
cupcakes = 29
per_box = 4
leftover = cupcakes % per_box
print("Leftover cupcakes: 1", flush=leftover)
""",
            marks=pytest.mark.task(taskno=2),
        ),
        pytest.param(
            3,
            """
players = 23
team_size = 5
complete_teams = players // team_size
print("Complete teams: 4", flush=complete_teams)
""",
            marks=pytest.mark.task(taskno=3),
        ),
        pytest.param(
            4,
            """
stickers = 23
stickers_per_sheet = 6
leftover = stickers % stickers_per_sheet
print("Leftover stickers: 5", flush=leftover)
""",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            5,
            """
total_points = 20
games = 3
average_points = total_points / games
average_points = round(average_points, 1)
print("Average points: 6.7", flush=average_points)
""",
            marks=pytest.mark.task(no=5),
        ),
        pytest.param(
            6,
            """
price = 1.257
amount = 3
total = price * amount
total = round(total, 2)
print("Total cost: £3.77", flush=total)
""",
            marks=pytest.mark.task(taskno=6),
        ),
        pytest.param(
            7,
            """
minutes = 125
hours = minutes // 60
minutes_left = minutes % 60
print("125 minutes is 2 hours and 5 minutes", flush=hours, end=minutes_left)
""",
            marks=pytest.mark.task(taskno=7),
        ),
        pytest.param(
            8,
            """
pence = 389
pounds = pence // 100
leftover_pence = pence % 100
print("389p is £3 and 89p", flush=pounds, end=leftover_pence)
""",
            marks=pytest.mark.task(taskno=8),
        ),
        pytest.param(
            9,
            """
distance = 86.25
time_hours = 2
speed = distance / time_hours
speed = round(speed, 1)
print("Average speed: 43.1 km/h", flush=speed)
""",
            marks=pytest.mark.task(taskno=9),
        ),
        pytest.param(
            10,
            """
crayons = 26
per_box = 4
total_price = 10.99
full_boxes = crayons // per_box
leftover = crayons % per_box
price_per_box = total_price / full_boxes
price_per_box = round(price_per_box, 2)
print("Full boxes: 6", flush=full_boxes)
print("Leftover crayons: 2", flush=leftover)
print("Price per box: £1.83", flush=price_per_box)
""",
            marks=pytest.mark.task(taskno=10),
        ),
    ],
)
def test_target_must_be_in_positional_print_payload(exercise_no: int, code: str) -> None:
    issues = _adversarial_issues(exercise_no, code)
    assert any("positional payload" in issue for issue in issues), issues
    _assert_required_flow(exercise_no)


@pytest.mark.task(taskno=1)
@pytest.mark.parametrize("keyword", ["end", "file", "sep"])
def test_print_control_keywords_cannot_satisfy_target_dependency(keyword: str) -> None:
    code = f"""
students = 29
group_size = 4
full_groups = students // group_size
print("Full groups: 7", {keyword}=full_groups)
"""
    issues = _adversarial_issues(1, code)
    assert any("positional payload" in issue for issue in issues), issues
    _assert_required_flow(1)


@pytest.mark.task(taskno=1)
def test_lookup_default_does_not_count_as_target_payload() -> None:
    code = """
students = 29
group_size = 4
full_groups = students // group_size
lookup = {"answer": "Full groups: 7"}
print(lookup.get("answer", full_groups))
"""
    issues = _adversarial_issues(1, code)
    assert any("attributes or lookup methods" in issue for issue in issues), issues
    assert any("positional payload" in issue for issue in issues), issues
    _assert_required_flow(1)


# ---------------------------------------------------------------------------
# Hardcoded/dead required operations are rejected for every task.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("exercise_no", "code"),
    [
        pytest.param(
            1,
            """
students = 29
group_size = 4
decoy = students // group_size
full_groups = 7
print("Full groups: " + str(full_groups))
""",
            marks=pytest.mark.task(taskno=1),
        ),
        pytest.param(
            2,
            """
cupcakes = 29
per_box = 4
decoy = cupcakes % per_box
leftover = 1
print("Leftover cupcakes: " + str(leftover))
""",
            marks=pytest.mark.task(taskno=2),
        ),
        pytest.param(
            3,
            """
players = 23
team_size = 5
decoy = players // team_size
complete_teams = 4
print("Complete teams: " + str(complete_teams))
""",
            marks=pytest.mark.task(taskno=3),
        ),
        pytest.param(
            4,
            """
stickers = 23
stickers_per_sheet = 6
decoy = stickers % stickers_per_sheet
leftover = 5
print("Leftover stickers: " + str(leftover))
""",
            marks=pytest.mark.task(taskno=4),
        ),
        pytest.param(
            5,
            """
total_points = 20
games = 3
decoy = round(total_points / games, 1)
average_points = 6.7
print("Average points: " + str(average_points))
""",
            marks=pytest.mark.task(taskno=5),
        ),
        pytest.param(
            6,
            """
price = 1.257
amount = 3
decoy = round(price * amount, 2)
total = 3.77
print("Total cost: £" + str(total))
""",
            marks=pytest.mark.task(taskno=6),
        ),
        pytest.param(
            7,
            """
minutes = 125
decoy_hours = minutes // 60
decoy_left = minutes % 60
hours = 2
minutes_left = 5
print(str(minutes) + " minutes is " + str(hours) + " hours and " + str(minutes_left) + " minutes")
""",
            marks=pytest.mark.task(taskno=7),
        ),
        pytest.param(
            8,
            """
pence = 389
decoy_pounds = pence // 100
decoy_left = pence % 100
pounds = 3
leftover_pence = 89
print(str(pence) + "p is £" + str(pounds) + " and " + str(leftover_pence) + "p")
""",
            marks=pytest.mark.task(taskno=8),
        ),
        pytest.param(
            9,
            """
distance = 86.25
time_hours = 2
decoy = round(distance / time_hours, 1)
speed = 43.1
print("Average speed: " + str(speed) + " km/h")
""",
            marks=pytest.mark.task(taskno=9),
        ),
        pytest.param(
            10,
            """
crayons = 26
per_box = 4
total_price = 10.99
decoy_boxes = crayons // per_box
decoy_left = crayons % per_box
decoy_price = round(total_price / decoy_boxes, 2)
full_boxes = 6
leftover = 2
price_per_box = 1.83
print("Full boxes: " + str(full_boxes))
print("Leftover crayons: " + str(leftover))
print("Price per box: £" + str(price_per_box))
"""
            , marks=pytest.mark.task(taskno=10),
        ),
    ],
)
def test_hardcoded_or_dead_required_operation_is_rejected(exercise_no: int, code: str) -> None:
    assert _adversarial_issues(exercise_no, code)
    _assert_required_flow(exercise_no)


# ---------------------------------------------------------------------------
# The explicit straight-line allowlist rejects the newly identified bypasses.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        pytest.param("value = True and False", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = 1 == 1", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = 1 if True else 2", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = values[0]", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = object.value", marks=pytest.mark.task(taskno=1)),
        pytest.param("def helper():\n    return 1", marks=pytest.mark.task(taskno=1)),
        pytest.param("import math", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = 1\nvalue += 1", marks=pytest.mark.task(taskno=1)),
        pytest.param("value = (other := 1)", marks=pytest.mark.task(taskno=1)),
        pytest.param("print = str", marks=pytest.mark.task(taskno=1)),
        pytest.param("input = str", marks=pytest.mark.task(taskno=1)),
    ],
)
def test_straight_line_allowlist_rejects_bypass_constructs(code: str) -> None:
    assert _construct_checks.straight_line_issues(ast.parse(code), 1)
    _assert_required_flow(1)


# ---------------------------------------------------------------------------
# Structural notebook integrity: both variants have one code cell per tag.
# ---------------------------------------------------------------------------


@pytest.mark.task(taskno=1)
def test_each_notebook_has_exactly_one_code_cell_per_exercise_tag() -> None:
    _assert_one_code_cell_per_exercise_tag()
    # Keep the structural case useful under the initial-failure rule as well.
    _assert_required_flow(1)
