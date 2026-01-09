# Copilot Custom Instructions — PythonTutorExercises

You are assisting in a classroom repository of Python exercises for secondary school students (ages 14-18).

## Project Overview

This repository provides notebook-based Python exercises with automated grading via pytest, designed for GitHub Classroom integration.

**Core concept**: Students work in Jupyter notebooks, writing code in metadata-tagged cells. The grading system extracts and executes these tagged cells using pytest, enabling automated feedback.

## Quick Reference

**For exercise creation**: Use the exercise generation custom agent (`.github/agents/exercise_generation.md.agent.md`)

**Documentation**:
- [Project Structure](../docs/project-structure.md) - Repository organisation and file layout
- [Testing Framework](../docs/testing-framework.md) - How the grading system works
- [Exercise Generation](../docs/exercise-generation.md) - Creating new exercises
- [Setup Guide](../docs/setup.md) - Installation and configuration
- [Development Guide](../docs/development.md) - Contributing and maintenance

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

The same tests run against both sets:
- Default: `pytest` (tests student notebooks)
- Solutions: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest`

### Exercise Organisation

Exercises are organised by construct and type:
- **Constructs**: `sequence`, `selection`, `iteration`, `data_types`, `lists`, `dictionaries`, `functions`, `file_handling`, `exceptions`, `libraries`, `oop`
- **Types**: `debug` (fix errors), `modify` (change working code), `make` (create from scratch)

### Pedagogical Progression

Students learn constructs in order. Exercises must only use constructs students have already learned. See the exercise generation agent for detailed pedagogical guidelines.

## Coding Standards

### Python Style

- **Language**: Python 3.11+
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Type hints**: Use modern syntax (e.g., `list[str]` not `List[str]`)
- **Docstrings**: Required for public functions in infrastructure code

### Testing Standards

- **Fast**: Each test should complete in < 1s
- **Deterministic**: No randomness, time-based checks, or network calls
- **Coverage**: At least 3 positive tests, 2 edge cases per exercise
- **Isolation**: Each tagged cell executes independently

### Notebook Standards

- **Format**: Standard `.ipynb` JSON
- **Cell metadata**: Must include `metadata.language` ("python" or "markdown")
- **Tags**: Exact match required (e.g., `exercise1`, not `Exercise1` or `exercise_1`)
- **Function names**: Prefer `solve()` for consistency

## Common Commands

```bash
# Create new exercise
python scripts/new_exercise.py ex042 "Title" --slug slug_name

# Run tests
pytest -q

# Test solutions
scripts/verify_solutions.sh -q

# Lint code
ruff check .

# Start Jupyter
jupyter lab
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
- `exec_tagged_code(notebook_path, *, tag="student")` - Execute tagged cells and return namespace
- `resolve_notebook_path(notebook_path)` - Handle `PYTUTOR_NOTEBOOKS_DIR` redirection

See [Testing Framework](../docs/testing-framework.md) for details.

## Constraints

**Do not**:
- Include full solutions in student-facing notebooks
- Add heavy dependencies (keep installation simple for students)
- Use network access in exercises or tests
- Create exercises that require constructs students haven't learned
- Use generic best practices that aren't specific to this codebase

**Do**:
- Keep instructions clear and age-appropriate (14-18 year olds)
- Write concise, accurate documentation
- Use the scaffolding tools for consistency
- Test both student and solution notebooks
- Follow the existing patterns in the codebase
