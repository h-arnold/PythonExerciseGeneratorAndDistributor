# Debugging Exercise Formats

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

A shortened JSON excerpt from a finished two-part debug notebook is shown below. It illustrates the exercise-local tag and cell structure that `scripts/new_exercise.py --type debug` scaffolds and that the tests rely on after you replace the generic placeholders with real exercise content:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "id": "7a1f4c2d", "language": "markdown" },
      "source": [
        "# Debug Syntax Errors\n",
        "In this notebook, you'll fix common syntax errors...\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "1d93b6ef", "language": "markdown" },
      "source": [
        "## Exercise 1 — Print a message\n",
        "**Expected output:**\n",
        "```\n",
        "Hello World!\n",
        "```"
      ]
    },
    {
      "cell_type": "code",
      "metadata": { "id": "e4cb98a1", "language": "python", "tags": ["exercise1"] },
      "execution_count": null,
      "outputs": [],
      "source": [
        "print(\"Hello World!\"\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "0fb3d217", "language": "markdown", "tags": ["explanation1"] },
      "source": [
        "### What actually happened\n",
        "Describe briefly what happened when you ran the code.\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "9a6d50ce", "language": "markdown" },
      "source": [
        "## Exercise 2 — Join two words\n",
        "**Expected output:**\n",
        "```\n",
        "Learning Python\n",
        "```"
      ]
    },
    {
      "cell_type": "code",
      "metadata": { "id": "3f2ab471", "language": "python", "tags": ["exercise2"] },
      "execution_count": null,
      "outputs": [],
      "source": [
        "print(\"Learning\" \"Python\")\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "b82a6405", "language": "markdown", "tags": ["explanation2"] },
      "source": [
        "### What actually happened\n",
        "Explain the error or incorrect output you observed.\n"
      ]
    }
  ]
}
```

**Tag requirements**

- Each buggy code cell that the grader executes **must** carry exactly one `exerciseN` tag. Tests such as [exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py](../../exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py) and [exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py](../../exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py) rely on these tags when calling `run_cell_and_capture_output()`.
- The reflection markdown cell after each buggy implementation **must** carry the matching `explanationN` tag. Automated checks use `get_explanation_cell()` to enforce this.
- Tags are case-sensitive; do not use variations like `Exercise1` or `exercise_1`.

**Explanation expectations**

- Students must rewrite the code so it behaves correctly **and** complete the explanation cell with a meaningful summary of the bug. Fresh scaffolds can start with local placeholder explanation-validation constants in the generated test module, but once the exercise contract stabilises, move those values into shared expectations rather than inlining them in individual tests. Ex004 shows the target pattern: the live minimum is `EX004_MIN_EXPLANATION_LENGTH = 50` in [tests/exercise_expectations/ex004_sequence_debug_syntax.py](../../tests/exercise_expectations/ex004_sequence_debug_syntax.py), and [exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py](../../exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py) imports that value.
- The student-facing explanation prompt stays neutral. Teacher-facing clarifications belong in the exercise-local solution notebook, which keeps the same tags but may include fuller commentary.

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

- Student notebook (`notebooks/student.ipynb` inside the exercise folder): neutral titles and prompts, buggy code, concise reflection prompt.
- Solution notebook (`notebooks/solution.ipynb` inside the same exercise folder): includes the corrected code plus optional teaching notes, keeping the same tag structure so tests can run against either version via the explicit variant contract (`--variant student|solution`). When writing the corrected code, favour stepwise, one-change-per-line examples so students can observe how variables change (for example, cast the input to `age` on one line, then increment with `age = age + 1` on the next). Avoid compressing multiple transformations into single, compact expressions which hide intermediate steps.

### 6. **Progress difficulty deliberately**

Early parts typically focus on single syntax slips; later parts can combine syntax and logic bugs (for example, a missing cast *and* a string format error) as long as the resulting debugging task stays manageable for Years 9-11.

## Testing guidance (required)

- Use helpers from `exercise_runtime_support.exercise_framework` to execute tagged cells and capture output. They respect the active variant contract so the same checks run against student and solution notebooks.
- Verify both the corrected programme behaviour and the filled-in explanation cells.
- For input-driven exercises, prefer `run_cell_with_input()` to provide deterministic inputs.

Example pattern for a mature debug exercise test module:

```python
import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from tests.exercise_expectations import ex004_sequence_debug_syntax as ex004

EXERCISE_KEY = "ex004_sequence_debug_syntax"
NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
CACHE = RuntimeCache()

@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("exercise1", ex004.EX004_EXPECTED_SINGLE_LINE[1]),
        ("exercise2", ex004.EX004_EXPECTED_SINGLE_LINE[2]),
    ],
)
def test_exercise_output(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag, cache=CACHE)
    assert output.strip() == expected


def test_exercise7_handles_input() -> None:
    output = run_cell_with_input(
        NOTEBOOK_PATH,
        tag="exercise7",
        inputs=["5"],
        cache=CACHE,
    )
    assert ex004.EX004_PROMPT_STRINGS[7] in output
    assert ex004.EX004_FORMAT_VALIDATION[7] in output


@pytest.mark.parametrize("tag", [f"explanation{i}" for i in range(1, 11)])
def test_explanations_have_content(tag: str) -> None:
    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=tag)
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )
```

## Summary checklist for authoring debug exercises

- [ ] Every exercise cell contains a real bug (syntax, runtime, or logic).
- [ ] Exercise titles and prompts remain neutral (no spoilers, no hints).
- [ ] Buggy code cells are tagged `exercise1` … `exerciseN` and contain executable code.
- [ ] Reflection markdown cells are tagged `explanation1` … `explanationN` and the default text encourages students to describe what went wrong.
- [ ] Solution notebooks mirror the structure and tags while demonstrating the corrected code.
- [ ] Tests verify the corrected behaviour *and* enforce explanation content using the helpers in `exercise_runtime_support.exercise_framework`.
