# Exercise Generation CLI tool

> 🧑‍🤝‍🧑**Note for humans**: This CLI tool is designed to be used by the `Exercise Generation` agent to make exercise creation more reliable. You probably won't need to use this unless you plan to hand write all the exercises, solutions and tests. If you desperately want to use a specific set of exercises, pass them to the `Exercise Generation` agent to reformat and create tests for you.

This document describes how to use the CLI tool to scaffold new Python exercises in the repository. The scaffolder writes directly to the canonical authoring tree at `exercises/<construct>/<exercise_key>/`. Do not move scaffold output after creation. See [execution-model.md](../developers/execution-model.md) for the full runtime contract.

## Quick Start

### Single Exercise

```bash
uv run python -m scripts.new_exercise ex042 "Variables and Types" \
  --construct sequence \
  --type modify \
  --slug variables_and_types
```

For a debug exercise (scaffolds expected-output and explanation cells plus explanation tags):

```bash
uv run python -m scripts.new_exercise ex004 "Debug Syntax" \
  --construct sequence \
  --type debug \
  --slug syntax
```

This creates:

- `exercises/sequence/ex042_sequence_modify_variables_and_types/__init__.py`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/README.md`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/exercise.json`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/notebooks/student.ipynb`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/notebooks/solution.ipynb`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/tests/test_ex042_sequence_modify_variables_and_types.py`
- `exercises/sequence/ex042_sequence_modify_variables_and_types/tests/expectations.py` — exercise-local expected-output skeleton
- `exercises/sequence/ex042_sequence_modify_variables_and_types/tests/student_checker_support.py` — exercise-local student checker skeleton

### Multi-Part Exercise (10 exercises in one notebook)

```bash
uv run python -m scripts.new_exercise ex043 "Week 1 Practice" \
  --construct sequence \
  --type modify \
  --slug week1 \
  --parts 10
```

This creates the same structure but scaffolds 10 tagged cells (`exercise1` through `exercise10`) in the notebook.

## The `new_exercise.py` Script

### Purpose

Scaffolds the boilerplate for new exercises to ensure consistency across the repository.

### Command-Line Arguments

```bash
python scripts/new_exercise.py <id> <title> --construct CONSTRUCT --type TYPE [--slug SLUG] [--parts N]
```

Run it through the managed environment, for example `uv run python -m scripts.new_exercise ...`, so the correct dependencies are used and local package imports resolve correctly.

> **ℹ️ Note**: You can also run `uv run python scripts/new_exercise.py ...`, but the `-m` form is preferred because it keeps the repository root on `sys.path`, preventing `ModuleNotFoundError` in local imports.

**Required**:

- `id`: Exercise identifier (format: `exNNN`, e.g., `ex001`, `ex042`)
- `title`: Human-readable title (e.g., "Variables and Types")
- `--construct`: Programming construct directory (for example `sequence`)
- `--type`: Exercise type (`debug`, `modify`, `make`, or `gaps`)

**Optional**:

- `--slug`: Snake-case slug suffix (default: auto-generated from title)
- `--parts`: Number of exercise parts in one notebook (default: 1, max: 20)

When `--type debug` is used the scaffolder includes an "Expected output" markdown cell and an `explanationN` markdown cell for each exercise part.

### What Gets Created

#### 1. Exercise Directory

Canonical authoring target: `exercises/<construct>/<exercise_key>/`

Canonical repository-side exercise tests live under `exercises/<construct>/<exercise_key>/tests/`.

The generated `exercise_key` is `exNNN_<construct>_<type>_<slug>`, so a modify exercise for the sequence construct becomes `ex042_sequence_modify_variables_and_types`. The scaffolder writes directly to that canonical location. Do **not** add an extra `/<type>/` path segment or manually move the scaffold after creation.

Relevant metadata values:

- **CONSTRUCT**: `sequence`, `selection`, `iteration`, `data_types`, `lists`, `dictionaries`, `functions`, `file_handling`, `exceptions`, `libraries`, `oop`
- **TYPE**: `debug`, `modify`, `make`, `gaps`

Created files:

- `__init__.py`: Keeps the package importable
- `README.md`: Prefilled with student prompt and teacher notes placeholders (update both sections)
- `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`: Canonical repository-side exercise test within the exercise folder
- (Add manually) `OVERVIEW.md`: Detailed teaching notes

Instructor reference solutions live beside the student notebook under `notebooks/solution.ipynb`.

#### 2. Student Notebook

`exercises/<construct>/<exercise_key>/notebooks/student.ipynb`

Contains:

- Markdown cell with title and instructions
- Code cell(s) tagged `exercise1`, `exercise2`, etc.
- For multi-part notebooks, a markdown prompt precedes each tagged cell
- Self-check scratch cell (not graded)
- Auto-appended untagged code cell that imports `exercise_runtime_support.student_checker.run_notebook_checks` and runs it against the canonical `exercise_key` so students see grouped local check results before submitting

Important: the final checker cell must pass the canonical `exercise_key` string to `run_notebook_checks(...)`, not a notebook path string. If shared infrastructure has already resolved a notebook location, it must preserve that value as a `Path` when calling resolver-backed helpers rather than coercing it back to `str(...)`.

The scaffolder adds the final check-your-answers cell to both the student and solution notebooks to keep the verification helper consistent across copies.

On notebooks with multiple exercises (ex003 and later) that final helper now prints grouped rows for each check with columns `Exercise`, `Check`, `Status` and `Error`, mirroring the ex002 experience. Long error text wraps inside the Error column so continuation lines belong to the same cell rather than introducing extra separators, and this grouped layout replaces the older single-notebook summary output that appeared for ex003+.

Debug notebooks contain, for each part:

- A markdown cell describing expected behaviour and output
- A tagged code cell containing placeholder buggy code (`exerciseN`)
- A tagged explanation markdown cell (`explanationN`) that students complete after fixing the bug

For `--parts N`, creates N tagged exercise cells.

#### 3. Solution Notebook

`exercises/<construct>/<exercise_key>/notebooks/solution.ipynb`

Initially identical to the student notebook. You should:

- Fill in the exercise cells with correct solutions
- Verify tests pass: `uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q`

#### 4. Exercise Test File

`exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`

This is the canonical repository-side test file generated by the scaffolder.

Contains:

- Imports for `run_cell_and_capture_output` (and, for debug exercises, `get_explanation_cell`) alongside pytest
- Placeholder tests that execute each tagged cell, assert output was produced, and guard against leaving the `TODO` placeholder in place
- Debug exercises also include parametrised checks ensuring each `explanationN` cell is populated with >10 characters
- For multi-part exercises, parametrised tests cover every exercise tag

## Post-Scaffolding Workflow

After running `new_exercise.py`, follow these two phases. **Phase 2 must not start until the teacher has approved Phase 1 output.**

### Phase 1 — Notebook Authoring

| Step | Action | Go/no-go |
|---|---|---|
| 1 | **Author the notebook**: edit `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`. Add context (goal + 1–2 examples). Keep cells tagged correctly (`exercise1`, `exercise2`, etc.). Replace placeholder `print(...)` with starter code or buggy snippet. Each cell must target one learning objective. | — |
| 2 | **Verify notebook structure** matches the required layout below. | Must match exactly |
| 3 | **Run quality gate**: invoke the **Exercise Reviewer** (`.github/agents/exercise_reviewer.md.agent.md`) to check Gates A (type compliance), B (sequencing), C (tags/metadata). | PASS or PASS WITH NITS |
| 4 | **Teacher handoff**: present notebooks (student + solution) to the teacher for review and approval. Ensure `README.md`, `OVERVIEW.md`, and `OrderOfTeaching.md` are in place. | Teacher approves |

**Required notebook structure:**

```text
1. Markdown: Title and goal
2. Markdown/Code: Examples or context
3. Code (tagged exercise1): Student solution cell
4. [Repeat for exercise2, exercise3, etc. if multi-part]
5. Code (untagged): Self-check scratch cell
6. Code (untagged): Auto-appended check-your-answers cell that runs
   `exercise_runtime_support.student_checker.run_notebook_checks('<exercise_key>')`
```

> **⚠️ Important**: pass the canonical `exercise_key` string to `run_notebook_checks(...)` — never a notebook path, absolute `.ipynb` path, or `str(path)`. String inputs are exercise keys; resolved `Path` values must stay as `Path`.

### Phase 2 — Test Authoring (after teacher approval)

| Step | Action | Go/no-go |
|---|---|---|
| 5 | **Write tests** in `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`. Replace placeholder assertions with real tests (see pattern below). | All tests pass on solution variant |
| 6 | **Fill in solution notebook** at `notebooks/solution.ipynb`. Keep same tags. Use stepwise, per-line transformations (avoid compact one-liners). | — |
| 7 | **Verify**: run commands below and confirm green. | All pass |

**Required test criteria:**

- At least 3 positive tests, 2 edge cases, 1 invalid-input test (where appropriate)
- Fast (< 1s each), deterministic (no randomness, time, or network)
- Remove scaffold guard assertions (`assert output.strip()`, `assert 'TODO' not in output`) after replacing placeholders
- For debug exercises: keep or strengthen `explanationN` checks
- Import helpers from `exercise_runtime_support.exercise_framework` only

**Default test pattern:**

```python
from exercise_runtime_support.exercise_framework import (
  RuntimeCache,
  resolve_exercise_notebook_path,
  run_cell_and_capture_output,
)

_EXERCISE_KEY = "ex042_sequence_modify_variables_and_types"
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()


def test_exercise1_greets_user() -> None:
  output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag="exercise1", cache=_CACHE)
  assert output == "Hello"
```

If the exercise defines Python objects instead of printing, use `exec_tagged_code(...)` for targeted tests. This is an exercise-specific choice, not a default contract.

**Verification commands:**

```bash
# Test student notebook (often fails until authoring is complete)
uv run pytest exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -v

# Test solution notebook (must pass)
uv run python scripts/run_pytest_variant.py --variant solution \
  exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -v

# Structural checks (add --skip-empty-checks during Phase 1 when student_checker_support.py is not yet populated)
uv run python scripts/verify_exercise_quality.py <exercise_key>
```

## Files
- Notebook: `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- Tests: `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`
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

1. Show the expected behaviour in a markdown cell
2. Student fixes the buggy starter code in the tagged `exerciseN` cell
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
- Provide clear task text and expected output examples
- Use the same tagged-cell scaffold as other non-debug exercises
- Only require a named function when the exercise content genuinely teaches functions

**Notebook structure**:

1. Explain the problem and show expected output or worked examples
2. Student writes the solution in a tagged cell
3. Tests capture output or provide deterministic input

### Gap-Fill Exercises

Students are given a partial program and must write the missing line(s) of code to make it work. This type bridges modify/debug exercises (where the program is essentially complete) and make exercises (where students write from scratch).

**Key points**:

- Each tagged cell includes surrounding scaffold code plus a `# YOUR CODE HERE` comment marking where the student must write
- Early exercises (1-3): one missing line, highly scaffolded surround
- Later exercises (7-10): multiple missing lines, less contextual scaffolding, may revisit earlier constructs alongside the new one
- Test output rather than source code, since valid line-level completions are often equivalent
- Use AST checks only when the gap must use a specific construct (e.g. a `while` loop rather than a `for` loop)

**Notebook structure**:

1. Markdown cell with task description and expected output
2. Code cell with partial program and `# YOUR CODE HERE — <description>` comment(s)
3. Tests verify the corrected output

See `docs/exercise-agents/exercise-types/gaps.md` for full authoring rules.

## Multi-Part Notebooks (10 exercises)

When creating a notebook with `--parts 10`:

### Consistent Structure

- Each part in its own tagged cell: `exercise1`, `exercise2`, ..., `exercise10`
- For non-debug multi-part notebooks, place a short markdown prompt before each tagged cell
- Progressive difficulty: exercises 1-3 trivial, 4-7 moderate, 8-10 challenging
- Only standardise on a function name if a specific later-construct notebook explicitly teaches functions

### Testing Pattern

```python
import pytest
from exercise_runtime_support.exercise_framework import (
  RuntimeCache,
  resolve_exercise_notebook_path,
  run_cell_and_capture_output,
)

_EXERCISE_KEY = "ex043_sequence_modify_week1"
_NOTEBOOK_PATH = resolve_exercise_notebook_path(_EXERCISE_KEY)
_CACHE = RuntimeCache()
TAGS = [f"exercise{i}" for i in range(1, 11)]

@pytest.mark.parametrize("tag", TAGS)
def test_exercise_cells_execute(tag):
  output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)
  assert output.strip()
  assert "TODO" not in output

@pytest.mark.parametrize(
  ("tag", "expected"),
    [
    ("exercise1", "2"),
    ("exercise2", "10"),
        # ... more cases
    ],
)
def test_exercise_behaviour(tag, expected):
  output = run_cell_and_capture_output(_NOTEBOOK_PATH, tag=tag, cache=_CACHE)
  assert output == expected
```

## Canonical vs Transitional Paths

- Canonical authoring path: `exercises/<construct>/<exercise_key>/`
- Exercise type: stored in `exercise.json`, not in the path
- Canonical resolver input: `exercise_key`
- Flattened notebook/test mirrors are not part of the supported contract and must not be introduced in scaffold output

When documenting or authoring new exercises, prefer the canonical exercise-local notebook and test paths.

## Best Practices

1. **Naming**: Use descriptive slugs that indicate the topic
2. **Tagged cells**: Keep each tagged cell self-contained and aligned with its test expectations
3. **Docstrings**: Include only when the exercise deliberately teaches functions and that construct has been taught
4. **No network**: Avoid external dependencies or API calls
5. **Fast tests**: Keep test execution under 1s per test
6. **Isolation**: Each exercise cell should be self-contained

## Common Pitfalls

- **Wrong tag**: Ensure cell metadata tag matches what tests expect
- **Unrelated features**: Don't introduce constructs students haven't learned
- **Heavy dependencies**: Keep dependencies minimal
- **Slow tests**: Avoid large inputs or expensive computations
- **Non-determinism**: No random values, time-based checks, or network calls
