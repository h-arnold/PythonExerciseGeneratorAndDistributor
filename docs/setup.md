# Setup Guide

This guide covers setting up the PythonTutorExercises repository for development or use in a classroom.

## Recommended environment

For a consistent toolchain, open the repository in GitHub Codespaces or the supplied VS Code Dev Container (`.devcontainer/devcontainer.json`). The container image installs Python 3.11, uv, the GitHub CLI, and Git LFS, then runs `uv sync` and activates the virtual environment automatically. Wait for the post-create tasks to finish before running commands.

## Prerequisites

- Git
- uv (Python package manager)
- Python 3.11 or later (only required when working outside the dev container)
- VS Code Dev Containers extension or Docker Desktop (optional, only if you plan to run the dev container locally)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Bassaleg-School/PythonTutorExercises.git
cd PythonTutorExercises
```

### 2. Install uv (if you are not using the dev container)

uv ships as a standalone binary. Install it with the official installer script (it adds uv to `~/.local/bin` on Unix-like systems):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -c "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://astral.sh/uv/install.ps1 | iex}"
```

If uv is already available (e.g., in Codespaces or the dev container), you can skip this step.

### 3. Sync dependencies with uv

```bash
uv sync
```

`uv sync` creates the `.venv` folder, installs every dependency from `pyproject.toml`, and makes the console scripts (like `template_repo_cli`) available on your PATH when the virtual environment is activated (so you can call them directly as `template_repo_cli` or use `python -m template_repo_cli`).

This installs:

- `pytest` (testing framework)
- `ruff` (linter)
- `ipykernel` (Jupyter kernel)
- `jupyterlab` (notebook interface)

### 4. Use the environment

After syncing you can either activate the virtual environment or run commands through uv:

```bash
source .venv/bin/activate  # deactivate with "deactivate"
```

or prefix commands with `uv run`, for example `uv run pytest`. The dev container keeps the environment active automatically.

## Verification

### Run Tests

```bash
uv run pytest -q
```

All tests should pass (or fail for incomplete student exercises, which is expected).

### Run Tests Against Solutions

```bash
uv run ./scripts/verify_solutions.sh -q
```

or:

```bash
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q
```

All solution tests should pass.

### Start Jupyter Lab

```bash
uv run jupyter lab
```

This opens the Jupyter interface in your browser where you can work on notebooks.

## For Students

If you're a student working on exercises:

1. **Clone the repository** (or accept the GitHub Classroom assignment)
2. **Install dependencies** as described above (run `uv sync` to create `.venv` and install dev tools)
3. **Open a notebook** in Jupyter Lab:

   ```bash
   uv run jupyter lab notebooks/ex001_sanity.ipynb
   ```

4. **Complete the exercise** in the cell tagged `exercise1` (or `exercise2`, etc.)
5. **Run tests** to check your work:

   ```bash
   uv run pytest tests/test_ex001_sanity.py -v
   ```

6. **Repeat** until all tests pass

## For Teachers

If you're creating or modifying exercises:

1. **Complete the setup** as described above
2. **Review the documentation**:
   - [Project Structure](project-structure.md)
   - [Testing Framework](testing-framework.md)
   - [Exercise Generation CLI](exercise-generation-cli.md) — Instructions for using the exercise generation CLI tool to scaffold new Python exercises
3. **Create exercises** using the scaffolding script:

   ```bash
   uv run python scripts/new_exercise.py ex042 "Your Title" --slug your_slug
   ```

4. **Author the exercise** following the guidelines in [Exercise Generation CLI](exercise-generation-cli.md), which documents how to use the exercise generation CLI tool to scaffold new Python exercises.
5. **Verify solutions** pass tests:

   ```bash
   uv run ./scripts/verify_solutions.sh tests/test_ex042_your_slug.py
   ```

## Linting and Code Quality

### Run Ruff Linter

```bash
uv run ruff check .
```

### Auto-Fix Issues

```bash
uv run ruff check --fix .
```

Configuration is in `pyproject.toml`.

## GitHub Classroom Integration

This repository is designed to work with GitHub Classroom:

1. **Create an assignment** from this template repository
2. **Students accept** the assignment and get their own copy
3. **Students complete exercises** and push commits
4. **Autograding runs** via GitHub Actions (`.github/workflows/tests.yml`)
5. **Tests verify** student solutions automatically

### Autograding Configuration

The `.github/workflows/tests.yml` workflow:

- Triggers on every push and pull request
- Sets up Python 3.11
- Installs dependencies
- Runs `pytest`

Students see test results in the GitHub Actions tab of their repository.

## Development Workflow

Recommended workflow for creating and testing exercises:

```bash
# 1. Create a new branch
git checkout -b add-ex042-variables

# 2. Generate the exercise
uv run python scripts/new_exercise.py ex042 "Variables and Types" --slug variables_and_types

# 3. Organise the folder
mv exercises/ex042_variables_and_types exercises/sequence/modify/

# 4. Author the notebook
uv run jupyter lab notebooks/ex042_variables_and_types.ipynb

# 5. Write tests
$EDITOR tests/test_ex042_variables_and_types.py

# 6. Complete the solution
uv run jupyter lab notebooks/solutions/ex042_variables_and_types.ipynb

# 7. Verify tests pass on solution
uv run ./scripts/verify_solutions.sh tests/test_ex042_variables_and_types.py -v

# 8. Verify tests fail on student notebook
uv run pytest tests/test_ex042_variables_and_types.py -v

# 9. Commit and push
git add exercises/ notebooks/ tests/
git commit -m "Add ex042: Variables and Types"
git push origin add-ex042-variables

# 10. Create a pull request
```

## Troubleshooting

### Tests Fail with "No module named 'tests'"

Ensure you're running pytest from the repository root and that your uv-managed environment is up to date:

```bash
uv sync
```

### Notebook Not Found Error

Check that:

- The notebook exists at the expected path
- The path in the test file matches the actual notebook location
- If using `PYTUTOR_NOTEBOOKS_DIR`, the solution notebook exists

### Cell Tag Not Found

Verify the cell metadata in Jupyter:

1. Open the notebook in Jupyter Lab
2. Select the code cell
3. Click the gear icon (property inspector) in the right sidebar
4. Check that the tag (e.g., `exercise1`) is listed under "Cell Tags"

### Import Errors in Student Code

Students sometimes forget imports. Remind them that:

- Each tagged cell is executed in isolation
- All necessary imports must be in the tagged cell
- They cannot rely on imports from other cells

## Environment Variables

### `PYTUTOR_NOTEBOOKS_DIR`

Redirects notebook lookups to a different directory.

**Usage**:

```bash
export PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions
uv run pytest
```

**Purpose**: Run the same tests against solution notebooks to verify they're correct.

## CI/CD Workflows

### `tests.yml`

Runs on every push and pull request:

- Installs dependencies
- Runs pytest against student notebooks
- Reports pass/fail status

### `tests-solutions.yml`

Manual workflow (workflow_dispatch) to verify solution notebooks:

- Sets `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`
- Runs pytest against solution notebooks
- Useful for verifying solutions are correct before releasing exercises

Trigger manually in the GitHub Actions tab.
