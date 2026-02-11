"""Public entry points for student-friendly notebook checks."""

from __future__ import annotations

from .checks import (
    check_ex001,
    check_ex002_summary,
    check_ex003,
    check_ex004,
    check_ex005,
    check_ex006,
    run_ex002_checks,
    run_ex003_checks,
    run_ex004_checks,
    run_ex005_checks,
    run_ex006_checks,
)
from .models import NotebookCheckSpec
from .reporting import (
    print_ex002_results,
    print_ex003_results,
    print_ex004_results,
    print_ex005_results,
    print_ex006_results,
    print_results,
    run_check,
    run_checks,
)

_EX001_SLUG = "ex001_sanity"
_EX002_SLUG = "ex002_sequence_modify_basics"
_EX003_SLUG = "ex003_sequence_modify_variables"
_EX004_SLUG = "ex004_sequence_debug_syntax"
_EX005_SLUG = "ex005_sequence_debug_logic"
_EX006_SLUG = "ex006_sequence_modify_casting"
_NOTEBOOK_ORDER = [
    _EX001_SLUG,
    _EX002_SLUG,
    _EX003_SLUG,
    _EX004_SLUG,
    _EX005_SLUG,
    _EX006_SLUG,
]


def check_exercises() -> None:
    """Run a simple check for exercises 1-6 and print a summary table."""
    checks = _get_checks()
    ordered_checks = [checks[slug] for slug in _NOTEBOOK_ORDER]
    results = run_checks(ordered_checks)
    print_results(results)


def check_notebook(notebook_slug: str) -> None:
    """Run checks for a single notebook and print a summary table."""
    checks = _get_checks()
    check = checks.get(notebook_slug)
    if check is None:
        available = ", ".join(sorted(checks))
        raise ValueError(f"Unknown notebook '{notebook_slug}'. Available: {available}")
    run_check(check)


def check_ex002_notebook() -> None:
    """Run checks for ex002 and print a grouped summary table."""
    check_notebook(_EX002_SLUG)


def check_ex003_notebook() -> None:
    """Run checks for ex003 and print a notebook-specific summary table."""
    check_notebook(_EX003_SLUG)


def check_ex004_notebook() -> None:
    """Run checks for ex004 and print a notebook-specific summary table."""
    check_notebook(_EX004_SLUG)


def _get_checks() -> dict[str, NotebookCheckSpec]:
    return {
        _EX001_SLUG: NotebookCheckSpec("ex001 Sanity", check_ex001),
        _EX002_SLUG: NotebookCheckSpec(
            "ex002 Sequence Modify Basics",
            check_ex002_summary,
            _print_ex002_notebook_results,
        ),
        _EX003_SLUG: NotebookCheckSpec(
            "ex003 Sequence Modify Variables",
            check_ex003,
            lambda: print_ex003_results(run_ex003_checks()),
        ),
        _EX004_SLUG: NotebookCheckSpec(
            "ex004 Debug Syntax Errors",
            check_ex004,
            lambda: print_ex004_results(run_ex004_checks()),
        ),
        _EX005_SLUG: NotebookCheckSpec(
            "ex005 Debug Logical Errors",
            check_ex005,
            lambda: print_ex005_results(run_ex005_checks()),
        ),
        _EX006_SLUG: NotebookCheckSpec(
            "ex006 Casting and Type Conversion",
            check_ex006,
            lambda: print_ex006_results(run_ex006_checks()),
        ),
    }


def _print_ex002_notebook_results() -> None:
    print_ex002_results(run_ex002_checks())
