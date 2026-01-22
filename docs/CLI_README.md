# Template Repository CLI

A command-line tool for creating GitHub template repositories from subsets of Python exercises. This tool is designed to help instructors create customized exercise sets for GitHub Classroom.

## Installation

The CLI is part of this repository. Make sure you have the development dependencies installed via uv:

```bash
python -m pip install --upgrade pip uv
uv sync
```

After syncing, you can run `template_repo_cli --help` to confirm the console script is available (the script will be on your PATH when the virtual environment is activated).

Note: Installing the package with the `.[dev]` extras also provides a console script named `template_repo_cli` (exposed via `pyproject.toml`) so you can run `template_repo_cli --help` after installation.

## Prerequisites

- Python 3.11 or higher
- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated (required for creating repositories)
- `gh auth login` completed (for creating repositories)

## Usage

### Basic Commands

The CLI provides four main commands:

1. **`create`** - Create a GitHub template repository
2. **`update-repo`** - Push a refreshed template into an existing repository
3. **`list`** - List available exercises
4. **`validate`** - Validate exercise selection

### Global Options

- `--dry-run` - Build and validate without executing `gh` commands (create and update-repo)
- `--verbose` / `-v` - Show detailed progress information
- `--output-dir PATH` - Copy the packaged workspace to PATH instead of cleaning up the temp directory

## Examples

### List Available Exercises

```bash
# List all exercises
template_repo_cli list

# List exercises in a specific construct
template_repo_cli list --construct sequence

# Output as JSON
template_repo_cli list --format json
```

### Validate Selection

```bash
# Validate exercises by construct
template_repo_cli validate --construct sequence

# Validate by construct and type
template_repo_cli validate --construct sequence --type modify
```

### Create Template Repository

#### By Construct

```bash
# Create template with all sequence exercises
template_repo_cli create \
  --construct sequence \
  --repo-name sequence-exercises

# Create template with multiple constructs
template_repo_cli create \
  --construct sequence selection iteration \
  --repo-name week1-exercises \
  --name "Week 1: Control Flow Exercises"
```

#### By Type

```bash
# Create template with only modify exercises from sequence
template_repo_cli create \
  --construct sequence \
  --type modify \
  --repo-name sequence-modify \
  --name "Sequence Modification Exercises"
```

#### By Specific Notebooks

```bash
# Create template with specific exercises
template_repo_cli create \
  --notebooks ex001_sanity ex002_sequence_modify_basics \
  --repo-name getting-started \
  --name "Getting Started with Python"

# Create template with pattern matching
template_repo_cli create \
  --notebooks "ex00*" \
  --repo-name first-ten \
  --name "First Ten Exercises"
```

#### Advanced Options

```bash
# Create private repository in an organization
template_repo_cli create \
  --construct sequence \
  --repo-name sequence-exercises \
  --private \
  --org my-organization

# Test without creating the repository (dry-run)
template_repo_cli --dry-run create \
  --construct sequence \
  --repo-name test-repo

# Save to local directory instead of creating repository
template_repo_cli \
  --output-dir ./my-template \
  --dry-run \
  create \
  --construct sequence \
  --repo-name sequence-exercises

# Create a repository but do NOT mark it as a template (opposite of the default)
template_repo_cli create \
  --construct sequence \
  --repo-name sequence-exercises \
  --no-template

# Create a repository based on an existing GitHub template repository
template_repo_cli create \
  --construct sequence \
  --repo-name sequence-exercises \
  --template-repo "owner/template-repo"
```

#### Verbose Mode

```bash
# Show detailed progress
template_repo_cli --verbose create \
  --construct sequence \
  --repo-name sequence-exercises

```

### Update Existing Repository

`update-repo` packages the selected exercises and force-pushes them into an existing repository. The target repository must already exist, and you should supply it as either a simple slug (for your personal account) or `owner/repo` when pushing elsewhere. The branch defaults to `main`.

```bash
# Push updated content into an existing repository
template_repo_cli update-repo \
  --construct sequence \
  --repo-name organisation/sequence-exercises \
  --branch main

# Preview the update without pushing
template_repo_cli --dry-run update-repo \
  --notebooks ex001_sanity ex002_sequence_modify_basics \
  --repo-name organisation/sequence-exercises

# Keep a local copy of the packaged workspace after the push
template_repo_cli --output-dir ./latest-template update-repo \
  --construct sequence \
  --repo-name organisation/sequence-exercises
```

The `--name` flag is optional when updating but, if provided, refreshes the README title in the generated workspace before it is pushed.

## What Gets Included in Templates

Each generated template repository includes:

### Exercise Files

- Student notebooks (`notebooks/exNNN_slug.ipynb`)
- Test files (`tests/test_exNNN_slug.py`)

### Infrastructure Files

- `pyproject.toml` - Project configuration (micropip-compatible for VS Code web)
- `pytest.ini` - Test configuration
- `.gitignore` - Git ignore patterns
- `README.md` - Auto-generated with exercise list
- `INSTRUCTIONS.md` - Student setup guide

### Development Setup

- `.devcontainer/devcontainer.json` - VS Code dev container configuration with all settings and extensions
- `.github/workflows/tests.yml` - CI/CD for autograding

### Testing Framework

The template includes only the selected test files for the exercises. The full grading framework (for example, `tests/notebook_grader.py` and other infrastructure) is **not** included by default. If you want the complete grading framework to be present in generated templates, add the required files to the `template_repo_files` directory before creating the template. See `template_repo_files/README.md.template` for guidance on what to include.

## Available Constructs

- `sequence` - Basic sequential execution
- `selection` - Conditional statements
- `iteration` - Loops
- `data_types` - Type system
- `lists` - List operations
- `dictionaries` - Dictionary operations
- `functions` - Function definitions
- `file_handling` - File I/O
- `exceptions` - Error handling
- `libraries` - External libraries
- `oop` - Object-oriented programming

## Available Types

- `debug` - Fix broken code
- `modify` - Change working code
- `make` - Create from scratch

## GitHub Classroom Integration

Templates created by this tool are designed to work seamlessly with GitHub Classroom:

1. **Template Repository** - Repositories are marked as templates by default
2. **Autograding** - GitHub Actions workflow included for automatic testing
3. **Student-Ready** - Complete setup instructions and VS Code configuration
4. **Web Compatible** - All dependencies are micropip-compatible for VS Code for the Web

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
template_repo_cli validate --construct sequence
```

## Development

### Running Tests

```bash
# Run all CLI tests
pytest tests/template_repo_cli/ -v

# Run specific test file
pytest tests/template_repo_cli/test_selector.py -v

# Run with coverage
pytest tests/template_repo_cli/ --cov=scripts.template_repo_cli
```

### Code Quality

```bash
# Run linter
ruff check scripts/template_repo_cli/

# Auto-fix issues
ruff check --fix scripts/template_repo_cli/
```

## Architecture

The CLI is organized into modular components:

```
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

## License

See repository LICENSE file.
