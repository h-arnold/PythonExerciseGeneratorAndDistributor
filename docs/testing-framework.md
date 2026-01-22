# Infrastructure Testing Framework

This document describes the testing framework for the **codebase itself**, ensuring the reliability of the tools, scripts, and automation used to generate and manage exercises.

For details on **testing student notebooks**, see [Exercise Testing](exercise-testing.md).

## Overview

The repository's infrastructure (scaffolding scripts, grader logic, CLI tools, and documentation) is tested using `pytest`. These tests ensure that:

1. **Exercise Generation**: The `new_exercise` script creates valid, compilable, and standards-compliant exercises.
2. **Grading Logic**: The `notebook_grader.py` module correctly extracts and executes code from notebooks.
3. **Template CLI**: The template repository tools work as expected.
4. **Documentation**: Exercise validation rules are respected.

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

### 1. Exercise Scaffolding (`tests/test_new_exercise.py`)

Tests for `scripts/new_exercise.py`. Checks include:

- Generating files with correct paths and names.
- Creating valid JSON notebook structures.
- Populating default content.

### 2. Template CLI (`tests/template_repo_cli/`)

Integration tests for the template repository CLI. These tests verify:

- Filesystem operations (copying files and directories, workspace creation/cleanup).
- GitHub interactions (via mocked `subprocess.run` or `gh` command outputs).
- Configuration parsing and selection logic.
- Packaging behaviour (e.g., that `TemplatePackager` copies the required base files and, when present, the project's `tests/notebook_grader.py` into the generated workspace).

> **Tip:** The `tests/template_repo_cli/conftest.py` file exposes useful pytest fixtures (e.g., `repo_root`, `temp_dir`, `sample_exercises`, and `mock_gh_*`) that are intentionally reusable for new tests.

### 3. Supporting helpers & locations

This repository provides a small set of shared helpers used across infrastructure tests and the CLI; knowing their locations helps future contributors write consistent tests and tools.

- `tests/notebook_grader.py` — grading helpers used by notebook-related tests (e.g., `exec_tagged_code`, `run_cell_and_capture_output`, and `resolve_notebook_path`). Detailed behaviour for notebook grading is documented in `docs/exercise-testing.md`.

- `scripts/template_repo_cli/utils/` — utility functions for the template CLI and packager, notably:
  - `filesystem.py` (e.g., `safe_copy_file`, `safe_copy_directory`, `resolve_notebook_path`)
  - `validation.py` (name/construct/type validators)
  - `config.py` (configuration helpers)

- `scripts/template_repo_cli/core/` — core components implementing CLI behaviour: `collector.py`, `packager.py`, `selector.py`, and `github.py`.

Important note on similarly-named helpers:

- There are two helpers named `resolve_notebook_path()` in the codebase:
  - `tests/notebook_grader.py::resolve_notebook_path` is intended for grading-related resolution and respects the `PYTUTOR_NOTEBOOKS_DIR` override.
  - `scripts/template_repo_cli/utils/filesystem.py::resolve_notebook_path` is a small CLI utility used for local path resolution in packaging.

Recommendation: Use the helper from `tests/notebook_grader.py` when writing tests or tooling that interacts with student/solution notebooks; use the CLI utility for packager and local filesystem logic.

### 4. Exercise Quality (`tests/test_exercise_type_docs.py`)

Sanity checks for the documentation and exercise type definition files.

## Continuous Integration

The repository uses GitHub Actions to run these tests automatically.

- **`tests.yml`**: Runs the full suite on every push and pull request.
- **`tests-solutions.yml`**: Specifically runs the notebook tests against the *solution* notebooks (using `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`) to ensure the instructor solutions are valid and passing.

## Adding New Infrastructure Tests

When adding new scripts or tools:

1. Create a corresponding test file in `tests/` (e.g., `test_myscript.py`).
2. Use standard `pytest` fixtures.
3. Mock filesystem operations/network calls where possible (keep tests fast).
4. Run `ruff check .` to ensure the new tests meet linting standards.
