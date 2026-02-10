"""Exercise testing framework public surface."""

from tests.exercise_framework.api import (
    EX002_SLUG,
    ExerciseCheckResult,
    NotebookCheckResult,
    run_all_checks,
    run_detailed_ex002_check,
    run_notebook_check,
)
from tests.exercise_framework.paths import resolve_notebook_path
from tests.exercise_framework.runtime import (
    RuntimeCache,
    exec_tagged_code,
    extract_tagged_code,
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

__all__ = [
    "EX002_SLUG",
    "ExerciseCheckResult",
    "NotebookCheckResult",
    "RuntimeCache",
    "exec_tagged_code",
    "extract_tagged_code",
    "get_explanation_cell",
    "resolve_notebook_path",
    "run_all_checks",
    "run_cell_and_capture_output",
    "run_cell_with_input",
    "run_detailed_ex002_check",
    "run_notebook_check",
]
