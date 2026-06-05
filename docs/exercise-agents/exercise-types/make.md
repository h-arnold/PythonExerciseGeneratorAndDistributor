### Make Exercise Formats

Make exercises ask students to write code from scratch in tagged notebook cells. They use the same canonical exercise-local layout and the same tagged-cell grading model as modify and debug exercises:

- `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- `exercises/<construct>/<exercise_key>/notebooks/solution.ipynb`
- `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`

We normally include three to five make exercises per notebook. Each graded part should:

- explain the task clearly in nearby markdown;
- state the expected output or behaviour with one or two examples;
- keep the student work inside a tagged code cell (`exercise1`, `exercise2`, ...);
- stay within constructs the students have already been taught.

#### From scaffold to final notebook

`scripts/new_exercise.py --type make` now uses the same non-debug scaffold pattern as `--type modify`. Each tagged code cell starts with the generic output-oriented placeholder `print('TODO: Write your solution here')`, and the generated exercise-local test file uses `run_cell_and_capture_output(...)` placeholder checks. The current CLI requires `--type`; do not rely on construct-specific defaults when scaffolding.

Replace the generic prompt text and `TODO` placeholder with the real task, worked examples, and starter code for the exercise. Mirror the finished implementation in the exercise-local `notebooks/solution.ipynb`. If a later-construct make exercise genuinely asks students to define a function, that is part of the authored exercise content, not a repository-wide scaffolding contract.

#### Expected cell structure

Below is a minimal JSON example that matches the tagged-cell structure consumed by the grader and tests:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "## Exercise 1",
        "Write a program that prints the total cost for 3 apples at 2 pounds each."
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "language": "python",
        "tags": ["exercise1"]
      },
      "source": [
        "# Exercise 1",
        "# Replace the placeholder with your working solution.",
        "",
        "print('TODO: Write your solution here')"
      ]
    }
  ]
}
```

For multi-part notebooks, add a short markdown prompt before each tagged code cell. Keep the tagged cell self-contained so tests can execute it independently.

#### Testing pattern

Use the same exercise-local output-capture pattern as other non-debug exercises. A typical repository-side test module looks like this:

```python
import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
)

EXERCISE_KEY = "ex099_sequence_make_example"
NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
CACHE = RuntimeCache()


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("exercise1", "6"),
        ("exercise2", "Hello Sam"),
    ],
)
def test_make_outputs(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag, cache=CACHE)
    assert output.strip() == expected
```

For input-driven tasks, use `run_cell_with_input(...)` instead of calling `input()` interactively inside the test.

- Run the exercise-local student tests from the repository root with `uv run pytest -q exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`.
- Verify the mirrored solution notebook with `uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q`.
- Keep at least three positive checks and two edge or robustness cases per exercise where the task warrants them.
- The student notebook should still fail until the placeholder is replaced with a real solution.
- If an authored make exercise deliberately teaches functions later in the curriculum, state that explicitly in the prompt and test the named function on purpose rather than relying on an implicit `solve()` convention.
