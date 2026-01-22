# Testing Framework

This document describes the notebook grading system used to automatically test student exercises.

## Overview

The testing framework extracts code from tagged cells in Jupyter notebooks and executes it to verify correctness. Tests primarily verify **notebook cell output** (what students print), not function return values. This approach:
- Keeps grading deterministic and automated
- Works with GitHub Classroom autograding
- Allows students to work in familiar Jupyter notebooks while being graded via pytest
- Matches how students naturally interact with notebooks (printing results, not returning values)

## Core Components

### `notebook_grader.py`

The core grading module provides functions for extracting, executing, and testing notebook cells.

#### `extract_tagged_code(notebook_path, *, tag="student") -> str`

Extracts source code from all cells tagged with the specified tag.

**Parameters**:
- `notebook_path`: Path to the `.ipynb` file
- `tag`: Cell metadata tag to extract (default: `"student"`)

**Returns**: Concatenated source code from all matching cells

**Raises**: `NotebookGradingError` if no cells with the tag are found

#### `exec_tagged_code(notebook_path, *, tag="student", filename_hint=None) -> dict`

Extracts and executes code from tagged cells, returning the resulting namespace.

**Parameters**:
- `notebook_path`: Path to the `.ipynb` file
- `tag`: Cell metadata tag to extract and execute (default: `"student"`)
- `filename_hint`: Optional filename for error messages

**Returns**: Dictionary containing the execution namespace (variables, functions, etc.)

**Raises**: `NotebookGradingError` if extraction or execution fails

**Note**: This is a low-level function. Most tests should use the higher-level helpers below.

#### `run_cell_and_capture_output(notebook_path, *, tag) -> str`

**Primary testing function** for notebook exercises. Executes a tagged cell and captures its print output.

**Parameters**:
- `notebook_path`: Path to the `.ipynb` file
- `tag`: Cell metadata tag to execute (e.g., `"exercise1"`)

**Returns**: The captured stdout output as a string

**Example**:
```python
output = run_cell_and_capture_output("notebooks/ex001.ipynb", tag="exercise1")
assert output.strip() == "Hello Python!"
```

#### `run_cell_with_input(notebook_path, *, tag, inputs) -> str`

For exercises requiring user input, this function mocks `input()` with predetermined values while capturing print output.

**Parameters**:
- `notebook_path`: Path to the `.ipynb` file
- `tag`: Cell metadata tag to execute (e.g., `"exercise1"`)
- `inputs`: List of strings to provide as `input()` values

**Returns**: The captured stdout output as a string

**Raises**: `RuntimeError` if the code calls `input()` more times than provided

**Example**:
```python
output = run_cell_with_input(
    "notebooks/ex002.ipynb",
    tag="exercise1",
    inputs=["Alice", "Smith"]
)
assert "Alice Smith" in output
```

#### `get_explanation_cell(notebook_path, *, tag) -> str`

Extracts explanation/reflection cell content by tag. Used to verify students have filled in markdown explanation cells in debugging exercises.

**Parameters**:
- `notebook_path`: Path to the `.ipynb` file
- `tag`: Cell metadata tag to extract (e.g., `"explanation1"`)

**Returns**: The markdown cell content as a string

**Raises**: `AssertionError` if no cell with the specified tag is found

**Example**:
```python
explanation = get_explanation_cell("notebooks/ex001.ipynb", tag="explanation1")
assert len(explanation.strip()) > 10, "Explanation must have content"
```

### `resolve_notebook_path(notebook_path) -> Path`

Resolves notebook paths with optional redirection via the `PYTUTOR_NOTEBOOKS_DIR` environment variable.

**Purpose**: Allows the same tests to run against either:
- Student notebooks (default): `notebooks/exNNN_slug.ipynb`
- Solution mirrors: `notebooks/solutions/exNNN_slug.ipynb`

**Best practice**: Almost always test against the solution mirror first to ensure tests work correctly. Testing against student notebooks is primarily for GitHub Classroom autograding.

**Usage**:
```bash
# Test solution notebooks (recommended for development)
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest

# Test student notebooks (for GitHub Classroom)
pytest
```

## Writing Tests

### Basic Test Pattern (Cell Output)

The most common pattern tests what a cell prints:

```python
from tests.notebook_grader import run_cell_and_capture_output

def test_exercise1_prints_hello():
    output = run_cell_and_capture_output("notebooks/ex001_example.ipynb", tag="exercise1")
    assert output.strip() == "Hello Python!", f"Expected 'Hello Python!' but got {output!r}"
```

### Testing Input-Based Exercises

For exercises requiring user input:

```python
from tests.notebook_grader import run_cell_with_input

def test_exercise2_name_greeting():
    output = run_cell_with_input(
        "notebooks/ex002_example.ipynb",
        tag="exercise2",
        inputs=["Alice"]
    )
    assert "Hello, Alice!" in output
```

### Multi-Part Exercise Pattern

For exercises with multiple parts (exercise1, exercise2, etc.):

```python
import pytest
from tests.notebook_grader import run_cell_and_capture_output

@pytest.mark.parametrize("tag,expected", [
    ("exercise1", "Result: 5"),
    ("exercise2", "Result: 10"),
    ("exercise3", "Result: 15"),
])
def test_exercises(tag: str, expected: str):
    output = run_cell_and_capture_output("notebooks/ex010_multipart.ipynb", tag=tag)
    assert expected in output, f"Expected '{expected}' in output for {tag}, got: {output}"
```

### Testing Explanation Cells

For debugging exercises with reflection components:

```python
from tests.notebook_grader import get_explanation_cell

def test_explanation1_has_content():
    explanation = get_explanation_cell("notebooks/ex001_example.ipynb", tag="explanation1")
    assert len(explanation.strip()) > 10, "Explanation must be more than 10 characters"
```

### Testing Best Practices

1. **Isolation**: Each tagged cell is executed in its own namespace. Tests should not assume state from previous cells. This is the default pattern but can be deviated from for multi-part exercises where later exercises build on earlier ones.

2. **Speed**: Keep tests fast (< 1s each). Use small inputs and avoid expensive operations.

3. **Coverage**: Include:
   - At least 3 positive test cases
   - At least 2 edge cases (empty input, boundary values)
   - 1 invalid input test where appropriate

4. **Parametrization**: Use `pytest.mark.parametrize` to test multiple inputs efficiently:
   ```python
   @pytest.mark.parametrize("input_val,expected", [
       ("Alice", "Hello, Alice!"),
       ("Bob", "Hello, Bob!"),
       ("", "Hello, !"),  # Edge case: empty input
   ])
   def test_greeting(input_val, expected):
       output = run_cell_with_input(
           "notebooks/ex001_example.ipynb",
           tag="exercise1",
           inputs=[input_val]
       )
       assert expected in output
   ```

5. **Determinism**: Avoid random values, time-based tests, or network calls. All tests must be reproducible.

## Cell Tagging

The `new_exercise.py` script automatically tags cells when generating notebooks. Students write their code in these pre-tagged cells.

The tag must exactly match what tests expect (e.g., `exercise1`, `exercise2`).

**Manually adding tags in Jupyter** (if needed):
1. Select the code cell
2. Open the property inspector (gear icon in the right sidebar)
3. Add the tag (e.g., `exercise1`) under "Cell Tags"

**Deprecated**: Marker comments like `# STUDENT` are no longer supported. Only metadata tags are used.

## Environment Variable: `PYTUTOR_NOTEBOOKS_DIR`

When set, `resolve_notebook_path()` redirects notebook lookups to the specified directory.

**Use case**: Run the same tests against solution notebooks to verify they pass:
```bash
export PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions
pytest
```

Or use the helper script:
```bash
scripts/verify_solutions.sh -q
```

## Error Handling

The framework raises `NotebookGradingError` for common issues:
- Notebook file not found
- Invalid JSON in notebook
- No cells tagged with the specified tag

Tests can catch these to provide better error messages or skip gracefully.

## Notebook Format Requirements

The grading system expects standard Jupyter `.ipynb` files:
- Each cell has `cell_type` ("code" or "markdown")
- Cell source is either a list of strings or a single string
- Cell metadata may include a `tags` field (list of strings)

The system is pure Python stdlib (no nbformat/nbclient dependency) to reduce installation friction for students.

## Running Tests

### Locally

```bash
# Run all tests
pytest -q

# Run specific test file
pytest tests/test_ex001_sanity.py -v

# Run and show print statements
pytest tests/test_ex001_sanity.py -s
```

### CI/CD

The repository includes GitHub Actions workflows:
- `.github/workflows/tests.yml`: Runs tests on every push/PR
- `.github/workflows/tests-solutions.yml`: Manual workflow to verify solutions

## Common Patterns

### Helper Function Pattern

When multiple tests share setup logic:

```python
from tests.notebook_grader import run_cell_and_capture_output

NOTEBOOK_PATH = "notebooks/ex001_example.ipynb"

def _run_and_capture(tag: str) -> str:
    """Execute the tagged cell and capture its print output."""
    return run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)

def test_exercise1():
    output = _run_and_capture("exercise1")
    assert output.strip() == "Hello Python!"

def test_exercise2():
    output = _run_and_capture("exercise2")
    assert output.strip() == "Goodbye!"
```

### Checking Multiple Lines of Output

```python
def test_multiline_output():
    output = run_cell_and_capture_output("notebooks/ex001_example.ipynb", tag="exercise1")
    lines = output.strip().split('\n')
    assert len(lines) == 3, "Expected 3 lines of output"
    assert lines[0] == "First line"
    assert lines[1] == "Second line"
    assert lines[2] == "Third line"
```
