"""Public entry points for student-friendly exercise checks."""

from __future__ import annotations

from functools import partial

from exercise_runtime_support.exercise_catalogue import (
    get_exercise_catalogue,
)

from .checks import (
    check_exercise_summary,
    has_exercise_checks,
    run_exercise_checks,
)
from .models import NotebookCheckSpec
from .reporting import (
    print_exercise_results,
    print_results,
    run_check,
    run_checks,
)


def check_exercises() -> None:
    """Run summary checks for all supported live exercises and print a table."""
    checks = _get_checks()
    ordered_checks = [
        checks[entry.exercise_key]
        for entry in get_exercise_catalogue()
        if entry.exercise_key in checks
    ]
    results = run_checks(ordered_checks)
    print_results(results)


def check_exercise(exercise_key: str) -> None:
    """Run checks for a single exercise key and print a summary table."""
    checks = _get_checks()
    check = checks.get(exercise_key)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(
            f"Unknown exercise key '{exercise_key}'. Available: {available}")
    run_check(check)


def _get_checks() -> dict[str, NotebookCheckSpec]:
    checks: dict[str, NotebookCheckSpec] = {}
    for entry in get_exercise_catalogue():
        if not has_exercise_checks(entry.exercise_key):
            continue
        checks[entry.exercise_key] = NotebookCheckSpec(
            entry.display_label,
            partial(check_exercise_summary, entry.exercise_key),
            partial(_print_notebook_results, entry.exercise_key),
        )
    return checks


def _print_notebook_results(exercise_key: str) -> None:
    print_exercise_results(run_exercise_checks(exercise_key))
