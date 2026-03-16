# Outstanding Issues

## Phase 1 — Repository Inventory And Canonical Model

## Phase 2 — Metadata And Resolution Layer

## Phase 3 — Metadata Consolidation And Registry Replacement

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
