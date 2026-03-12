# Phase 4 Migration Checklist

## Required Migration Rules

These rules are restated from [ACTION_PLAN.md](./ACTION_PLAN.md) and apply throughout this checklist:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless [ACTION_PLAN.md](./ACTION_PLAN.md) is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into [ACTION_PLAN.md](./ACTION_PLAN.md).

## Checklist Header

- Checklist title: Phase 4 Migration Checklist — Execution Model And Source-To-Export Contract
- Related action-plan phase or stream: Phase 4 — Execution Model And Source-To-Export Contract
- Author: Codex Implementer Agent
- Date: 2026-03-12
- Status: `draft`
- Scope summary: Define, document, and then implement the repository execution model for exercise discovery, notebook variant selection, shared grading/runtime imports, repository pytest discovery, and source-to-export packaging so later migration phases can move exercise-local tests and canonical authoring files without ambiguity.
- Explicitly out of scope: bulk migration of every exercise into the future canonical `exercises/<construct>/<exercise_key>/...` layout; adding new metadata fields beyond the agreed minimal schema; final public API renames in student-facing helpers; moving all top-level tests immediately; authoring new notebook exercises; changing student notebook content; cutting over all legacy callers before the replacement model is proven.

## Objective

When this checklist is complete, the repository should have one explicit, repo-specific execution contract covering four things that are currently entangled:

- how repository tests are discovered when exercise-specific tests no longer live only under top-level `tests/`
- how shared grading/runtime support is imported by repository tests and by exported Classroom repositories
- how student versus solution notebook selection works without using `PYTUTOR_NOTEBOOKS_DIR` as a layout-compatibility escape hatch
- how canonical authoring files in `exercises/` map to the flattened export contract already used by Classroom templates

More specifically:

- the future implementation agent should be able to update `pyproject.toml`, `pytest.ini`, the grading helpers, the template packager, docs, and workflows without inventing missing rules mid-migration
- top-level path assumptions such as `notebooks/<exercise_key>.ipynb`, `notebooks/solutions/<exercise_key>.ipynb`, and `tests/test_<exercise_key>.py` should stop being treated as the authoring truth, even though the exported Classroom contract may continue to use those flattened paths
- repository execution and exported Classroom execution should be treated as separate first-class contracts with separate verification surfaces
- failure behaviour should become intentional: if an exercise is marked as migrated but its canonical files are missing, the resolver and packager must fail hard rather than silently falling back to old paths

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [x] Required decisions from [ACTION_PLAN.md](./ACTION_PLAN.md) are settled.
- [x] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly.

Notes:

- Decisions relied on:
  - `exercise_key` is the only canonical resolver input.
  - Exported Classroom repositories remain metadata-free.
  - Flattened export remains the current expected Classroom contract unless [ACTION_PLAN.md](./ACTION_PLAN.md) changes.
  - `PYTUTOR_NOTEBOOKS_DIR` must not remain a layout-compatibility fallback in the target model.
  - Deliberate breakage is preferred over compatibility wrappers once the replacement model exists.
- Open assumptions:
  - Phase 2 will provide the shared resolver and migration-manifest layer that Phase 4 execution code can call.
  - Phase 3 will provide metadata-driven exercise identity and catalogue information so Phase 4 does not need to maintain a second registry.
  - A sensible pilot should include at least `ex002_sequence_modify_basics` and `ex007_sequence_debug_casting`, because the current repo already uses both a top-level exercise test and a nested `tests/ex002_sequence_modify_basics/` parity surface, plus interactive/debug self-check behaviour.
  - The current repo still contains duplicate and inconsistent legacy artefacts, so Phase 4 implementation must expect pre-clean-up states until earlier phases are complete.

## Affected Surfaces Inventory

### Files And Paths To Update

- [ ] Source files:
  - Phase 2 shared resolver/metadata module (path to be chosen in Phase 2) — must become the only execution-path source of truth used by repository tests, student checker code, packager code, and verification scripts.
  - `pyproject.toml` — currently pins pytest discovery to `testpaths = ["tests"]`, packages `tests`, and exposes `template_repo_cli`; must encode the agreed repository discovery and import model.
  - `pytest.ini` — duplicates the current top-level `tests` discovery contract and must be kept aligned with `pyproject.toml`.
  - `tests/notebook_grader.py` — currently accepts raw notebook paths and uses `PYTUTOR_NOTEBOOKS_DIR` root swapping with a silent `candidate.exists()` fallback; must move to the new resolver and explicit variant-selection contract.
  - `tests/helpers.py` — currently proxies notebook path resolution and autograde environment setup; must stay consistent with the new execution model.
  - `tests/exercise_framework/paths.py` — duplicates notebook-path override logic and currently treats path strings as canonical inputs.
  - `tests/exercise_framework/runtime.py` — wraps `tests.notebook_grader` and caches by notebook path; must align with the future exercise-key-driven execution model.
  - `tests/exercise_framework/api.py` — currently runs notebook checks from hard-coded notebook path constants and ordered slug lists.
  - `tests/exercise_framework/expectations.py` — resolves `EX002_NOTEBOOK_PATH` and will need to consume the new execution contract rather than raw path constants.
  - `tests/exercise_expectations/__init__.py` and the per-exercise expectation modules — currently expose notebook path constants that imply the old flattened authoring layout.
  - `tests/student_checker/api.py` — currently hard-codes `_EX001_SLUG` through `_EX007_SLUG`, `_NOTEBOOK_ORDER`, and slug-based labels.
  - `tests/student_checker/notebook_runtime.py` — currently accepts a notebook path string, scans tags from the physical notebook, and executes tagged cells via raw path calls.
  - `tests/student_checker/checks/ex003.py`, `tests/student_checker/checks/ex004.py`, `tests/student_checker/checks/ex005.py`, `tests/student_checker/checks/ex006.py`, `tests/student_checker/checks/ex007.py` — each contains `_resolve_ex00X_notebook_path()` helpers that still encode notebook-path assumptions.
  - `scripts/build_autograde_payload.py` — currently validates `PYTUTOR_NOTEBOOKS_DIR` against `notebooks` and `notebooks/solutions`, and derives failure semantics from that value.
  - `scripts/verify_solutions.sh` — hard-codes `PYTUTOR_NOTEBOOKS_DIR="notebooks/solutions"`.
  - `scripts/new_exercise.py` — currently scaffolds top-level `notebooks/<exercise_key>.ipynb`, `notebooks/solutions/<exercise_key>.ipynb`, and `tests/test_<exercise_key>.py`, and writes self-check examples against that legacy layout.
  - `scripts/verify_exercise_quality.py` — currently infers exercise directories and notebook relationships from the flattened notebook tree and current `exercises/` shape.
  - `scripts/template_repo_cli/core/collector.py` — currently assumes source notebooks live at `notebooks/<exercise_key>.ipynb` and tests at `tests/test_<exercise_key>.py`.
  - `scripts/template_repo_cli/core/packager.py` — currently copies selected notebooks into `workspace/notebooks/` and selected tests into `workspace/tests/`, while also copying runtime support from top-level `tests/`.
  - `scripts/template_repo_cli/core/selector.py` — currently infers construct/type membership from `exercises/<construct>/<type>/<exercise_key>/` path shape.
  - `scripts/template_repo_cli/utils/filesystem.py` — currently has a separate `resolve_notebook_path()` helper that treats a bare filename as a notebook under `notebooks/`.
  - `scripts/template_repo_cli/cli.py` — should remain aligned with the new source-selection and packaging rules.
- [ ] Test files:
  - `tests/exercise_framework/test_paths.py` — currently pins the duplicate `resolve_notebook_path()` behaviour.
  - `tests/exercise_framework/test_runtime.py` — currently asserts runtime wrappers behave correctly with `PYTUTOR_NOTEBOOKS_DIR`.
  - `tests/exercise_framework/test_api_contract.py` — validates notebook checks under current solution-selection semantics.
  - `tests/exercise_framework/test_parity_paths.py` — parity checks for path-resolution helpers.
  - `tests/exercise_framework/test_autograde_parity.py` and `tests/exercise_framework/test_parity_autograde_ex002.py` — currently run parity checks using `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` and explicit test file paths.
  - `tests/student_checker/test_notebook_runtime.py` — currently validates notebook-runtime execution using direct notebook path inputs.
  - `tests/student_checker/test_reporting.py` and `tests/student_checker/test_checks_aliasing.py` — may need minor updates if the self-check contract changes shape.
  - `tests/template_repo_cli/test_collector.py` — pins top-level source file discovery.
  - `tests/template_repo_cli/test_filesystem.py` — pins legacy `resolve_notebook_path()` behaviour for bare filenames and `notebooks/` paths.
  - `tests/template_repo_cli/test_packager.py` — pins flattened output layout and copied support assets.
  - `tests/template_repo_cli/test_integration.py` — validates dry-run template output, including notebook self-check invocation inside the packaged workspace.
  - `tests/template_repo_cli/test_selector.py` — construct/type selection tests may need updates if selection stops relying only on directory shape.
  - `tests/test_build_autograde_payload.py` — currently asserts environment validation and autograde payload logic under the old variant-selection contract.
  - `tests/test_integration_autograding.py` — repository-to-autograde integration surface.
  - `tests/test_new_exercise.py` — will need updates once the scaffold target layout is decided in later phases, but Phase 4 must list the required contract changes now.
  - `tests/test_ex001_sanity.py`, `tests/test_ex002_sequence_modify_basics.py`, `tests/test_ex003_sequence_modify_variables.py`, `tests/test_ex004_sequence_debug_syntax.py`, `tests/test_ex005_sequence_debug_logic.py`, `tests/test_ex006_sequence_modify_casting.py`, `tests/test_ex007_construct_checks.py`, `tests/test_ex007_sequence_debug_casting.py` — current exercise-specific tests that still rely on flattened notebook paths.
  - `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` — existing nested exercise-specific parity test surface that should inform the future discovery model.
- [ ] Docs:
  - `docs/CLI_README.md` — explicitly documents flattened template contents under "What Gets Included in Templates".
  - `docs/testing-framework.md` — documents multiple `resolve_notebook_path()` helpers and the current execution semantics.
  - `docs/development.md` — teaches `PYTUTOR_NOTEBOOKS_DIR` as the current solution-selection mechanism.
  - `docs/project-structure.md` — describes current top-level `notebooks/` and `tests/` assumptions.
  - `docs/exercise-testing.md` — includes runtime helper contracts.
  - `docs/exercise-types/debug.md` and `docs/exercise-types/modify.md` — reference current test locations and helper usage.
  - `docs/github-classroom-autograding-guide.md` — must remain consistent with template workflow and exported repository behaviour.
- [ ] Workflows:
  - `.github/workflows/tests.yml` — currently runs all repository tests with `PYTUTOR_NOTEBOOKS_DIR: notebooks/solutions`.
  - `.github/workflows/tests-solutions.yml` — duplicates the same solution-selection environment contract.
  - `template_repo_files/.github/workflows/classroom.yml` — currently runs autograding in student mode using `PYTUTOR_NOTEBOOKS_DIR: notebooks`.
- [ ] Agent instructions:
  - `.github/agents/exercise_generation.md.agent.md` — currently teaches dual notebook trees and `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` verification.
  - `.github/agents/exercise_verifier.md.agent.md` — currently teaches the same execution model and path layout.
  - `AGENTS.md` — should remain consistent once repository execution and export contracts are updated in later phases.
- [ ] Template/export files:
  - `template_repo_files/pyproject.toml` — packaged pytest contract for exported Classroom repositories.
  - `template_repo_files/pytest.ini` — duplicate packaged pytest discovery contract.
  - `template_repo_files/.github/workflows/classroom.yml` — packaged execution mode for student repositories.
  - `template_repo_files/README.md.template` — may need wording updates if exported behaviour is described explicitly.
- [ ] Exercise directories:
  - `exercises/sequence/modify/ex002_sequence_modify_basics/`
  - `exercises/sequence/modify/ex003_sequence_modify_variables/`
  - `exercises/sequence/debug/ex004_sequence_debug_syntax/`
  - `exercises/sequence/debug/ex005_sequence_debug_logic/`
  - `exercises/sequence/modify/ex006_sequence_modify_casting/`
  - `exercises/sequence/debug/ex007_sequence_debug_casting/`
  - `exercises/ex001_sanity/` and `exercises/ex006_sequence_modify_casting/` — currently non-canonical duplicate roots that must be accounted for in migration planning.

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
  - `tests.notebook_grader` — current low-level notebook executor using path input plus environment override.
  - `tests.exercise_framework.paths` — duplicate path resolution logic.
  - `tests.exercise_framework.runtime` — public runtime wrapper layer.
  - `tests.exercise_framework.api` — public notebook-check API keyed by slug lists and notebook paths.
  - `tests.student_checker.api` and `tests.student_checker.notebook_runtime` — student-facing self-check API and notebook runner.
  - `scripts.template_repo_cli.core.collector`, `scripts.template_repo_cli.core.packager`, `scripts.template_repo_cli.core.selector`, `scripts.template_repo_cli.utils.filesystem` — source selection and export mapping.
  - `scripts.build_autograde_payload` — workflow-facing execution and autograde payload builder.
  - `scripts.new_exercise` — scaffold contract that must eventually emit canonical authoring files without breaking the current Classroom export surface.
- [ ] Public functions or methods:
  - `tests.notebook_grader.resolve_notebook_path()` — current behaviour: accepts notebook paths and may silently fall back to the original path if the override candidate does not exist; required change: replace or retire in favour of resolver calls keyed by `exercise_key` plus explicit variant selection.
  - `tests.notebook_grader.extract_tagged_code()`, `exec_tagged_code()`, `run_cell_and_capture_output()`, `run_cell_with_input()`, `get_explanation_cell()` — current behaviour: accept path inputs; required change: agree whether public call sites switch to `exercise_key` and `variant`, or whether only an internal adapter layer remains during transition.
  - `tests.exercise_framework.paths.resolve_notebook_path()` — current behaviour: second implementation of environment-based path swapping; required change: remove duplicated path rules and call the shared execution model.
  - `tests.exercise_framework.runtime.resolve_notebook_path()` — current behaviour: thin wrapper over `tests.notebook_grader.resolve_notebook_path()`; required change: reflect the final runtime contract.
  - `tests.exercise_framework.api.run_all_checks()` and `run_notebook_check()` — current behaviour: drive checks via hard-coded slug order and expectation-module notebook constants; required change: consume the shared execution contract.
  - `tests.student_checker.api.check_notebook()` — current behaviour: accepts a slug and looks it up in a hard-coded dictionary; required change: keep `exercise_key`-based entry but remove hidden layout assumptions.
  - `tests.student_checker.notebook_runtime.run_notebook_checks()` — current behaviour: accepts a notebook path; required change: define whether the long-term student self-check interface should accept `exercise_key`, a resolved canonical notebook path, or both during a short internal-only transition.
  - `tests.student_checker.checks.ex003._resolve_ex003_notebook_path()` and the matching `_resolve_ex00X_notebook_path()` helpers in the other checker modules — current behaviour: local path helpers; required change: remove these in favour of the shared resolver.
  - `scripts.build_autograde_payload.validate_environment()` and `_should_zero_scores_on_failure()` — current behaviour: variant semantics are inferred from `PYTUTOR_NOTEBOOKS_DIR`; required change: bind autograde behaviour to the new student/solution selector contract.
  - `scripts.template_repo_cli.core.collector.FileCollector.collect_files()` — current behaviour: builds source file paths from top-level conventions; required change: collect canonical authoring files and export destinations explicitly.
  - `scripts.template_repo_cli.core.packager.TemplatePackager.copy_exercise_files()` — current behaviour: copies source notebook/test files into flattened `workspace/notebooks/` and `workspace/tests/`; required change: keep or adjust the flattened export contract deliberately, not accidentally.
  - `scripts.template_repo_cli.utils.filesystem.resolve_notebook_path()` — current behaviour: filename-only inputs are assumed to live under `notebooks/`; required change: remove assumptions that bypass the shared resolver.
  - `scripts.new_exercise._check_exercise_not_exists()`, `_make_check_answers_cell()`, `_make_notebook_with_parts()`, and `main()` — current behaviour: scaffold flattened source notebooks and tests; required change: align scaffolding with the future authoring contract once Phase 4 makes that contract explicit.
- [ ] CLI commands or flags:
  - `template_repo_cli list` — must remain able to show selectable exercises regardless of where exercise-local tests physically live.
  - `template_repo_cli validate` — must validate selection and packaging rules against the new source contract.
  - `template_repo_cli create` and `template_repo_cli update-repo` — must package from canonical source files while keeping exported Classroom repositories metadata-free.
  - `python scripts/build_autograde_payload.py` — workflow entry point whose variant semantics must match the new contract.
  - `scripts/verify_solutions.sh` — local helper that must stop teaching the wrong long-term selection mechanism.
- [ ] Environment variables:
  - `PYTUTOR_NOTEBOOKS_DIR` — current meaning is overloaded between variant selection and path-root swapping; Phase 4 must replace or tightly narrow this contract.
- [ ] Workflow jobs or steps:
  - `tests.yml:pytest` — repository CI must run the correct variant and discover both shared and exercise-local tests under the agreed source layout.
  - `tests-solutions.yml:pytest_solutions` — same requirement for solution-mode CI.
  - `template_repo_files/.github/workflows/classroom.yml:autograding` — exported Classroom workflow must grade the student variant without requiring source metadata or source-repo path layout.
- [ ] Packaging/export contracts:
  - Source repository contract — future canonical authoring paths are expected to live under `exercises/<construct>/<exercise_key>/...`.
  - Exported Classroom contract — current flattened output remains `notebooks/exNNN_slug.ipynb`, `tests/test_exNNN_slug.py`, shared runtime support under `tests/`, workflow files under `.github/workflows/`, and no `exercise.json` or `exercises/` tree.
- [ ] Notebook self-check contracts:
  - `from tests.student_checker import check_notebook; check_notebook('<exercise_key>')` — currently used in generated workspaces and agent guidance; must stay usable in exported repositories.
  - Optional notebook self-check cells generated by `scripts.new_exercise.py` — must not depend on source-repo metadata files being present in Classroom exports.

### Current Assumptions Being Removed

- [ ] The repository test suite is discoverable only because `pytest` is pinned to top-level `tests/` in both `pyproject.toml` and `pytest.ini`.
- [ ] Shared runtime code can safely live in the importable `tests` package without an explicit decision about how that interacts with pytest collection once exercise-local tests move under `exercises/**/tests/`.
- [ ] Student versus solution selection is the same thing as changing the notebook root directory via `PYTUTOR_NOTEBOOKS_DIR`.
- [ ] Silent fallback from `notebooks/solutions/<relative-path>` to the original notebook path is acceptable when the override file is missing.
- [ ] Packaging source files from top-level `notebooks/` and `tests/` means the export contract is already defined.
- [ ] A bare notebook filename such as `ex001_sanity.ipynb` can be treated as implicitly living under `notebooks/`.
- [ ] Self-check and grading code may keep their own local `_resolve_ex00X_notebook_path()` helpers without creating a second execution model.
- [ ] Duplicate exercise-specific test surfaces, such as the top-level `tests/test_ex002_sequence_modify_basics.py` and the nested `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`, do not matter to future discovery design.

## Implementation Tasks

### Code Changes

- [ ] Add:
  - one explicit execution-model document or module-level contract that defines repository discovery, runtime imports, variant selection, and source-to-export mapping in the same place
  - a single shared execution/resolution entry point that the current notebook grader, exercise framework, student checker, packager, and workflow helpers all call
  - a deliberate repository pytest discovery configuration that includes exercise-local tests when they move under `exercises/**/tests/`
  - explicit source-to-export mapping logic for canonical authoring assets, rather than constructing source or destination paths ad hoc in multiple modules
  - fail-fast validation that distinguishes these cases clearly:
    - unknown `exercise_key`
    - exercise marked as migrated but missing canonical notebook/test files
    - caller still using a legacy path-based entry point
    - source packaging request that would export metadata or source-only files
- [ ] Update:
  - `pyproject.toml` and `pytest.ini` so repository discovery no longer relies on top-level `tests` alone
  - `tests/notebook_grader.py` and `tests/exercise_framework/paths.py` so path-swapping logic is not duplicated
  - `tests/exercise_framework/runtime.py` and `tests/student_checker/notebook_runtime.py` so variant selection is explicit and layout validation is strict
  - `tests/student_checker/api.py` and `tests/exercise_framework/api.py` so they consume the same execution model rather than keeping their own layout assumptions
  - `scripts/build_autograde_payload.py` so student-mode failure behaviour is keyed to the new variant selection contract rather than the `PYTUTOR_NOTEBOOKS_DIR` string value
  - `scripts/template_repo_cli/core/collector.py` and `scripts/template_repo_cli/core/packager.py` so they collect from canonical source assets and still export the agreed flattened output
  - `scripts/template_repo_cli/utils/filesystem.py` so it no longer provides a shadow notebook-resolution rule that bypasses the shared contract
  - `scripts/verify_solutions.sh`, `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml`, and `template_repo_files/.github/workflows/classroom.yml` so workflow semantics match the new execution model exactly
- [ ] Remove:
  - silent path fallback behaviour in notebook resolution helpers
  - duplicate notebook-path resolution functions that exist only to preserve the old layout model
  - legacy assumptions in template packager code that top-level source layout is canonical
  - documentation and agent guidance that instructs `PYTUTOR_NOTEBOOKS_DIR` as a long-term layout selector
- [ ] Rename or relocate:
  - move or rename shared runtime helpers only if the Phase 4 decision is to stop using top-level `tests` as the support package; if this decision changes the current high-level plan, update [ACTION_PLAN.md](./ACTION_PLAN.md) first
  - relocate exercise-specific test files only after the repository discovery model has been proved on a pilot exercise set
- [ ] Fail-fast behaviour to add:
  - path-based resolver inputs fail with a clear error naming the replacement `exercise_key` contract
  - student-versus-solution selector rejects unknown values and does not try to infer layout fallbacks
  - packaging fails if an exercise is selected for export but canonical authoring files are missing
  - repository test runs fail clearly if duplicate discovery causes the same exercise-specific surface to be collected twice

### Data And Metadata Changes

- [ ] `exercise.json` changes:
  - none should be added for notebook paths, test paths, workflow names, tag names, or self-check flags
  - if Phase 4 appears to need new metadata fields, treat that as an action-plan escalation rather than a local checklist shortcut
- [ ] Derived-data/index changes:
  - extend the Phase 2/3 derived index or migration manifest so execution code can tell whether an exercise still uses legacy source paths or canonical authoring paths
  - record source-layout state in the migration manifest or equivalent derived data, not in exported Classroom artefacts
  - derive export destinations (`notebooks/exNNN_slug.ipynb`, `tests/test_exNNN_slug.py`) from the canonical authoring record rather than storing them per exercise as metadata
- [ ] Registry replacement work:
  - remove local path registries from notebook grader, student checker, exercise framework, and template CLI code once the shared execution model exists
  - keep behavioural expectations in `tests/exercise_expectations`, but stop using those modules as a second path registry
- [ ] Migration manifest updates:
  - make the manifest explicit about which exercises are safe to resolve from canonical authoring paths
  - require the manifest to trigger hard failure when a supposedly migrated exercise is missing canonical notebook or test files

### Test Changes

List both existing tests to update and new tests to add.

- [ ] Update existing unit tests:
  - `tests/exercise_framework/test_paths.py`
  - `tests/exercise_framework/test_runtime.py`
  - `tests/exercise_framework/test_api_contract.py`
  - `tests/exercise_framework/test_parity_paths.py`
  - `tests/student_checker/test_notebook_runtime.py`
  - `tests/template_repo_cli/test_collector.py`
  - `tests/template_repo_cli/test_filesystem.py`
  - `tests/test_build_autograde_payload.py`
- [ ] Update integration tests:
  - `tests/exercise_framework/test_autograde_parity.py`
  - `tests/exercise_framework/test_parity_autograde_ex002.py`
  - `tests/template_repo_cli/test_integration.py`
  - `tests/test_integration_autograding.py`
  - any future pilot exercise-local tests under `exercises/**/tests/`
- [ ] Update packaging/template tests:
  - `tests/template_repo_cli/test_packager.py`
  - `tests/template_repo_cli/test_integration.py`
  - `tests/template_repo_cli/conftest.py` sample exercise fixtures
- [ ] Update workflow-related tests:
  - `tests/test_build_autograde_payload.py`
  - `tests/exercise_framework/test_autograde_parity.py`
  - `tests/exercise_framework/test_parity_autograde_ex002.py`
  - add a workflow-facing test for the final student/solution selector contract if that logic lives outside existing modules
- [ ] Remove obsolete tests:
  - tests that explicitly assert `PYTUTOR_NOTEBOOKS_DIR` root swapping and silent fallback behaviour once the new selector exists
  - tests that depend on filename-only notebook resolution through `scripts.template_repo_cli.utils.filesystem.resolve_notebook_path()` if that helper is retired
  - any temporary parity tests that exist only to support an abandoned intermediate import/discovery model

### New Test Cases Required

Every checklist should spell out the behaviour that must be proved, not just the files to edit.

- [ ] Positive case:
  - resolving `ex002_sequence_modify_basics` in repository mode returns the canonical authoring notebook and canonical exercise-local test file once that exercise is marked as migrated
  - repository pytest discovery collects a pilot exercise test from `exercises/**/tests/` while still collecting shared framework tests from top-level `tests/`
  - `check_notebook('ex002_sequence_modify_basics')` still works in an exported template repository without `exercise.json`
- [ ] Failure case:
  - path-based resolver input such as `notebooks/ex002_sequence_modify_basics.ipynb` fails with a clear, non-fallback error once the public execution model has been cut over
  - a migrated exercise whose canonical `student.ipynb`, `solution.ipynb`, or `tests/test_<exercise_key>.py` is missing causes a hard failure in repository test runs and in packaging
  - variant selection rejects invalid values rather than defaulting silently
- [ ] Regression case:
  - existing exercise-specific checks for `ex002_sequence_modify_basics` still produce the same task metadata in autograde payloads after the execution model changes
  - shared runtime imports used by `tests/student_checker` and `tests/exercise_framework` continue to work after repository discovery changes
  - duplicate collection is detected and prevented when both a legacy top-level test and a migrated exercise-local test exist for the same exercise during a transition window
- [ ] Export/package case:
  - packaging a migrated exercise from canonical authoring files still writes `workspace/notebooks/ex002_sequence_modify_basics.ipynb` and `workspace/tests/test_ex002_sequence_modify_basics.py`
  - packaged templates exclude `exercise.json`, migration manifests, and the source `exercises/` tree
  - packaged templates still include the required shared runtime support files copied by `TemplatePackager.REQUIRED_TEST_FILES` and `TemplatePackager.REQUIRED_TEST_DIRECTORIES`
- [ ] Student-mode case:
  - the exported Classroom workflow runs the student variant and zeroes scores on failure according to the new explicit student-mode contract
  - notebook self-check commands in a packaged workspace continue to run against the student notebook variant only
- [ ] Solution-mode case:
  - repository CI can run the solution variant without relying on notebook-root path swapping
  - solution verification for pilot exercises still passes once the notebook authoring files live under canonical exercise directories

## Docs, Agents, And Workflow Updates

- [ ] Contributor docs:
  - update `docs/development.md`, `docs/testing-framework.md`, and `docs/project-structure.md` to explain the repository execution model and the difference between source-repo authoring paths and exported Classroom paths
- [ ] Teaching docs:
  - update `docs/exercise-testing.md`, `docs/exercise-types/debug.md`, and `docs/exercise-types/modify.md` where they currently name top-level test paths or legacy runtime helpers
- [ ] Agent docs:
  - update `.github/agents/exercise_generation.md.agent.md` and `.github/agents/exercise_verifier.md.agent.md` so they stop teaching `PYTUTOR_NOTEBOOKS_DIR` as the canonical long-term solution-selection model
  - update `AGENTS.md` if the implementation changes the practical default commands contributors should run
- [ ] Repository workflows:
  - update `.github/workflows/tests.yml` and `.github/workflows/tests-solutions.yml` to use the new variant-selection mechanism and repository discovery contract
- [ ] Template workflows:
  - update `template_repo_files/.github/workflows/classroom.yml` so exported autograding stays student-mode, metadata-free, and aligned with the new execution model
- [ ] CLI examples:
  - update `docs/CLI_README.md` examples and packaged-content documentation to describe the intentional flattening contract and the fact that source-repo authoring paths may differ

## Verification Plan

State exactly how this migration unit will be verified.

### Commands To Run

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/exercise_framework/test_paths.py \
  tests/exercise_framework/test_runtime.py \
  tests/exercise_framework/test_api_contract.py \
  tests/student_checker/test_notebook_runtime.py
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/template_repo_cli/test_collector.py \
  tests/template_repo_cli/test_filesystem.py \
  tests/template_repo_cli/test_packager.py \
  tests/template_repo_cli/test_integration.py \
  tests/test_build_autograde_payload.py
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/exercise_framework/test_autograde_parity.py \
  tests/exercise_framework/test_parity_autograde_ex002.py \
  tests/test_integration_autograding.py
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m scripts.template_repo_cli.cli \
  --dry-run \
  --output-dir /tmp/phase4-template-check \
  create \
  --notebooks ex001_sanity ex002_sequence_modify_basics \
  --repo-name phase4-template-check
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q
```

Recommended additions during implementation:

- once the final variant selector name is chosen, add one repository-mode command and one exported-student-mode command that use the exact supported selector entry point and remove obsolete `PYTUTOR_NOTEBOOKS_DIR` examples from this section

### Expected Results

- [ ] Expected passing behaviour:
  - repository tests pass using the agreed discovery model and shared runtime import model
  - pilot exercise-local tests are collected from their canonical location without breaking shared-framework tests
- [ ] Expected failure behaviour:
  - legacy path-based entry points fail clearly where the new contract requires them to fail
  - missing canonical files for migrated exercises fail immediately in both repository execution and packaging
- [ ] Expected packaging/export behaviour:
  - exported templates still contain flattened `notebooks/` and `tests/` exercise files, shared runtime support, and no source metadata files
  - exported notebook self-check commands still work in the packaged workspace
- [ ] Expected docs/workflow outcome:
  - repository docs, agent guidance, and workflows no longer describe `PYTUTOR_NOTEBOOKS_DIR` as the primary long-term execution contract

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old path-based behaviour fails where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model
- [ ] Explicit proof that repository pytest discovery collects the intended pilot exercise-local tests and does not double-collect legacy duplicates

## Risks, Ambiguities, And Blockers

This section is mandatory. Do not leave it out just because nothing is blocked yet.

### Known Risks

- [ ] Risk: keeping shared runtime support in a package literally named `tests` may continue to blur the line between importable support code and collected test code once exercise-local tests move under `exercises/**/tests/`.
- [ ] Risk: moving repository discovery too early could double-collect exercise-specific tests during the transition, especially where both top-level and nested parity surfaces already exist, such as `ex002_sequence_modify_basics`.
- [ ] Risk: template packaging may appear to work even when canonical source files are wrong if collector and packager code are not forced through the same resolver path.
- [ ] Risk: student self-check behaviour could drift away from repository grading behaviour if `tests.student_checker` and `tests.exercise_framework` are migrated on different timelines.

### Open Questions

- [ ] Question: should shared grading/runtime helpers remain importable from top-level `tests`, or should they move into a dedicated support package before exercise-local test discovery changes land?
- [ ] Question: what is the exact public selector for student versus solution execution in the target model: an explicit function argument, a context object, a CLI flag, a narrowly-scoped environment variable, or a combination of these?
- [ ] Question: should repository pytest discovery move directly to collecting `exercises/**/tests/`, or should there be a short transitional period with top-level proxy test modules that import exercise-local tests explicitly?
- [ ] Question: should exported Classroom repositories keep only student notebooks plus tests, or should any additional generated runtime index be allowed as long as it remains metadata-free from an authoring perspective?

### Blockers

- [ ] Blocker: earlier resolver and metadata phases are not yet implemented, so Phase 4 execution code cannot be finalised until the shared resolver/manifests exist.
- [ ] Blocker: the live repo still contains non-canonical duplicate exercise directories at `exercises/ex001_sanity/` and `exercises/ex006_sequence_modify_casting/`, which could confuse any discovery or source-selection implementation.
- [ ] Blocker: the live repo has an `ex007` naming inconsistency between `notebooks/ex007_sequence_debug_casting.ipynb` and `notebooks/solutions/ex007_data_types_debug_casting.ipynb`, which must be resolved or explicitly handled before the variant-selection contract is treated as authoritative.
- [ ] Blocker: the current repo already contains duplicate exercise test surfaces for `ex002_sequence_modify_basics`, which makes it unsafe to change pytest discovery without an explicit duplicate-collection strategy.

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue:
  - record the duplicate non-canonical exercise directories `exercises/ex001_sanity/` and `exercises/ex006_sequence_modify_casting/` as a concrete migration blocker for any discovery or packaging work that assumes one authoritative exercise directory per `exercise_key`
- [ ] New affected surface:
  - record the existing duplicate `ex002_sequence_modify_basics` test surfaces as an execution-model discovery concern, not just a local test oddity
- [ ] Incorrect assumption in current plan:
  - if the final decision is to move shared runtime support out of top-level `tests`, update the current high-level assumption that shared framework code stays there
- [ ] Missing acceptance criterion:
  - add an explicit acceptance criterion that repository discovery must reject duplicate collection during mixed-layout transitions
- [ ] Missing migration stream:
  - if resolving the live `ex007` naming mismatch requires separate clean-up before Phase 4 implementation, add that as a dedicated action-plan prerequisite rather than hiding it inside this checklist

### Follow-Up Action

- [ ] Update [ACTION_PLAN.md](./ACTION_PLAN.md) before marking this checklist complete
- [ ] Cross-link this checklist from the relevant phase in [ACTION_PLAN.md](./ACTION_PLAN.md) if useful
- [ ] Future agents must feed any newly discovered blocker, hidden coupling, stale doc contract, or workflow mismatch back into [ACTION_PLAN.md](./ACTION_PLAN.md) before treating Phase 4 as complete

## Completion Criteria

Do not mark the checklist complete until all of the following are true.

- [ ] In-scope code changes are complete
- [ ] In-scope tests are updated
- [ ] New required test cases are added
- [ ] Verification commands have been run or explicitly deferred with a reason
- [ ] Docs/agents/workflows in scope are updated
- [ ] Known blockers and risks are recorded
- [ ] New action-plan feedback has been folded into [ACTION_PLAN.md](./ACTION_PLAN.md), or confirmed unnecessary
- [ ] The checklist states clearly what remains for later phases

## Checklist Notes

- On 2026-03-12, the current live repo was inspected before writing this checklist.
- The following current-state verification commands passed locally in the existing `.venv`:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/exercise_framework/test_paths.py \
  tests/template_repo_cli/test_collector.py \
  tests/template_repo_cli/test_packager.py \
  tests/student_checker/test_notebook_runtime.py
```

- `uv run` could not be used for local verification in this environment because network access is restricted and `uv` attempted to resolve build requirements remotely; use the existing `.venv` for local verification in this sandbox unless network access is restored.
- This checklist intentionally names concrete current files even where later phases may replace them, so the future implementation agent can update or delete those surfaces deliberately rather than missing them.
