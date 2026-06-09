# Template Repository CLI

A command-line tool for creating GitHub template repositories from subsets of Python exercises. This tool helps instructors create customised exercise sets for GitHub Classroom.

> Source of truth: The template CLI follows a canonical-only exercise-local contract with no legacy compatibility paths. See [execution-model.md](execution-model.md) for the canonical contract.

## Installation

The CLI is part of this repository. Install the development dependencies via uv:

```bash
uv sync
```

After syncing, run `repoman --help` to confirm the console script is available (the script is on your `PATH` when the virtual environment is activated).

Alternatively, run the CLI as a module: `uv run python -m scripts.template_repo_cli --help`.

> **Note on naming:** The package source lives under `scripts/template_repo_cli/`, but the preferred console entry point is `repoman` (short for *repository manager*). Both `template_repo_cli` and `repoman` invoke the same CLI — use `repoman` for everyday work.

## Prerequisites

- Python 3.11 or higher
- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated (required for creating/updating repositories)
- `gh auth login` completed (for creating/updating repositories)

## Usage

### Basic Commands

The CLI provides four main commands:

1. **`create`** — Create a GitHub template repository
2. **`update`** — Push a refreshed template into an existing repository
3. **`list`** — List available exercises
4. **`validate`** — Validate exercise selection

### Global Options

- `--dry-run` — Build and validate without executing `gh` commands (create and update)
- `--verbose` / `-v` — Show detailed progress information
- `--output-dir PATH` — Copy the packaged workspace to `PATH` instead of cleaning up the temp directory

## Examples

### List Available Exercises

```bash
# List all exercises
repoman list

# List exercises in a specific construct
repoman list --construct sequence

# Output as JSON
repoman list --format json
```

### Validate Selection

```bash
# Validate exercises by construct
repoman validate --construct sequence

# Validate by construct and type
repoman validate --construct sequence --type modify
```

### Create Template Repository

#### By Construct

```bash
# Create template with all sequence exercises
repoman create \
  --construct sequence \
  --repo-name sequence-exercises

# Create template with multiple constructs
repoman create \
  --construct sequence selection iteration \
  --repo-name week1-exercises \
  --name "Week 1: Control Flow Exercises"
```

#### By Type

```bash
# Create template with only modify exercises from sequence
repoman create \
  --construct sequence \
  --type modify \
  --repo-name sequence-modify \
  --name "Sequence Modification Exercises"
```

#### By Specific Exercise Keys

> Phase 10 breaking change: the old `--notebooks` selector has been removed. Use
> `--exercise-keys` for explicit exercise selection and exercise-key glob
> patterns.

```bash
# Create template with specific exercises
repoman create \
  --exercise-keys ex002_sequence_modify_basics ex003_sequence_modify_variables \
  --repo-name getting-started \
  --name "Getting Started with Python"

# Create template with pattern matching
repoman create \
  --exercise-keys "ex00*" \
  --repo-name first-ten \
  --name "First Ten Exercises"
```

#### Advanced Options

```bash
# Create private repository in an organisation
repoman create \
  --construct sequence \
  --repo-name sequence-exercises \
  --private \
  --org my-organization

# Test without creating the repository (dry-run)
repoman --dry-run create \
  --construct sequence \
  --repo-name test-repo

# Save to local directory instead of creating repository
repoman \
  --output-dir ./my-template \
  --dry-run \
  create \
  --construct sequence \
  --repo-name sequence-exercises

# Create a repository but do NOT mark it as a template (opposite of the default)
repoman create \
  --construct sequence \
  --repo-name sequence-exercises \
  --no-template

# Create a repository based on an existing GitHub template repository
repoman create \
  --construct sequence \
  --repo-name sequence-exercises \
  --template-repo "owner/template-repo"
```

#### Verbose Mode

```bash
# Show detailed progress
repoman --verbose create \
  --construct sequence \
  --repo-name sequence-exercises
```

### Update Existing Repository

`update` (formerly `update-repo`) packages the selected exercises and force-pushes them into an existing repository. The target repository must already exist; supply it as either a simple slug (for your personal account) or `owner/repo` when pushing elsewhere. The branch defaults to `main`.

```bash
# Push updated content into an existing repository
repoman update \
  --construct sequence \
  --repo-name organisation/sequence-exercises \
  --branch main

# Preview the update without pushing
repoman --dry-run update \
  --exercise-keys ex002_sequence_modify_basics ex003_sequence_modify_variables \
  --repo-name organisation/sequence-exercises

# Keep a local copy of the packaged workspace after the push
repoman --output-dir ./latest-template update \
  --construct sequence \
  --repo-name organisation/sequence-exercises
```

The `--name` flag is optional when updating but, if provided, refreshes the README title in the generated workspace before it is pushed.

## What Gets Included in Templates

Each generated template repository includes:

### Exercise Files

- `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- `exercises/<construct>/<exercise_key>/tests/`
- Exported per-exercise metadata (`exercise.json`); no solution notebooks and no flattened notebook/test mirrors

### Infrastructure Files

- `pyproject.toml` — Project configuration (micropip-compatible for VS Code web)
- `pytest.ini` — Test configuration
- `.gitignore` — Git ignore patterns
- `README.md` — Auto-generated with exercise list
- `INSTRUCTIONS.md` — Student setup guide

### Development Setup

- `.devcontainer/devcontainer.json` — VS Code dev container configuration with all settings and extensions
- `.github/workflows/classroom.yml` — GitHub Classroom autograding workflow

### Testing Framework

Generated templates include the selected exercise tests and the required shared test infrastructure used by the current checks and notebook self-check API:

- `tests/__init__.py`
- `tests/notebook_grader.py`
- `tests/autograde_plugin.py`
- `tests/helpers.py`
- `tests/test_autograde_plugin.py`
- `tests/test_build_autograde_payload.py`
- `tests/exercise_framework/` (runtime files only)
- `exercise_runtime_support/` (packaged runtime support package)
- `exercise_metadata/` (metadata-backed catalogue and resolver package)
- `exercises/<construct>/<exercise_key>/exercise.json`
- `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- `exercises/<construct>/<exercise_key>/tests/`

When these shared directories are copied into generated templates, non-runtime artefacts are excluded (`__pycache__`, `*.pyc`, and `test_*.py` / `*_test.py`).

This set is sufficient for exercise test imports, autograde payload/plugin checks, the generic programmatic student-checker API via `from exercise_runtime_support.student_checker import check_exercise`, and notebook self-check usage via `from exercise_runtime_support.student_checker import run_notebook_checks`. Packaged workspaces import `exercise_metadata` directly and rely on per-exercise metadata discovered via `exercise.json` files under the canonical exercise tree instead of compatibility fallbacks.

The export contract rejects authoring-only assets such as `solution.ipynb` and flattened notebook/test mirrors, while keeping student notebooks and canonical exercise-local tests at their canonical exercise-local paths.

## Available Constructs

- `sequence` — Basic sequential execution
- `selection` — Conditional statements
- `iteration` — Loops
- `data_types` — Type system
- `lists` — List operations
- `dictionaries` — Dictionary operations
- `functions` — Function definitions
- `file_handling` — File I/O
- `exceptions` — Error handling
- `libraries` — External libraries
- `oop` — Object-oriented programming

## Available Types

- `debug` — Fix broken code
- `modify` — Change working code
- `make` — Create from scratch

## GitHub Classroom Integration

Templates created by this tool are designed to work seamlessly with GitHub Classroom:

1. **Template Repository** — Repositories are marked as templates by default
2. **Autograding** — GitHub Actions workflow included for automatic testing
3. **Student-Ready** — Complete setup instructions and VS Code configuration
4. **Web Compatible** — All dependencies are micropip-compatible for VS Code for the Web

### Using with GitHub Classroom

1. Create a template repository using this CLI
2. In GitHub Classroom, create a new assignment
3. Select your template repository
4. Students can accept the assignment and start working
5. Tests run automatically on push via GitHub Actions

## Troubleshooting

### `gh` CLI Not Found

Install the GitHub CLI:

- macOS: `brew install gh`
- Windows: `winget install GitHub.cli`
- Linux: See <https://github.com/cli/cli#installation>

### Authentication Required

Run `gh auth login` and follow the prompts to authenticate.

### No Exercises Found

Make sure:

- The construct name is spelled correctly (lowercase)
- The exercise type is valid (`debug`, `modify`, or `make`)
- Exercises exist for the specified criteria

### Validation Errors

Run the `validate` command to check for missing files:

```bash
repoman validate --construct sequence
```

## Development

### Running Tests

```bash
# Run all CLI tests
uv run pytest tests/template_repo_cli/ -v

# Run specific test file
uv run pytest tests/template_repo_cli/test_selector.py -v

# Run with coverage
uv run pytest tests/template_repo_cli/ --cov=scripts.template_repo_cli
```

### Code Quality

```bash
# Run linter
uv run ruff check scripts/template_repo_cli/

# Auto-fix issues
uv run ruff check --fix scripts/template_repo_cli/
```

## Architecture

The CLI is organised into modular components:

```text
scripts/template_repo_cli/
├── cli.py              # Main entry point (argparse)
├── __main__.py         # Module execution support
├── core/
│   ├── selector.py     # Exercise selection logic
│   ├── collector.py    # File collection
│   ├── packager.py     # Template assembly
│   └── github.py       # GitHub operations (gh CLI wrapper)
└── utils/
    ├── validation.py   # Input validation
    └── filesystem.py   # File operations
```

## Contributing

This tool was built following Test-Driven Development (TDD):

- 138 comprehensive tests
- All tests passing
- Modular, maintainable architecture

When adding features:

1. Write tests first
2. Implement functionality
3. Ensure all tests pass
4. Run linter

## Authentication Notes

When running inside a GitHub Codespace, the environment sets a `GITHUB_TOKEN` scoped only to the current repository. This token does **not** have permission to create repositories in other organisations or your personal account. If you encounter authentication failures when running `create` or `update`:

```bash
unset GITHUB_TOKEN
gh auth login
```

`unset GITHUB_TOKEN` clears the auto-set, scoped token. `gh auth login` then prompts you to authenticate with full credentials (you can choose "Login with a browser" and use a token or web-based flow). After this, the CLI has the permissions needed to create and update repositories.

## Licence

See the repository `LICENSE` file for terms.
