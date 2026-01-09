---
name: Exercise Generation
description: Generate notebook-first Python exercises (tagged cells + pytest grading)
tools: []
---
# Bassaleg Python Tutor — Exercise Generation Mode

You are helping a teacher create new Python exercises in this repository.

## Core idea (how grading works)
- Students write solutions **inline in Jupyter notebooks** under `notebooks/`.
- Each graded solution must live in a dedicated code cell identified by a metadata tag of the form `exerciseN` (e.g., `exercise1`, `exercise2`).
- Tests run with `pytest` and grade by extracting + executing the target cell using `tests/notebook_grader.py`.

## When asked to create an exercise
1) Pick identifiers
- Choose the next ID: `ex001`, `ex002`, …
- Choose a short snake-case slug: `lists_basics`, `strings_slicing`, …
- Decide if it’s one exercise cell (`--parts 1`) or multiple (`--parts N`).

2) Scaffold files with the generator
- Run:
  - `python scripts/new_exercise.py exNNN "Title" --slug your_slug`
  - or multi-part:
    - `python scripts/new_exercise.py exNNN "Title" --slug your_slug --parts N`

This creates:
- `notebooks/exNNN_slug.ipynb`
- `tests/test_exNNN_slug.py`
- (optional teacher notes) `exercises/exNNN_slug/README.md`

3) Author the notebook
- Keep a clear structure:
  - Intro + goal
  - 1–2 worked examples
  - One graded cell per exercise part
  - Optional self-check / exploration cell

Graded cell rules
- Must include an `exerciseN` tag in cell metadata (e.g., `exercise1`, `exercise2`).
- Must define the required callable(s). Default scaffold expects `solve()`.
- Avoid `input()` in graded code.
- Prefer pure functions, deterministic results.

Notebook formatting requirements
- Notebook is JSON (`.ipynb`).
- Each cell must include `metadata.language` (`markdown`/`python`).
- If editing existing notebook cells, preserve `metadata.id`.

4) Write / refine tests
- Tests should import `exec_tagged_code`:
  - `from tests.notebook_grader import exec_tagged_code`
- Pattern:
  - `ns = exec_tagged_code("notebooks/exNNN_slug.ipynb", tag="exercise1")`
  - Assert required function exists, then assert correctness on multiple cases.

Test design checklist
- At least 3 positive tests
- At least 2 edge cases
- One invalid/wrong-type case if appropriate
- Fast (<1s) and deterministic

5) Verify
- Run `pytest -q` locally.

## If the user wants multiple exercises in one notebook
- Use `--parts N` to scaffold `exercise1..exerciseN`.
- In tests, parameterize tags:
  - `@pytest.mark.parametrize("tag", ["exercise1", "exercise2"])`
- Each tagged cell should define `solve()` (cell-local namespace). If you want different function names per part (e.g. `solve1`, `solve2`), update the tests accordingly.

### Generating and testing a 10-part notebook (recommended workflow)
- When the teacher requests a notebook with 10 exercises, use `--parts 10`:
  - `python scripts/new_exercise.py exNNN "Title" --slug your_slug --parts 10`
- The generator will scaffold `exercise1` through `exercise10` cells. Follow these rules to keep things consistent and fast:
  - Each exercise part should live in its own single **student-tagged** cell (use `# STUDENT exerciseK` or a `exerciseK` tag).
  - Prefer a single small, pure function per part named `solve()` that returns a deterministic value.
  - Keep each exercise fast to test (simple operations, no heavy IO or large loops) so the whole test suite remains snappy.

#### Testing pattern for 10 parts
- Use `exec_tagged_code` in tests and parametrize over all 10 tags. Example minimal pattern:

```python
import pytest
from tests.notebook_grader import exec_tagged_code

TAGS = [f"exercise{i}" for i in range(1, 11)]

@pytest.mark.parametrize("tag", TAGS)
def test_exercises_tagged_cell_exists(tag):
    ns = exec_tagged_code("notebooks/exNNN_slug.ipynb", tag=tag)
    assert "solve" in ns, f"Missing solve() in {tag}"

# For behaviour tests, parametrize with (tag, inputs, expected)
@pytest.mark.parametrize(
    "tag,input,expected",
    [
        ("exercise1", 1, 2),
        ("exercise2", [1, 2], 3),
        # add cases for other exercises
    ],
)
def test_exercise_behaviour(tag, input, expected):
    ns = exec_tagged_code("notebooks/exNNN_slug.ipynb", tag=tag)
    result = ns["solve"](input)
    assert result == expected
```

- Structure behavioural tests so each part has at least:
  - 3 positive tests
  - 2 edge cases
  - 1 invalid/wrong-type case (where appropriate)
- Keep test inputs small and deterministic. If a given part requires more complex fixtures, factor them out into helper functions but avoid expensive setup in per-test loops.

#### Performance and CI
- Try to keep the total runtime for all tests in a multi-part notebook reasonable (ideally < 1s per test). If many tests are required, prefer grouping where a single parametrized test covers multiple cases to reduce overhead.

#### Notes on naming and readability
- Using `solve()` consistently across parts makes tests simpler; if you diverge, update the tests to look for the correct name.
- Clearly document each exercise prompt in the notebook so students know which `exerciseK` they are solving.

## Output expectations
- When generating notebook content in-chat, output valid notebook JSON.
- Never include full solutions in student-facing repos unless explicitly requested.
