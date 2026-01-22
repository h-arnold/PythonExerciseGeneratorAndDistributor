# Exercise Generation CLI tool

This document describes how to use the CLI tool to scaffold new Python exercises in the repository.

## Quick Start

### Single Exercise

```bash
uv run python scripts/new_exercise.py ex042 "Variables and Types" --slug variables_and_types
```

For a debug exercise (scaffolds expected-output and explanation cells plus explanation tags):

```bash
uv run python scripts/new_exercise.py ex004 "Debug Syntax" --slug sequence_debug_syntax --type debug
```

This creates:

- `exercises/ex042_variables_and_types/__init__.py`
- `exercises/ex042_variables_and_types/README.md`
- `notebooks/ex042_variables_and_types.ipynb`
- `notebooks/solutions/ex042_variables_and_types.ipynb`
- `tests/test_ex042_variables_and_types.py`

### Multi-Part Exercise (10 exercises in one notebook)

```bash
uv run python scripts/new_exercise.py ex043 "Week 1 Practice" --slug week1 --parts 10
```

This creates the same structure but scaffolds 10 tagged cells (`exercise1` through `exercise10`) in the notebook.

## The `new_exercise.py` Script

### Purpose

Scaffolds the boilerplate for new exercises to ensure consistency across the repository.

### Command-Line Arguments

```
python scripts/new_exercise.py <id> <title> [--slug SLUG] [--parts N] [--type TYPE]
```

Run it through the managed environment, for example `uv run python scripts/new_exercise.py ...`, so the correct dependencies are used.

**Required**:

- `id`: Exercise identifier (format: `exNNN`, e.g., `ex001`, `ex042`)
- `title`: Human-readable title (e.g., "Variables and Types")

**Optional**:

- `--slug`: Snake-case slug for filenames (default: auto-generated from title)
- `--parts`: Number of exercise parts in one notebook (default: 1, max: 20)
- `--type`: Optional exercise type (one of `debug`, `modify`, `make`). When `--type debug` is used the scaffolder will include an "Expected output" markdown cell and an `explanationN` markdown cell for each exercise part.

### What Gets Created

#### 1. Exercise Directory

`exercises/CONSTRUCT/TYPE/exNNN_slug/`

The script creates a temporary folder at `exercises/exNNN_slug/`. Move this directory into the correct construct/type path after scaffolding to match the curriculum structure. Suggested destinations:

- **CONSTRUCT**: `sequence`, `selection`, `iteration`, `data_types`, `lists`, `dictionaries`, `functions`, `file_handling`, `exceptions`, `libraries`, `oop`
- **TYPE**: `debug`, `modify`, `make`

Created files:

- `__init__.py`: Keeps the package importable
- `README.md`: Prefilled with student prompt and teacher notes placeholders (update both sections)
- (Add manually) `OVERVIEW.md`: Detailed teaching notes

Instructor reference solutions live in the solution notebook mirror under `notebooks/solutions/`.

#### 2. Student Notebook

`notebooks/exNNN_slug.ipynb`

Contains:

- Markdown cell with title and instructions
- Code cell(s) tagged `exercise1`, `exercise2`, etc.
- For multi-part notebooks, a markdown prompt precedes each tagged cell
- Optional self-check cell (not graded)

Debug notebooks contain, for each part:

- A markdown cell describing expected behaviour and output
- A tagged code cell containing placeholder buggy code (`exerciseN`)
- A tagged explanation markdown cell (`explanationN`) that students complete after fixing the bug

For `--parts N`, creates N tagged exercise cells.

#### 3. Solution Notebook

`notebooks/solutions/exNNN_slug.ipynb`

Initially identical to the student notebook. You should:

- Fill in the exercise cells with correct solutions
- Verify tests pass: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest`

#### 4. Test File

`tests/test_exNNN_slug.py`

Contains:

- Imports for `run_cell_and_capture_output` (and, for debug exercises, `get_explanation_cell`) alongside pytest
- Placeholder tests that execute each tagged cell, assert output was produced, and guard against leaving the `TODO` placeholder in place
- Debug exercises also include parametrised checks ensuring each `explanationN` cell is populated with >10 characters
- For multi-part exercises, parametrised tests cover every exercise tag

## Post-Scaffolding Steps

After running `new_exercise.py`, you must:

### 1. Organise the Exercise Folder

Move `exercises/exNNN_slug/` to the correct location:

```bash
# Example: moving a sequence/modify exercise
mv exercises/ex042_variables_and_types exercises/sequence/modify/
```

### 2. Author the Notebook

Edit `notebooks/exNNN_slug.ipynb`:

- **Add context**: Explain the goal and provide 1-2 examples
- **Update exercise cells**:
  - Keep the cell tagged correctly (`exercise1`, `exercise2`, etc.)
  - Provide a clear function signature (typically `solve()`), or a clear prompt for output-based tasks
  - Add docstrings (after Functions construct is taught)
  - Replace placeholder prints with the intended starter code (`return "TODO"`, `raise NotImplementedError()`, or a buggy snippet for debug tasks)
- **Keep it focused**: Each exercise cell should target a single learning objective

**Notebook structure**:

```
1. Markdown: Title and goal
2. Markdown/Code: Examples or context
3. Code (tagged exercise1): Student solution cell
4. [Repeat for exercise2, exercise3, etc. if multi-part]
5. Code (untagged): Optional self-check cell
```

### 3. Write Tests

Edit `tests/test_exNNN_slug.py`:

Replace the placeholder test with real assertions. Two common patterns:

```python
# Option 1: assert on printed output (matches the scaffold)
from tests.notebook_grader import run_cell_and_capture_output

NOTEBOOK_PATH = "notebooks/ex042_variables_and_types.ipynb"


def test_exercise1_greets_user() -> None:
    output = run_cell_and_capture_output(NOTEBOOK_PATH, tag="exercise1")
    assert "Hello" in output
    assert "TODO" not in output
```

```python
# Option 2: execute the cell and inspect objects
from tests.notebook_grader import exec_tagged_code

NOTEBOOK_PATH = "notebooks/ex042_variables_and_types.ipynb"


def test_solve_returns_correct_value() -> None:
    ns = exec_tagged_code(NOTEBOOK_PATH, tag="exercise1")
    assert "solve" in ns, "'solve' function not found in notebook"
    assert ns["solve"](5) == 10


def test_solve_handles_edge_case() -> None:
    ns = exec_tagged_code(NOTEBOOK_PATH, tag="exercise1")
    assert "solve" in ns, "'solve' function not found in notebook"
    assert ns["solve"](0) == 0
```

**Test requirements**:

- At least 3 positive tests
- At least 2 edge cases
- 1 invalid input test (where appropriate)
- Fast (< 1s each)
- Deterministic (no randomness or time-based checks)
- Remove the scaffold guard assertions (`assert output.strip()`, `assert 'TODO' not in output`) once you replace the placeholder
- For debug exercises, keep or strengthen the checks that ensure `explanationN` cells contain meaningful reflections

### 4. Fill in the Solution Notebook

Edit `notebooks/solutions/exNNN_slug.ipynb`:

- Complete the exercise cells with correct implementations
- Keep the same cell tags
- Ensure the solution is pedagogically appropriate (don't use advanced features students haven't learned)

### 5. Verify

Run tests locally:

```bash
# Test against student notebook (should fail until students complete it)
uv run pytest tests/test_exNNN_slug.py -v

# Test against solution notebook (should pass)
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest tests/test_exNNN_slug.py -v

# Or use the helper script
scripts/verify_solutions.sh tests/test_exNNN_slug.py -v
```

### 6. Create Supporting Documentation

Add to `exercises/CONSTRUCT/TYPE/exNNN_slug/`:

**`README.md`** (update the generated template):

```markdown
# Exercise Title

**ID**: exNNN
**Construct**: sequence | selection | iteration | ...
**Type**: debug | modify | make
**Difficulty**: very easy | easy | medium | hard

## Learning Objective
One sentence describing what students will learn.

## Files
- Notebook: `notebooks/exNNN_slug.ipynb`
- Tests: `tests/test_exNNN_slug.py`
```

**`OVERVIEW.md`** (create new):

```markdown
# Teaching Notes: Exercise Title

## Prerequisites
- Students should know: X, Y, Z
- Previous exercises: ex001, ex002

## Common Misconceptions
- Students often think...
- Watch for...

## Teaching Approach
1. Demonstrate...
2. Guide students to...
3. Common hints needed...

## Worked Example
[Optional: step-by-step solution walkthrough]
```

If you need extra teacher-only notes beyond the solution notebook:

- add them to `OVERVIEW.md` (recommended), or
- add teacher-only markdown cells in the solution notebook mirror.

## Exercise Types

### Debug Exercises

Students fix broken code.

**Key points**:

- Early exercises (1-5): one error each
- Later exercises (6-10): 2-3 errors
- Use realistic errors beginners make
- Mix syntactic and logical errors

**Notebook structure**:

1. Show the buggy code in a non-graded cell
2. Student fixes it in a tagged cell
3. Tests verify the fix

### Modify Exercises

Students change working code to meet new requirements.

**Key points**:

- Start with simple modifications (change a value, swap operators)
- Progress to structural changes (add conditions, loops)
- Clearly state what should change

**Notebook structure**:

1. Show working code
2. Explain the modification task
3. Student modifies in tagged cell
4. Tests verify the modification

### Make Exercises

Students write code from scratch.

**Key points**:

- Typically 3-5 exercises per notebook (more challenging)
- Provide a clear function signature and docstring
- Give 1-2 example inputs/outputs
- Use consistent function names (`solve()` is conventional)

**Notebook structure**:

1. Explain the problem
2. Show example inputs/outputs
3. Student implements in tagged cell (with skeleton)
4. Tests verify correctness

## Multi-Part Notebooks (10 exercises)

When creating a notebook with `--parts 10`:

### Consistent Structure

- Use the same function name across parts (typically `solve()`)
- Each part in its own tagged cell: `exercise1`, `exercise2`, ..., `exercise10`
- Progressive difficulty: exercises 1-3 trivial, 4-7 moderate, 8-10 challenging

### Testing Pattern

```python
import pytest
from tests.notebook_grader import exec_tagged_code

TAGS = [f"exercise{i}" for i in range(1, 11)]

@pytest.mark.parametrize("tag", TAGS)
def test_exercise_exists(tag):
    ns = exec_tagged_code("notebooks/ex043_week1.ipynb", tag=tag)
    assert "solve" in ns, f"Missing solve() in {tag}"

@pytest.mark.parametrize(
    "tag,input_val,expected",
    [
        ("exercise1", 1, 2),
        ("exercise2", 5, 10),
        # ... more cases
    ],
)
def test_exercise_behaviour(tag, input_val, expected):
    ns = exec_tagged_code("notebooks/ex043_week1.ipynb", tag=tag)
    assert ns["solve"](input_val) == expected
```

## Best Practices

1. **Naming**: Use descriptive slugs that indicate the topic
2. **Function names**: Prefer `solve()` for consistency
3. **Docstrings**: Include after Functions construct is taught
4. **No network**: Avoid external dependencies or API calls
5. **Fast tests**: Keep test execution under 1s per test
6. **Isolation**: Each exercise cell should be self-contained

## Common Pitfalls

- **Wrong tag**: Ensure cell metadata tag matches what tests expect
- **Unrelated features**: Don't introduce constructs students haven't learned
- **Heavy dependencies**: Keep dependencies minimal
- **Slow tests**: Avoid large inputs or expensive computations
- **Non-determinism**: No random values, time-based checks, or network calls
