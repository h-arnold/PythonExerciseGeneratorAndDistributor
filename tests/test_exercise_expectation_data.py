"""Data-quality guards for exercise-local ``expectations.py`` modules.

``scripts/verify_exercise_quality.py`` lints each exercise's expectations data
and reports a part declared in both a static and an interactive expectation dict
as a warning. A lint warning is not enforced anywhere, so the duplication it
flags shipped unnoticed. These tests make the same data contract enforceable
across every exercise, using the verifier's own classification so the contract
has a single definition:

- a part is declared in exactly one expectation family, unless the static dict
  is a value-for-value mirror of the input cases (the derived quick-reference
  alias used by ex003/ex004);
- a static expected-output value is never an empty placeholder.

Both are data-integrity rules about what the tables assert, not preferences
about how they are formatted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.exercise_catalogue import get_exercise_catalogue
from exercise_runtime_support.exercise_test_support import resolve_exercise_tests_dir
from scripts import verify_exercise_quality

# pyright: reportPrivateUsage=false

EXERCISES_WITH_EXPECTATIONS: list[str] = [
    entry.exercise_key
    for entry in get_exercise_catalogue()
    if (resolve_exercise_tests_dir(entry.exercise_key) / "expectations.py").is_file()
]


def _exercise_dir(exercise_key: str) -> Path:
    """Return the canonical exercise directory for an exercise key."""
    return resolve_exercise_tests_dir(exercise_key).parent


def _load_expectations(exercise_dir: Path) -> object:
    """Import the expectations module of an exercise directory."""
    module = verify_exercise_quality._load_exercise_local_module(exercise_dir, "expectations")
    assert module is not None, f"{exercise_dir.name}: expectations.py could not be imported"
    return module


def test_catalogue_exercises_expose_expectations_modules() -> None:
    """Guard the guard: the sweep must still have exercises to inspect."""
    assert EXERCISES_WITH_EXPECTATIONS, "no exercise-local expectations.py files found"


@pytest.mark.parametrize("exercise_key", EXERCISES_WITH_EXPECTATIONS, ids=lambda key: key)
def test_no_part_is_declared_in_both_expectation_families(exercise_key: str) -> None:
    """Each part is declared once, or the static table is a derived input-case mirror.

    Two hand-written declarations of the same expected output can drift apart,
    so the part silently acquires two different truths. Only a dict computed
    from the input cases is safe to keep alongside them.
    """
    exercise_dir = _exercise_dir(exercise_key)
    declared = verify_exercise_quality._declared_family_parts(
        exercise_dir / "tests" / "expectations.py",
        verify_exercise_quality._collect_expectation_dicts(_load_expectations(exercise_dir)),
    )
    duplicated = sorted(declared.static & declared.interactive)

    assert not duplicated, (
        f"{exercise_key}: parts {duplicated} are declared in both a static and an "
        "interactive expectation dict; keep one declaration, or derive the static "
        "dict from the input cases as ex003/ex004 do"
    )


@pytest.mark.parametrize("exercise_key", EXERCISES_WITH_EXPECTATIONS, ids=lambda key: key)
def test_no_static_expectation_is_an_empty_placeholder(exercise_key: str) -> None:
    """A static expected output is never an empty string.

    An empty value asserts that a cell prints nothing, which is never the
    intended expectation for these exercises and silently contradicts the
    transcript the input case declares for the same part.
    """
    expectations = verify_exercise_quality._collect_expectation_dicts(
        _load_expectations(_exercise_dir(exercise_key))
    )
    placeholders: dict[str, list[int]] = {}
    for name, declared in expectations.static.items():
        empty_parts = sorted(
            part for part, value in declared.items() if isinstance(value, str) and value == ""
        )
        if empty_parts:
            placeholders[name] = empty_parts

    assert not placeholders, (
        f"{exercise_key}: static expectation dicts hold empty placeholder values for "
        f"{placeholders}; declare the real expected output, or drop the entry when the "
        "part's expectation lives in an input case"
    )
