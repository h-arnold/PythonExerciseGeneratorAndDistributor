# Development Guide

This guide is for contributors and maintainers working on the Python Tutor Exercises infrastructure.

> Source of truth: execution and variant contracts are defined in [docs/execution-model.md](execution-model.md).

## Repository status

The source repository has completed the exercise-local layout cutover. Treat `--variant` and `PYTUTOR_ACTIVE_VARIANT` as canonical for selection logic, and treat derived packaging outputs as non-authoring surfaces.

## Development Setup

Follow the [Setup Guide](setup.md) to install dependencies and configure your environment.

After cloning the repository, set up the managed virtual environment and run commands through `uv`:

```bash
uv sync

# Optionally activate the virtualenv for ad-hoc work
source .venv/bin/activate

# Or prefix commands with uv run (preferred)
uv run python -V
```

## Repository Architecture

### Key Design Decisions

1. **Jupyter notebooks for student work**: Familiar, interactive environment for learners
2. **pytest for grading**: Industry-standard, automated, works with GitHub Classroom
3. **Tagged cells**: Metadata-based extraction avoids fragile comment parsing
4. **Parallel notebook sets**: Student and solution notebooks tested by the same code
5. **Pure stdlib grading**: No nbformat/nbclient dependency reduces installation friction

### Code Organisation

- `exercises/<construct>/<exercise_key>/`: Canonical authoring home for exercise-specific assets and `exercise.json`
- `exercise_runtime_support/exercise_framework/`: Core grading framework (runtime execution, assertions, reporting)
- `exercise_runtime_support/notebook_grader.py`: Low-level notebook parsing and execution helpers used by the framework
- `scripts/new_exercise.py`: Exercise scaffolding tool
- `scripts/verify_solutions.sh`: Helper to test solutions via `--variant solution`
- `scripts/verify_exercise_quality.py`: Static checks for newly scaffolded exercises
- `AGENTS.md`: Repo-wide Copilot context
- `.github/agents/exercise_generation.md.agent.md`: Exercise generation custom agent
- `scripts/template_repo_cli/`: Source for the GitHub Classroom template repository CLI

The canonical source-repository authoring model is now exercise-local: `exercises/<construct>/<exercise_key>/notebooks/{student,solution}.ipynb` with `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`. Top-level `notebooks/`, `notebooks/solutions/`, and exercise-specific files materialised under the root `tests/` tree are derived compatibility surfaces only when explicitly generated.

Run the helper directly during development:

```bash
./scripts/verify_solutions.sh
```

## Working on the Grading System

### `exercise_runtime_support.exercise_framework`

The grading system now uses the exercise framework, which wraps the low-level notebook grader.

Import the canonical public helper surface from `exercise_runtime_support.exercise_framework`.
The supported runtime and path helpers are re-exported from
`exercise_runtime_support/exercise_framework/__init__.py`; treat compatibility wrappers as
internal shims rather than the primary contributor-facing API.

Core helpers (via `exercise_runtime_support.exercise_framework`):

1. **`resolve_exercise_notebook_path()`**: Resolves an exercise-local notebook from an `exercise_key`, respecting the active variant contract (`--variant` / `PYTUTOR_ACTIVE_VARIANT`)
2. **`resolve_notebook_path()`**: Resolves an explicit notebook location using the same active variant contract
3. **`extract_tagged_code()`**: Parses `.ipynb` JSON and concatenates source from tagged cells
4. **`exec_tagged_code()`**: Extracts and executes code, returning the namespace
5. **`run_cell_and_capture_output()`**: Executes a tagged code cell and returns stdout (primary test helper)
6. **`run_cell_with_input()`**: Executes a tagged code cell while supplying mocked `input()` values
7. **`get_explanation_cell()`**: Retrieves markdown content for tagged explanation/reflection cells

Exercise-specific expected outputs, prompts, and input data should live in helper modules within
`exercises/<construct>/<exercise_key>/tests/` so each exercise keeps its own canonical support data next to the canonical test file.

**Design principles**:

- Pure stdlib (no external notebook libraries)
- Simple error messages for students
- Fast execution (no unnecessary processing)

**Testing changes**:

```bash
# Always test against the solution notebooks first
uv run python scripts/run_pytest_variant.py --variant solution -q

# Focus on a specific exercise (still targeting solutions)
uv run python scripts/run_pytest_variant.py --variant solution \
    exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py -q

# Only switch to student notebooks when validating the classroom experience
uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py -q
```

### Adding Features to the Grader

When modifying grading logic:

1. **Preserve backwards compatibility**: Existing tests must continue to work
2. **Keep it simple**: Students need to understand error messages
3. **Document behaviour**: Update `docs/testing-framework.md`
4. **Test edge cases**: Invalid JSON, missing tags, malformed cells

## Autograding Development Workflow

### Run the autograde plugin locally

Always exercise the pytest plugin with an explicit results path so the Classroom payload can be inspected:

```bash
uv run python scripts/build_autograde_payload.py \
    --variant solution \
    --pytest-args=-q \
    --results-json=tmp/autograde/solutions.json

uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py -q \
    --autograde-results-path tmp/autograde/student.json
```

The first command targets the instructor notebooks; the second intentionally hits the student notebooks to confirm failure messaging. Replace `exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py` with focused paths as needed.

### Build Classroom payloads with the CLI

Use `scripts/build_autograde_payload.py` to mirror the GitHub Classroom workflow. Pass `--variant <student|solution>` so the same contract is used locally and in CI:

```bash
uv run python scripts/build_autograde_payload.py \
    --variant solution \
    --pytest-args=-q \
    --pytest-args=exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py \
    --results-json=tmp/autograde/results.json
```

If you omit `--variant`, the script exercises the solution notebooks. The CLI writes both the raw plugin JSON and the Base64 payload expected by `autograding-grading-reporter`. Full reference: [docs/autograding-cli.md](autograding-cli.md).

### Test workflow changes safely

- Use [act](https://github.com/nektos/act) to dry-run workflow edits against the repository configuration before pushing
- Push experiment branches to a sandbox Classroom template and run the full workflow end-to-end
- Keep payload fields backward compatible: preserve the plugin option names, JSON structure, and Base64 encoding so existing Classroom assignments keep working
- Review the GitHub Classroom integration guidance in [docs/github-classroom-autograding-guide.md](github-classroom-autograding-guide.md) when adjusting CI steps

## Working on the Exercise Generator

### `new_exercise.py`

The generator scaffolds new exercises with consistent structure.

**Key functions**:

- `_make_notebook_with_parts()`: Creates notebook JSON structure
- `_validate_and_parse_args()`: Validates command-line arguments
- `main()`: Orchestrates file creation

**Testing changes**:

```bash
# From the repository root
uv run scripts/new_exercise.py ex999 "Test" \
    --construct sequence --type modify --slug test_exercise

# Verify created files
ls exercises/sequence/ex999_sequence_modify_test_exercise/
ls exercises/sequence/ex999_sequence_modify_test_exercise/notebooks/
ls exercises/sequence/ex999_sequence_modify_test_exercise/tests/

# Run static verification (fast checks for structure and metadata)
uv run scripts/verify_exercise_quality.py ex999_sequence_modify_test_exercise

# Remove the scaffolding when done experimenting
rm -rf exercises/sequence/ex999_sequence_modify_test_exercise
```

### Extending the Generator

When adding features:

1. **Update argument parsing**: Add new CLI flags if needed
2. **Update template generation**: Modify `_make_notebook_with_parts()` for notebook changes
3. **Update documentation**: Reflect changes in `docs/exercise-generation-cli.md` (instructions for using the exercise generation CLI tool to scaffold new Python exercises)
4. **Test the generated output**: Ensure notebooks and tests work correctly

## Code Quality Standards

### Linting

All code must pass Ruff checks (run via `uv`):

```bash
uv run ruff check .
```

Auto-fix where possible:

```bash
uv run ruff check --fix .
```

Use Ruff's formatter for Python sources:

```bash
uv run ruff format
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
def test_new_feature() -> None:
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

Repository CI and exported Classroom autograding are separate surfaces.

**`tests.yml`**:

- Runs on push/PR
- Validates pytest collection/discovery in the source repository
- Runs the explicit `--variant solution` authoring-repo pass

**`tests-solutions.yml`**:

- Manual trigger
- Maintainer-focused targeted rerun of the explicit `--variant solution` pass
- Accepts optional pytest args for focused checks

**`template_repo_files/.github/workflows/classroom.yml`**:

- Exported to Classroom/template repositories
- Runs `scripts/build_autograde_payload.py --variant student`
- Validates the metadata-free student contract rather than the source-repository authoring contract

## Updating Exercises

When updating existing exercises:

1. **Preserve exercise IDs**: Never change exNNN identifiers
2. **Update both notebooks**: Student and solution
3. **Update tests**: If behaviour changes
4. **Verify**: Run both student and solution tests

## Deprecating Exercises

If an exercise needs to be removed:

1. **Don't delete**: Move to `exercises/deprecated/<exercise_key>/`
2. **Update README**: Document why it was deprecated
3. **Keep tests**: Mark with `@pytest.mark.skip` and reason
4. **Remove from student notebooks**: But keep in repository for reference

## GitHub Copilot Integration

### Custom Instructions

`AGENTS.md` provides repo-wide context to Copilot.

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
python -c "import json; json.load(open('exercises/sequence/ex004_sequence_debug_syntax/notebooks/student.ipynb'))"
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
- `docs/exercise-generation-cli.md`: Instructions for using the exercise generation CLI tool to scaffold new Python exercises
- `docs/setup.md`: Installation and configuration
- `docs/development.md`: This file - contributor guide
