# Setup Guide

This guide covers setting up the PythonExerciseGeneratorAndDistributor repository for development or use in a classroom.

> Source of truth: execution/runtime contracts are defined in [docs/execution-model.md](execution-model.md).

## Repository status

Use `--variant` workflows as the canonical way to select student/solution notebooks. The source repository now uses the exercise-local layout under `exercises/<construct>/<exercise_key>/`; packaging may produce derived outputs, but canonical exercise-specific tests stay under each exercise's own `tests/` directory.

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
git clone <your-repository-url>/PythonExerciseGeneratorAndDistributor.git
cd PythonExerciseGeneratorAndDistributor
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
uv run python scripts/run_pytest_variant.py --variant solution -q
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
   uv run jupyter lab exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb
   ```

4. **Complete the exercise** in the cell tagged `exercise1` (or `exercise2`, etc.)
5. **Run tests** to check your work:

   In this source repository, run the canonical exercise-local test file:

   ```bash
   uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py -v
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
    uv run python scripts/new_exercise.py ex042 "Your Title" \
      --construct sequence \
      --type modify \
      --slug your_slug
   ```

4. **Author the exercise** following the guidelines in [Exercise Generation CLI](exercise-generation-cli.md), which documents how to use the exercise generation CLI tool to scaffold new Python exercises.
5. **Verify solutions** pass tests:

   ```bash
    uv run ./scripts/verify_solutions.sh \
      exercises/sequence/ex042_sequence_modify_your_slug/tests/test_ex042_sequence_modify_your_slug.py
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

This repository uses two separate GitHub Actions surfaces:

1. **Source-repository validation** in this repository checks the authoring contract before changes are merged.
2. **Exported Classroom autograding** runs in repositories created from `template_repo_files/` and checks the student-facing contract.

### Source-repository workflows

The `.github/workflows/tests.yml` workflow:

- Triggers on every push and pull request
- Validates pytest collection/discovery in the authoring repository
- Runs `scripts/run_pytest_variant.py --variant solution -q` so exercise-local tests execute against instructor notebooks

The `.github/workflows/tests-solutions.yml` workflow:

- Is manual (`workflow_dispatch`)
- Keeps the explicit `--variant solution` contract
- Accepts optional pytest args for targeted maintainer reruns

### Exported Classroom workflow

`template_repo_files/.github/workflows/classroom.yml` is copied into exported assignment repositories:

- Triggers the student-facing autograding run
- Runs `scripts/build_autograde_payload.py --variant student`
- Validates the metadata-free student contract used in Classroom

Students see assignment autograding results from `classroom.yml` in the GitHub Actions tab of their Classroom repository.

## Development Workflow

Recommended workflow for creating and testing exercises:

> Warning: In the source repository, canonical exercise-specific tests belong under `exercises/<construct>/<exercise_key>/tests/`. Any remaining flattened `tests/test_exNNN_slug.py` files are transitional compatibility or migration-debt surfaces only; do not create new ones.

```bash
# 1. Create a new branch
git checkout -b add-ex042-variables

# 2. Generate the exercise
uv run python scripts/new_exercise.py ex042 "Variables and Types" \
  --construct sequence \
  --type modify \
  --slug variables_and_types

# 3. Author the student notebook
uv run jupyter lab \
  exercises/sequence/ex042_sequence_modify_variables_and_types/notebooks/student.ipynb

# 4. Write exercise-local tests
$EDITOR \
  exercises/sequence/ex042_sequence_modify_variables_and_types/tests/test_ex042_sequence_modify_variables_and_types.py

# 5. Complete the solution notebook
uv run jupyter lab \
  exercises/sequence/ex042_sequence_modify_variables_and_types/notebooks/solution.ipynb

# 6. Verify tests pass on the solution notebook
uv run ./scripts/verify_solutions.sh \
  exercises/sequence/ex042_sequence_modify_variables_and_types/tests/test_ex042_sequence_modify_variables_and_types.py -v

# 7. Verify the student notebook path
uv run pytest \
  exercises/sequence/ex042_sequence_modify_variables_and_types/tests/test_ex042_sequence_modify_variables_and_types.py -v

# 8. Run the quality checks
uv run python scripts/verify_exercise_quality.py \
  ex042_sequence_modify_variables_and_types

# 9. Commit and push
git add exercises/sequence/ex042_sequence_modify_variables_and_types/
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
- If using transitional compatibility, ensure the mapped solution notebook exists

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

## CI/CD Workflows

### `tests.yml`

Runs on every push and pull request for source-repository validation:

- Installs dependencies
- Validates pytest collection/discovery
- Runs the explicit solution-variant test pass for the authoring repository

### `tests-solutions.yml`

Manual maintainer workflow (`workflow_dispatch`) for targeted solution reruns:

- Uses explicit `--variant solution` orchestration
- Accepts optional forwarded pytest args for focused reruns
- Useful when a maintainer wants to re-check specific exercise tests without re-running the full push/PR workflow

Trigger manually in the GitHub Actions tab.

### `template_repo_files/.github/workflows/classroom.yml`

Exported GitHub Classroom autograding workflow:

- Copied into assignment repositories generated from this source repo
- Runs the student variant via `scripts/build_autograde_payload.py --variant student`
- Validates the metadata-free student notebook contract, not the source-repository authoring contract
