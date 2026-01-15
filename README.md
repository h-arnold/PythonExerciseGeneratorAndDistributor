# Bassaleg Python Tutor Exercises

Notebook-based Python exercises with automated grading via pytest, designed for secondary school students learning Python.

## Repo layout

- `notebooks/`
	- One notebook per exercise: `notebooks/exNNN_slug.ipynb`
	- Students write code **inline** in a dedicated exercise cell that **must** be tagged with `exerciseN` in the cell metadata (e.g., `exercise1`, `exercise2`). 
	- Teacher/CI solution mirrors (optional): `notebooks/solutions/exNNN_slug.ipynb`
- `tests/`
	- `tests/test_exNNN_slug.py` contains automated tests
	- Tests extract + execute the student cell (see `tests/notebook_grader.py`)
- `scripts/new_exercise.py`
	- Scaffolds a new exercise skeleton

Optional (teacher notes / materials):
- `exercises/`
	- One folder per exercise: `exercises/exNNN_slug/README.md`

## Quickstart

Create a virtualenv and install dev dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Run all tests:

```bash
pytest -q
```

See the [Setup Guide](docs/setup.md) for detailed instructions.

## For Teachers

Use the [exercise generation custom agent](https://github.com/features/copilot) to create new exercises. Simply describe the exercise you want and the agent will generate the notebook, tests, and supporting materials.

For manual scaffolding or to understand the structure, see the [Exercise Generation Guide](docs/exercise-generation.md).

### Verifying Solutions

```bash
# Test solution notebooks
scripts/verify_solutions.sh -q
```

## Documentation

- **[Project Structure](docs/project-structure.md)** - Repository organisation and file layout
- **[Testing Framework](docs/testing-framework.md)** - How the automated grading works
- **[Exercise Generation](docs/exercise-generation.md)** - Creating new exercises
- **[Setup Guide](docs/setup.md)** - Installation and configuration
- **[Development Guide](docs/development.md)** - Contributing and maintenance

## Quick Reference

### Repository Structure

```
notebooks/          # Student exercise notebooks
tests/              # Automated grading tests
exercises/          # Teacher materials (organised by construct/type)
scripts/            # Utilities (exercise generator, solution verifier)
docs/               # Documentation
```

### Common Commands

```bash
pytest -q                               # Run tests
pytest tests/test_ex001_sanity.py -v   # Test specific exercise
jupyter lab                             # Open Jupyter interface
ruff check .                            # Lint code
scripts/verify_solutions.sh -q          # Test solutions
```

## How It Works

1. Students write code in **tagged cells** (`exercise1`, `exercise2`, etc.) in Jupyter notebooks
2. Tests use `exec_tagged_code()` to extract and execute these cells
3. Assertions verify correctness
4. GitHub Actions runs tests automatically on push/PR

See [Testing Framework](docs/testing-framework.md) for technical details.

## GitHub Classroom Integration

This repository is designed for GitHub Classroom:
- Autograding runs via `.github/workflows/tests.yml`
- Students get immediate feedback on test results
- Teachers can track progress through GitHub Classroom dashboard

## License

See [LICENSE](LICENSE) file for details.
