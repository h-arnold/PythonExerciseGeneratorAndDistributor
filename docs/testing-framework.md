# Testing Framework

This document describes the notebook grading system used to automatically test student exercises.

## Overview

The testing framework extracts code from tagged cells in Jupyter notebooks and executes it in isolation to verify correctness. This approach:
- Keeps grading deterministic and automated
- Works with GitHub Classroom autograding
- Allows students to work in familiar Jupyter notebooks while being graded via pytest

## Core Components

### `notebook_grader.py`

The core grading module provides two main functions:

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

### Basic Test Pattern

```python
from tests.notebook_grader import exec_tagged_code

def test_exercise_functionality():
    # Extract and execute the tagged cell
    ns = exec_tagged_code("notebooks/ex001_example.ipynb", tag="exercise1")

    # Verify expected function exists
    assert "solve" in ns, "Student cell must define solve()"

    # Test the function
    result = ns["solve"](input_value)
    assert result == expected_value
```

### Multi-Part Exercise Pattern

For exercises with multiple parts (exercise1, exercise2, etc.):

```python
import pytest
from tests.notebook_grader import exec_tagged_code

@pytest.mark.parametrize("tag", ["exercise1", "exercise2", "exercise3"])
def test_exercise_cells_run(tag: str):
    ns = exec_tagged_code(f"notebooks/ex010_multipart.ipynb", tag=tag)
    assert "solve" in ns
    result = ns["solve"]()
    assert result != "TODO"  # Placeholder guard
```

### Testing Best Practices

1. **Isolation**: Each tagged cell is executed in its own namespace. Tests should not assume state from previous cells. This is the default pattern but can be deviated from for multi-part exercises where later exercises build on earlier ones.

2. **Speed**: Keep tests fast (< 1s each). Use small inputs and avoid expensive operations.

3. **Coverage**: Include:
   - At least 3 positive test cases
   - At least 2 edge cases (empty lists, zero, boundary values)
   - 1 invalid input test where appropriate

4. **Parametrization**: Use `pytest.mark.parametrize` to test multiple inputs efficiently:
   ```python
   @pytest.mark.parametrize(
       "input_val,expected",
       [
           (1, 2),
           (5, 10),
           (0, 0),
       ]
   )
   def test_solve(input_val, expected):
       ns = exec_tagged_code("notebooks/ex001_example.ipynb", tag="exercise1")
       assert ns["solve"](input_val) == expected
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
def _run_exercise(tag: str, input_val):
    ns = exec_tagged_code("notebooks/ex001_example.ipynb", tag=tag)
    assert "solve" in ns, f"Missing solve() in {tag}"
    return ns["solve"](input_val)

def test_positive_case():
    assert _run_exercise("exercise1", 5) == 10

def test_edge_case():
    assert _run_exercise("exercise1", 0) == 0
```

### Checking Multiple Functions

```python
def test_exercise_defines_functions():
    ns = exec_tagged_code("notebooks/ex001_example.ipynb", tag="exercise1")
    assert "add" in ns, "Missing add() function"
    assert "multiply" in ns, "Missing multiply() function"

    assert ns["add"](2, 3) == 5
    assert ns["multiply"](2, 3) == 6
```
