**SPEC: Unify Exercise Resolution on Metadata Catalogue (Source + Packaged)**

## 1. Problem Statement

Current runtime resolution is split:

- Source repo path: `exercise_metadata.registry.build_exercise_catalogue()`
- Packaged export path: JSON snapshot fallback in `exercise_runtime_support/exercise_catalogue.py`

This creates dual behavior, duplicated guarantees, and test/docs complexity around metadata-free packaged mode.

### Target

Use one resolution method everywhere: metadata-catalogue resolution (`exercise_metadata` + manifest + per-exercise `exercise.json`) for both source and packaged exports, with fail-fast behavior and `exercise_key` as the only resolver identity.

## 2. Target Architecture

- `exercise_runtime_support.exercise_catalogue.get_exercise_catalogue()` always builds from `exercise_metadata.registry.build_exercise_catalogue()`.
- Runtime notebook path resolution always delegates through metadata resolver semantics.
- No snapshot file generation, loading, or validation.
- No environment-based “has metadata package?” branching.

### 2.1 Packaged Runtime Contract

Packaged exports MUST include the following at repo root:

- `exercise_metadata/` package (including `__init__.py`, `registry.py`, `resolver.py`, `loader.py`, `manifest.py`, `schema.py`)
- `exercises/migration_manifest.json`
- `exercises/<construct>/<exercise_key>/exercise.json` for every exported exercise
- `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- `exercises/<construct>/<exercise_key>/tests/` (canonical exercise-local tests path)

Importability contract:

- `exercise_metadata` must be importable via normal repo-root Python import resolution (`import exercise_metadata...`) without runtime path hacks.
- Packaged runtime and tests must not depend on snapshot artifacts.
- Flattened notebook/test mirrors in packaged outputs are forbidden for this migration target. Packaging and runtime must treat canonical exercise-local paths as the only valid authoring and execution surfaces.

### 2.2 Error Contract (Fail-Fast)

No silent fallback is allowed. Preserve existing module-level exception families and require diagnostic message fragments:

- Missing manifest: `FileNotFoundError` containing `Migration manifest not found`
- Unknown exercise key in manifest resolution: `LookupError` containing `not in the migration manifest`
- Missing/invalid canonical metadata for canonical resolution: `LookupError` containing `exercise.json is missing or invalid`
- Missing canonical notebook: `LookupError` containing `expected notebook is missing`
- Unknown catalogue key/id: `ValueError` containing `Unknown exercise key` or `Unknown exercise_id`

API-to-error mapping for primary entrypoints:

- `exercise_metadata.manifest.load_migration_manifest()`:
  missing manifest -> `FileNotFoundError` with `Migration manifest not found`
- `exercise_metadata.resolver.resolve_notebook_path()`:
  unknown manifest key -> `LookupError` with `not in the migration manifest`
- `exercise_metadata.resolver.resolve_notebook_path()`:
  canonical metadata missing/invalid -> `LookupError` with `exercise.json is missing or invalid`
- `exercise_metadata.resolver.resolve_notebook_path()`:
  canonical notebook missing -> `LookupError` with `expected notebook is missing`
- `exercise_runtime_support.exercise_catalogue.get_catalogue_entry()`:
  unknown key -> `ValueError` with `Unknown exercise key`
- `exercise_runtime_support.exercise_catalogue.get_catalogue_key_for_exercise_id()`:
  unknown id -> `ValueError` with `Unknown exercise_id`

## 3. Exact Files/Modules to Modify (with rationale)

- [`exercise_runtime_support/exercise_catalogue.py`](/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_catalogue.py)  
  Remove snapshot constants/functions and import-branch logic; make metadata catalogue the sole source.

- [`exercise_runtime_support/exercise_framework/paths.py`](/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_framework/paths.py)  
  Remove metadata-presence branching and packaged fallback resolver path; always resolve by exercise key via metadata-driven flow.

- [`exercise_runtime_support/exercise_test_support.py`](/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_test_support.py)  
  Remove `tests/<construct>/<exercise_key>` packaged fallback and use canonical exercise-local tests only under `exercises/<construct>/<exercise_key>/tests`.

- [`scripts/template_repo_cli/core/packager.py`](/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/packager.py)  
  Stop writing/validating snapshot; package metadata module + manifest + per-exercise `exercise.json`; ensure canonical exercise-local tests are exported.

- [`scripts/template_repo_cli/core/collector.py`](/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/collector.py)  
  Collect metadata runtime surfaces required by the packaged runtime contract.

- [`scripts/template_repo_cli/core/selector.py`](/workspaces/PythonExerciseGeneratorAndDistributor/scripts/template_repo_cli/core/selector.py)  
  Remove silent empty-registry behavior when manifest is missing; fail fast under metadata contract violations.

- [`template_repo_files/.devcontainer/devcontainer.json`](/workspaces/PythonExerciseGeneratorAndDistributor/template_repo_files/.devcontainer/devcontainer.json)  
  Add/adjust `files.exclude` to hide metadata files/folders from student-facing explorer views.

- [`docs/execution-model.md`](/workspaces/PythonExerciseGeneratorAndDistributor/docs/execution-model.md), [`docs/testing-framework.md`](/workspaces/PythonExerciseGeneratorAndDistributor/docs/testing-framework.md), [`docs/development.md`](/workspaces/PythonExerciseGeneratorAndDistributor/docs/development.md), [`docs/setup.md`](/workspaces/PythonExerciseGeneratorAndDistributor/docs/setup.md), [`AGENTS.md`](/workspaces/PythonExerciseGeneratorAndDistributor/AGENTS.md)  
  Remove metadata-free/snapshot language and document unified metadata-catalogue runtime contract.

## 4. Migration Policy and Rollout

- No backward compatibility requirement for snapshot-based packaged exports.
- Any failures caused by this migration are in-scope and must be fixed in the migration PR(s).
- New template exports must satisfy the Packaged Runtime Contract in §2.1.
- Classroom usability is preserved by keeping canonical student notebook/test workflows operational.

Rollout order:

1. Land packager + collector + runtime changes together.
2. Update tests to enforce metadata-only behavior and remove snapshot assumptions.
3. Update docs/contracts in the same PR to avoid mixed guidance.
4. Validate acceptance gates in §5 before merge.

## 5. Validation and Acceptance Criteria

A migration is complete only when all gates below pass.

### 5.1 Environment/Workflow Matrix

- Source repo runtime: metadata catalogue resolution works and snapshot path is absent.
- Packaged dry-run runtime: `exercise_metadata` imports successfully and catalogue/path resolution works without snapshot.
- Solution variant: solution checks pass.
- Student variant contract: expected failing-student behavior remains unchanged.

### 5.2 Required Test Changes

Replace/remove snapshot-era assertions in:

- [`tests/exercise_runtime_support/test_exercise_catalogue.py`](/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_runtime_support/test_exercise_catalogue.py)
- [`tests/exercise_framework/test_paths.py`](/workspaces/PythonExerciseGeneratorAndDistributor/tests/exercise_framework/test_paths.py)
- [`tests/template_repo_cli/test_packager.py`](/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_packager.py)
- [`tests/template_repo_cli/test_integration.py`](/workspaces/PythonExerciseGeneratorAndDistributor/tests/template_repo_cli/test_integration.py)

Add/adjust assertions for:

- Missing metadata/manifest fail-fast behavior per §2.2.
- Packaged dry-run workspace includes all required metadata assets in §2.1.
- Packaged runtime imports `exercise_metadata` and executes checks successfully.
- No snapshot artifact references remain in runtime tests, packager tests, and integration tests.

### 5.3 Command Gates

Run and pass these commands before merge:

1. `uv run pytest -q tests/exercise_runtime_support/test_exercise_catalogue.py tests/exercise_framework/test_paths.py tests/template_repo_cli/test_packager.py tests/template_repo_cli/test_integration.py`
2. `uv run python scripts/run_pytest_variant.py --variant solution -q`
3. `uv run ./scripts/verify_solutions.sh -q`
4. `uv run python scripts/template_repo_cli/cli.py --dry-run --output-dir /tmp/template_repo_dryrun create --exercise-keys ex002_sequence_modify_basics --repo-name template-repo-dryrun-check`
5. `cd /tmp/template_repo_dryrun && uv run python - <<'PY'\nfrom exercise_runtime_support.exercise_catalogue import get_exercise_catalogue\nfrom exercise_runtime_support.exercise_framework.paths import resolve_exercise_notebook_path\nentry = get_exercise_catalogue()[0]\nresolved = resolve_exercise_notebook_path(entry.exercise_key, variant='student')\nprint(entry.exercise_key)\nprint(resolved)\nPY`

For student-variant expectations, preserve existing repository contract and related tests; do not alter tests merely to force student variants to pass.

## 6. Risks and Mitigations

- Risk: path contract mismatch between packaged outputs and runtime lookup.
  Mitigation: enforce canonical `exercises/<construct>/<exercise_key>/tests` export and remove alternate lookup paths.

- Risk: metadata import regressions in packaged repos.
  Mitigation: explicit packaged runtime contract + integration tests asserting import success.

- Risk: accidental reintroduction of fallback behavior.
  Mitigation: add tests asserting absence of snapshot symbols, snapshot files, and snapshot docs references.

- Risk: student UX clutter from added metadata files.
  Mitigation: required `files.exclude` entries in template devcontainer configuration.

## 7. Ordered Implementation Action Plan

1. Remove snapshot API and fallback branches in runtime catalogue and path resolver modules.
2. Update exercise test-support path resolution to canonical exercise-local tests only.
3. Update packager/collector to emit required metadata surfaces and canonical exercise-local tests.
4. Tighten selector behavior to fail fast when metadata prerequisites are missing.
5. Rewrite runtime + packager + integration tests to enforce metadata-only contract and error contract.
6. Remove snapshot artifacts and references from code, fixtures, and docs.
7. Run acceptance gates in §5 and fix all resulting migration regressions.

### 7.1 Snapshot Removal Checklist

- Remove snapshot symbols from [`exercise_runtime_support/exercise_catalogue.py`](/workspaces/PythonExerciseGeneratorAndDistributor/exercise_runtime_support/exercise_catalogue.py):
  - `CATALOGUE_SNAPSHOT_FILENAME`
  - `get_catalogue_snapshot_path`
  - `load_catalogue_snapshot`
  - `write_catalogue_snapshot`
  - snapshot-based branching in `get_exercise_catalogue`
- Remove runtime/package expectations for `exercise_catalogue_snapshot.json` across tests and packaging validation.
- Remove snapshot-focused tests and fixture setup in runtime/packager/integration suites.
- Remove snapshot terminology from docs and AGENTS guidance.
