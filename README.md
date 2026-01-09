# Bassaleg Python Tutor Exercises

Notebook-based Python exercises with automated grading via pytest, designed for secondary school students learning Python.

## What is This?

A collection of Jupyter notebook exercises where:
- **Students** write code in tagged notebook cells
- **pytest** automatically grades their work
- **GitHub Classroom** integration provides instant feedback

## For Students

### Getting Started

1. **Clone the repository** or accept the GitHub Classroom assignment
2. **Install dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. **Open a notebook** in Jupyter Lab:
   ```bash
   jupyter lab
   ```
4. **Complete the exercises** in cells tagged `exercise1`, `exercise2`, etc.
5. **Test your work**:
   ```bash
   pytest -q
   ```

See the [Setup Guide](docs/setup.md) for detailed instructions.

## For Teachers

### Creating Exercises

```bash
# Single exercise
python scripts/new_exercise.py ex042 "Variables and Types" --slug variables_and_types

# Multi-part exercise (10 parts in one notebook)
python scripts/new_exercise.py ex043 "Week 1 Practice" --slug week1 --parts 10
```

See the [Exercise Generation Guide](docs/exercise-generation.md) for detailed workflow.

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
