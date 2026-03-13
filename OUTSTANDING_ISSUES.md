# Outstanding Issues

This report reflects the repository state after the maintained docs and agent guidance were updated to the canonical model.

## Current status

- Maintained docs and agent instructions now describe `exercises/<construct>/<exercise_key>/` as the canonical authoring location.
- Remaining references to `exercises/<construct>/<type>/<exercise_key>/` in maintained guidance are warnings or legacy-state notes, not target-model instructions.
- The remaining gaps are implementation issues in the live repository, not documentation drift.

## Outstanding implementation issues

### 1. Metadata has drifted back into legacy `/<type>/` exercise folders

The canonical location for exercise-specific assets is `exercises/<construct>/<exercise_key>/`. That is still not true for most metadata files in the live tree.

Current non-canonical metadata locations:

- `exercises/sequence/modify/ex002_sequence_modify_basics/exercise.json`
- `exercises/sequence/modify/ex003_sequence_modify_variables/exercise.json`
- `exercises/sequence/debug/ex005_sequence_debug_logic/exercise.json`
- `exercises/sequence/modify/ex006_sequence_modify_casting/exercise.json`
- `exercises/sequence/debug/ex007_sequence_debug_casting/exercise.json`
- `exercises/ex001_sanity/exercise.json`

Only the Phase 2 pilot currently has metadata in the canonical location:

- `exercises/sequence/ex004_sequence_debug_syntax/exercise.json`

This is the highest-priority remaining issue because it reintroduces the exact path contract the migration is supposed to remove.

### 2. Registry logic still tolerates legacy metadata placement

The metadata registry still contains fallback logic that searches for `exercise.json` in arbitrary matching directories instead of enforcing the canonical home.

Relevant files:

- `exercise_metadata/registry.py`
  - `_find_metadata_directory()` falls back to `root.rglob(exercise_key)` and accepts any matching directory containing `exercise.json`
- `exercise_metadata/resolver.py`
  - `resolve_exercise_dir()` still scans for legacy matches to build a hint, which is acceptable for diagnostics
  - `resolve_notebook_path()` still tells callers they can use the legacy `notebooks/` path directly for now, which keeps the mixed model visible in the resolver contract

What still needs to happen:

- Metadata loading must fail unless `exercise.json` is at `exercises/<construct>/<exercise_key>/`.
- Legacy metadata locations should not be treated as acceptable runtime inputs.

### 3. Runtime catalogue still has a hard-coded fallback registry

The new runtime catalogue is not yet fully metadata-driven because it ships a checked-in fallback snapshot.

Relevant file:

- `exercise_runtime_support/exercise_catalogue.py`
  - `_FALLBACK_CATALOGUE` hard-codes all exercises, titles, construct values, types, ids, and layouts

Why this is still a problem:

- It recreates a second registry layer outside the metadata system.
- It can drift from `exercise.json` and `exercises/migration_manifest.json`.
- It weakens the Phase 3 goal of replacing duplicated hand-maintained registries.

### 4. Framework and student-checker code still depend on notebook-path constants from `tests.exercise_expectations`

The codebase is still not fully `exercise_key`-first. Several public runtime surfaces still import top-level notebook path constants from the legacy expectations modules.

Relevant files:

- `exercise_runtime_support/exercise_framework/api.py`
- `exercise_runtime_support/exercise_framework/expectations.py`
- `exercise_runtime_support/student_checker/checks/ex001.py`
- `exercise_runtime_support/student_checker/checks/ex003.py`
- `exercise_runtime_support/student_checker/checks/ex004.py`
- `exercise_runtime_support/student_checker/checks/ex005.py`
- `exercise_runtime_support/student_checker/checks/ex006.py`
- `exercise_runtime_support/student_checker/checks/ex007.py`
- `tests/exercise_expectations/__init__.py`
- per-exercise expectation modules under `tests/exercise_expectations/`

Examples of the remaining coupling:

- `exercise_runtime_support/exercise_framework/api.py` imports `EX001_NOTEBOOK_PATH`, `EX003_NOTEBOOK_PATH`, `EX004_NOTEBOOK_PATH`, `EX005_NOTEBOOK_PATH`, and `EX006_NOTEBOOK_PATH`
- multiple student-checker modules still call `resolve_framework_notebook_path(...)` using `EX00X_NOTEBOOK_PATH` constants

What still needs to happen:

- Move these call sites to metadata-derived `exercise_key` resolution.
- Keep behavioural expectations in `tests.exercise_expectations`, but remove notebook identity ownership from that package.

### 5. Identity clean-up blockers are still present in the repository

Several known structural anomalies still exist and can interfere with later phases.

Current blockers still visible in the tree:

- obsolete root-level exercise directory: `exercises/ex001_sanity`
- duplicate ex006 directory: `exercises/ex006_sequence_modify_casting`
- legacy ex006 directory: `exercises/sequence/modify/ex006_sequence_modify_casting`
- stray placeholder tree: `exercises/PythonExerciseGeneratorAndDistributor`

These should be resolved before later migration phases rely on a single authoritative exercise home per `exercise_key`.

### 6. `ex007` identity drift still needs full clean-up

The repo still carries legacy `data_types` naming in at least one live test path.

Relevant file:

- `tests/test_ex007_sequence_debug_casting.py`
  - still imports `tests.exercise_expectations.ex007_data_types_debug_casting`

This remains a concrete mismatch between the canonical target identity `ex007_sequence_debug_casting` and the live test surface.

## Recommended next order of work

1. Fix canonical metadata placement first.
2. Remove registry fallback behaviour that accepts legacy metadata homes.
3. Replace the runtime fallback catalogue with a single metadata-driven source of truth.
4. Move framework and student-checker code off `EX00X_NOTEBOOK_PATH` constants.
5. Clean up `ex001`, duplicate `ex006`, the stray placeholder tree, and the remaining `ex007` alias drift.

## Files changed in the docs alignment pass

The following maintained docs and guidance were updated before this report was written:

- `AGENTS.md`
- `.github/agents/exercise_generation.md.agent.md`
- `.github/agents/exercise_verifier.md.agent.md`
- `README.md`
- `docs/project-structure.md`
- `docs/exercise-generation-cli.md`
- `docs/testing-framework.md`
- `docs/development.md`
- `PHASE_10_MIGRATION_CHECKLIST.md`
- `PHASE_3_MIGRATION_CHECKLIST.md`
- `PHASE_2_MIGRATION_CHECKLIST.md`

Those updates were reviewed and no remaining documentation findings were reported in scope.
