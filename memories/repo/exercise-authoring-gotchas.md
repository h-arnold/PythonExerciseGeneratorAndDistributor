# Exercise Authoring Gotchas

## Two things that MUST happen after scaffolding a new exercise

1. **Create `tests/student_checker_support.py` + `tests/expectations.py`** — Without these, the self-checker falls back to a lenient "does it execute?" check that passes on any syntactically valid code, even if the output is completely wrong. Students will see all-green results on broken code. Follow the pattern in exercises like `ex009_sequence_modify_fstrings/tests/`.

2. **Set `PYTUTOR_ACTIVE_VARIANT` in solution notebook's self-checker cell** — The self-checker defaults to `"student"` variant unless the env var is set. Solution notebooks need `os.environ["PYTUTOR_ACTIVE_VARIANT"] = "solution"` at the top of their self-checker cell, otherwise they silently read from `student.ipynb` instead of `solution.ipynb` and all checks fail.

## Checklist for new exercises
- [ ] `exercises/<construct>/OrderOfTeaching.md` includes the new exercise
- [ ] `tests/expectations.py` exists with correct expected outputs
- [ ] `tests/student_checker_support.py` exists and loads from expectations
- [ ] Solution notebook self-checker cell sets `PYTUTOR_ACTIVE_VARIANT=solution`
- [ ] Student self-checker fails (requires code fixes)
- [ ] Solution self-checker passes (code is correct)
- [ ] Pytest solution variant passes: `uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q`
