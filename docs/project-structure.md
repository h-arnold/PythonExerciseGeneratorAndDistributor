# Project Structure

This document describes the organisation of the PythonTutorExercises repository.

## Directory Layout

``` text
PythonTutorExercises/
├── notebooks/              # Student-facing exercise notebooks
│   ├── exNNN_slug.ipynb   # One notebook per exercise
│   └── solutions/         # Instructor solution mirrors
├── tests/                 # Automated pytest-based grading
│   ├── notebook_grader.py # Core grading framework
│   └── test_exNNN_*.py    # Test files for each exercise
├── exercises/             # Teacher materials and metadata
│   └── CONSTRUCT/TYPE/exNNN_slug/
│       ├── README.md      # Exercise metadata
│       ├── OVERVIEW.md    # Teaching notes
│       # Instructor reference solutions live in notebooks/solutions/
├── scripts/               # Automation and utilities
│   ├── new_exercise.py    # Exercise scaffolding tool
│   └── verify_solutions.sh # Solution verification script
└── docs/                  # Project documentation
```

## Key Directories

### `notebooks/`

Contains Jupyter notebooks where students complete exercises. Each notebook:

- Is named `exNNN_slug.ipynb` (e.g., `ex001_sanity.ipynb`)
- Contains one or more code cells tagged with `exerciseN` (e.g., `exercise1`, `exercise2`)
- Students write their solutions directly in these tagged cells
- The notebook provides context, examples, and instructions

The `notebooks/solutions/` subdirectory contains instructor solution mirrors that are identical to student notebooks but with completed exercise cells.

### `tests/`

Contains pytest-based automated grading:

- `notebook_grader.py`: Core framework that extracts and executes tagged cells from notebooks
- `test_exNNN_slug.py`: Test files for each exercise that verify student solutions

Tests use `exec_tagged_code()` to extract student code from tagged cells and assert correctness.

### `exercises/`

Teacher materials organised by construct and type:

**Folder structure**: `exercises/CONSTRUCT/TYPE/exNNN_slug/`

Where:

- **CONSTRUCT** is one of: `sequence`, `selection`, `iteration`, `data_types`, `lists`, `dictionaries`, `functions`, `file_handling`, `exceptions`, `libraries`, `oop`
- **TYPE** is one of: `debug`, `modify`, `make`

Each exercise folder contains:

- `README.md`: Exercise metadata (title, construct, difficulty, links)
- `OVERVIEW.md`: Pedagogical notes for teachers

Instructor reference solutions live in the solution notebook mirror under `notebooks/solutions/`.

- `OrderOfTeaching.md`: (at construct level) recommended exercise sequence

### `scripts/`

Automation tools:

- `new_exercise.py`: Scaffolds new exercises (notebooks, tests, and metadata)
- `verify_solutions.sh`: Runs tests against solution notebooks

- `template_repo_cli/`: CLI and utilities for packaging and publishing template repositories. See `scripts/template_repo_cli/core/github.py` which provides a `run_subprocess()` wrapper used to centralize subprocess handling for `git`/`gh` commands. The wrapper supports three output modes (`capture`, `stream`, `silent`) to ensure consistent output behaviour and make testing subprocess interactions easier.

### `.github/`

GitHub-specific configuration:

- `copilot-instructions.md`: Repo-wide custom instructions for GitHub Copilot
- `agents/exercise_generation.md.agent.md`: Custom agent for exercise generation
- `workflows/`: CI/CD workflows for testing

## File Naming Conventions

- Exercise IDs: `exNNN` where NNN is a zero-padded number (e.g., `ex001`, `ex042`)
- Slugs: snake_case descriptive names (e.g., `variables_and_types`)
- Full exercise names: `exNNN_slug` (e.g., `ex001_sanity`)

## Tagged Cell System

Students write code in cells tagged with `exerciseN` in the cell metadata:

- Single-part exercises: one cell tagged `exercise1`
- Multi-part exercises: multiple cells tagged `exercise1`, `exercise2`, etc.

Tests extract these tagged cells using `notebook_grader.exec_tagged_code()` and execute them in isolation to verify correctness.

## Parallel Notebook Sets

The repository maintains two parallel sets of notebooks:

- **Student notebooks** (`notebooks/`): contain scaffolding and empty exercise cells
- **Solution notebooks** (`notebooks/solutions/`): identical structure with completed exercises

The same tests can run against either set:

- Default: `pytest` (runs against student notebooks)
- Solutions: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest` (runs against solutions)

This allows verification that:

- Tests pass on known-good solutions
- Tests fail on incomplete student notebooks
