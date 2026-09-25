"""Repository-only analyzer regressions for ex015."""

from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex015_sequence_make_consolidation_v2"
_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")


def _analysis(source: str):
    """Return the conservative analysis for a synthetic source string."""
    return _checks.analyze_sequence(ast.parse(source))


def _issues(source: str, exercise_no: int) -> list[str]:
    """Return construct and data-flow issues for a synthetic source string."""
    tree = ast.parse(source)
    return [
        *_checks.construct_issues(tree, exercise_no),
        *_checks.data_flow_issues(tree, exercise_no),
    ]


def test_rejects_required_operation_hidden_in_print_keyword() -> None:
    analysis = _analysis(
        """
age = int(input())
print(f"Dog years: {age}", end=f"{age * 7}")
"""
    )

    assert analysis.payload_operators == ()
    assert any("positional printed payload" in issue for issue in analysis.issues)
    assert any("printed payload must use *" in issue for issue in _issues(
        "age = int(input())\nprint(f'Dog years: {age}', end=f'{age * 7}')",
        3,
    ))


def test_rejects_operation_hidden_in_nonempty_format_spec() -> None:
    analysis = _analysis(
        """
age = int(input())
print(f"Dog years: {age:{age * 7}}")
"""
    )

    assert analysis.payload_operators == ()
    assert any("format specifications" in issue for issue in analysis.issues)
    assert any("positional printed payload" in issue for issue in analysis.issues)


def test_accepts_empty_format_spec() -> None:
    analysis = _analysis("age = int(input())\nprint(f'Dog years: {age:}')")

    assert not any("format specifications" in issue for issue in analysis.issues)


def test_rejects_protected_builtin_rebinding() -> None:
    for source in (
        "print = 1\nage = int(input())\nprint(f'{age * 7}')",
        "input = 1\nage = int(input())\nprint(f'{age * 7}')",
        "int, float, round, str = 1, 2.0, 3, 'x'\nprint(f'{round}')",
    ):
        issues = _issues(source, 3)
        assert any("protected name" in issue for issue in issues)


def test_rejects_lookup_and_hardcoded_payload() -> None:
    lookup = _issues(
        """
pizzas = int(input())
people = int(input())
answers = {(3, 5): "canned"}
print(f"{answers[(pizzas, people)]}")
""",
        4,
    )
    assert any("lookup" in issue.lower() for issue in lookup)

    hardcoded = _issues(
        """
age = int(input())
print(f"If you were a dog, you would be {28} years old.")
""",
        3,
    )
    assert any("must reach" in issue for issue in hardcoded)


def test_accepts_named_constant_and_alias_flow() -> None:
    assert _issues(
        """
age = int(input())
factor = 7
factor_alias = factor
answer = age * factor_alias
print(f"If you were a dog, you would be {answer} years old.")
""",
        3,
    ) == []


def test_accepts_named_pack_constants_and_equivalent_tuple_annotation() -> None:
    assert _issues(
        """
students, pencils, erasers = int(input()), int(input()), int(input())
pencil_pack_size: int = 24
eraser_pack_size: int = 15
total_pencils = students * pencils
total_erasers = students * erasers
pencil_packs = (total_pencils + pencil_pack_size - 1) // pencil_pack_size
eraser_packs = (total_erasers + eraser_pack_size - 1) // eraser_pack_size
leftover_pencils = pencil_packs * pencil_pack_size - total_pencils
leftover_erasers = eraser_packs * eraser_pack_size - total_erasers
print(f"For {students} students:")
print(f"Each student needs {pencils} pencils and {erasers} erasers.")
print(f"Order {pencil_packs} packs of pencils ({pencil_pack_size} per pack) — {leftover_pencils} pencils will be left over.")
print(f"Order {eraser_packs} packs of erasers ({eraser_pack_size} per pack) — {leftover_erasers} erasers will be left over.")
""",
        10,
    ) == []


def test_rejects_control_flow_imports_and_arbitrary_calls() -> None:
    sources = (
        "age = int(input())\nif age:\n    answer = age * 7\nprint(f'{answer}')",
        "import math\nage = int(input())\nprint(f'{age * 7}')",
        "age = int(input())\nanswer = len(str(age * 7))\nprint(f'{answer}')",
    )
    for source in sources:
        assert _issues(source, 3)


@pytest.mark.parametrize("source", [
    "name = 'Sam'\nprint(f'Hello {name!r}')",
    "name = 'Sam'\nname += '!'\nprint(f'Hello {name}')",
    "name = (message := 'Sam')\nprint(f'Hello {name}')",
])
def test_rejects_unsafe_fstring_and_assignment_forms(source: str) -> None:
    assert _issues(source, 1)
