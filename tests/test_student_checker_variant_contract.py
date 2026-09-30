"""Regression guards for exercise-local student checker support modules.

Checker modules must let the runtime resolver pick the notebook variant.
Passing an explicit ``variant=`` to the grader helpers overrides
``PYTUTOR_ACTIVE_VARIANT``, so a correct solution notebook reports failures
(see ex007, ex010 and ex011 in the sequence construct).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from exercise_runtime_support.exercise_catalogue import get_exercise_catalogue
from exercise_runtime_support.exercise_test_support import resolve_exercise_tests_dir

REPO_ROOT = Path(__file__).resolve().parents[1]

CHECKER_MODULE_NAME = "student_checker_support.py"


def _checker_modules() -> list[Path]:
    """Return every exercise-local student_checker_support.py path."""
    return [
        resolve_exercise_tests_dir(entry.exercise_key) / CHECKER_MODULE_NAME
        for entry in get_exercise_catalogue()
        if (resolve_exercise_tests_dir(entry.exercise_key) / CHECKER_MODULE_NAME).is_file()
    ]


def _forced_variant_lines(source: str) -> list[int]:
    """Return line numbers of calls that pass an explicit ``variant=``."""
    forced: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not any(kw.arg == "variant" for kw in node.keywords):
            continue
        forced.append(node.lineno)
    return forced


def test_catalogue_exposes_checker_modules() -> None:
    """Guard the guard: the catalogue must still resolve checker modules."""
    modules = _checker_modules()
    assert modules, "no exercise-local student_checker_support.py files found"


@pytest.mark.parametrize(
    "checker_path",
    _checker_modules(),
    ids=lambda path: path.parent.parent.name,
)
def test_checker_module_does_not_force_a_variant(checker_path: Path) -> None:
    """Checker modules must not override the resolver-selected variant."""
    source = checker_path.read_text(encoding="utf-8")
    forced = _forced_variant_lines(source)
    assert not forced, (
        f"{checker_path.relative_to(REPO_ROOT)} forces a notebook variant on "
        f"line(s) {forced}; omit the variant argument so "
        "PYTUTOR_ACTIVE_VARIANT selects the notebook"
    )
