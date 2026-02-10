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
- **Student notebook tests should always fail before being attempted**: The student notebook tests must *all* fail in their initial state. If any test passes before the student writes code, it is not a useful test.
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

**IMPORTANT:** Not all tasks need multiple tests. If an exercise has a single clear criterion, one test is sufficient. Equally, some exercises will be complex enough to warrant 4+ tests. Use your judgement based on the learning objectives.

### Choosing the Right Number of Tests (real repository examples)

Use professional judgement per exercise, not a fixed "always three tests" rule.

#### 1) One-test example (ex006 Exercise 7)

Use one test where there is a single clear success criterion.

**Starter code (student notebook):**
```python
# Exercise 7 — YOUR CODE
print("Enter price:")
price = input()
print("Two items cost: " + price + price)
```

**Grading test:**
```python
@pytest.mark.task(taskno=7)
def test_exercise7_logic() -> None:
    output = _run_with_inputs(7, list(ex006.EX006_INPUT_EXPECTATIONS[7]["inputs"]))
    assert ex006.EX006_INPUT_EXPECTATIONS[7]["prompt_contains"] in output
    expected_output = ex006.EX006_INPUT_EXPECTATIONS[7].get("output_contains")
    assert expected_output is not None
    assert expected_output in output
```

Why one test is enough here: the exercise is outcome-focused (prompt and resulting output), and there is no additional construct to score separately.

#### 2) Three-test example (ex003 Exercise 4)

Use three tests when logic, formatting, and construct are all distinct learning goals.

**Starter code (student notebook):**
```python
# Exercise 4 — YOUR CODE
# Update the prompt to the new wording and the final message
print("What is your favourite fruit?")
fruit = input()
print("My favourite fruit is " + fruit)
```

**Grading tests:**
```python
@pytest.mark.task(taskno=4)
def test_exercise4_logic() -> None:
    fruit = "dragonfruit"
    descriptor = "sweet"
    output = _exercise_output_with_inputs(4, [fruit, descriptor])
    lines = output.strip().splitlines()
    assert lines == [
        ex003.EX003_EXPECTED_PROMPTS[4][0],
        ex003.EX003_EXPECTED_PROMPTS[4][1],
        ex003.EX003_EXPECTED_INPUT_MESSAGES[4].format(value1=fruit, value2=descriptor),
    ]

@pytest.mark.task(taskno=4)
def test_exercise4_formatting() -> None:
    output = _exercise_output_with_inputs(4, ["mango", "tropical"])
    expected = f"{ex003.EX003_EXPECTED_PROMPTS[4][0]}\n{ex003.EX003_EXPECTED_PROMPTS[4][1]}\n{ex003.EX003_EXPECTED_INPUT_MESSAGES[4].format(value1='mango', value2='tropical')}\n"
    assert output == expected

@pytest.mark.task(taskno=4)
def test_exercise4_construct() -> None:
    tree = _exercise_ast(4)
    constants = _string_constants(tree)
    assert ex003.EX003_EXPECTED_PROMPTS[4][0] in constants
    assert ex003.EX003_EXPECTED_PROMPTS[4][1] in constants
    assert ex003.EX003_ORIGINAL_PROMPTS[4] not in constants
```

#### 3) 4+ test example (ex004 Exercise 1)

Use more than three tests only when the task genuinely has extra criteria.

**Starter code + explanation prompt (student notebook):**
```python
print("Hello World!"
```

```markdown
### What actually happened
Describe what error you got and why. Fix the code above.
```

**Grading tests:**
```python
@pytest.mark.task(taskno=1)
def test_exercise1_logic() -> None:
    output = _exercise_output(1)
    assert output.strip() == ex004.EX004_EXPECTED_SINGLE_LINE[1]

@pytest.mark.task(taskno=1)
def test_exercise1_formatting() -> None:
    output = _exercise_output(1)
    assert output == f"{ex004.EX004_EXPECTED_SINGLE_LINE[1]}\n"

@pytest.mark.task(taskno=1)
def test_exercise1_construct() -> None:
    tree = _exercise_ast(1)
    assert _has_print_constant(tree, ex004.EX004_EXPECTED_SINGLE_LINE[1])

@pytest.mark.task(taskno=1)
def test_exercise1_explanation() -> None:
    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=_explanation_tag(1))
    assert is_valid_explanation(
        explanation,
        min_length=ex004.EX004_MIN_EXPLANATION_LENGTH,
        placeholder_phrases=ex004.EX004_PLACEHOLDER_PHRASES,
    )
```

If you cannot justify extra tests with a clear learning objective, do not add them.

## Autograding Integration Details

- **One test, one point**: The autograde plugin assigns one point per collected test. Keep each assertion focused on a single learning objective so Classroom feedback remains clear.
- **Task markers**: Annotate every grading test with `@pytest.mark.task(taskno=<int>)`. The optional `name="Short title"` argument overrides the label surfaced to students.
- **Unmarked tests**: If a test omits the `task` marker, the plugin records it with `task=None`. These tests still count for one point but appear in the "Ungrouped" bucket. Use this sparingly (for infrastructure smoke tests, for example).
- **Authoring guidance**: Prefer many small tests over one large test. Avoid `pytest.skip`, `xfail`, or dynamically generated param ids that obscure the student-facing label. Keep failure messages concise; the plugin truncates long output, so craft assertions with informative `assert ... , "Helpful feedback"` messages.
- **Name collisions**: Reuse the same `taskno` for related criteria (logic, formatting, construct checks). Classroom totals the scores per task number, so consistency across files is important when exercises span multiple modules.
- **Tests must fail initially**: Before the student writes any code, all tests should fail. If any test passes in the initial state, it is not a useful test and should be revised or discarded.

### Initial-Failure Rule: Examples and Non-Examples

A test is only useful for grading if it distinguishes an unattempted notebook from a completed one.

**Good examples (useful tests):**
- Checking exact required output against scaffold text that is intentionally wrong.

```python
# student starter code
print("Hello from Python!")

# test
assert output.strip() == "Hi there!"
```

- Checking an updated input flow with new prompt wording.

```python
# student starter code
print("What is your favourite fruit?")
fruit = input()
print("My favourite fruit is " + fruit)

# test
assert ex003.EX003_EXPECTED_PROMPTS[4][0] in constants
assert ex003.EX003_ORIGINAL_PROMPTS[4] not in constants
```

- Checking explanation quality where the notebook starts with a placeholder prompt.

```python
# markdown starter prompt
"""Describe what error you got and why. Fix the code above."""

# test
assert is_valid_explanation(...)
```

**Non-examples (useless tests):**
- A test that checks only for `print(` when scaffold code already contains `print(...)`.

```python
# bad test (passes immediately)
assert "print(" in code
```

- A test that checks only for a variable name already present in starter code.

```python
# bad test (passes immediately if starter already has price = input())
assert "price" in code
```

- A test that accepts unchanged placeholder output.

```python
# bad test (passes immediately)
assert "Hello from Python!" in output
```

If a test passes on the untouched student notebook, either tighten the assertion (preferred) or remove the test.

### Simulating Input

Use the runtime helper `run_cell_with_input` to inject data into `input()` calls.

```python
from tests.exercise_framework import runtime

@pytest.mark.task(taskno=1)
def test_exercise1_happy_path():
    # Simulate user typing "Alice" then "Blue"
    output = runtime.run_cell_with_input(..., tag="exercise1", inputs=["Alice", "Blue"])
    assert "Alice" in output
    assert "Blue" in output
```

## Template for a Good Test Suite (Exercise 1)

```python
from tests.exercise_framework import runtime

@pytest.mark.task(taskno=1)
def test_exercise1_logic():
    """Criteria 1: Arithmetic logic is correct."""
    output = runtime.run_cell_with_input(..., tag="exercise1", inputs=["5"])
    assert "25" in output  # The answer

@pytest.mark.task(taskno=1)
def test_exercise1_construct():
    """Criteria 2: Used the required loop."""
    code = runtime.extract_tagged_code(..., tag="exercise1")
    assert "for " in code and " in " in code

@pytest.mark.task(taskno=1)
def test_exercise1_formatting():
    """Criteria 3: Output format is precise."""
    output = runtime.run_cell_with_input(..., tag="exercise1", inputs=["5"])
    # Strict check for casing/punctuation
    assert "The square is: 25" in output
```

## Summary Checklist

- [ ] **Strictness**: Does the test enforce correct casing/whitespace (unless explicitly checking for loose constraints)?
- [ ] **Constructs**: If this is a `for` loop lesson, does the test fail if no loop is used?
- [ ] **Granularity**: Are logic, constructs, and formatting tested separately (where appropriate) for better partial credit?
- [ ] **Grouping**: Is every test marked with `@pytest.mark.task(taskno=N)`?
- [ ] **Failure**: Do all tests fail before the student writes code?

## Technical Reference: Exercise Framework

The testing framework now lives under [tests/exercise_framework/](../tests/exercise_framework/).
Use the runtime helpers and shared expectations when authoring or updating tests.

### Core Modules and Responsibilities

- `runtime.py`: notebook loading, tag extraction, execution, input simulation.
- `expectations.py`: normalised output and print-call expectations (exercise-level).
- `assertions.py`: consistent error messages for construct checks.
- `constructs.py`: AST-first construct checks (print usage, operators).
- `reporting.py`: table formatting and error normalisation for student-facing output.
- `api.py`: stable entry points for scripts and CLI checks.

Exercise-specific expectations data lives under [tests/exercise_expectations/](../tests/exercise_expectations/).
Treat those modules as the canonical source of expected outputs, prompt text, and input data.

### Runtime Helpers

### Core Helpers

#### `runtime.run_cell_and_capture_output(notebook_path, *, tag) -> str`

**Primary testing function** for notebook exercises. Executes a tagged cell and captures its print output.

- **Parameters**: `notebook_path` (str/Path), `tag` (str)
- **Returns**: Captured stdout. `input()` prompts are included.

```python
output = runtime.run_cell_and_capture_output("notebooks/ex001.ipynb", tag="exercise1")
assert output.strip() == "Hello Python!"
```

#### `runtime.run_cell_with_input(notebook_path, *, tag, inputs) -> str`

For exercises requiring user input, this function mocks `input()` with predetermined values while capturing print output.

- **Parameters**: `notebook_path` (str/Path), `tag` (str), `inputs` (list[str])
- **Returns**: Captured stdout (including prompts).
- **Raises**: `RuntimeError` if code calls `input()` more times than provided.

```python
output = runtime.run_cell_with_input(
    "notebooks/ex002.ipynb",
    tag="exercise1",
    inputs=["Alice", "Smith"]
)
assert "Alice Smith" in output
```

#### `runtime.get_explanation_cell(notebook_path, *, tag) -> str`

Extracts content from markdown reflection cells.

- **Parameters**: `notebook_path` (str/Path), `tag` (str)
- **Returns**: Cell content string.

```python
expl = runtime.get_explanation_cell("notebooks/ex.ipynb", tag="explanation1")
assert len(expl.strip()) > 10
```

### Advanced Helpers

#### `runtime.extract_tagged_code(notebook_path, *, tag="student") -> str`

Extracts raw source code from tagged cells. Useful for **AST checks** (verifying constructs).

```python
code = runtime.extract_tagged_code(path, tag="exercise1")
assert "for " in code, "Must use a for loop"
```

#### `runtime.exec_tagged_code(notebook_path, *, tag="student", filename_hint=None) -> dict`

Low-level executor. Returns the variable namespace (dict). Useful if you need to inspect variable values directly (rarely needed).

### Environment & Paths

#### `runtime.resolve_notebook_path(notebook_path) -> Path`

Most tests use `NOTEBOOK_PATH` constant. This function resolves that path, strictly adhering to the `PYTUTOR_NOTEBOOKS_DIR` environment variable if set.

**Usage in tests**:
Tests generally define a constant at the top:

```python
NOTEBOOK_PATH = "notebooks/ex001_slug.ipynb"
```

The runtime helpers call `resolve_notebook_path` internally, so you usually don't need to call this directly.

#### `PYTUTOR_NOTEBOOKS_DIR`

Environment variable to redirect tests to a different directory (e.g., solutions).

```bash
# Run tests against solution notebooks
export PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions
uv run pytest -q
```

### Expectations Modules

Exercise expectations live in [tests/exercise_expectations/](../tests/exercise_expectations/).
Tests should import expectations from there instead of hard-coding outputs or prompts.
Example for ex002:

```python
from tests.exercise_expectations import EX002_EXPECTED_SINGLE_LINE
```

### Reporting Helpers

Student-facing check tables should be generated via [tests/exercise_framework/reporting.py](../tests/exercise_framework/reporting.py)
so formatting and error normalisation stay consistent across exercises.

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
