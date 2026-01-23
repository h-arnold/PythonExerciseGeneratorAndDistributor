# Exercise Testing Conventions

This document outlines the testing philosophy and conventions for verifying student notebook exercises.

## Philosophy: "Task Completion" with Good Habits

The goal of our tests is to verify that a student has **achieved the learning objective** while fostering precise coding habits.

We follow a **"Task Completion"** testing model:

1. **Does the code run?** (No syntax/runtime/logic errors)
2. **Does it produce the correct outcome?** (Output matches expectation **strictly** by default)
3. **Does it use the required constructs?** (e.g., If the lesson teaches `for` loops, a `for` loop is mandatory)

## Core Testing Rules

### 1. Output Matching: Strict by Default

Developing the habit of precise output (casing, whitespace, punctuation) is critical for programming.

- **Default to Strict Checks**: Require exact matches (or at least `in` checks that preserve case and punctuation) unless there is a strong pedagogical reason not to.
- **Exceptions**: For "Make" tasks or creative exercises, looser checks (case-insensitive, normalized whitespace) are acceptable.
- **Why**: "Close enough" is often a bug in the real world.

**Example:**
*Exercise: Ask for a name and print "Hello <name>!"*

```python
# PREFERRED: Strict logic
# Teaches students that capital letters and punctuation matter.
assert "Hello Alice!" in output
```

### 2. Constraints & Construct Checking

Most exercises are designed to teach specific constructs (Sequence, Selection, Iteration, etc.).

- **Enforce the Lesson Construct**: If the lesson covers **Iteration**, code that manually prints 10 times instead of looping is **incorrect**.
- **Use AST Checks**: Verify that the required syntax (`for`, `if`, etc.) is present.
- **Allow flexibility in "Make" tasks**: "Make" tasks are strictly about the outcome; if they achieve the result using valid code, be more permissive with implementation details.

### 3. Edge Cases

- **Only test edge cases requested in the prompt.**
- Do not test for defensive coding unless specifically asked for.

## Grouping & Scoring (GitHub Classroom)

We group tests using `@pytest.mark.task(taskno=N)` to align with the GitHub Classroom runner.

### Scoring Strategy

Each **exercise** (e.g., Exercise 1) often has **multiple success criteria**.
To provide granular feedback, implement **multiple tests** for a single exercise, all tagged with the same `taskno`.

**Example Criteria for Exercise 1:**

1. **Logic**: Did it calculate the correct answer?
2. **Construct**: Did it use a `for` loop?
3. **Formatting**: Was the output message formatted correctly?

If an exercise has 3 such tests and 1 fails, the student receives 2/3 of the points for that exercise.

## Autograding Integration Details

- **One test, one point**: The autograde plugin assigns one point per collected test. Keep each assertion focused on a single learning objective so Classroom feedback remains clear.
- **Task markers**: Annotate every grading test with `@pytest.mark.task(taskno=<int>)`. The optional `name="Short title"` argument overrides the label surfaced to students.
- **Unmarked tests**: If a test omits the `task` marker, the plugin records it with `task=None`. These tests still count for one point but appear in the "Ungrouped" bucket. Use this sparingly (for infrastructure smoke tests, for example).
- **Authoring guidance**: Prefer many small tests over one large test. Avoid `pytest.skip`, `xfail`, or dynamically generated param ids that obscure the student-facing label. Keep failure messages concise; the plugin truncates long output, so craft assertions with informative `assert ... , "Helpful feedback"` messages.
- **Name collisions**: Reuse the same `taskno` for related criteria (logic, formatting, construct checks). Classroom totals the scores per task number, so consistency across files is important when exercises span multiple modules.

### Simulating Input

Use the helper `run_cell_with_input` to inject data into `input()` calls.

```python
from tests.notebook_grader import run_cell_with_input

@pytest.mark.task(taskno=1)
def test_exercise1_happy_path():
    # Simulate user typing "Alice" then "Blue"
    output = run_cell_with_input(..., inputs=["Alice", "Blue"])
    assert "Alice" in output
    assert "Blue" in output
```

## Template for a Good Test Suite (Exercise 1)

```python
@pytest.mark.task(taskno=1)
def test_exercise1_logic():
    """Criteria 1: Arithmetic logic is corect."""
    output = run_cell_with_input(..., inputs=["5"])
    assert "25" in output  # The answer

@pytest.mark.task(taskno=1)
def test_exercise1_construct():
    """Criteria 2: Used the required loop."""
    code = extract_tagged_code(..., tag="exercise1")
    assert "for " in code and " in " in code

@pytest.mark.task(taskno=1)
def test_exercise1_formatting():
    """Criteria 3: Output format is precise."""
    output = run_cell_with_input(..., inputs=["5"])
    # Strict check for casing/punctuation
    assert "The square is: 25" in output
```

## Summary Checklist

- [ ] **Strictness**: Does the test enforce correct casing/whitespace (unless explicitly checking for loose constraints)?
- [ ] **Constructs**: If this is a `for` loop lesson, does the test fail if no loop is used?
- [ ] **Granularity**: Are logic, constructs, and formatting tested separately (where appropriate) for better partial credit?
- [ ] **Grouping**: Is every test marked with `@pytest.mark.task(taskno=N)`?

## Technical Reference: `notebook_grader.py`

This section details the helper functions available for writing tests.

### Core Helpers

#### `run_cell_and_capture_output(notebook_path, *, tag) -> str`

**Primary testing function** for notebook exercises. Executes a tagged cell and captures its print output.

- **Parameters**: `notebook_path` (str/Path), `tag` (str)
- **Returns**: Captured stdout. `input()` prompts are included.

```python
output = run_cell_and_capture_output("notebooks/ex001.ipynb", tag="exercise1")
assert output.strip() == "Hello Python!"
```

#### `run_cell_with_input(notebook_path, *, tag, inputs) -> str`

For exercises requiring user input, this function mocks `input()` with predetermined values while capturing print output.

- **Parameters**: `notebook_path` (str/Path), `tag` (str), `inputs` (list[str])
- **Returns**: Captured stdout (including prompts).
- **Raises**: `RuntimeError` if code calls `input()` more times than provided.

```python
output = run_cell_with_input(
    "notebooks/ex002.ipynb",
    tag="exercise1",
    inputs=["Alice", "Smith"]
)
assert "Alice Smith" in output
```

#### `get_explanation_cell(notebook_path, *, tag) -> str`

Extracts content from markdown reflection cells.

- **Parameters**: `notebook_path` (str/Path), `tag` (str)
- **Returns**: Cell content string.

```python
expl = get_explanation_cell("notebooks/ex.ipynb", tag="explanation1")
assert len(expl.strip()) > 10
```

### Advanced Helpers

#### `extract_tagged_code(notebook_path, *, tag="student") -> str`

Extracts raw source code from tagged cells. Useful for **AST checks** (verifying constructs).

```python
code = extract_tagged_code(path, tag="exercise1")
assert "for " in code, "Must use a for loop"
```

#### `exec_tagged_code(notebook_path, *, tag="student", filename_hint=None) -> dict`

Low-level executor. Returns the variable namespace (dict). Useful if you need to inspect variable values directly (rarely needed).

### Environment & Paths

#### `resolve_notebook_path(notebook_path) -> Path`

Most tests use `NOTEBOOK_PATH` constant. This function resolves that path, strictly adhering to the `PYTUTOR_NOTEBOOKS_DIR` environment variable if set.

**Usage in tests**:
Tests generally define a constant at the top:

```python
NOTEBOOK_PATH = "notebooks/ex001_slug.ipynb"
```

The helpers call `resolve_notebook_path` internally, so you usually don't need to call this directly.

#### `PYTUTOR_NOTEBOOKS_DIR`

Environment variable to redirect tests to a different directory (e.g., solutions).

```bash
# Run tests against solution notebooks
export PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions
pytest -q
```

## Running Tests

### Locally

```bash
# Run all tests
uv run pytest -q

# Run specific test file
uv run pytest tests/test_ex001_sanity.py -v

# Run and show output (debug prints)
uv run pytest tests/test_ex001_sanity.py -s
```

### CI/CD

- **`.github/workflows/tests.yml`**: Runs tests on every push/PR with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` (verifying the instructor solutions pass).
- **GitHub Classroom**: Runs tests against the student's submission (default path).

## Cell Tagging

Students write code in cells pre-tagged by the generator.

- **Tag format**: `exerciseN` (e.g., `exercise1`).
- **Matching**: Tags must match exactly.
- **Marker comments**: `# STUDENT` comments are **deprecated** and ignored. Only metadata tags are used.
