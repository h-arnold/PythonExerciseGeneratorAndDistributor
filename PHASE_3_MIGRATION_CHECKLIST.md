# Phase 3 Migration Checklist

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

- Checklist title: Phase 3 Migration Checklist — Metadata Consolidation And Registry Replacement
- Related action-plan phase or stream: Phase 3 — Metadata Consolidation And Registry Replacement
- Author: Codex Implementer Agent
- Date: 2026-03-12
- Status: `draft`
- Scope summary: Replace duplicated exercise identity, title, construct, type, and ordering registries with metadata-driven loading from `exercise.json` and derived indexes, while keeping checker wiring in code and keeping exported Classroom repositories metadata-free.
- Explicitly out of scope: moving notebooks or tests into canonical exercise folders; replacing `PYTUTOR_NOTEBOOKS_DIR`; changing repository pytest discovery; changing exported template layout; changing the scaffold output in `scripts/new_exercise.py`; broad docs/agent cutover work outside the metadata ownership contract; public API signature breakage such as renaming `notebook_slug` parameters before later execution-model phases are complete.

## Objective

When this checklist is complete, the repository should have a concrete, repo-specific implementation path for moving exercise registry data out of hard-coded lists and into `exercise.json`, with one shared metadata/index layer driving the exercise catalogue.

More specifically:

- hard-coded exercise order, display labels, construct grouping, and exercise-type grouping should no longer need to live in more than one code path
- `tests/exercise_framework` and `tests/student_checker` should consume the same metadata-derived catalogue for exercise identity and display data
- `tests/exercise_expectations` should keep behavioural expectations only, rather than also owning notebook identity data where that can be derived elsewhere
- template selection and packaging should read exercise metadata from the source repository, but exported Classroom repositories should still contain only flattened notebooks, flattened tests, and shared runtime support files
- convention-based fields such as notebook file names, test file names, tag names, ordering rules, and self-check presence should remain derived conventions rather than new metadata fields

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [x] Required decisions from [ACTION_PLAN.md](./ACTION_PLAN.md) are settled.
- [x] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly.

Notes:

- Decisions relied on:
  - `exercise_key` is the only canonical resolver input.
  - The agreed metadata schema is limited to `schema_version`, `exercise_key`, `exercise_id`, `slug`, `title`, `construct`, `exercise_type`, and `parts`.
  - Exported Classroom repositories must remain metadata-free.
  - Convention-based fields must stay out of `exercise.json`.
  - Deliberate breakage is preferred over compatibility layers once replacement contracts exist.
- Open assumptions:
  - The shared metadata/resolver module created in Phase 2 will exist before this phase is implemented; this checklist assumes all new metadata loading goes through that single module.
  - The pilot set has not yet been confirmed. The current live exercise set is almost entirely under `exercises/sequence/**`, but there are duplicate and non-canonical exercise directories that must be resolved before metadata indexing is treated as authoritative.
  - Phase 3 must not invent a second registry layer; if a derived index is needed, it must be produced from `exercise.json` rather than hand-maintained lists.

## Affected Surfaces Inventory

### Files And Paths To Update

- [ ] Source files:
  - Phase 2 shared metadata/index module (path to be the one chosen in Phase 2) — must become the only metadata loader used by the files below.
  - `tests/exercise_framework/api.py` — currently hard-codes `EX001_SLUG` through `EX006_SLUG`, `NOTEBOOK_ORDER`, and notebook display labels.
  - `tests/exercise_framework/__init__.py` — re-exports registry-style values such as `EX002_SLUG` from `tests.exercise_framework.api`.
  - `tests/exercise_framework/expectations.py` — currently imports `EX002_NOTEBOOK_PATH` from `tests.exercise_expectations`, mixing behavioural expectations with notebook identity.
  - `tests/student_checker/api.py` — currently hard-codes `_EX001_SLUG` through `_EX007_SLUG`, `_NOTEBOOK_ORDER`, and student-facing labels.
  - `tests/student_checker/__init__.py` — public API export surface; may need export reshaping once metadata-driven catalogue helpers exist.
  - `tests/student_checker/checks/ex001.py`
  - `tests/student_checker/checks/ex002.py`
  - `tests/student_checker/checks/ex003.py`
  - `tests/student_checker/checks/ex004.py`
  - `tests/student_checker/checks/ex005.py`
  - `tests/student_checker/checks/ex006.py`
  - `tests/student_checker/checks/ex007.py`
    — adjacent consumers of expectation-module notebook constants; these are likely to be touched if identity data is removed from `tests/exercise_expectations`.
  - `tests/exercise_expectations/__init__.py` — currently re-exports notebook-path constants alongside actual behavioural expectations.
  - `tests/exercise_expectations/ex001_sanity.py`
  - `tests/exercise_expectations/ex002_sequence_modify_basics_exercise_expectations.py`
  - `tests/exercise_expectations/ex003_sequence_modify_variables.py`
  - `tests/exercise_expectations/ex004_sequence_debug_syntax.py`
  - `tests/exercise_expectations/ex005_sequence_debug_logic.py`
  - `tests/exercise_expectations/ex006_sequence_modify_casting.py`
  - `tests/exercise_expectations/ex007_sequence_debug_casting.py`
    — each currently embeds an `EX00X_NOTEBOOK_PATH` constant.
  - `scripts/template_repo_cli/core/selector.py` — currently derives construct/type membership from the `exercises/<construct>/<type>/<exercise_key>/` tree and derives notebook availability from top-level `notebooks/*.ipynb`.
  - `scripts/template_repo_cli/core/collector.py` — currently constructs notebook and test paths as `notebooks/<exercise_key>.ipynb` and `tests/test_<exercise_key>.py` instead of using shared metadata-derived resolution.
  - `scripts/template_repo_cli/core/packager.py` — must keep packaging metadata-free even once source selection becomes metadata-driven.
  - `scripts/template_repo_cli/cli.py` — command entry points use selector/collector behaviour and will need to stay aligned with the new metadata-driven source model.
  - `scripts/template_repo_cli/utils/validation.py` — `VALID_TYPES` should remain the enum of allowed values, but any per-exercise grouping logic should move out of path assumptions.
  - `scripts/verify_exercise_quality.py` — not a Phase 3 implementation target, but must be recorded as an adjacent surface because it still reflects current construct/type path assumptions.
- [ ] Test files:
  - `tests/exercise_framework/test_api_contract.py` — currently asserts fixed notebook count and uses `EX002_SLUG`.
  - `tests/exercise_framework/test_expectations.py` — currently asserts `FRAMEWORK_EX002_NOTEBOOK_PATH == EX002_NOTEBOOK_PATH`.
  - `tests/exercise_framework/test_runtime.py` — adjacent, because expectation-module path constants are part of the current runtime contract.
  - `tests/exercise_framework/test_paths.py` — adjacent, because path resolution tests currently work with legacy notebook paths.
  - `tests/student_checker/test_checks_aliasing.py` — likely impacted if check-list exports or registry bindings change.
  - `tests/student_checker/test_reporting.py` — likely impacted if ordering and display labels become metadata-derived.
  - `tests/template_repo_cli/test_selector.py` — currently assumes construct/type discovery comes from directory shape and notebook discovery comes from top-level notebook files.
  - `tests/template_repo_cli/test_collector.py` — currently assumes collector returns direct top-level notebook and test paths.
  - `tests/template_repo_cli/test_packager.py` — must keep asserting flattened export output and no solution notebook leakage; add metadata-free export assertions here.
  - `tests/template_repo_cli/test_integration.py` — CLI integration coverage for list/validate/create/update flows will need metadata-driven expectations.
  - `tests/template_repo_cli/test_validation.py` — validate that allowed `exercise_type` values still match the metadata schema.
  - `tests/test_exercise_type_docs.py` — adjacent surface because the allowed exercise types and their documentation remain a contract that metadata must honour.
  - Top-level exercise tests: `tests/test_ex001_sanity.py`, `tests/test_ex002_sequence_modify_basics.py`, `tests/test_ex003_sequence_modify_variables.py`, `tests/test_ex004_sequence_debug_syntax.py`, `tests/test_ex005_sequence_debug_logic.py`, `tests/test_ex006_sequence_modify_casting.py`, `tests/test_ex007_sequence_debug_casting.py`, and `tests/test_ex007_construct_checks.py` — not the primary Phase 3 targets, but they should be revisited if notebook identity constants move out of expectation modules.
- [ ] Docs:
  - `README.md` — currently describes the legacy split model and should later describe metadata as the source of truth for exercise identity.
  - `docs/project-structure.md` — will need to distinguish metadata-driven source-of-truth from later layout migration work.
  - `docs/testing-framework.md` — currently documents top-level notebook/test assumptions and the `PYTUTOR_NOTEBOOKS_DIR` solution flow.
  - `docs/exercise-testing.md` — currently teaches `NOTEBOOK_PATH` constants in expectation/test modules.
  - `docs/CLI_README.md` — must continue to document flattened exports and should later document metadata-driven source selection.
  - `docs/development.md` — currently points contributors at top-level notebook/test files and `PYTUTOR_NOTEBOOKS_DIR` workflows.
- [ ] Workflows:
  - `.github/workflows/tests.yml` — no immediate code change required for Phase 3, but metadata-driven source-of-truth work must not leak into the exported contract or break current solution-mode CI assumptions prematurely.
  - `.github/workflows/tests-solutions.yml` — same constraint as above.
- [ ] Agent instructions:
  - `AGENTS.md` — later documentation update must explain that exercise identity lives in metadata, not duplicated registries.
  - `.github/agents/exercise_generation.md.agent.md`
  - `.github/agents/exercise_verifier.md.agent.md`
  - `.github/agents/implementer.md.agent.md`
  - `.github/agents/tidy_code_review.md.agent.md`
    — later updates must point future agents at the metadata-driven source-of-truth model once implemented.
- [ ] Template/export files:
  - `template_repo_files/.github/workflows/classroom.yml` — export workflow must continue to operate without `exercise.json`.
  - `template_repo_files/README.md.template` — exercise lists may later be generated from metadata-derived selection, but the exported README must not imply that metadata files are present in the package.
  - `template_repo_files/pyproject.toml`
  - `template_repo_files/pytest.ini`
    — no direct Phase 3 changes expected, but keep them in the inventory because packaging tests cover the metadata-free export contract.
- [ ] Exercise directories:
  - `exercises/sequence/modify/ex002_sequence_modify_basics/` — current teacher-material home; will need canonical metadata.
  - `exercises/sequence/modify/ex003_sequence_modify_variables/` — current teacher-material home; will need canonical metadata.
  - `exercises/sequence/modify/ex006_sequence_modify_casting/` — current teacher-material home; duplicates a root-level directory of the same exercise key.
  - `exercises/sequence/debug/ex004_sequence_debug_syntax/` — current teacher-material home; will need canonical metadata.
  - `exercises/sequence/debug/ex005_sequence_debug_logic/` — current teacher-material home; will need canonical metadata.
  - `exercises/sequence/debug/ex007_sequence_debug_casting/` — current teacher-material home; note current solution notebook naming drift.
  - `exercises/ex001_sanity/` — non-canonical root-level exercise directory; must not be silently indexed as if it already matched the target layout.
  - `exercises/ex006_sequence_modify_casting/` — duplicate root-level directory; must be resolved before metadata indexing becomes authoritative.
  - `exercises/sequence/OrderOfTeaching.md` — teaching-order document that will eventually need to align with metadata-derived display and ordering.
  - `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` — placeholder subtree that should not be mistaken for a construct or exercise source when scanning for metadata.

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
  - Phase 2 metadata/index module — must expose the single authoritative metadata loader and derived exercise catalogue.
  - `tests.exercise_framework.api` — should consume metadata-derived exercise identity and labels.
  - `tests.student_checker.api` — should consume the same metadata-derived exercise identity and labels as `tests.exercise_framework.api`.
  - `tests.exercise_expectations` — should own behavioural expectations only.
  - `scripts.template_repo_cli.core.selector` — should use metadata-derived construct/type grouping instead of directory shape.
  - `scripts.template_repo_cli.core.collector` — should collect source files using shared metadata/resolution instead of handcrafted path assembly.
  - `scripts.template_repo_cli.core.packager` — should continue to package flattened, metadata-free exports.
- [ ] Public functions or methods:
  - `tests.exercise_framework.api.run_all_checks` — currently uses a hard-coded order list; should iterate in metadata-derived order.
  - `tests.exercise_framework.api.run_notebook_check` — currently validates against a hand-built dict keyed by slug-like strings; should validate against the metadata-driven catalogue.
  - `tests.exercise_framework.api._get_check_definitions` — currently duplicates display labels that belong in metadata-derived display data.
  - `tests.student_checker.api.check_exercises` — currently renders checks in `_NOTEBOOK_ORDER`; should use metadata-derived order.
  - `tests.student_checker.api.check_notebook` — currently validates against a hand-built dict; should validate against the metadata-driven catalogue.
  - `tests.student_checker.api._get_checks` — currently duplicates display labels; keep runner wiring here or a sibling code registry, but derive display text from metadata.
  - `scripts.template_repo_cli.core.selector.get_all_notebooks` — currently scans `notebooks/*.ipynb`; should become a metadata-driven list of available exercise keys in the source repository.
  - `scripts.template_repo_cli.core.selector.select_by_construct` — currently walks `exercises/<construct>/<type>/`; should filter metadata entries by `construct`.
  - `scripts.template_repo_cli.core.selector.select_by_type` — currently walks type directories; should filter metadata entries by `exercise_type`.
  - `scripts.template_repo_cli.core.selector.select_by_construct_and_type` — should intersect metadata fields rather than path segments.
  - `scripts.template_repo_cli.core.collector.collect_files` — should resolve source files from shared metadata/resolution instead of assuming top-level source paths.
  - `scripts.template_repo_cli.core.packager.copy_exercise_files` — should still write `notebooks/<exercise_key>.ipynb` and `tests/test_<exercise_key>.py` to exported workspaces, even if source collection becomes metadata-driven.
  - `scripts.template_repo_cli.core.packager.generate_readme` — should continue to list exercise keys/titles from the selected set without copying metadata into the package.
- [ ] CLI commands or flags:
  - `template_repo_cli list` — selected exercise listing should eventually come from metadata-derived inventory.
  - `template_repo_cli validate` — construct/type validation should use metadata-derived exercise membership.
  - `template_repo_cli create` — selection remains metadata-driven in the source repo, but output stays flattened and metadata-free.
  - `template_repo_cli update-repo` — same contract as `create`.
- [ ] Environment variables:
  - `PYTUTOR_NOTEBOOKS_DIR` — still part of the current execution model, but Phase 3 must not rely on it as a metadata compatibility mechanism or registry substitute.
- [ ] Workflow jobs or steps:
  - `tests.yml:pytest` — repository CI should stay green once metadata-driven registries are introduced, without requiring exported metadata files.
  - `tests-solutions.yml:pytest_solutions` — solution-mode CI should continue to pass with metadata-driven catalogue changes.
  - `template_repo_files/.github/workflows/classroom.yml` — packaged exports must still run without `exercise.json`.
- [ ] Packaging/export contracts:
  - Authoring repository contract — source selection may become metadata-driven.
  - Exported Classroom contract — packaged repositories still contain `notebooks/exNNN_slug.ipynb`, `tests/test_exNNN_slug.py`, shared runtime support, and no `exercise.json` or `exercises/` tree.
- [ ] Notebook self-check contracts:
  - `tests.student_checker.check_notebook('<exercise_key>')` — keep the self-check entry point exercise-key-based; do not force notebook cells to import metadata files directly.
  - Student self-check labels should come from metadata-derived display data once Phase 3 lands, but the self-check mechanism itself remains code-driven.

### Current Assumptions Being Removed

- [ ] Exercise order and display labels are hard-coded separately in `tests/exercise_framework/api.py` and `tests/student_checker/api.py`.
- [ ] Exercise type membership is inferred from the current `exercises/<construct>/<type>/<exercise_key>/` directory shape rather than `exercise.json`.
- [ ] `tests/exercise_expectations` must also own notebook identity data such as `EX00X_NOTEBOOK_PATH`.
- [ ] Top-level `notebooks/*.ipynb` is the authoritative catalogue of available exercises for template selection.
- [ ] A duplicated or stale exercise directory can sit in the repo without being surfaced as a metadata/indexing problem.

## Implementation Tasks

### Code Changes

- [ ] Add:
  - a derived exercise catalogue built from `exercise.json` via the shared Phase 2 metadata module
  - fail-fast validation for duplicate `exercise_key`, duplicate `exercise_id`, missing required metadata fields, and mismatches between metadata and discovered directory names
  - a small shared representation for metadata-derived display information so `tests.exercise_framework` and `tests.student_checker` do not each reformat titles and ordering independently
- [ ] Update:
  - `tests/exercise_framework/api.py` to replace `EX001_SLUG`…`EX006_SLUG`, `NOTEBOOK_ORDER`, and hand-written labels with metadata-derived display data
  - `tests/student_checker/api.py` to replace `_EX001_SLUG`…`_EX007_SLUG`, `_NOTEBOOK_ORDER`, and hand-written labels with the same metadata-derived catalogue
  - `tests/exercise_framework/__init__.py` so exported registry-style constants do not remain as another hand-maintained metadata source
  - `tests/exercise_expectations/__init__.py` and the per-exercise expectation modules so notebook path constants are removed or clearly demoted out of the metadata ownership path
  - `scripts/template_repo_cli/core/selector.py` so construct/type queries use metadata fields rather than path shape
  - `scripts/template_repo_cli/core/collector.py` so it stops constructing source paths from string concatenation alone
  - `scripts/template_repo_cli/core/packager.py` only as needed to keep the export contract stable while using metadata-driven source selection
- [ ] Remove:
  - duplicated exercise title registries in API modules
  - duplicated exercise ordering lists where metadata can derive order from `exercise_id`
  - duplicated exercise-type grouping logic that currently lives in path traversal only
  - notebook identity constants from `tests/exercise_expectations` if those values can be derived through the shared resolver/index path
- [ ] Rename or relocate:
  - any internal helpers whose names imply slug/path ownership rather than `exercise_key` ownership, but defer public API renames until later public-interface phases
  - any temporary registry helpers added during Phase 2 if they duplicate the new metadata-derived catalogue
- [ ] Fail-fast behaviour to add:
  - refuse to build the exercise catalogue when duplicate directories claim the same `exercise_key`
  - refuse to index an exercise when `exercise.json` disagrees with its directory name or expected construct/type assignment
  - refuse to package or select exercises from unresolved duplicate sources
  - fail clearly if a caller requests an `exercise_key` that is missing from the metadata-derived catalogue

### Data And Metadata Changes

- [ ] `exercise.json` changes:
  - add `exercise.json` to each exercise that participates in the Phase 3 pilot, using only the agreed minimal schema
  - populate `title`, `exercise_id`, `construct`, `exercise_type`, and `parts` from the real exercise data rather than from duplicated code constants
  - do not add notebook paths, test paths, tag names, self-check flags, ordering lists, or checker wiring to `exercise.json`
- [ ] Derived-data/index changes:
  - add a derived exercise index sorted by `exercise_id`
  - add derived display labels from metadata, for example `ex006 Casting and Type Conversion`
  - add derived construct/type groupings from metadata for template selection and future docs generation
  - explicitly ignore non-exercise directories such as `exercises/PythonExerciseGeneratorAndDistributor/`
- [ ] Registry replacement work:
  - replace hard-coded order and title lists in `tests/exercise_framework/api.py` and `tests/student_checker/api.py`
  - replace path-derived construct/type grouping in `scripts/template_repo_cli/core/selector.py`
  - keep checker wiring out of metadata; it may remain a code-owned mapping keyed by `exercise_key`
  - decide whether `tests/exercise_expectations` keeps per-exercise modules only for behavioural assertions or whether some identity helpers move entirely into the shared metadata/index layer
- [ ] Migration manifest updates:
  - use the Phase 2 migration manifest, if it exists, to exclude unresolved legacy/duplicate exercises from the metadata pilot rather than silently indexing them
  - if the current manifest model cannot express duplicate or ambiguous homes, record that as a blocker back into `ACTION_PLAN.md`

### Test Changes

- [ ] Update existing unit tests:
  - `tests/exercise_framework/test_api_contract.py`
  - `tests/exercise_framework/test_expectations.py`
  - `tests/student_checker/test_checks_aliasing.py`
  - `tests/student_checker/test_reporting.py`
  - `tests/template_repo_cli/test_selector.py`
  - `tests/template_repo_cli/test_collector.py`
  - `tests/template_repo_cli/test_validation.py`
- [ ] Update integration tests:
  - `tests/template_repo_cli/test_integration.py`
  - `tests/test_exercise_type_docs.py` if metadata enum/type guidance is cross-checked there
  - top-level exercise tests only where expectation-module identity constants are removed from their support path
- [ ] Update packaging/template tests:
  - `tests/template_repo_cli/test_packager.py` — add explicit assertions that packaged workspaces exclude `exercise.json` and the `exercises/` authoring tree
- [ ] Update workflow-related tests:
  - any packaging smoke tests that rely on the exported repository contract remaining metadata-free
  - any solution-mode smoke tests that rely on registry-derived exercise ordering or labels
- [ ] Remove obsolete tests:
  - tests whose only job is to prove a hand-maintained slug list or notebook-path constant remains exported as-is
  - tests that assert construct/type membership by current folder shape rather than metadata

### New Test Cases Required

- [ ] Positive case:
  - building the metadata-derived exercise catalogue returns the pilot exercise set in `exercise_id` order and exposes the correct `title`, `construct`, `exercise_type`, and `parts` for each `exercise_key`
- [ ] Failure case:
  - duplicate `exercise_key` metadata entries fail with a clear error that names both conflicting directories, including the current `ex006_sequence_modify_casting` duplicate-home situation if it remains unresolved
  - a directory whose `exercise.json` disagrees with its own folder name or construct/type assignment fails clearly
- [ ] Regression case:
  - `tests.exercise_framework.api.run_all_checks()` and `tests.student_checker.api.check_exercises()` consume the same metadata-derived order and labels instead of diverging hand-written lists
  - requesting an unknown exercise from `run_notebook_check()` or `check_notebook()` reports the metadata-derived available keys
- [ ] Export/package case:
  - `template_repo_cli create` and `template_repo_cli update-repo` still produce `notebooks/<exercise_key>.ipynb` and `tests/test_<exercise_key>.py`
  - packaged workspaces do not contain any `exercise.json`
  - packaged workspaces do not contain the source `exercises/` directory tree
- [ ] Student-mode case:
  - notebook self-check output for a migrated exercise uses the metadata-derived display label while still running the existing code-owned checker wiring
  - student checker selection by `exercise_key` succeeds for metadata-backed exercises and fails clearly for unknown keys
- [ ] Solution-mode case:
  - solution-mode checks still pass when labels/order come from metadata rather than duplicated constants
  - `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` continues to work for the current execution model, but metadata loading must not depend on that environment variable

Use explicit statements such as:

- metadata index returns `ex004_sequence_debug_syntax`, `ex005_sequence_debug_logic`, and `ex006_sequence_modify_casting` with titles from `exercise.json`
- template selection by `construct=sequence` and `exercise_type=modify` is driven by metadata, not by directory depth under `exercises/sequence/modify/`
- duplicate metadata for `ex006_sequence_modify_casting` fails clearly until the duplicate home is resolved
- packaged template excludes `exercise.json` and the `exercises/` source tree

### Docs, Agents, And Workflow Updates

- [ ] Contributor docs:
  - queue updates for `README.md`, `docs/project-structure.md`, and `docs/development.md` so they describe metadata as the source of truth for exercise identity once implementation is complete
- [ ] Teaching docs:
  - queue updates for `docs/testing-framework.md`, `docs/exercise-testing.md`, and `exercises/sequence/OrderOfTeaching.md` where titles/order are currently maintained separately from metadata
- [ ] Agent docs:
  - queue updates for `AGENTS.md` and `.github/agents/*.md.agent.md` to tell future agents not to add new hand-maintained exercise registries
- [ ] Repository workflows:
  - confirm `.github/workflows/tests.yml` and `.github/workflows/tests-solutions.yml` need no Phase 3 logic change beyond remaining compatible with metadata-driven catalogue loading
- [ ] Template workflows:
  - confirm `template_repo_files/.github/workflows/classroom.yml` remains valid for metadata-free exports
- [ ] CLI examples:
  - queue updates for `docs/CLI_README.md` so examples describe metadata-driven source selection while preserving flattened export output

## Verification Plan

### Commands To Run

- [ ] Command:

```bash
source .venv/bin/activate
uv run pytest -q \
  tests/exercise_framework/test_api_contract.py \
  tests/exercise_framework/test_expectations.py \
  tests/student_checker/test_checks_aliasing.py \
  tests/student_checker/test_reporting.py \
  tests/template_repo_cli/test_selector.py \
  tests/template_repo_cli/test_collector.py \
  tests/template_repo_cli/test_packager.py \
  tests/template_repo_cli/test_integration.py \
  tests/template_repo_cli/test_validation.py
```

- [ ] Command:

```bash
source .venv/bin/activate
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions \
uv run pytest -q \
  tests/exercise_framework/test_api_contract.py \
  tests/student_checker/test_reporting.py
```

- [ ] Command:

```bash
source .venv/bin/activate
uv run ruff check .
```

- [ ] Command:

```bash
source .venv/bin/activate
uv run template_repo_cli list --format json
uv run template_repo_cli validate --construct sequence --type modify
```

Only include broader test runs after the targeted metadata and template-selection surfaces are stable.

### Expected Results

- [ ] Expected passing behaviour:
  - framework and student-checker tests pass while consuming one metadata-derived catalogue for ordering and labels
  - selector and collector tests pass while reading construct/type membership from metadata rather than folder depth
- [ ] Expected failure behaviour:
  - duplicate or inconsistent metadata fails clearly and names the offending exercise directories
  - unknown exercise-key lookups fail clearly without silently falling back to path guesses
- [ ] Expected packaging/export behaviour:
  - packaged templates remain flattened and metadata-free
  - packaged smoke tests continue to pass without `exercise.json`
- [ ] Expected docs/workflow outcome:
  - in-scope docs queued for update no longer describe hand-maintained exercise registries as authoritative once the implementation lands

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old path-based behaviour fails where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model

## Risks, Ambiguities, And Blockers

### Known Risks

- [ ] No `exercise.json` files currently exist anywhere in the repository, so Phase 3 cannot be implemented without either creating pilot metadata files first or explicitly staging that work under the Phase 2/3 boundary.
- [ ] The current repository contains duplicate or stale exercise homes, notably `exercises/ex006_sequence_modify_casting/` alongside `exercises/sequence/modify/ex006_sequence_modify_casting/`; a metadata scan could otherwise index both.
- [ ] `tests/exercise_framework/api.py` currently covers ex001–ex006, while `tests/student_checker/api.py` covers ex001–ex007; replacing duplicated registries may surface additional inconsistencies in what the repository considers the active exercise set.
- [ ] `notebooks/solutions/ex007_data_types_debug_casting.ipynb` does not match the student notebook and exercise directory key `ex007_sequence_debug_casting`, so any metadata-derived identity check will expose this mismatch immediately.
- [ ] The placeholder tree `exercises/PythonExerciseGeneratorAndDistributor/` may confuse naive metadata or exercise-directory scanners.

### Open Questions

- [ ] Should Phase 3 create metadata in the current legacy exercise directories first, or must it wait for canonical directory migration under `exercises/<construct>/<exercise_key>/`?
- [x] Decision: framework and student-checker display labels should be derived by a tiny shared formatter that consumes metadata objects rather than stored separately.
- [x] Decision: `tests/exercise_expectations` should become purely behavioural data plus types, not an identity/path registry.
- [x] Decision: template selection should allow a mixed mode controlled by the Phase 2 migration manifest rather than requiring metadata-valid-only exercises.

### Blockers

- [ ] A sequencing gap exists between the planned canonical `exercise.json` location and the current on-disk exercise layout; this must be resolved or explicitly documented before implementation starts.
- [ ] The ex006 duplicate-home situation must be resolved or represented in the migration manifest before metadata indexing can be trusted.
- [ ] The ex007 solution notebook naming mismatch must be resolved or represented in the migration manifest before metadata-derived identity checks can be enabled safely.

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue:
  - Phase 3 depends on a decision about where `exercise.json` lives before Phase 9 completes the canonical directory migration. The current plan names only the final canonical metadata path, but the repository still uses legacy `exercises/<construct>/<type>/<exercise_key>/` directories for most exercises.
- [ ] New affected surface:
  - `scripts/template_repo_cli/core/collector.py` and `scripts/template_repo_cli/core/packager.py` are directly affected by metadata registry replacement, not just later packaging phases, because the source-selection model and metadata-free export contract must stay aligned.
- [ ] Incorrect assumption in current plan:
  - the repository does not currently have one consistent active exercise registry: `tests.exercise_framework.api` and `tests.student_checker.api` disagree about whether ex007 is in the active set.
- [ ] Missing acceptance criterion:
  - Phase 3 should explicitly require duplicate-home detection and clear failure messaging for conflicting metadata entries.
- [ ] Missing migration stream:
  - none identified yet beyond the need to clarify the metadata-file location during mixed-layout migration.

### Follow-Up Action

- [ ] Update [ACTION_PLAN.md](./ACTION_PLAN.md) before marking this checklist complete.
- [ ] Cross-link this checklist from the relevant phase in [ACTION_PLAN.md](./ACTION_PLAN.md) if useful.

## Completion Criteria

Do not mark the checklist complete until all of the following are true.

- [ ] In-scope code changes are complete.
- [ ] In-scope tests are updated.
- [ ] New required test cases are added.
- [ ] Verification commands have been run or explicitly deferred with a reason.
- [ ] Docs/agents/workflows in scope are updated.
- [ ] Known blockers and risks are recorded.
- [ ] New action-plan feedback has been folded into [ACTION_PLAN.md](./ACTION_PLAN.md), or confirmed unnecessary.
- [ ] The checklist states clearly what remains for later phases.

## Checklist Notes

- Current exercise inventory relevant to this phase:
  - top-level student notebooks: `notebooks/ex001_sanity.ipynb`, `notebooks/ex002_sequence_modify_basics.ipynb`, `notebooks/ex003_sequence_modify_variables.ipynb`, `notebooks/ex004_sequence_debug_syntax.ipynb`, `notebooks/ex005_sequence_debug_logic.ipynb`, `notebooks/ex006_sequence_modify_casting.ipynb`, `notebooks/ex007_sequence_debug_casting.ipynb`
  - top-level solution notebooks: `notebooks/solutions/ex001_sanity.ipynb`, `notebooks/solutions/ex002_sequence_modify_basics.ipynb`, `notebooks/solutions/ex003_sequence_modify_variables.ipynb`, `notebooks/solutions/ex004_sequence_debug_syntax.ipynb`, `notebooks/solutions/ex005_sequence_debug_logic.ipynb`, `notebooks/solutions/ex006_sequence_modify_casting.ipynb`, `notebooks/solutions/ex007_data_types_debug_casting.ipynb`
  - top-level exercise tests: `tests/test_ex001_sanity.py`, `tests/test_ex002_sequence_modify_basics.py`, `tests/test_ex003_sequence_modify_variables.py`, `tests/test_ex004_sequence_debug_syntax.py`, `tests/test_ex005_sequence_debug_logic.py`, `tests/test_ex006_sequence_modify_casting.py`, `tests/test_ex007_sequence_debug_casting.py`, `tests/test_ex007_construct_checks.py`
- Keep the later-phase boundary explicit:
  - Phase 3 owns metadata and registry replacement.
  - Phase 4 owns the execution model and source-to-export contract.
  - Phase 5 owns scaffolding and verification changes.
  - Phase 7 owns pytest discovery and packaging cutover.
  - Phase 9 owns exercise data migration into canonical exercise-local notebook/test locations.
- Future implementation agents must feed any newly discovered blocker, sequencing issue, or hidden coupling back into [ACTION_PLAN.md](./ACTION_PLAN.md) before treating the migration work as complete.
