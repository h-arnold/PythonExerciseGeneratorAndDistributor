# Outstanding Issues

This report reflects the current live repository after the metadata, registry, runtime catalogue, notebook-path, and most identity-cleanup work completed.

## Current status

- Canonical exercise metadata now lives under `exercises/<construct>/<exercise_key>/exercise.json` for the migrated exercises.
- Metadata discovery rejects legacy metadata homes and resolves only canonical exercise directories.
- The runtime catalogue no longer relies on the old checked-in fallback tuple registry.
- Framework and student-checker code now resolve notebooks from `exercise_key` rather than notebook-path constants owned by `tests.exercise_expectations`.
- The obsolete `ex001_sanity` tree, stale `ex006` duplicate homes, and the stray `exercises/PythonExerciseGeneratorAndDistributor/` placeholder tree have been removed.
- `scripts/verify_exercise_quality.py` now understands the canonical `exercises/<construct>/<exercise_key>/` layout and fails loudly on invalid canonical metadata.

## Remaining implementation issues

### 1. `ex007` notebook identity is still not fully canonical

The remaining live `data_types` drift is now isolated to the ex007 notebooks.

Relevant files:

- `notebooks/ex007_sequence_debug_casting.ipynb`
- `notebooks/solutions/ex007_data_types_debug_casting.ipynb`

Current mismatch:

- The solution notebook still uses the legacy stem `ex007_data_types_debug_casting.ipynb` instead of the canonical `ex007_sequence_debug_casting.ipynb`.
- The self-check cell in the student notebook still calls `check_notebook('ex007_data_types_debug_casting')`.
- The self-check cell in the solution notebook still calls `check_notebook('ex007_data_types_debug_casting')`.

What still needs to happen:

- Rename the solution notebook to `notebooks/solutions/ex007_sequence_debug_casting.ipynb`.
- Update the self-check cell in both ex007 notebooks to use `check_notebook('ex007_sequence_debug_casting')`.
- Re-run the ex007-specific path, checker, and notebook tests after that normalization.

### 2. Final targeted verification is still pending

The broad migration slices have changed substantially, but the final focused verification pass has not been completed yet.

Recommended verification slice after ex007 is normalized:

- `tests/test_exercise_metadata.py`
- `tests/test_exercise_registry.py`
- `tests/exercise_framework/test_paths.py`
- `tests/exercise_framework/test_expectations.py`
- `tests/template_repo_cli/test_integration.py`
- `tests/test_verify_exercise_quality.py`
- `tests/test_ex007_sequence_debug_casting.py`

Why this still matters:

- ex007 solution-mode behavior cannot be treated as trustworthy while the solution notebook stem is still mismatched.
- The packaging and framework/path surfaces have changed enough that they should be re-checked together once the last identity mismatch is gone.

## Recommended next order of work

1. Normalize the ex007 notebook filename and self-check slug to the canonical `ex007_sequence_debug_casting` identity.
2. Run the targeted verification slice across metadata, framework, packaging, verifier, and ex007 test surfaces.
3. Triage any remaining failures after that pass as either migration blockers or separate notebook-content issues.
