"""Public entry points for student-friendly notebook checks."""

from __future__ import annotations

from exercise_runtime_support.exercise_catalogue import (
    get_catalogue_entry,
    get_catalogue_key_for_exercise_id,
    get_exercise_catalogue,
)
from exercise_runtime_support.support_matrix import SupportRole, has_support_role

from .checks import (
    check_ex002_summary,
    check_ex003,
    check_ex004,
    check_ex005,
    check_ex006,
    check_ex007,
    run_ex002_checks,
    run_ex003_checks,
    run_ex004_checks,
    run_ex005_checks,
    run_ex006_checks,
    run_ex007_checks,
)
from .models import NotebookCheckSpec
from .reporting import (
    print_ex002_results,
    print_ex003_results,
    print_ex004_results,
    print_ex005_results,
    print_ex006_results,
    print_ex007_results,
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


def check_notebook(notebook_slug: str) -> None:
    """Run checks for a single notebook and print a summary table."""
    checks = _get_checks()
    catalogue_entry = get_catalogue_entry(notebook_slug)
    check = checks.get(catalogue_entry.exercise_key)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown notebook '{notebook_slug}'. Available: {available}")
    run_check(check)


def check_ex002_notebook() -> None:
    """Run checks for ex002 and print a grouped summary table."""
    check_notebook(get_catalogue_key_for_exercise_id(2))


def check_ex003_notebook() -> None:
    """Run checks for ex003 and print a notebook-specific summary table."""
    check_notebook(get_catalogue_key_for_exercise_id(3))


def check_ex004_notebook() -> None:
    """Run checks for ex004 and print a notebook-specific summary table."""
    check_notebook(get_catalogue_key_for_exercise_id(4))


def check_ex007_notebook() -> None:
    """Run checks for ex007 and print a notebook-specific summary table."""
    check_notebook(get_catalogue_key_for_exercise_id(7))


def _get_checks() -> dict[str, NotebookCheckSpec]:
    configured_checks = {
        2: (check_ex002_summary, _print_ex002_notebook_results),
        3: (check_ex003, lambda: print_ex003_results(run_ex003_checks())),
        4: (check_ex004, lambda: print_ex004_results(run_ex004_checks())),
        5: (check_ex005, lambda: print_ex005_results(run_ex005_checks())),
        6: (check_ex006, lambda: print_ex006_results(run_ex006_checks())),
        7: (check_ex007, lambda: print_ex007_results(run_ex007_checks())),
    }

    checks: dict[str, NotebookCheckSpec] = {}
    for entry in get_exercise_catalogue():
        if not has_support_role(entry.exercise_id, SupportRole.STUDENT_CHECKER):
            continue
        configured = configured_checks.get(entry.exercise_id)
        if configured is None:
            continue
        summary_runner, detailed_printer = configured
        checks[entry.exercise_key] = NotebookCheckSpec(
            entry.display_label,
            summary_runner,
            detailed_printer,
        )
    return checks


def _print_ex002_notebook_results() -> None:
    print_ex002_results(run_ex002_checks())
