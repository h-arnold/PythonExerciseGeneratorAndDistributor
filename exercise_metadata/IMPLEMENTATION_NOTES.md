# Phase 2 Implementation Notes

## Canonical Behaviour Proof

Phase 2 canonical behaviour is proved by both:

1. **Live pilot exercise** – `ex004_sequence_debug_syntax` has a full `exercise.json`
   and canonical notebooks at
   `exercises/sequence/debug/ex004_sequence_debug_syntax/notebooks/student.ipynb`
   and `exercises/sequence/debug/ex004_sequence_debug_syntax/notebooks/solution.ipynb`.
   `resolve_notebook_path("ex004_sequence_debug_syntax", "student")` and
   `resolve_notebook_path("ex004_sequence_debug_syntax", "solution")` return these
   files verified to exist.

2. **Isolated fixtures** – `tests/test_exercise_metadata.py` uses `tmp_path` fixtures
   to test error cases (missing notebooks for canonical exercise, missing exercise.json,
   wrong schema_version) independently of the live filesystem.

## PYTUTOR_NOTEBOOKS_DIR

`PYTUTOR_NOTEBOOKS_DIR` is deliberately **ignored** by this resolver.  It was a
legacy mechanism for switching between student and solution notebook roots.  The
new resolver uses an explicit `variant` argument (`"student"` or `"solution"`) and
reads from the canonical `exercises/<construct>/<key>/notebooks/` tree.

## Modules That Need To Move Onto The Resolver

The following modules still use legacy path-based resolution and must be migrated
in later phases:

- `tests/notebook_grader.py` – `resolve_notebook_path()` uses `PYTUTOR_NOTEBOOKS_DIR`
- `tests/exercise_framework/paths.py` – mirrors notebook_grader behaviour
- `tests/exercise_expectations/` – all `*_NOTEBOOK_PATH` constants are legacy paths
- `tests/student_checker/` – resolves notebooks by filename/slug
- `scripts/build_autograde_payload.py` – assumes `notebooks/` and `notebooks/solutions/`
- `scripts/template_repo_cli/` – path-based exercise collection

These modules should fail hard once migrated; do not add silent compatibility bridges.
