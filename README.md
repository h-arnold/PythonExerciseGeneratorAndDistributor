# Bassaleg Python Tutor Exercises

Notebook-based Python exercises with automated grading via `pytest` (GitHub Classroom friendly).

## Repo layout

- `notebooks/`
	- One notebook per exercise: `notebooks/exNNN_slug.ipynb`
	- Students write code **inline** in a dedicated exercise cell that **must** be tagged with `exerciseN` in the cell metadata (e.g., `exercise1`, `exercise2`). Marker comments like `# STUDENT` or `# STUDENT exercise1` are deprecated and will **not** be accepted by the autograder.
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

## Create a new exercise

```bash
python scripts/new_exercise.py ex001 "Variables and Types" --slug variables_and_types
```

Multiple exercises in one notebook:

```bash
python scripts/new_exercise.py ex010 "Week 1" --slug week1 --parts 3
```

This creates:
- `notebooks/ex001_variables_and_types.ipynb`
- `tests/test_ex001_variables_and_types.py`

And (optional):
- `exercises/ex001_variables_and_types/README.md`

## Notes

- The notebook is for explanation and scratch work.
- Grading is driven by `pytest` (see `.github/workflows/tests.yml`).

## Copilot authoring mode

- See `.github/prompts/exercise_generation.chatmode.md` for a “chat mode” style guide you can use while generating new exercises.

