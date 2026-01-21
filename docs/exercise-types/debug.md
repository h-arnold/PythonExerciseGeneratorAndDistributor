#### Debugging Exercise Formats

Students should be presented with a mixture of syntactic and logical errors. Where possible, the bugs should be common or typical errors that beginners make when learning this structure.

**Error count progression**:

- Exercises 1-5: Each should contain exactly **one error** to help students build confidence and focus on a single issue at a time.
- Exercises 6-10: Gradually increase the number of errors where possible and appropriate to the task (e.g., exercise 6 might have 1-2 errors, exercise 10 might have 2-3).
- Errors should be **realistic** (what students would actually write) whenever possible. If realistic errors aren't appropriate for the learning objective, then use contrived errors that serve the pedagogical goal.

**CRITICAL: Every Exercise Must Contain an Actual Bug**

There should be no "working code" exercises disguised as debug tasks. If the code runs without error and produces the correct output, it is not a debugging exercise.

**Common syntactic and logical errors (examples)**

- **Selection (if/elif/else):**
  - Syntax: forgetting the colon, e.g. `if x > 0` -> SyntaxError; correct: `if x > 0:`
  - Logical: wrong branch order, e.g. `if x > 0: ... elif x > 10: ...` — the `elif` never runs for `x > 10` because the first condition already matches.

- **Iteration (for/while):**
  - Syntax: missing indentation after the loop header causes IndentationError.
  - Logical: off-by-one or infinite loops, e.g. `while i >= 0:` without decrementing `i` causes an infinite loop.
  - Logical: mutating a list while iterating, e.g. `for x in items: items.remove(x)`, which skips elements.

- **Data types & casting:**
  - Logical/runtime: `input()` returns a string — `n = input(); total = n + 5` leads to concatenation or TypeError; cast with `int()`/`float()` as appropriate.
  - Runtime: passing `'3.5'` to `int()` raises ValueError — choose the right converter.

- **Lists:**
  - Logical: index errors (`mylist[3]` when length is 3 -> IndexError).
  - Semantic: using parentheses `()` instead of brackets `[]` creates a tuple rather than a list.
  - Logical: aliasing vs copying, e.g. `b = a` shares the same list; use `a.copy()` when you need a separate copy.

- **Dictionaries:**
  - Logical: `d['key']` on a missing key raises KeyError; prefer `d.get('key')` or `if 'key' in d:`.
  - TypeError: using an unhashable key (like a list) fails — keys must be immutable/hashable.

- **Functions & return values:**
  - Logical: forgetting `return` (function implicitly returns `None`).
  - Semantic: referencing the function object instead of calling it (`f` vs `f()`).
  - Logical: mutable default arguments, e.g. `def f(x, lst=[])` reuses the same list across calls.

- **File handling:**
  - Logical: opening a file with `'w'` unintentionally truncates it; use `'a'` to append when appropriate.
  - Resource bug: not using `with open(...) as f:` can leave files open when exceptions occur.

- **Exception handling:**
  - Logical: overly broad `except:` hides unrelated bugs — prefer explicit exceptions like `except ValueError:`.
  - Logical: catching and ignoring exceptions (`except: pass`) masks failures that tests should detect.

Debugging exercises should be presented to students as a small notebook with a clear, student-facing structure. The grader will execute only the single code cell tagged `exercise1` (or `exerciseN` for multi-part notebooks). The recommended layout for a single-part debug exercise is:

1. A *markdown* cell that describes what the program should do and **shows the expected output** (do not tell the student how to fix the code; only display the correct output that should appear when the corrected code is run).
2. A *code* cell containing the buggy implementation. This *code* cell should be tagged with `exercise1` so students edit it directly to fix the behaviour.
3. A *markdown* cell titled **"What actually happened"** that prompts the student to describe what occurred when they ran (or attempted to run) the code. This markdown cell must include the metadata tag `explanation1` (or `explanationN` for multi-part notebooks).

Below is a JSON-formatted example that matches the notebook format used by the generator and the test harness. Notice the order: expected-output markdown, the buggy `exercise1` code cell, then the `explanation1` markdown cell:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown" },
      "source": [
        "# Exercise 1 — Expected behaviour",
        "The function below should return the sum of a list of numbers.\n",
        "### Expected output\n",
        "``\n",
        "buggy_sum([1, 2, 3])  -> 6\n",
        "``"
      ]
    },
    {
      "cell_type": "code",
      "metadata": { "language": "python", "tags": ["exercise1"] },
      "source": [
        "# BUGGY IMPLEMENTATION (students edit this tagged cell)\n",
        "def buggy_sum(nums):\n",
        "    total = 0\n",
        "    for n in nums:\n",
        "        total = n  # bug: should accumulate, not replace\n",
        "    return total\n"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": { "language": "markdown", "tags": ["explanation1"] },
      "source": [
        "### What actually happened\n",
        "Describe briefly what happened when you ran the code (include any error messages or incorrect output).",
        "\n",
        "Example: `I got 3 instead of 6 because the loop replaces rather than accumulates.`"
      ]
    }
  ]
}
```

Testing guidance (required):

- Tests for debug exercises should still verify the corrected behaviour by executing the tagged `exercise1` cell and checking function outputs.
- Additionally, tests must assert that the student's explanation in the `explanationN` markdown cell is meaningfully filled in. For now, tests should check that the explanation is more than 10 characters (non-whitespace).

Example test helper to read an explanation cell from a notebook using the standard library:

```python
import json

def _get_explanation(notebook_path: str, tag: str = "explanation1") -> str:
    nb = json.load(open(notebook_path, "r", encoding="utf-8"))
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            return "".join(cell.get("source", []))
    raise AssertionError(f"No explanation cell with tag {tag}")

# Example test
def test_explanation_has_content():
    explanation = _get_explanation("notebooks/ex004_sequence_debug_syntax.ipynb", tag="explanation1")
    assert len(explanation.strip()) > 10, "Explanation must be more than 10 characters"
```

## Critical Principles for Student-Facing Debugging Exercises

### 1. **NEVER Reveal the Bug in the Exercise Title**

Students must discover the bug themselves. Telling them what to fix defeats the learning objective.

❌ **Bad** (reveals the bug):

- "Exercise 1 — Missing closing parenthesis"
- "Exercise 3 — Typo in variable name"
- "Exercise 5 — Missing quotes around string"

✅ **Good** (neutral, student discovers the bug):

- "Exercise 1 — Print a message"
- "Exercise 3 — Print a greeting"
- "Exercise 5 — Use a variable"

### 2. **NEVER Explain What the Bug Is in the Prompt or Code**

The buggy code cell should NOT include hints or descriptions of what's wrong. Only show:

- What the program should do (briefly, neutral)
- What the expected output is
- The buggy code itself (clean, no hint comments)

❌ **Bad** (explains the bug in title and prompt):

```markdown
## Exercise 2 — Missing quotes around string

**What's wrong?** Text must be wrapped in quotes.

**Buggy code:**
```python
print(I like Python)
```

```

✅ **Good** (neutral, requires investigation):

```markdown
## Exercise 2 — Print a message

**Expected output:**
```

I like Python

```

**Buggy code:**
```python
print(I like Python)
```

```

### 3. **EVERY Exercise Must Contain an Actual Bug**

Each exercise should fail to run (syntax error, runtime error) or produce incorrect output. There should be NO "working code" exercises disguised as debug tasks.

❌ **Bad** (no bug—code works perfectly):

```markdown
## Exercise 7 — Greet the user

**Expected output:**
```

Hello world

```

**Buggy code:**
```python
print("Hello world")
```

```

This code runs without error and produces the correct output—it's not a debugging exercise!

### 4. **Keep Student Notebook Prompts Neutral**

Explanation cells should prompt students to investigate and reflect, not give hints.

❌ **Bad** (hints at the solution):

```markdown
### What actually happened

Describe what error you got. Fix the code above.

*Hint: Check if all parentheses are matched.*
```

✅ **Good** (neutral, invites investigation):

```markdown
### What actually happened

Describe what error you got or what incorrect output appeared.
```

### 5. **The Solutions Notebook Is Where You Explain the Bugs**

- **Student notebook (`notebooks/exNNN.ipynb`)**: Neutral titles and prompts. Buggy code with NO hints. Students must investigate to discover the bug.
- **Solutions notebook (`notebooks/solutions/exNNN.ipynb`)**: CAN include detailed explanations in markdown cells. Teachers read these to understand the pedagogical intent. Students never see this version.

Example comparison:

**Student notebook:**

```markdown
## Exercise 4 — Multiply two numbers

**Expected output:**
```

50

```

**Buggy code:**
```python
print(5 + 10)
```

```

**Solutions notebook (for teacher reference):**
```markdown
## Exercise 4 — Multiply two numbers

**Expected output:**
```

50

```

**Buggy code:**
```python
print(5 + 10)
```

### What's actually wrong

The code uses `+` (addition) instead of `*` (multiplication). This is a common mistake when students are first learning operators.

### Corrected code

```python
print(5 * 10)
```

### Teaching notes

Common misconceptions:

- Students may try `/` (division) instead
- Some may not understand why Python doesn't infer the correct operator

Reinforce: Python requires explicit operator choice; it cannot guess your intent from context.

```

### 6. **Do NOT Include Hint Comments in Student Buggy Code**

Buggy code should be clean—no comments revealing what's wrong.

❌ **Bad** (reveals the bug):

```python
phrase = 'It's nice'  # Bug: apostrophe inside single quotes
print(phrase)
```

✅ **Good** (clean code):

```python
phrase = 'It's nice'
print(phrase)
```

## Testing Guidance

Tests for debug exercises should:

1. Execute the fixed code (from the student's corrected cell) and verify it produces the correct output.
2. Assert that the student filled in the explanation cell with meaningful content (more than 10 non-whitespace characters).

Example test helper to read an explanation cell:

```python
import json

def _get_explanation(notebook_path: str, tag: str = "explanation1") -> str:
    nb = json.load(open(notebook_path, "r", encoding="utf-8"))
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        if tag in tags:
            return "".join(cell.get("source", []))
    raise AssertionError(f"No explanation cell with tag {tag}")

# Example test
def test_explanation_has_content():
    explanation = _get_explanation("notebooks/ex004_sequence_debug_syntax.ipynb", tag="explanation1")
    assert len(explanation.strip()) > 10, "Explanation must be more than 10 characters"
```

---

## Summary Checklist for Authoring Debug Exercises

Before finalising a debug notebook, ensure:

- [ ] **Every exercise has an actual bug** (fails to run or produces incorrect output)
- [ ] **Exercise titles are neutral** (do not reveal the bug type)
- [ ] **Prompts are neutral** (no hints, no explanations of what's wrong)
- [ ] **Buggy code is clean** (no comments hinting at the bug)
- [ ] **Detailed explanations are in solutions notebook only** (not visible to students)
- [ ] **Each cell is tagged correctly** (`exercise1`–`exercise10`, `explanation1`–`explanation10`)
- [ ] **Tests verify correctness AND explanation content** (explanation > 10 characters)
