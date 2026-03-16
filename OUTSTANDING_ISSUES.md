# Outstanding Issues

## Phase 1 — Repository Inventory And Canonical Model

## Phase 2 — Metadata And Resolution Layer

### 4. `resolve_notebook_path()` can resolve a canonical notebook even when `exercise.json` is missing
- **Action-plan requirement:** if an exercise is marked canonical, missing canonical files must fail hard.
- **Verified evidence:**
  - `exercise_metadata/resolver.py:150-158`
  - In a temporary canonical fixture with a manifest entry and `notebooks/student.ipynb` present, `resolve_notebook_path()` succeeded even though `exercise.json` was absent.
  - Existing tests only prove missing notebook files fail: `tests/test_exercise_metadata.py:140-157`
- **Why this blocks completion:** a canonical exercise is currently not required to have its metadata file at notebook-resolution time.

### 5. The repo does not prove by test that the shared resolver ignores `PYTUTOR_NOTEBOOKS_DIR`
- **Action-plan requirement:** Phase 2 completion must prove the shared resolver ignores `PYTUTOR_NOTEBOOKS_DIR` entirely.
- **Verified evidence:**
  - `tests/test_exercise_metadata.py:6-12` states the contract in comments.
  - The same test file contains no `setenv()` / `delenv()` coverage for `PYTUTOR_NOTEBOOKS_DIR`.
- **Why this blocks completion:** the intended behaviour may be correct, but the required proof point is missing.

## Phase 3 — Metadata Consolidation And Registry Replacement

### 6. Template selection still depends partly on legacy paths instead of metadata
- **Action-plan requirement:** template selection should derive available exercises, construct grouping, and type grouping from metadata rather than `notebooks/*.ipynb` or `exercises/<construct>/<type>/...` path shape.
- **Verified evidence:**
  - `scripts/template_repo_cli/core/selector.py:32-43` still implements `get_all_notebooks()` by scanning `notebooks/ex*.ipynb`.
  - `scripts/template_repo_cli/core/selector.py:77-151,153-246` still discovers legacy exercises by walking `exercises/<construct>/<type>/...`.
  - `scripts/template_repo_cli/cli.py:778-784` still uses `get_all_notebooks()` for unfiltered listing.
  - In a temporary repo with a manifest entry plus canonical metadata only, `ExerciseSelector.get_all_notebooks()` and `select_by_type(["modify"])` both returned empty.
- **Why this blocks completion:** metadata is not yet the single source of truth for selector-driven exercise discovery.

### 7. The metadata catalogue does not fail fast on duplicate `exercise_id` values
- **Action-plan requirement:** Phase 3 calls for fail-fast validation for duplicate exercise identities in the metadata-backed catalogue.
- **Verified evidence:**
  - `exercise_metadata/registry.py:106-159`
  - In a temporary canonical fixture with two exercises sharing the same `exercise_id`, `build_exercise_catalogue()` succeeded and returned both entries.
- **Why this blocks completion:** the catalogue can still build inconsistent metadata-derived identity/order views.

## Phase 4 — Execution Model And Source-To-Export Contract

### 8. The canonical ex004 pilot test still uses legacy env/path fallback logic
- **Action-plan requirement:** Phase 4 requires student/solution selection to follow the explicit variant contract and shared resolver, without silent path/env fallback.
- **Verified evidence:**
  - `exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py:28-67`
    - `_current_variant()` reads `PYTUTOR_NOTEBOOKS_DIR`
    - `_resolve_notebook_path()` probes multiple locations and falls back silently
  - Behavioural mismatch:
    - `python -m pytest -q exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py` passes
    - `python scripts/run_pytest_variant.py --variant solution -q exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py` fails because the test resolves and executes `student.ipynb` instead of the solution notebook
- **Why this blocks completion:** the live pilot proof is not actually aligned with the Phase 4 execution contract.

### 9. The execution-model consumer inventory does not include all current consumers
- **Action-plan requirement:** Phase 4 must identify every consumer that depends on the execution model, including docs and guidance surfaces.
- **Verified evidence:**
  - `exercise_runtime_support/consumer_matrix.py:25-81`
  - `docs/execution-model.md:72-86`
  - `AGENTS.md:148-180` still documents the old `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` execution path, but `AGENTS.md` is not included in the consumer matrix or the mirrored table in `docs/execution-model.md`.
- **Why this blocks completion:** the consumer inventory is incomplete, so the repo still lacks a full execution-model dependency map.
