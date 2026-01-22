# Infrastructure Testing Framework

This document describes the testing framework for the **codebase itself**, ensuring the reliability of the tools, scripts, and automation used to generate and manage exercises.

For details on **testing student notebooks**, see [Exercise Testing](exercise-testing.md).

## Overview

The repository's infrastructure (scaffolding scripts, grader logic, CLI tools, and documentation) is tested using `pytest`. These tests ensure that:

1.  **Exercise Generation**: The `new_exercise` script creates valid, compilable, and standards-compliant exercises.
2.  **Grading Logic**: The `notebook_grader.py` module correctly extracts and executes code from notebooks.
3.  **Template CLI**: The template repository tools work as expected.
4.  **Documentation**: Exercise validation rules are respected.

## Running Tests

### Standard Execution

Run the full suite using `uv`:

```bash
uv run pytest -q
```

### Targeted Execution

Run tests for specific components:

```bash
# Test the grading logic itself
uv run pytest tests/notebook_grader.py

# Test the exercise generator script
uv run pytest tests/test_new_exercise.py

# Test the template repo CLI
uv run pytest tests/template_repo_cli/
```

## Key Test Suites

### 1. Grading Infrastructure (`tests/notebook_grader.py`)
These tests verify that the `notebook_grader` can:
- Parse `.ipynb` files correctly.
- Handle missing files or invalid JSON gracefully (`NotebookGradingError`).
- Extract code from tagged cells.
- Execute code in isolated namespaces.
- Mock `input()` correctly.

### 2. Exercise Scaffolding (`tests/test_new_exercise.py`)
Tests for `scripts/new_exercise.py`. Checks include:
- Generating files with correct paths and names.
- creating valid JSON notebook structures.
- Populating default content.

### 3. CLI Tools (`tests/template_repo_cli/`)
Tests for the command-line interface used in template repositories. These integration tests verify filesystem operations, GitHub API interactions (mocked), and configuration parsing.

### 4. Exercise Quality (`tests/test_exercise_type_docs.py`)
Sanity checks for the documentation and exercise type definition files.

## Continuous Integration

The repository uses GitHub Actions to run these tests automatically.

- **`tests.yml`**: Runs the full suite on every push and pull request.
- **`tests-solutions.yml`**: Specifically runs the notebook tests against the *solution* notebooks (using `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`) to ensure the instructor solutions are valid and passing.

## Adding New Infrastructure Tests

When adding new scripts or tools:
1.  Create a corresponding test file in `tests/` (e.g., `test_myscript.py`).
2.  Use standard `pytest` fixtures.
3.  Mock filesystem operations/network calls where possible (keep tests fast).
4.  Run `ruff check .` to ensure the new tests meet linting standards.
