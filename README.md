# PythonTutorExercises

This repository contains all of the Bassaleg Python Tutor Exercises and System Prompt for the Gemini Gem.

## Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Bassaleg-School/PythonTutorExercises.git
cd PythonTutorExercises
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. Install the package in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Using GitHub Copilot

This repository is configured for optimal use with GitHub Copilot:

1. Install the recommended VS Code extensions (you'll be prompted when opening the project)
2. Open any Python file in the `exercises/` directory
3. Copilot will provide suggestions based on function signatures, docstrings, and comments
4. Use Copilot Chat to ask questions about exercises or get help with solutions

## Project Structure

```
PythonTutorExercises/
├── exercises/          # Exercise files go here
│   ├── __init__.py
│   └── example_hello.py
├── tests/              # Test files go here
│   ├── __init__.py
│   └── test_example_hello.py
├── .vscode/            # VS Code configuration
│   ├── settings.json   # Python and Copilot settings
│   ├── launch.json     # Debug configurations
│   └── extensions.json # Recommended extensions
├── pyproject.toml      # Project configuration and dependencies
├── .gitignore
├── LICENSE
└── README.md
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=exercises --cov-report=term-missing
```

Run a specific test file:
```bash
pytest tests/test_example_hello.py
```

## Linting and Formatting

This project uses Ruff for linting and formatting.

Check for linting issues:
```bash
ruff check .
```

Auto-fix linting issues:
```bash
ruff check --fix .
```

Format code:
```bash
ruff format .
```

## Creating New Exercises

1. Create a new Python file in the `exercises/` directory (e.g., `exercises/my_exercise.py`)
2. Add exercise instructions in the docstring
3. Define function signatures with type hints
4. Create corresponding test file in `tests/` directory (e.g., `tests/test_my_exercise.py`)
5. Use Copilot to help generate solutions and tests

## Development Workflow

1. Write exercise description and function signature
2. Use Copilot to generate initial solution
3. Write tests to verify the solution
4. Run tests: `pytest`
5. Format code: `ruff format .`
6. Commit changes

## Contributing

When creating exercises:
- Include clear docstrings with examples
- Add type hints to function signatures
- Write comprehensive tests
- Follow PEP 8 style guide (enforced by Ruff)

## License

See LICENSE file for details.
