# Copilot Custom Instructions — PythonTutorExercises

You are assisting in a classroom repo of Python exercises.
The repo is organized so students work in Jupyter notebooks, but **grading is done via pytest**.

## Goals
- Create new exercises quickly and consistently.
- Put student code **inline in notebooks** (in a tagged cell).
- Keep grading deterministic via `pytest`.
- Put checks in **tests/**.

## Authoring help
- Use the repository chat mode prompt in `.github/prompts/exercise_generation.chatmode.md` to generate consistent notebook + tests.

## Repository layout (must follow)
- `notebooks/`
  - One notebook per exercise: `notebooks/exNNN_slug.ipynb`
  - Students write their solution in a dedicated code cell that **must** be tagged with `exerciseN` (e.g., `exercise1`, `exercise2`). Tests and tooling will look only for `exerciseN` tags; marker comments are deprecated.
- `tests/`
  - `tests/test_exNNN_slug.py` contains automated tests.
- `scripts/new_exercise.py` generates skeletons.

Optional:
- `exercises/`
  - One folder per exercise: `exercises/exNNN_slug/README.md` (teacher notes + prompt)

## When asked to "create a new exercise"
1. Choose the next ID (ex001, ex002, …) and a short snake-case slug.
2. Use / extend `scripts/new_exercise.py` output rather than ad-hoc files.
3. Ensure the notebook includes a **single** code cell tagged `student`.
4. Tests should read `notebooks/exNNN_slug.ipynb`, extract the target cell by metadata tag (e.g. `exercise1`), execute it, and assert on the defined functions/variables.
5. Update `README.md` index table with the new exercise.

## Exercise design rules
- Student cell must expose **small pure functions** where possible.
- Include clear docstrings + type hints.
- Prefer deterministic behavior.
- Avoid requiring user input (`input()`) in graded functions.
- Avoid printing in graded functions unless explicitly required; return values instead.

## Testing rules
- Use `pytest`.
- Tests must be fast (< 1s each) and deterministic.
- Include:
  - at least 3 positive tests
  - at least 2 edge cases
  - one "wrong type" or "invalid value" case if appropriate
- Prefer **Option A** grading: extract + `exec()` the `student` cell (see `tests/notebook_grader.py`).
- Avoid executing entire notebooks in CI unless explicitly requested.

## Notebook rules
- Notebook should:
  - explain the goal
  - show 1–2 examples
  - include one `student`-tagged cell where students write their solution
  - optionally include a non-graded self-check cell
- Keep notebook outputs minimal.

## Do not do
- Do not include full solutions in student repos.
- Do not depend on network access.
- Do not add heavy dependencies.
