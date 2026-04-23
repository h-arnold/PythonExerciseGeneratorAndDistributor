# Implementation Action Plan: Metadata-Only Exercise Resolution Migration

## 1. Documentation Updates (Contract Lock-First)

Objective: Lock the metadata-only, fail-fast contract before code changes so all agents implement against the same rules and do not reintroduce snapshot/fallback behavior.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/docs/execution-model.md`
- `/workspaces/PythonExerciseGeneratorAndDistributor/docs/testing-framework.md`
- `/workspaces/PythonExerciseGeneratorAndDistributor/docs/development.md`
- `/workspaces/PythonExerciseGeneratorAndDistributor/docs/setup.md`
- `/workspaces/PythonExerciseGeneratorAndDistributor/AGENTS.md`

Tasks:

- Remove all snapshot export, metadata-free mode, and fallback-path guidance.
- Document canonical-only runtime surfaces: `exercise_metadata/`, `exercises/migration_manifest.json`, `exercises/<construct>/<exercise_key>/exercise.json`, canonical notebooks, canonical exercise-local tests.
- Document strict fail-fast error contract and message fragments from SPEC §2.2.
- State explicitly that flattened notebook/test mirrors are forbidden in packaged outputs.

Verification:

- Contract assertions are explicitly present in docs:
  - metadata-only catalogue resolution
  - flattened mirrors forbidden
  - fail-fast error contract summary aligned to SPEC §2.2
  - packaged runtime contract surfaces aligned to SPEC §2.1
- `rg -n "snapshot|metadata-free" /workspaces/PythonExerciseGeneratorAndDistributor/docs /workspaces/PythonExerciseGeneratorAndDistributor/AGENTS.md` is reviewed and any remaining occurrences are intentional historical context or removed.
- Owner checks: doc review checklist in PR description + contract spot-check against SPEC §2.1/§2.2.

Dependencies and sequencing:

- Prepared first for implementation guidance.
- Docs are drafted and reviewed first, then merged in the same migration PR as runtime/packager/test changes to stay aligned with SPEC §4 rollout.

## 2. Runtime Catalogue and Path Resolver Unification

Objective: Make metadata catalogue resolution the only runtime path in source and packaged modes.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_catalogue.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_framework/paths.py`

Tasks:

- Remove snapshot constants/functions and all snapshot-based branch logic.
- Remove environment-based “metadata package present?” branching.
- Ensure `get_exercise_catalogue()` always uses `exercise_metadata.registry.build_exercise_catalogue()`.
- Ensure notebook resolution always delegates through metadata resolver semantics using `exercise_key`.

Verification:

- Unit tests for runtime catalogue and path resolution pass after test updates.
- `rg -n "CATALOGUE_SNAPSHOT_FILENAME|get_catalogue_snapshot_path|load_catalogue_snapshot|write_catalogue_snapshot"` in runtime modules returns no matches.
- Owner tests: `/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_runtime_support/test_exercise_catalogue.py`, `/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_framework/test_paths.py`.

Dependencies and sequencing:

- Depends on Section 1 contract lock.
- Must precede packaging integration validation.

## 3. Test-Support Canonical Path Enforcement

Objective: Remove non-canonical packaged test lookup and enforce exercise-local tests path only.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_test_support.py`

Tasks:

- Remove `tests/<construct>/<exercise_key>` packaged fallback logic.
- Resolve tests only from `exercises/<construct>/<exercise_key>/tests`.

Verification:

- Targeted tests confirm canonical lookup works and non-canonical fallback no longer exists.
- Grep check confirms no fallback path strings remain in this module.
- Owner tests: `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_integration.py` plus exercise test-support coverage that loads exercise-local modules.

Dependencies and sequencing:

- Depends on Section 2 runtime semantics.
- Must be done before packager validation to keep path contract aligned.

## 4. Packager and Collector Metadata-Surface Enforcement

Objective: Ensure generated template repos always include required metadata runtime surfaces and no snapshot artifacts.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/packager.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/collector.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/template_repo_files/.devcontainer/devcontainer.json`

Tasks:

- Stop writing/validating snapshot artifacts.
- Export `exercise_metadata/`, manifest, per-exercise `exercise.json`, canonical notebooks, canonical exercise-local tests.
- Enforce flattened notebook/test mirrors as forbidden outputs.
- Add/update `.devcontainer` `files.exclude` entries to hide metadata clutter from student view without changing runtime behavior.

Verification:

- Dry-run package output contains all required assets from SPEC §2.1.
- Dry-run package output contains no snapshot artifacts and no flattened mirrors.
- Owner tests: `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_packager.py`, `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_integration.py`.

Dependencies and sequencing:

- Depends on Sections 2 and 3 to match runtime expectations.
- Must complete before integration test rewrites finish.

## 5. Selector Fail-Fast Behavior Tightening

Objective: Remove silent empty-registry behavior when metadata prerequisites are missing.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/selector.py`

Tasks:

- Replace silent fallback with fail-fast exceptions aligned to SPEC §2.2.
- Selector-facing contract:
  - missing manifest in selector-backed flows -> `FileNotFoundError` with `Migration manifest not found` (propagated from metadata manifest loader)
  - unknown/invalid user-selected exercise keys -> existing selector `ValueError` semantics remain
  - metadata-backed resolver failures surfaced by selection/packaging retain required SPEC §2.2 message fragments

Verification:

- Targeted tests assert exact exception type + message fragment behavior for missing manifest and invalid metadata scenarios.
- Owner tests: `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_selector.py`, `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_integration.py`.

Dependencies and sequencing:

- Depends on Section 1 documented error contract.
- Should complete before finalizing CLI/packager integration tests.

## 6. Test Suite Migration to Metadata-Only Contract

Objective: Rewrite snapshot-era tests to enforce metadata-only behavior, canonical paths, and fail-fast errors.

Files:

- `/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_runtime_support/test_exercise_catalogue.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_framework/test_paths.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_packager.py`
- `/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_integration.py`

Tasks:

- Remove snapshot assumptions and fixtures.
- Add assertions for required error mapping/message fragments from SPEC §2.2.
- Add assertions that packaged dry-run includes required metadata assets and supports `exercise_metadata` import.
- Add explicit checks that snapshot references/artifacts are absent.
- Add anti-regression assertions that flattened notebook/test mirrors are not produced by packaging and are not consulted by runtime/test-support lookup paths.

Contract test matrix (mandatory coverage):

| Entrypoint | Expected error | Required message fragment | Owning test file |
| --- | --- | --- | --- |
| `exercise_metadata.manifest.load_migration_manifest()` | `FileNotFoundError` | `Migration manifest not found` | `tests/test_exercise_metadata.py` |
| `exercise_metadata.resolver.resolve_notebook_path()` (unknown key) | `LookupError` | `not in the migration manifest` | `tests/test_exercise_metadata.py` |
| `exercise_metadata.resolver.resolve_notebook_path()` (missing/invalid metadata) | `LookupError` | `exercise.json is missing or invalid` | `tests/test_exercise_metadata.py` |
| `exercise_metadata.resolver.resolve_notebook_path()` (missing notebook) | `LookupError` | `expected notebook is missing` | `tests/test_exercise_metadata.py` |
| `exercise_runtime_support.exercise_catalogue.get_catalogue_entry()` | `ValueError` | `Unknown exercise key` | `tests/exercise_runtime_support/test_exercise_catalogue.py` |
| `exercise_runtime_support.exercise_catalogue.get_catalogue_key_for_exercise_id()` | `ValueError` | `Unknown exercise_id` | `tests/exercise_framework/test_api_contract.py` |

Verification:

- Required command gate passes:
  - `uv run pytest -q tests/exercise_runtime_support/test_exercise_catalogue.py tests/exercise_framework/test_paths.py tests/template_repo_cli/test_packager.py tests/template_repo_cli/test_integration.py tests/test_exercise_metadata.py tests/exercise_framework/test_api_contract.py`
- Matrix-owning tests above are updated and passing.

Dependencies and sequencing:

- Depends on Sections 2–5.
- Must complete before full acceptance gate run.

## 7. Acceptance Gates and Regression Sweep

Objective: Validate full migration across source and packaged flows with solution/student contract preserved.

Files:

- Uses repository code and dry-run output under `/tmp/template_repo_dryrun`.

Tasks:

- Run all SPEC §5.3 command gates exactly as written.
- Fix regressions until all solution-path gates pass.
- Preserve student variant contract (expected failing-student behavior unchanged).
- Enforce anti-regression guards:
  - packager must not emit flattened notebook/test mirrors
  - runtime/test-support must not include legacy fallback path resolution
  - snapshot symbols/files must remain absent from runtime and packaged outputs

Verification:

- All gates pass:
  - `uv run pytest -q ...` (targeted suites)
  - `uv run python scripts/run_pytest_variant.py --variant solution -q`
  - `uv run ./scripts/verify_solutions.sh -q`
  - CLI dry-run create command
  - dry-run runtime import/resolution smoke script
- Recommended hard guard: add CI check that fails if forbidden snapshot symbols or flattened-mirror generation logic is reintroduced.

Dependencies and sequencing:

- Depends on Sections 1–6 complete.
- Final release/merge gate.

## Critical Path Summary

1. Section 1 freezes implementation contract early to prevent drift.
2. Runtime unification (Section 2) and canonical test path enforcement (Section 3) establish core behavior.
3. Packager/collector (Section 4) and selector fail-fast tightening (Section 5) align packaging and selection with runtime contract.
4. Test migration (Section 6) enforces non-regression and mandatory fail-fast/error mapping coverage.
5. Final gates (Section 7) validate metadata-only behavior end-to-end with no snapshot/fallback path.
6. Merge order follows SPEC §4: docs + runtime + packaging + tests land together in the migration PR, with docs prepared first and verified continuously during implementation.

## Execution Tracker

### Section 1 - Documentation Updates (Contract Lock-First)

- Status: Completed
- Red tests added: Completed (`tests/exercise_runtime_support/test_runtime_contract.py`)
- Red review clean: Completed
- Green implementation complete: Completed
- Green review clean: Completed (after one fix cycle)
- Checks passed: Completed
- Action plan updated: Completed
- Commit created: Completed
- Push completed: Completed

Implementation notes:
- Added a focused docs contract test that enforces required metadata-only/fail-fast fragments and forbids stale snapshot/metadata-free wording.
- Updated docs to align with SPEC §2.1/§2.2 contract language.
- Review finding resolved: corrected `docs/CLI_README.md` contradiction about exporting per-exercise `exercise.json` and strengthened guard assertions to prevent regression.
- No approved deviations from Section 1 scope.
- Commit evidence:
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `9ff7f2c` - `docs: lock metadata-only runtime contract and add guard test`
  - Commit: `905d65d` - `chore: record section 1 execution tracker status`
  - Push: `git push` succeeded to `origin/refactor/simplifyExerciseRegistry`

### Section 2 - Runtime Catalogue and Path Resolver Unification

- Status: Completed
- Red tests added: Completed (`tests/exercise_runtime_support/test_exercise_catalogue.py`, `tests/exercise_framework/test_paths.py`)
- Red review clean: Completed
- Green implementation complete: Completed
- Green review clean: Completed
- Checks passed: Completed
- Action plan updated: Completed
- Commit created: Completed
- Push completed: Completed

Implementation notes:
- Removed snapshot constants, snapshot loading/writing helpers, and metadata-presence branching from the scoped runtime modules.
- `get_exercise_catalogue()` now always builds directly from `exercise_metadata.registry`.
- `resolve_exercise_notebook_path()` now delegates directly to metadata resolver semantics for both variants.
- Updated the targeted runtime tests to assert metadata-only catalogue resolution and metadata-resolver delegation, with no fallback branches.
- Commit evidence:
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `80a90ce` - `refactor: simplify exercise resolution by removing snapshot handling and enhancing metadata integration`
  - Push: commit is present on `origin/refactor/simplifyExerciseRegistry`
- Deviation noted:
  - The section commit also touched `.codex/agents/tidy_code_review.toml` (outside the planned Section 2 file list). Kept as-is; no rollback performed.

### Section 3 - Test-Support Canonical Path Enforcement

- Status: Completed
- Red tests added: Completed (`tests/exercise_runtime_support/test_exercise_test_support.py`)
- Red review clean: Completed
- Green implementation complete: Completed
- Green review clean: Completed
- Checks passed: Completed
- Action plan updated: Completed
- Commit created: Completed (section code commit recorded)
- Push completed: Completed

Implementation notes:
- Added focused red-phase tests for canonical-only exercise test directory resolution and module loading behaviour.
- Resolved red-review findings by replacing brittle source-text assertions with behaviour-based tests and ensuring local lint/type cleanliness for the test slice.
- Removed legacy packaged fallback path resolution from `exercise_runtime_support/exercise_test_support.py`; resolution is now canonical-only via `exercises/<construct>/<exercise_key>/tests`.
- Updated fail-fast error messaging to reference the missing canonical exercise-local tests directory explicitly.
- Green-phase review passed with no findings after targeted verification.
- Commit evidence (code):
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `d7d073a` - `refactor: enforce canonical-only exercise test support paths`
- Commit evidence (plan/tracker):
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `3f3d15d` - `chore: record section 3 execution tracker status`
  - Push: `git push` succeeded to `origin/refactor/simplifyExerciseRegistry`

### Section 4 - Packager and Collector Metadata-Surface Enforcement

- Status: Completed
- Red tests added: Completed (`tests/template_repo_cli/test_section4_metadata_contract.py`)
- Red review clean: Completed
- Green implementation complete: Completed
- Green review clean: Completed
- Checks passed: Completed
- Action plan updated: Completed
- Commit created: Completed (section code commit recorded)
- Push completed: Completed

Implementation notes:
- Added isolated Section 4 contract coverage in `tests/template_repo_cli/test_section4_metadata_contract.py` to keep metadata-surface assertions explicit and maintainable.
- Updated packager and collector flows to export metadata-backed surfaces (`exercise_metadata/`, subset `exercises/migration_manifest.json`, per-exercise `exercise.json`) and removed snapshot-era snapshot export/validation behaviour.
- Enforced anti-regression checks that flattened notebook/test mirrors are forbidden in packaged outputs.
- Updated template `.devcontainer` `files.exclude` entries to hide metadata clutter while preserving runtime behaviour.
- Aligned runtime-contract assertions and test surfaces after refactor (including explicit shared runtime-support copy path expected by runtime contract tests).
- Commit evidence (code):
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `3f6ad43` - `refactor: enforce metadata-surface packaging contract`
- Commit evidence (plan/tracker):
  - Branch: `refactor/simplifyExerciseRegistry`
  - Commit: `d996b8d` - `chore: record section 4 execution tracker status`
  - Push: `git push` succeeded to `origin/refactor/simplifyExerciseRegistry`
