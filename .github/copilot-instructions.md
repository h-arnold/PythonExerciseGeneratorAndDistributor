# Copilot Custom Instructions — PythonTutorExercises

You are assisting in a classroom repository of Python exercises for secondary school students (ages 14-18).

## Project Overview

This repository provides notebook-based Python exercises with automated grading via pytest, designed for GitHub Classroom integration.

**Core concept**: Students work in Jupyter notebooks, writing code in metadata-tagged cells. The grading system extracts and executes these tagged cells using pytest, enabling automated feedback.

**Note on the Python environment**: This repository uses the `uv` tool to manage the Python environment. Use `uv sync` to create/update the project's virtual environment and run Python-related work through `uv` (or by activating the created `.venv` with `source .venv/bin/activate`). Avoid manipulating system Python or creating other virtual environments outside of `uv` so tests and tooling remain consistent.

## Quick Reference

**For exercise creation**: Use the exercise generation custom agent (`.github/agents/exercise_generation.md.agent.md`)

**Documentation (fetch on demand)**: Only read these files when a question specifically requires detailed information. Use `read_file` to fetch the exact file needed.

- `docs/project-structure.md` — project layout and file conventions
- `docs/testing-framework.md` — how the grading and test system works
- `docs/exercise-generation-cli.md` — CLI for scaffolding new exercises
- `docs/setup.md` — installation and environment setup
- `docs/development.md` — contributor and development guidelines

## Repository Structure

```
notebooks/              # Student exercise notebooks
  exNNN_slug.ipynb     # One notebook per exercise
  solutions/           # Instructor solution mirrors
tests/                 # pytest-based automated grading
  notebook_grader.py   # Core grading framework
  test_exNNN_*.py      # Tests for each exercise
exercises/             # Teacher materials and metadata
  CONSTRUCT/TYPE/exNNN_slug/
scripts/               # Automation utilities
  new_exercise.py      # Exercise scaffolding tool
docs/                  # Project documentation
```

## Key Concepts

### Tagged Cells

Students write solutions in code cells tagged with `exerciseN` (e.g., `exercise1`, `exercise2`) in the cell metadata. Tests extract these cells using `exec_tagged_code()` from `tests/notebook_grader.py`.

**Important**: Marker comments (e.g., `# STUDENT`) are deprecated. Only metadata tags are used.

### Parallel Notebook Sets

- **Student notebooks** (`notebooks/`): Scaffolding with incomplete exercises
- **Solution notebooks** (`notebooks/solutions/`): Completed versions

The same tests run against both sets. 

**IMPORTANT NOTE:** Always run the *Development* tests unless you are creating or verifying jupyter notebook exercises. The tests for the students notebooks are designed to fail until they are completed with the correct code.

- Development (recommended): `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q`
- Student grading: run `pytest -q` (tests the student notebooks)

> Note: When using the `uv`-managed environment, running `pytest -q` will use the virtual environment created by `uv sync`.

## Coding Standards

### Concise Standards (derived from lint + tidy review)

- Python 3.11+; use modern type hints (e.g., `list[str]`).
- Docstrings required for public functions.
- Keep logic simple (KISS): low complexity, shallow nesting, short functions.
- Avoid duplication (DRY): extract shared helpers when logic repeats.
- No dead code: remove unused imports/vars; no commented-out code.
- Deterministic, fast tests: no randomness, time, or network.
- Prefer stdlib; avoid new deps unless necessary and justified.
- Match Ruff rules in `pyproject.toml` (E/F/W/I/UP/B/C90/LOG/PIE/RUF/SIM/PLR).

### Python Style (for infrastructure code, not student exercises)

- **Language**: Python 3.11+
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Type hints**: Use modern syntax (e.g., `list[str]` not `List[str]`)
- **Docstrings**: Required for public functions

Student exercise code in notebooks may omit these standards as exercises are designed for learning.

### Testing Standards

- **Fast**: Each test should complete in < 1s
- **Deterministic**: No randomness, time-based checks, or network calls
- **Coverage**: At least 3 positive tests, 2 edge cases per exercise
- **Isolation**: Each tagged cell executes independently

### Notebook Standards

- **Format**: Standard `.ipynb` JSON
- **Cell metadata**: Generated notebooks include `metadata.language` ("python" or "markdown")
- **Tags**: Exact match required (e.g., `exercise1`, not `Exercise1` or `exercise_1`)
- **Function names**: Prefer `solve()` for consistency

## Common Commands

```bash
# Enable venv - it doesn't automatically activate in your terminal instances for some reason
source .venv/bin/activate

# Run tests
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q

# Lint code
ruff check . --fix

```

## When Asked to Create Exercises

**Delegate to the exercise generation custom agent** - it has specialised knowledge of pedagogical patterns, exercise types, and construct progression.

Do not create exercises manually. Use:
1. The exercise generation agent for authoring
2. `scripts/new_exercise.py` for scaffolding
3. The testing framework for grading

## Working with the Grading System

The grading system (`tests/notebook_grader.py`) provides:

- `extract_tagged_code(notebook_path, *, tag="student")` - Extract source from tagged cells
- `exec_tagged_code(notebook_path, *, tag="student")` - Execute tagged cells and return namespace. When developing or running tests, run these against the solutions notebook by default (use `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` or call `resolve_notebook_path()` so tests validate the instructor solution first).
- `resolve_notebook_path(notebook_path)` - Handle `PYTUTOR_NOTEBOOKS_DIR` redirection; by convention the agent should default this to `notebooks/solutions` when running tests during development.

See [Testing Framework](../docs/testing-framework.md) for details.

## Constraints

**Do not**:
- Include full solutions in student-facing notebooks
- Add dependencies that can't be installed via micropip (web VSCode compatibility)
- Use network access in exercises or tests
- Create exercises that require constructs students haven't learned
- Use generic best practices that aren't specific to this codebase

**Do**:
- Keep instructions clear and age-appropriate (14-18 year olds)
- Write concise, accurate documentation
- Use the scaffolding tools for consistency
- Test both student and solution notebooks
- Follow the existing patterns in the codebase

## Code Review & Tidy Checks

After making changes to code that **IS NOT** student notebooks, **you MUST** call the 'Tidy Code Reviewer' sub-agent using your `runSubagent` tool.

- Purpose: verify claimed changes, run lint/type diagnostics, apply safe cleanups (formatting, remove unused imports, small refactors), and report remaining issues.
- Typical workflow:
  1. Run tests and ruff locally (pytest -q; ruff check .).
  2. Give the agent a summary of all the changes you've made, ensuring you list all files touched in your coding session.
  3. Review the agent's report, address any remaining issues, re-run tests, and commit.

