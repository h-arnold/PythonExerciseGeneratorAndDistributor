### Make Exercise Formats

Make exercises are the final step in each construct sequence: students build a working solution from scratch instead of fixing or adapting existing code. These notebooks expect learners to apply everything introduced in earlier debug and modify activities, so keep the prompts focused, scaffolded, and explicit about the required behaviour.

We normally include three to five make exercises per notebook. Each graded cell must:

- provide a concise problem description and 1–2 worked examples in the surrounding markdown;
- define a small, pure function (conventionally `solve()` unless another name is pedagogically clearer);
- expose the implementation inside a tagged cell (`metadata.tags: ["exerciseN"]`) so the grader can import and execute it.

#### From scaffold to final notebook

`scripts/new_exercise.py --type make` (or omitting `--type` with sequence constructs) generates a placeholder notebook where each tagged cell contains `print('TODO: Write your solution here')`. Replace that placeholder with the function skeleton the students will complete, and mirror the change in `notebooks/solutions/` with the finished solution. The generator keeps the metadata ids and language fields valid—preserve them when editing cells.

#### Expected cell structure

Below is a minimal JSON example that matches the structure consumed by the grader and tests. Adjust the docstring usage to match the construct: omit it before the Functions unit; include it afterwards.

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "# Exercise 1 — Sum the squares",
        "Implement the function described below."
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "### Task",
        "Create `solve(nums)` that returns the sum of the squares of the integers in `nums`.",
        "",
        "### Examples",
        "```\nsolve([1, 2, 3]) -> 14\nsolve([-2, 4]) -> 20\n```"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "language": "python",
        "tags": ["exercise1"]
      },
      "source": [
        "# Students implement solve() in this tagged cell",
        "def solve(nums: list[int]) -> int:",
        "    \"\"\"Return the sum of squares for the provided integers.\"\"\"",
        "    raise NotImplementedError("Implement solve()")"
      ]
    }
  ]
}
```

Copy this cell into the solution notebook and replace the `NotImplementedError` with the completed implementation and any supporting helpers.

#### Testing pattern

Tests for make exercises should import `exec_tagged_code` and call the function directly, exercising multiple positive and edge cases. A typical pattern is shown below:

```python
import pytest

from tests.exercise_framework import runtime

NOTEBOOK_PATH = "notebooks/ex099_sequence_make_example.ipynb"


def _solve(tag: str, *args, **kwargs):
    ns = runtime.exec_tagged_code(NOTEBOOK_PATH, tag=tag)
    assert "solve" in ns, "solve() must be defined in the tagged cell"
    return ns["solve"](*args, **kwargs)


@pytest.mark.parametrize(
    "values, expected",
    [([1, 2, 3], 14), ([-2, 4], 20), ([0], 0)],
)
def test_sum_of_squares(values, expected):
    assert _solve("exercise1", values) == expected


def test_handles_empty_list():
    assert _solve("exercise1", []) == 0
```

- Run the suite with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q` to confirm the solution notebook passes.
- Keep at least three positive checks and two edge/robustness cases per exercise, following the testing framework guidance.
- Ensure the student notebook still fails after reverting to `NotImplementedError` so learners must supply the logic.

Once tests pass against the solution mirror, update the student notebook (usually via copy/paste from the solution while reintroducing `NotImplementedError`) and double-check the tagged cells remain unchanged apart from the placeholder.
