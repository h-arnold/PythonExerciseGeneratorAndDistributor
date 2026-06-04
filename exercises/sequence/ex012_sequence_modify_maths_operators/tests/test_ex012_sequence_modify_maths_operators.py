from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
)

_EXERCISE_KEY = 'ex012_sequence_modify_maths_operators'
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


def _run_and_capture(tag: str) -> str:
    """Execute the tagged cell and capture its print output."""
    return run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)


@pytest.mark.parametrize('tag', ['exercise1', 'exercise2', 'exercise3', 'exercise4', 'exercise5', 'exercise6', 'exercise7', 'exercise8', 'exercise9', 'exercise10'])
def test_exercise_cells_execute(tag: str) -> None:
    """Verify each tagged cell executes without error."""
    output = _run_and_capture(tag)
    assert output.strip(), f'{tag} should produce output'
    assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'
