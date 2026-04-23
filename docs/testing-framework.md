# Infrastructure Testing Framework

This document describes the testing framework for the **codebase itself**, ensuring the reliability of the tools, scripts, and automation used to generate and manage exercises.

For details on **testing student notebooks**, see [Exercise Testing](exercise-testing.md).

> Source of truth: execution/discovery/runtime contracts are defined in [docs/execution-model.md](execution-model.md).

## Repository status

Canonical exercise-specific tests belong in `exercises/<construct>/<exercise_key>/tests/`.

Exported Classroom repositories preserve exercise-local tests and export student notebooks to `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`.

Packaged templates remain metadata-free (no exported `exercise.json`) and exclude solution notebooks by default.

## Overview

The repository's infrastructure (scaffolding scripts, grader logic, CLI tools, and documentation) is tested using `pytest`. These tests ensure that:

1. **Exercise Generation**: The `new_exercise` script creates valid, compilable, and standards-compliant exercises.
2. **Grading Logic**: The public exercise framework lives under `exercise_runtime_support/exercise_framework/`, with compatibility coverage and repository tests under `tests/exercise_framework/`.
3. **Template CLI**: The template repository tools work as expected.
4. **Documentation**: Exercise validation rules are respected.

Pytest discovery uses the configured roots in `pyproject.toml` (`testpaths = ["tests", "exercises"]`) so shared infrastructure and canonical exercise-scoped tests are both discoverable.

## Running Tests

### Standard Execution

Run the full suite using `uv`:

```bash
uv run pytest -q
```

Because raw `uv run pytest -q` exercises the default solution variant, the CI-equivalent source-repository check is a collection pass plus the explicit solution-variant run:

```bash
uv run pytest --collect-only -q
uv run python scripts/run_pytest_variant.py --variant solution -q
```

### Targeted Execution

Run tests for specific components:

```bash
# Test the grading logic itself
uv run pytest tests/exercise_framework/test_runtime.py

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
- Packaging behaviour (e.g., that `TemplatePackager` copies the required base files, runtime-only shared `tests/` infrastructure for exercise checks and notebook self-checks, and the `.github` workflow directory).

> **Note:** Test-only helpers and fixtures are kept under `tests/` and are not part of the runtime surface. The template CLI follows a canonical-only exercise-local contract with no legacy compatibility paths.

### 3. Supporting helpers & locations

This repository provides a small set of shared helpers used across infrastructure tests and the CLI; knowing their locations helps future contributors write consistent tests and tools.

- `tests/exercise_framework/` — the current notebook testing framework. Use `runtime.py` for execution helpers, `constructs.py` for AST checks, `assertions.py` for consistent messages, and `reporting.py` for table output. Detailed behaviour for notebook grading is documented in `docs/exercise-testing.md`.

- `exercise_runtime_support/notebook_grader.py` — low-level grading helpers (JSON parsing, tagged cell extraction, execution). The compatibility wrapper at `tests/notebook_grader.py` exists for repository/test-template parity.

- `scripts/template_repo_cli/utils/` — utility functions for the template CLI and packager, notably:
  - `filesystem.py` (e.g., `safe_copy_file`, `safe_copy_directory`)
  - `validation.py` (name/construct/type validators; note that exercise type is canonical metadata rather than a canonical path segment)

- `scripts/template_repo_cli/core/` — core components implementing CLI behaviour: `collector.py`, `packager.py`, `selector.py`, and `github.py`.

Important note on similarly-named helpers:

- There are four helpers named `resolve_notebook_path()` in the codebase:
- `exercise_runtime_support.exercise_framework.paths::resolve_notebook_path` is the framework entry point and respects the current notebook-variant selection.
- `exercise_runtime_support.notebook_grader::resolve_notebook_path` is a low-level helper used by the framework runtime.
- `exercise_runtime_support.exercise_framework.runtime::resolve_notebook_path` is a runtime-oriented wrapper used by framework execution helpers.
- `exercise_metadata.resolver::resolve_notebook_path` resolves canonical notebook locations directly from `exercise_key` metadata.

Recommendation: For runtime and test execution helpers, prefer `exercise_runtime_support.exercise_framework.paths::resolve_notebook_path` (or the `runtime` wrapper where that API is already in use). For template CLI canonical file collection, use `exercise_metadata.resolver::resolve_notebook_path`. Do not treat notebook paths as the canonical exercise identity in new guidance or new APIs.

Resolver identity contract:

- For notebook self-check cells and author-facing exercise guidance, the canonical identity is the `exercise_key` string passed to `run_notebook_checks('<exercise_key>')`.
- For shared runtime or grading code that has already resolved a notebook location, keep the value as a `Path` when passing it into framework/grader helpers.
- Avoid converting a resolved `Path` back into `str(path)` before calling resolver-backed helpers; path-like strings are intentionally distinct from exercise-key strings in the framework contract.

### 4. Exercise Quality (`tests/test_exercise_type_docs.py`)

Sanity checks for the documentation and exercise type definition files.

## Continuous Integration

The repository uses GitHub Actions to run these tests automatically.

- **`tests.yml`**: Source-repository validation on every push and pull request. It checks pytest collection/discovery in the authoring repository and then runs `scripts/run_pytest_variant.py --variant solution -q`.
- **`tests-solutions.yml`**: Manual maintainer rerun surface. It keeps the explicit `--variant solution` contract and accepts optional forwarded pytest args for targeted solution checks.
- **`template_repo_files/.github/workflows/classroom.yml`**: Exported Classroom workflow. It runs `scripts/build_autograde_payload.py --variant student` against the metadata-free student contract.

## Adding New Infrastructure Tests

When adding new scripts or tools:

1. Create a corresponding test file in `tests/` (e.g., `test_myscript.py`).
2. Use standard `pytest` fixtures.
3. Mock filesystem operations/network calls where possible (keep tests fast).
4. Run `ruff check .` to ensure the new tests meet linting standards.
