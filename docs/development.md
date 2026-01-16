# Development Guide

This guide is for contributors and maintainers working on the PythonTutorExercises repository infrastructure.

## Development Setup

Follow the [Setup Guide](setup.md) to install dependencies and configure your environment.

## Repository Architecture

### Key Design Decisions

1. **Jupyter notebooks for student work**: Familiar, interactive environment for learners
2. **pytest for grading**: Industry-standard, automated, works with GitHub Classroom
3. **Tagged cells**: Metadata-based extraction avoids fragile comment parsing
4. **Parallel notebook sets**: Student and solution notebooks tested by the same code
5. **Pure stdlib grading**: No nbformat/nbclient dependency reduces installation friction

### Code Organisation

- `tests/notebook_grader.py`: Core grading logic (extract and execute tagged cells)
- `scripts/new_exercise.py`: Exercise scaffolding tool
- `scripts/verify_solutions.sh`: Helper to test solutions
- `.github/copilot-instructions.md`: Repo-wide Copilot context
- `.github/agents/exercise_generation.md.agent.md`: Exercise generation custom agent

## Working on the Grading System

### `notebook_grader.py`

The grading system has three main functions:

1. **`resolve_notebook_path()`**: Redirects to alternative notebook directories via `PYTUTOR_NOTEBOOKS_DIR`
2. **`extract_tagged_code()`**: Parses `.ipynb` JSON and concatenates source from tagged cells
3. **`exec_tagged_code()`**: Extracts and executes code, returning the namespace

**Design principles**:
- Pure stdlib (no external notebook libraries)
- Simple error messages for students
- Fast execution (no unnecessary processing)

**Testing changes**:
```bash
# Test the grading system itself
pytest tests/ -v

# Test against various notebooks
pytest tests/test_ex001_sanity.py -v
pytest tests/test_ex002_sequence_modify_basics.py -v
```

### Adding Features to the Grader

When modifying `notebook_grader.py`:

1. **Preserve backwards compatibility**: Existing tests must continue to work
2. **Keep it simple**: Students need to understand error messages
3. **Document behaviour**: Update `docs/testing-framework.md`
4. **Test edge cases**: Invalid JSON, missing tags, malformed cells

## Working on the Exercise Generator

### `new_exercise.py`

The generator scaffolds new exercises with consistent structure.

**Key functions**:
- `_make_notebook_with_parts()`: Creates notebook JSON structure
- `_validate_and_parse_args()`: Validates command-line arguments
- `main()`: Orchestrates file creation

**Testing changes**:
```bash
# Test in a temporary directory
cd /tmp
python /path/to/PythonTutorExercises/scripts/new_exercise.py ex999 "Test" --slug test_exercise

# Verify created files
ls -la exercises/ex999_test_exercise/
ls -la notebooks/ex999_test_exercise.ipynb
ls -la notebooks/solutions/ex999_test_exercise.ipynb
ls -la tests/test_ex999_test_exercise.py

# Clean up
rm -rf exercises/ex999_test_exercise notebooks/ex999_test_exercise.ipynb \
       notebooks/solutions/ex999_test_exercise.ipynb tests/test_ex999_test_exercise.py
```

### Extending the Generator

When adding features:

1. **Update argument parsing**: Add new CLI flags if needed
2. **Update template generation**: Modify `_make_notebook_with_parts()` for notebook changes
3. **Update documentation**: Reflect changes in `docs/exercise-generation.md`
4. **Test the generated output**: Ensure notebooks and tests work correctly

## Code Quality Standards

### Linting

All code must pass Ruff checks:
```bash
ruff check .
```

Auto-fix where possible:
```bash
ruff check --fix .
```

### Type Hints

Use type hints for function signatures (Python 3.11+ style):
```python
def extract_tagged_code(notebook_path: str | Path, *, tag: str = "student") -> str:
    ...
```

### Docstrings

Public functions must have docstrings:
```python
def exec_tagged_code(notebook_path: str | Path, *, tag: str = "student") -> dict[str, Any]:
    """Execute tagged code cells and return the resulting namespace.
    
    Args:
        notebook_path: Path to the .ipynb file
        tag: Cell metadata tag to extract and execute (default: "student")
        
    Returns:
        Dictionary containing the execution namespace
        
    Raises:
        NotebookGradingError: If extraction or execution fails
    """
```

### Testing

All new features must include tests:
```python
def test_new_feature():
    # Arrange
    input_data = ...
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

## Contributing Exercises

### Exercise Quality Checklist

Before submitting an exercise:

- [ ] Notebook has clear instructions and examples
- [ ] Exercise cells are tagged correctly
- [ ] Tests cover positive cases, edge cases, and invalid inputs
- [ ] Tests pass on solution notebook
- [ ] Tests fail on student notebook (until completed)
- [ ] Solution is pedagogically appropriate (no advanced features)
- [ ] Supporting documentation exists (README.md, OVERVIEW.md)
- [ ] Exercise fits the construct progression

### Pull Request Process

1. **Create a feature branch**: `git checkout -b add-exNNN-topic`
2. **Make focused commits**: One exercise per PR when possible
3. **Write clear commit messages**: "Add ex042: Variables and Types"
4. **Update documentation**: If adding new patterns or features
5. **Request review**: Tag a maintainer for review
6. **Address feedback**: Make requested changes
7. **Squash if needed**: Keep history clean

## CI/CD Maintenance

### GitHub Actions Workflows

**`tests.yml`**:
- Runs on push/PR
- Tests student notebooks
- Fast feedback for contributors

**`tests-solutions.yml`**:
- Manual trigger
- Tests solution notebooks
- Validates instructor answers

## Updating Exercises

When updating existing exercises:

1. **Preserve exercise IDs**: Never change exNNN identifiers
2. **Update both notebooks**: Student and solution
3. **Update tests**: If behaviour changes
4. **Verify**: Run both student and solution tests

## Deprecating Exercises

If an exercise needs to be removed:

1. **Don't delete**: Move to `exercises/deprecated/exNNN_slug/`
2. **Update README**: Document why it was deprecated
3. **Keep tests**: Mark with `@pytest.mark.skip` and reason
4. **Remove from student notebooks**: But keep in repository for reference

## GitHub Copilot Integration

### Custom Instructions

`.github/copilot-instructions.md` provides repo-wide context to Copilot.

**What to include**:
- Project structure overview
- Coding standards specific to this repo
- Links to detailed documentation
- Common patterns and conventions

**What NOT to include**:
- Generic best practices
- Content that duplicates custom agent instructions
- Overly verbose explanations

### Exercise Generation Agent

`.github/agents/exercise_generation.md.agent.md` is a custom agent for creating exercises.

**Maintenance**:
- Keep aligned with actual exercise patterns
- Update when pedagogical approach changes
- Test by generating sample exercises

## Troubleshooting Development Issues

### Tests Pass Locally But Fail in CI

Check:
- Python version matches CI (see `.github/workflows/tests.yml`)
- Dependencies are pinned or have minimum versions
- No reliance on local files or environment variables
- Tests are deterministic (no randomness or time-based behaviour)

### Notebook Won't Load in Jupyter

Validate JSON:
```bash
python -c "import json; json.load(open('notebooks/exNNN_slug.ipynb'))"
```

If invalid, fix manually or regenerate with the scaffolder.

### Generator Creates Wrong File Paths

Check:
- Running from repository root
- Exercise ID format is correct (exNNN)
- Slug is valid snake_case

## Getting Help

- **Documentation**: Start with `docs/` folder
- **Issues**: Check GitHub issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Code**: Read the source - it's kept simple deliberately

## Making Documentation Changes

When updating documentation:

1. **Be concise**: No generic waffle, only repo-specific content
2. **Be accurate**: Documentation must reflect actual codebase
3. **Use examples**: Show, don't just tell
4. **Cross-reference**: Link between related docs
5. **Test instructions**: Verify commands actually work

Documentation structure:
- `docs/project-structure.md`: Repository organisation
- `docs/testing-framework.md`: How grading works
- `docs/exercise-generation.md`: Creating exercises
- `docs/setup.md`: Installation and configuration
- `docs/development.md`: This file - contributor guide
