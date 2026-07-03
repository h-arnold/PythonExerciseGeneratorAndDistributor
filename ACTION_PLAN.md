# Action Plan: Modify Debug Exercise Scaffolding

## Status: COMPLETE

## Scope

Modified the debug exercise scaffolder (`scripts/exercise_scaffolder/debug.py` and `base.py`) to produce a new 5-cell-per-part structure instead of the current 3-cell structure. No existing exercises were migrated.

## Changes Made

### 1. `scripts/exercise_scaffolder/base.py`
- Added `extra` parameter to `make_meta()` for additional metadata fields (e.g., `deletable`, `editable`)
- Updated debug header instructions to explain the new workflow

### 2. `scripts/exercise_scaffolder/debug.py`
- Changed `_cells_per_exercise` from 3 to 5
- Rewrote `_build_exercise_cells()` to produce 5 cells per part:
  1. Markdown description (expected behaviour) — unchanged
  2. Read-only buggy code (`deletable: false`, `editable: false`) — new
  3. Explanation markdown (tagged `explanationN`) — unchanged
  4. "Debug this code" header markdown — new
  5. Editable buggy code (tagged `exerciseN`) — unchanged

### 3. `tests/test_exercise_scaffolder_debug.py`
- Updated cell count constants for new structure
- Updated all cell index references
- Added tests for read-only cell metadata
- Added tests for "Debug this code" header cell

### 4. `tests/test_new_exercise.py`
- Updated `test_make_notebook_debug_structure` for new cell ordering

### 5. Documentation
- Updated `docs/exercise-agents/exercise-generation-cli.md`
- Updated `docs/exercise-agents/exercise-types/debug.md`

## Section Checklist

- [x] Red tests added
- [x] Red review clean
- [x] Green implementation complete
- [x] Green review clean
- [x] Checks passed
- [x] Action plan updated
- [x] Commit created
- [x] Push completed
