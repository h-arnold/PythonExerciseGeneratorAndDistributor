# Phase 2 Implementation Notes

## Canonical Behaviour Proof

Phase 2 canonical behaviour is proved by both:

1. **Live pilot exercise** – `ex004_sequence_debug_syntax` has a full `exercise.json`
   and proves canonical resolver behaviour for one migrated exercise.
   The target naming convention used by the metadata layer is
   `exercises/<construct>/<exercise_key>/notebooks/`, as defined in
   `ACTION_PLAN.md`.
   `resolve_notebook_path("ex004_sequence_debug_syntax", "student")` and
   `resolve_notebook_path("ex004_sequence_debug_syntax", "solution")` return
   existing notebook files for that exercise.

2. **Isolated fixtures** – `tests/test_exercise_metadata.py` uses `tmp_path` fixtures
   to test error cases (missing notebooks for canonical exercise, missing exercise.json,
   wrong schema_version) independently of the live filesystem.

## PYTUTOR_NOTEBOOKS_DIR

`PYTUTOR_NOTEBOOKS_DIR` is deliberately **ignored** by this resolver.  It was a
legacy mechanism for switching between student and solution notebook roots.  The
new resolver uses an explicit `variant` argument (`"student"` or `"solution"`) and
reads from the canonical `exercises/<construct>/<exercise_key>/notebooks/` tree.

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

## Phase 3: Metadata Consolidation And Registry Replacement

### What Moves Into exercise.json

The following exercise-level properties MUST live in `exercise.json` for canonical exercises:
- `exercise_id` (numeric) - identity and sort order
- `title` - human-readable name
- `construct` - programming construct (e.g. "sequence")
- `exercise_type` - exercise type (e.g. "debug", "modify")
- `parts` - number of parts/tasks

### What Stays Hard-Coded By Convention

These fields are deliberately excluded from `exercise.json`:
- `tags` - derived from `parts` and `exercise_type` at runtime
- `notebook paths` - fixed by convention: `exercises/<construct>/<exercise_key>/notebooks/`
- `ordering` - derived from `exercise_id`, not configurable separately
- `mandatory self-check cell presence` - fixed by repository convention

### Hard-Coded Registries To Replace

The following locations contain hard-coded slug lists that should eventually
derive from `exercise_metadata.registry.get_all_exercise_keys()`:

| File | What to replace |
|------|----------------|
| `tests/exercise_framework/api.py` | `NOTEBOOK_ORDER`, `EX00X_SLUG` constants |
| `tests/student_checker/api.py` | `_NOTEBOOK_ORDER`, `_EX00X_SLUG` constants |

These have been annotated with `# TODO(Phase3)` comments and can be replaced
once all exercises are migrated to canonical layout with `exercise.json`.

### Exercise-Local vs Aggregate Views

- **Exercise-local**: Each exercise's `exercise.json` owns its own identity data.
- **Aggregate views**: `exercise_metadata.registry.build_exercise_registry()` derives
  a sorted list at runtime; no separate aggregate file is needed.

### Exported Classroom Repositories

Exported Classroom repositories (GitHub Classroom student repos) remain
**metadata-free by design**. They do NOT receive:
- `exercises/migration_manifest.json`
- `exercise.json` files
- The `exercise_metadata/` package

The registry is a source-repository authoring concept only.
