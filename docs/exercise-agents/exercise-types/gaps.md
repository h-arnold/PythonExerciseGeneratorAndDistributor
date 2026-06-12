# Gap-Fill Exercise Formats

Gap-fill exercises present students with partially written code and ask them to supply the missing **lines or blocks**. The surrounding code provides the program structure, variable names, and context; the gaps ask students to write complete statements, expressions, or control-flow constructs that are the learning objective for that exercise. This format is the stepping stone between modify/debug exercises (where the program is essentially complete) and make exercises (where students write from scratch): students practise composing correct Python without yet having to manage the full structure of a program themselves.

**Gap count and scaffolding progression**

- Exercises 1-3: **One focused gap per exercise — a single complete line** that directly practises the target construct. All other lines are supplied. A descriptive comment above the gap names the variable to assign or the action to perform so students can concentrate entirely on writing the construct correctly.
- Exercises 4-6: **Two to four lines to write**, which may include multi-line constructs (a loop header and its body, a conditional with a matching else branch). The surround still provides setup and tear-down; students supply only the construct under focus.
- Exercises 7-10: **Larger gaps spanning multiple constructs**, potentially revisiting earlier material (casting, f-strings, arithmetic operators) alongside the new construct. Descriptive comments are reduced; students must read the surrounding code to determine what each gap requires.

**Placeholder convention**

Mark every gap with a comment. For a single-line gap, place the comment on its own line where the student's code should go:

```python
price = 0.40
quantity = 6
# YOUR CODE HERE — calculate the total cost and store it in a variable called total
print(total)
```

For a multi-line gap (a loop, a conditional, or several sequential statements), use a comment that describes the whole block:

```python
count = 1
# YOUR CODE HERE — write a while loop that prints count and increments it until count exceeds 3
```

Students delete the comment and write their code in its place. The cell will raise a `NameError` or produce wrong output until they do — that is expected and intentional.

**Notebook structure produced by the scaffolder**

- Every gap-fill notebook begins with an orientation markdown cell (title, the construct being practised, how to work with the gaps).
- For each exercise part `N`:
  - A markdown cell with a heading, a short description of the task, and the **expected output** shown in a fenced code block.
  - Optionally: a worked analogy or a reminder of the relevant syntax (keep it brief; the purpose is to jog memory, not to repeat teaching notes verbatim).
  - A code cell tagged `exerciseN` containing the partially written program. Each gap is a `# YOUR CODE HERE` comment (with a brief description of what the student must write) placed where the missing lines should go.
- An untagged scratch cell may appear at the end for self-experimentation; the grader ignores it.

Reflection cells (`explanationN`) are optional for gap-fill exercises at the author's discretion. Include them when the gap requires a conceptual choice (for example, choosing `<` versus `<=` in a loop condition) and omit them when the gap is purely syntactic.

A shortened JSON excerpt from a two-part gap-fill notebook is shown below. Exercise 1 asks for a single assignment line; Exercise 2 asks for a complete `while` loop:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "id": "a1b2c3d4", "language": "markdown" },
      "source": [
        "# Gap-Fill: Arithmetic and Loops\n",
        "In each exercise, write the missing line or lines of code where indicated.\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "e5f6a7b8", "language": "markdown" },
      "source": [
        "## Exercise 1 — Total cost\n",
        "A shop sells apples for £0.40 each.\n",
        "Write the missing line so the program prints the total cost of buying 6 apples.\n",
        "\n",
        "**Expected output:**\n",
        "```\n",
        "2.4\n",
        "```\n"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "c9d0e1f2",
        "language": "python",
        "tags": ["exercise1"]
      },
      "execution_count": null,
      "outputs": [],
      "source": [
        "price = 0.40\n",
        "quantity = 6\n",
        "# YOUR CODE HERE — calculate the total cost and store it in a variable called total\n",
        "print(total)\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "id": "g3h4i5j6", "language": "markdown" },
      "source": [
        "## Exercise 2 — Count up\n",
        "Write a while loop that prints every number from 1 to 3.\n",
        "\n",
        "**Expected output:**\n",
        "```\n",
        "1\n",
        "2\n",
        "3\n",
        "```\n"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "k7l8m9n0",
        "language": "python",
        "tags": ["exercise2"]
      },
      "execution_count": null,
      "outputs": [],
      "source": [
        "count = 1\n",
        "# YOUR CODE HERE — write a while loop that prints count and increments it until count exceeds 3\n"
      ]
    }
  ]
}
```

**Tag requirements**

- Every tagged code cell **must** carry exactly one `exerciseN` tag.
- Optional reflection cells **must** carry the matching `explanationN` tag.
- Tags are case-sensitive: `exercise1`, not `Exercise1` or `exercise_1`.

**Gap validity rules**

1. **Test output, not spelling**. Because students write whole lines there will often be several correct completions (e.g. `total = price * quantity` and `total = 0.40 * 6` are both correct). Test the printed output rather than the source text so the tests do not reject equivalent valid solutions. Use AST checks only when the task explicitly requires a specific construct (e.g. a `while` loop rather than a `for` loop).
2. **Gap comments describe what to compute, not how**. State the required result or variable name ("store the result in a variable called `total`") but do not name the operator, method, or construct the student should use.
3. **Each gap cell must error or produce wrong output when unmodified** so the student-variant tests fail until the student acts.

## Critical Principles for Student-Facing Gap-Fill Exercises

### 1. **Target the gap, not the surrounding code**

The code around the gap should be as familiar and readable as possible. If the goal is to practise `while` loops, do not also introduce dictionary syntax in the same cell for the first time.

### 2. **State the task in terms of behaviour, not mechanism**

Describe what the program should do ("print the number of times the loop ran") rather than hinting at the solution ("use a counter variable").

### 3. **Keep the expected output unambiguous**

Show the exact stdout string, including spacing and punctuation, inside a fenced code block. Students should be able to verify their solution by visual inspection before running the tests.

### 4. **Maintain a gradual gradient from one line to many lines**

Early exercises ask for a single assignment or print statement. Their value is in the habit of writing the whole construct rather than recognising it in existing code, and in reinforcing correct syntax through repetition. Resist the temptation to make early gaps large "to save time"; the progression is the point.

### 5. **Solution notebooks pair corrected code with teaching notes**

- Student notebook (`notebooks/student.ipynb`): partial code with `# YOUR CODE HERE` comments marking each gap, neutral task prompts, expected output.
- Solution notebook (`notebooks/solution.ipynb`): all gaps resolved, with optional inline comments explaining the choice of operator or construct. As with other exercise types, prefer stepwise implementations — one transformation per line — so learners can trace how each gap contributes to the final result.

### 6. **Do not conflate gap-fill with modify**

In a modify exercise the starter code is _complete and working_; the student changes the behaviour. In a gap-fill exercise the starter code is _incomplete_; the student provides the missing piece to make it work. Both types are useful but serve different cognitive goals. Do not mix the formats within one tagged cell.

## Testing Guidance (required)

- Use `run_cell_and_capture_output()` as the primary correctness check unless the task requires user input, in which case use `run_cell_with_input()`.
- When a gap accepts meaningful variation (e.g., different valid variable names), test the output rather than the source code. When the gap must be a specific construct (e.g., an `f`-string rather than string concatenation), add an AST check using `extract_tagged_code()`.
- The student-variant tests **must fail** against the unmodified scaffold (the `# YOUR CODE HERE` comment left in place). Confirm this before publishing the exercise.

Example test module for a gap-fill exercise:

```python
import ast

import pytest

from exercise_runtime_support.exercise_framework import (
    RuntimeCache,
    extract_tagged_code,
    get_explanation_cell,
    resolve_exercise_notebook_path,
    run_cell_and_capture_output,
    run_cell_with_input,
)
from exercise_runtime_support.exercise_framework.expectations_helpers import (
    is_valid_explanation,
)
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = "ex099_sequence_gaps_arithmetic"
_ex099 = load_exercise_test_module(EXERCISE_KEY, "expectations")
_NOTEBOOK_PATH = resolve_exercise_notebook_path(EXERCISE_KEY)
_CACHE = RuntimeCache()


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("exercise1", _ex099.EX099_EXPECTED_OUTPUT[1]),
        ("exercise2", _ex099.EX099_EXPECTED_OUTPUT[2]),
        ("exercise3", _ex099.EX099_EXPECTED_OUTPUT[3]),
    ],
)
def test_exercise_output(tag: str, expected: str) -> None:
    output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)
    assert output == expected


def test_exercise4_uses_fstring() -> None:
    """Gap must be completed using an f-string, not concatenation."""
    code = extract_tagged_code(_NOTEBOOK_PATH, tag="exercise4", cache=_CACHE)
    tree = ast.parse(code)
    has_fstring = any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))
    assert has_fstring, "exercise4 must use an f-string"


def test_exercise5_handles_input() -> None:
    output = run_cell_with_input(
        _NOTEBOOK_PATH,
        tag="exercise5",
        inputs=["12"],
        cache=_CACHE,
    )
    assert _ex099.EX099_EXPECTED_OUTPUT[5] in output


@pytest.mark.parametrize("tag", [f"explanation{i}" for i in _ex099.EX099_EXPLANATION_PARTS])
def test_explanations_have_content(tag: str) -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=tag)
    assert is_valid_explanation(
        explanation,
        min_length=_ex099.EX099_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=_ex099.EX099_PLACEHOLDER_PHRASES,
    )
```

## Summary Checklist for Authoring Gap-Fill Exercises

- [ ] Every tagged cell contains at least one `# YOUR CODE HERE` gap comment.
- [ ] Gap comments describe what to compute or produce, not the construct or operator to use.
- [ ] The scaffold errors or produces wrong output when unmodified (student-variant tests fail).
- [ ] Surrounding code is as familiar as possible given the construct level.
- [ ] Expected output is shown verbatim in the markdown cell immediately above the code cell.
- [ ] Exercise titles are neutral (e.g., "Exercise 1 — Total cost"), not solution-revealing ("Exercise 1 — Use multiplication").
- [ ] Gap size escalates deliberately: one line early, multi-line constructs and revisited concepts late.
- [ ] Student notebook (`notebooks/student.ipynb`) contains the placeholder code; solution notebook (`notebooks/solution.ipynb`) mirrors the tag structure with all gaps resolved.
- [ ] Tests verify the corrected behaviour per tagged cell; AST checks are included where the gap requires a specific construct.
- [ ] The unmodified student scaffold fails its own tests.
