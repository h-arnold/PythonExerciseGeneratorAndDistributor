#### Debugging Exercise Formats

Students should be presented with a mixture of syntactic and logical errors. Where possible, choose mistakes that novice programmers genuinely make when learning the targeted construct.

**Error count progression**:

- Exercises 1-5: Exactly **one** error per exercise to build confidence and focus attention.
- Exercises 6-10: Increase difficulty gradually; later parts can contain 2-3 coordinated bugs when it supports the learning goal.
- Errors should be **realistic** whenever possible. If a contrived bug is needed to highlight the objective, keep the surrounding code authentic.

**Notebook structure produced by the scaffolder**

- Every debug notebook starts with an orientation markdown cell (title, what to practise, how to work).
- For each exercise part `N`, the generator emits:
  - A markdown cell describing the goal and showing the **expected output**.
  - A buggy code cell tagged `exerciseN` that students edit directly.
  - A markdown reflection cell tagged `explanationN` prompting the student to record what went wrong.
- After the final exercise, an optional untagged scratch cell can remain for experiments; the grader ignores it.

A shortened JSON excerpt from a two-part debug notebook is shown below. It reflects the structure emitted by `scripts/new_exercise.py --type debug` and required by the tests:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "# Debug Syntax Errors
",
        "In this notebook, you'll fix common syntax errors...
"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "## Exercise 1 — Print a message
",
        "**Expected output:**
",
        "```
",
        "Hello World!
",
        "```"
      ]
    },
    {
      "cell_type": "code",
      "metadata": { "language": "python", "tags": ["exercise1"] },
      "source": [
        "print("Hello World!""
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown", "tags": ["explanation1"] },
      "source": [
        "### What actually happened
",
        "Describe briefly what happened when you ran the code.
"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "## Exercise 2 — Join two words
",
        "**Expected output:**
",
        "```
",
        "Learning Python
",
        "```"
      ]
    },
    {
      "cell_type": "code",
      "metadata": { "language": "python", "tags": ["exercise2"] },
      "source": [
        "print("Learning" "Python")"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown", "tags": ["explanation2"] },
      "source": [
        "### What actually happened
",
        "Explain the error or incorrect output you observed.
"
      ]
    }
  ]
}
```

**Tag requirements**

- Each buggy code cell that the grader executes **must** carry exactly one `exerciseN` tag. Tests such as `test_ex002_sequence_modify_basics.py` and `test_ex004_sequence_debug_syntax.py` rely on these tags when calling `run_cell_and_capture_output()`.
- The reflection markdown cell after each buggy implementation **must** carry the matching `explanationN` tag. Automated checks use `get_explanation_cell()` to enforce this.
- Tags are case-sensitive; do not use variations like `Exercise1` or `exercise_1`.

**Explanation expectations**

- Students must rewrite the code so it behaves correctly **and** complete the explanation cell with a meaningful summary of the bug. Tests expect more than 10 non-whitespace characters (see `MIN_EXPLANATION_LENGTH = 10` in `tests/test_ex004_sequence_debug_syntax.py`).
- The student-facing explanation prompt stays neutral. Teacher-facing clarifications belong in the mirrored solutions notebook, which keeps the same tags but may include fuller commentary.

## Critical Principles for Student-Facing Debugging Exercises

### 1. **Never reveal the bug in the exercise title**

Students must discover the issue themselves.

❌ **Bad**: "Exercise 1 — Missing closing parenthesis"

✅ **Good**: "Exercise 1 — Print a message"

### 2. **Keep prompts and `What actually happened` neutral**

The buggy code cell and its surrounding markdown should only define the goal and expected output. Avoid hinting at the fix or naming the error category.

### 3. **Every exercise includes a genuine bug**

The buggy cell must either raise an error or emit incorrect output until the student fixes it. Working code masquerading as a debug exercise fails the learning objective and will cause tests that expect changes to be pointless.

### 4. **No hint comments in the buggy code**

Remove comments that point out the fault (for example, `# missing brackets`). Let the behaviour itself signal the problem.

### 5. **Separate student and teacher messaging**

- Student notebook (`notebooks/exNNN_slug.ipynb`): neutral titles and prompts, buggy code, concise reflection prompt.
- Solutions notebook (`notebooks/solutions/exNNN_slug.ipynb`): includes the corrected code plus optional teaching notes, keeping the same tag structure so tests can run against either version via `PYTUTOR_NOTEBOOKS_DIR`.

### 6. **Progress difficulty deliberately**

Early parts typically focus on single syntax slips; later parts can combine syntax and logic bugs (for example, a missing cast *and* a string format error) as long as the resulting debugging task stays manageable for Years 9-11.

## Testing guidance (required)

- Use helpers from `tests/notebook_grader.py` to execute tagged cells and capture output. They respect the `PYTUTOR_NOTEBOOKS_DIR` override so the same checks run against student and solution notebooks.
- Verify both the corrected programme behaviour and the filled-in explanation cells.
- For input-driven exercises, prefer `run_cell_with_input()` to provide deterministic inputs.

Example pattern for a debug exercise test module:

```python
import pytest

from tests.notebook_grader import (
    get_explanation_cell,
    run_cell_and_capture_output,
    run_cell_with_input,
)

NOTEBOOK_PATH = "notebooks/ex004_sequence_debug_syntax.ipynb"
MIN_EXPLANATION_LENGTH = 10

@pytest.mark.parametrize("tag,expected", [
    ("exercise1", "Hello World!"),
    ("exercise2", "I like Python"),
])
def test_exercise_output(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)
    assert expected in output


def test_exercise7_handles_input() -> None:
    output = run_cell_with_input(NOTEBOOK_PATH, tag="exercise7", inputs=["5"])
    assert "10" in output


@pytest.mark.parametrize("tag", [f"explanation{i}" for i in range(1, 11)])
def test_explanations_have_content(tag: str) -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=tag)
    assert len(explanation.strip()) > MIN_EXPLANATION_LENGTH
```

## Summary checklist for authoring debug exercises

- [ ] Every exercise cell contains a real bug (syntax, runtime, or logic).
- [ ] Exercise titles and prompts remain neutral (no spoilers, no hints).
- [ ] Buggy code cells are tagged `exercise1` … `exerciseN` and contain executable code.
- [ ] Reflection markdown cells are tagged `explanation1` … `explanationN` and the default text encourages students to describe what went wrong.
- [ ] Solution notebooks mirror the structure and tags while demonstrating the corrected code.
- [ ] Tests verify the corrected behaviour *and* enforce explanation content using the helpers in `tests/notebook_grader.py`.
