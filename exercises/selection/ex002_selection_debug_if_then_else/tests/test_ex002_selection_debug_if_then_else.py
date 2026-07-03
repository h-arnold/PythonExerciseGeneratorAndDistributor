from __future__ import annotations

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)

_EXERCISE_KEY = 'ex002_selection_debug_if_then_else'
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()
_MIN_EXPLANATION_LENGTH = 50
_PLACEHOLDER_PHRASES = (
    'describe what',
    'describe briefly',
    'your explanation',
    'explain here',
    'write your',
    'todo',
    '...',
    'include any error',
)


def _run_with_input(tag: str, inputs: list[str]) -> str:
    """Execute the tagged cell with input and capture its print output."""
    return run_cell_with_input(_NOTEBOOK_PATH, tag=tag, inputs=inputs, cache=_CACHE)


# Test cases for each exercise with appropriate input values
EXERCISE_INPUTS = {
    'exercise1': ['7'],           # Odd number
    'exercise2': ['6'],           # Radius 6, area > 100
    'exercise3': ['9'],           # Divisible by 3
    'exercise4': ['35'],          # 35^2 = 1225 > 1000
    'exercise5': ['blue'],        # Favourite colour
    'exercise6': ['5678'],        # Wrong PIN
    'exercise7': ['8'],           # Correct answer (3+5)
    'exercise8': ['140'],         # Tall enough to ride
    'exercise9': ['60'],          # Score >= 50
    'exercise10': ['Bob'],        # Name is Bob
    'exercise11': ['90'],         # Score >= 90 for Distinction
    'exercise12': ['12'],         # Age <= 12 for Child
    'exercise13': ['5'],          # Positive number
    'exercise14': ['python'],     # Correct password
    'exercise15': ['35'],         # Hot temperature
    'exercise16': ['7'],          # Odd number
    'exercise17': ['-5'],         # Invalid age
    'exercise18': ['95'],         # Excellent score
    'exercise19': ['10'],         # Number >= 10
    'exercise20': ['75'],         # Score >= 50
}


@pytest.mark.parametrize('tag', list(EXERCISE_INPUTS.keys()))
def test_exercise_cells_execute(tag: str) -> None:
    """Verify each tagged cell executes without error."""
    inputs = EXERCISE_INPUTS[tag]
    output = _run_with_input(tag, inputs)
    assert output.strip(), f'{tag} should produce output'
    assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'


# Explanation cell checks for debug exercises

EXPLANATION_TAGS = [f'explanation{i}' for i in range(1, 20 + 1)]


@pytest.mark.parametrize('tag', EXPLANATION_TAGS)
def test_explanations_have_content(tag: str) -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=tag)
    assert is_valid_explanation(
        explanation,
        min_length=_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_PLACEHOLDER_PHRASES,
    )
