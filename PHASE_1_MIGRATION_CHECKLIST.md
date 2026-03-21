# Phase 1 Migration Checklist — Repository Inventory And Canonical Model

This checklist is the repo-specific execution plan for **Phase 1: Repository Inventory And Canonical Model** from `ACTION_PLAN.md`.

It is intentionally concrete. It names the current files, paths, modules, functions, docs, workflows, and test surfaces that encode exercise identity today so that a later implementation agent can complete Phase 1 without guessing.

## Required Migration Rules

These rules come directly from `ACTION_PLAN.md` and must be treated as non-negotiable guardrails while executing Phase 1:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless `ACTION_PLAN.md` is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into `ACTION_PLAN.md`.

## Checklist Header

- Checklist title: `Phase 1 Migration Checklist — Repository Inventory And Canonical Model`
- Related action-plan phase or stream: `Phase 1: Repository Inventory And Canonical Model`
- Author: `Codex Implementer Agent`
- Date: `2026-03-12`
- Status: `completed`
- Execution artefact: `PHASE_1_REPOSITORY_INVENTORY.md`
- Scope summary: Produce a verified inventory of every current exercise identity, location, and naming anomaly; catalogue every path-based assumption in code/docs/workflows; and write down the canonical Phase 1 model that later resolver and migration phases will rely on.
- Explicitly out of scope: Implementing resolver changes, adding `exercise.json`, moving directories, renaming notebooks, editing any `.ipynb` file, changing export packaging, or changing public APIs.

## Objective

When this checklist has been executed successfully, the repository should have a written, reviewable inventory that makes the following true:

- Every current `exercise_key` is mapped to its existing teacher docs directory or directories, student notebook, solution notebook, and test surface.
- Every naming anomaly, duplicate directory, stale path, construct mismatch, and slug mismatch is recorded explicitly rather than left to implicit filesystem discovery.
- Every code path that currently treats exercise identity as a filename, a slug, a directory name, or a full path is known and listed.
- The canonical authoring model is agreed in writing: `exercise_key` is the only canonical resolver input, the canonical exercise home is `exercises/<construct>/<exercise_key>/`, notebook filenames will later become `student.ipynb` and `solution.ipynb`, exercise type moves into `exercise.json`, and top-level `tests/` remains shared infrastructure only.
- A pilot recommendation is backed by the inventory rather than assumption, with `ex004_sequence_debug_syntax` confirmed as the Phase 2 live pilot because it has tidy teacher docs, matched notebook/test names, and no duplicate artefacts needing resolution.

## Preconditions

- [x] Dependencies from earlier phases are complete or explicitly waived. Phase 1 is the starting phase.
- [x] Required decisions from `ACTION_PLAN.md` are settled enough to inventory against: canonical input is `exercise_key`, compatibility fallbacks are forbidden, export remains metadata-free, and `exercise.json` must stay small.
- [x] Scope boundaries are clear enough to avoid accidental spill into resolver implementation, metadata introduction, or filesystem migration.
- [x] Any pilot construct or target exercise(s) for this checklist are outputs of this phase rather than preconditions.

Notes:

- Decisions relied on:
  - Authoring repository contract and exported Classroom contract are separate first-class designs.
  - Public API breakage is deferred until later phases.
  - The construct stays in the canonical path; type leaves the path and moves into metadata later.
- Open assumptions:
  - `sequence` is the only currently populated construct tree under `exercises/<construct>/<type>/`, but that does **not** automatically make the whole construct the safest pilot.
  - Based on the current repo scan, the least ambiguous candidate exercises are `ex004_sequence_debug_syntax` and `ex005_sequence_debug_logic`.
  - `ex001_sanity` is obsolete, reserved for removal, and must be deleted before later phases begin; it is not a migration candidate.
  - `ex006_sequence_modify_casting` and `ex007_sequence_debug_casting` currently look unsuitable as first migration examples because they contain path or naming anomalies.
  - This phase must end by naming a pilot recommendation and recording rejected alternatives with reasons; do not leave pilot choice as an open assumption.

## Affected Surfaces Inventory

### Current Exercise Identity Inventory

The following matrix is based on the current codebase state in `/workspaces/PythonExerciseGeneratorAndDistributor`.

| Exercise key | Teacher docs path(s) today | Student notebook | Solution notebook | Primary test surface(s) today | Inventory notes |
| --- | --- | --- | --- | --- | --- |
| `ex001_sanity` | `exercises/ex001_sanity/` | `notebooks/ex001_sanity.ipynb` | `notebooks/solutions/ex001_sanity.ipynb` | `tests/test_ex001_sanity.py` | Obsolete sanity-check exercise. Decision: delete this directory entirely before later phases, as it is reserved for removal rather than canonical migration. |
| `ex002_sequence_modify_basics` | `exercises/sequence/modify/ex002_sequence_modify_basics/` | `notebooks/ex002_sequence_modify_basics.ipynb` | `notebooks/solutions/ex002_sequence_modify_basics.ipynb` | `tests/test_ex002_sequence_modify_basics.py`; `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` | Duplicate exercise-specific test locations; the live repo currently exposes an unresolved split contract. `scripts/template_repo_cli/core/collector.py` resolves the top-level test path, `tests/template_repo_cli/conftest.py` points at the nested path, and the ex002 parity suites deliberately execute both files. Later migration work may still choose the nested exercise-local path and retire the top-level file, but that is not the verified current repo contract. |
| `ex003_sequence_modify_variables` | `exercises/sequence/modify/ex003_sequence_modify_variables/` | `notebooks/ex003_sequence_modify_variables.ipynb` | `notebooks/solutions/ex003_sequence_modify_variables.ipynb` | `tests/test_ex003_sequence_modify_variables.py` | Teacher docs include an extra `solutions.md`; otherwise this is a relatively clean structured example. |
| `ex004_sequence_debug_syntax` | `exercises/sequence/debug/ex004_sequence_debug_syntax/` | `notebooks/ex004_sequence_debug_syntax.ipynb` | `notebooks/solutions/ex004_sequence_debug_syntax.ipynb` | `tests/test_ex004_sequence_debug_syntax.py` | Clean structured example with `README.md`, `OVERVIEW.md`, and matching notebook/test names. Strong pilot candidate. |
| `ex005_sequence_debug_logic` | `exercises/sequence/debug/ex005_sequence_debug_logic/` | `notebooks/ex005_sequence_debug_logic.ipynb` | `notebooks/solutions/ex005_sequence_debug_logic.ipynb` | `tests/test_ex005_sequence_debug_logic.py` | Clean structured example with matching teacher/notebook/test naming. Strong pilot candidate. |
| `ex006_sequence_modify_casting` | `exercises/ex006_sequence_modify_casting/`; `exercises/sequence/modify/ex006_sequence_modify_casting/` | `notebooks/ex006_sequence_modify_casting.ipynb` | `notebooks/solutions/ex006_sequence_modify_casting.ipynb` | `tests/test_ex006_sequence_modify_casting.py` | Duplicate teacher directories for the same exercise key. The authoritative current legacy home is `exercises/sequence/modify/ex006_sequence_modify_casting/`, and the later canonical target is `exercises/sequence/ex006_sequence_modify_casting/`; the root-level duplicate should be removed during migration. |
| `ex007_sequence_debug_casting` | `exercises/sequence/debug/ex007_sequence_debug_casting/` | `notebooks/ex007_sequence_debug_casting.ipynb` | **No matching file**; current file is `notebooks/solutions/ex007_data_types_debug_casting.ipynb` | `tests/test_ex007_sequence_debug_casting.py`; `tests/test_ex007_construct_checks.py` | Decision: canonical key is `ex007_sequence_debug_casting`. The solution notebook, self-check references, expectation imports, and test target names must all be normalised to that key, with `data_types` references removed entirely. |

### Repository-Wide Anomalies Already Confirmed

- [x] `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` exists as a repository-level placeholder and explicitly states that it exists to satisfy verifier checks. This is not a canonical construct folder.
- [x] `ex001_sanity` still lives directly under `exercises/`, but it is now classified as obsolete and must be removed before canonical migration is considered.
- [x] The root-level `exercises/ex006_sequence_modify_casting/` directory is a non-canonical duplicate and should be removed; `exercises/sequence/modify/ex006_sequence_modify_casting/` is the authoritative home.
- [x] `ex007_sequence_debug_casting` has no matching solution notebook path yet; the existing `notebooks/solutions/ex007_data_types_debug_casting.ipynb` should be renamed and normalised to the canonical `sequence` key family.
- [x] `tests/test_ex007_sequence_debug_casting.py`, `tests/test_ex007_construct_checks.py`, notebook self-check cells, and expectation imports must all be normalised to `ex007_sequence_debug_casting`, with all `data_types` references removed.
- [x] `tests/exercise_expectations/__init__.py` exports expectations up to `EX006_*` only; there is no `EX007_*` export surface there.
- [x] `tests/exercise_framework/api.py` still stops at `EX006_*`, so the framework API and the student checker do not share a clean ex007 registry surface.
- [x] `tests/test_ex007_sequence_debug_casting.py` imports `tests.exercise_expectations.ex007_data_types_debug_casting`, which confirms a live ex007 alias mismatch beyond notebook filenames.
- [x] `tests/template_repo_cli/conftest.py` points `ex002_sequence_modify_basics` at the nested test path, `scripts/template_repo_cli/core/collector.py` resolves the top-level test path, and `tests/exercise_framework/test_autograde_parity.py` plus `tests/exercise_framework/test_parity_autograde_ex002.py` deliberately execute both files.
- [x] `ex002_sequence_modify_basics` therefore has an unresolved current test-surface split; Phase 1 should not present either file as the verified current canonical surface. Later migration work may still choose the nested exercise-local path and retire the top-level file once discovery is redesigned.
- [x] Only the `sequence` construct currently appears as a real construct subtree under `exercises/`; the repo contains no structured `selection`, `iteration`, or other construct directories yet.
- [x] Only `debug` and `modify` exercise types are present in the current filesystem; `make` is documented but has no current exercise directories.

### Files And Paths To Update

#### Planning Artefacts Phase 1 Should Produce Or Maintain

- [x] `PHASE_1_MIGRATION_CHECKLIST.md` — keep this checklist aligned with any scope clarifications discovered during execution.
- [x] A dedicated Phase 1 inventory artefact (recommended: `PHASE_1_REPOSITORY_INVENTORY.md` or an agreed equivalent) — record the completed exercise matrix, anomaly register, and pilot recommendation in a stable document future phases can cite.
- [x] `ACTION_PLAN.md` — update only when new blockers, hidden coupling, or sequencing issues are discovered during Phase 1 execution.

#### Source Files To Audit During Phase 1

- [x] `scripts/new_exercise.py` — scaffolds root-level `exercises/<exercise_key>/`, root student notebook path, root solution notebook path, and top-level `tests/test_<exercise_key>.py`.
- [x] `scripts/verify_exercise_quality.py` — recursively locates `exercises/**/<slug>/`, prefers deeper construct/type paths, and infers construct/type from parent directories.
- [x] `scripts/build_autograde_payload.py` — constrains `legacy notebook-root override env var` to `notebooks` or `notebooks/solutions` and therefore encodes the current notebook-root contract.
- [x] `scripts/template_repo_cli/cli.py` — public CLI surface for `create`, `update-repo`, `list`, and `validate`; selection inputs currently revolve around constructs, types, and notebook IDs.
- [x] `scripts/template_repo_cli/core/collector.py` — synthesises file paths from an `exercise_id` using filename conventions.
- [x] `scripts/template_repo_cli/core/selector.py` — mixes notebook filename scanning with construct/type directory scanning.
- [x] `scripts/template_repo_cli/core/packager.py` — flattens selected exercise assets into exported template-repo paths.
- [x] `scripts/template_repo_cli/utils/filesystem.py` — still accepts bare notebook filenames and silently prepends `notebooks/`, which is a hidden identity dependency outside the core grader path.
- [x] `scripts/template_repo_cli/utils/validation.py` — validates construct names, type names, and notebook-selection patterns that are tied to today’s layout.
- [x] `tests/notebook_grader.py` — resolver and execution helpers consume notebook paths rather than canonical `exercise_key` values.
- [x] `tests/helpers.py` — helper layer defaults `legacy notebook-root override env var` and exposes notebook-path oriented helpers.
- [x] `tests/exercise_framework/paths.py` — public path-resolution helper mirrors `tests/notebook_grader.py` semantics.
- [x] `tests/exercise_framework/api.py` — manual slug registry for framework-level checks.
- [x] `tests/student_checker/api.py` — manual slug registry for student self-check commands.
- [x] `tests/exercise_expectations/*.py` — exercise-specific notebook path constants and expectations still point at flat notebook filenames.

Decision note: keep `scripts/verify_exercise_quality.py` as the Exercise Verifier agent’s lightweight checker and migrate it to the canonical `exercises/<construct>/<exercise_key>/` layout plus shared metadata/resolver contract rather than retire or replace it; the agent depends on its fast checks and updating the path inference is far less intrusive than inventing a new tool.

#### Test Files And Fixtures To Audit During Phase 1

- [x] `tests/test_new_exercise.py` — hard-codes scaffold output paths.
- [x] `tests/test_build_autograde_payload.py` — asserts allowed `legacy notebook-root override env var` values and grading expectations for `notebooks` versus `notebooks/solutions`.
- [x] `tests/test_integration_autograding.py` — integration contract for the grading pipeline and environment semantics.
- [x] `tests/template_repo_cli/conftest.py` — fixture data reveals current hybrid path assumptions.
- [x] `tests/template_repo_cli/test_collector.py` — file collection contract.
- [x] `tests/template_repo_cli/test_selector.py` — construct/type/notebook selection contract.
- [x] `tests/template_repo_cli/test_validation.py` — notebook pattern and validation contract.
- [x] `tests/template_repo_cli/test_filesystem.py` — path resolution helpers used by the template CLI.
- [x] `tests/template_repo_cli/test_packager.py` — exported file placement and metadata-free packaging contract.
- [x] `tests/template_repo_cli/test_integration.py` — end-to-end template generation and dry-run workspace checks.
- [x] `tests/exercise_framework/test_paths.py` — parity between path resolvers.
- [x] `tests/exercise_framework/test_parity_paths.py` — notebook override resolution semantics.
- [x] `tests/exercise_framework/test_autograde_parity.py` — parity between exercise tests and packaged/duplicated exercise tests.
- [x] `tests/exercise_framework/test_parity_autograde_ex002.py` — ex002-specific parity contract.
- [x] `tests/test_ex007_sequence_debug_casting.py` and `tests/test_ex007_construct_checks.py` — already reveal ex007 naming divergence.

#### Docs, Workflows, And Agent Instructions To Audit During Phase 1

- [x] `README.md` — repo layout and template-repo quickstart still describe the current notebook/test layout.
- [x] `AGENTS.md` — root contributor instructions still describe `exercises/CONSTRUCT/TYPE/exNNN_slug/`, top-level `tests/`, and notebook mirrors.
- [x] `docs/project-structure.md` — formal layout reference for current repo organisation.
- [x] `docs/development.md` — contributor workflow, exercise creation, and cleanup examples.
- [x] `docs/setup.md` — setup and exercise-authoring workflow examples.
- [x] `docs/testing-framework.md` — testing surface descriptions and workflow expectations.
- [x] `docs/exercise-generation.md` — authoring workflow guidance and examples that still rely on current paths.
- [x] `docs/exercise-generation-cli.md` — scaffolding workflow and the manual “move the exercise folder afterwards” instruction.
- [x] `docs/CLI_README.md` — template CLI export contract.
- [x] `docs/autograding-cli.md` — `legacy notebook-root override env var` examples.
- [x] `docs/exercise-testing.md` — grading workflow references.
- [x] `.github/agents/exercise_generation.md.agent.md` — multiple current layout assumptions, plus an example that mentions `check_notebook('ex007_data_types_debug_casting')`.
- [x] `.github/agents/exercise_verifier.md.agent.md` — verifier contract tied to current layout.
- [x] `docs/agents/tidy_code_review/automated_review.md` and `docs/agents/tidy_code_review/manual_review.md` — reviewer guidance that references the current test and notebook layout.
- [x] `.github/workflows/tests.yml` — solution-test workflow uses `legacy notebook-root override env var=notebooks/solutions`.
- [x] `.github/workflows/tests-solutions.yml` — duplicate solution-testing workflow surface.
- [x] `template_repo_files/.github/workflows/classroom.yml` — exported Classroom grading workflow expects flat `notebooks/` and `tests/`.
- [x] `template_repo_files/README.md.template`, `template_repo_files/pyproject.toml`, and `template_repo_files/pytest.ini` — template contract surface for exported repositories.
- [x] `exercises/sequence/OrderOfTeaching.md` — current construct-level teaching-order source.
- [x] `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` — placeholder anomaly that must be recorded, not silently normalised.

### Modules, Functions, Classes, Commands, And Contracts

#### Identity Represented As A Filename Stem Or Notebook Name

- [x] `scripts.template_repo_cli.core.collector.FileCollector.collect_files()` — treats the input as a filename stem and constructs `notebooks/<exercise_id>.ipynb` and `tests/test_<exercise_id>.py`.
- [x] `scripts.template_repo_cli.core.collector.FileCollector.collect_multiple()` — repeats the same filename-stem assumption in batch form.
- [x] `scripts.template_repo_cli.core.packager.TemplatePackager.copy_exercise_files()` — writes flat exported paths based on the same exercise ID.
- [x] `scripts.template_repo_cli.core.selector.ExerciseSelector.get_all_notebooks()` — discovers exercises by scanning `notebooks/ex*.ipynb` and returning stems.
- [x] `scripts.template_repo_cli.utils.filesystem.resolve_notebook_path()` — treats a bare filename as implicitly living under `notebooks/` and resolves other relative notebook paths from the current working directory.
- [x] `tests/exercise_expectations/ex001_sanity.py`, `tests/exercise_expectations/ex002_sequence_modify_basics_exercise_expectations.py`, `tests/exercise_expectations/ex003_sequence_modify_variables.py`, `tests/exercise_expectations/ex004_sequence_debug_syntax.py`, `tests/exercise_expectations/ex005_sequence_debug_logic.py`, `tests/exercise_expectations/ex006_sequence_modify_casting.py`, and `tests/exercise_expectations/ex007_sequence_debug_casting.py` — encode notebook paths as flat `notebooks/<exercise_key>.ipynb` constants.

#### Identity Represented As A Directory Path Or Folder Hierarchy

- [x] `scripts.verify_exercise_quality._find_exercise_dir()` — searches the filesystem for any matching directory name and silently prefers deeper paths when duplicates exist.
- [x] `scripts.verify_exercise_quality._infer_construct_and_type()` — infers construct and type from directory parents.
- [x] `scripts.verify_exercise_quality._check_order_of_teaching()` — assumes construct-level `OrderOfTeaching.md` paths.
- [x] `scripts.template_repo_cli.core.selector._find_exercises_in_construct()` — assumes `exercises/<construct>/<type>/<exercise_key>/`.
- [x] `scripts.template_repo_cli.core.selector._find_exercises_by_type()` — assumes type is a directory under every construct.
- [x] `scripts.template_repo_cli.core.selector._find_exercises_in_type_dir()` — same assumption, but for construct-and-type selection.

#### Identity Represented As A Manual Slug Registry

- [x] `tests/student_checker/api.py` — `_EX001_SLUG` through `_EX007_SLUG`, `_NOTEBOOK_ORDER`, and `_get_checks()` manually register exercises.
- [x] `tests/exercise_framework/api.py` — `EX001_SLUG` through `EX006_SLUG`, `NOTEBOOK_ORDER`, and `_get_check_definitions()` manually register exercises.
- [x] `tests/exercise_expectations/__init__.py` — public export list is curated manually and currently omits ex007.

#### Identity Represented As A Notebook Path With Environment Override

- [x] `tests/notebook_grader.resolve_notebook_path()` — resolves a notebook path, optionally rebasing into `legacy notebook-root override env var`.
- [x] `tests/exercise_framework/paths.resolve_notebook_path()` — mirrors the same behaviour for framework users.
- [x] `tests/helpers.resolve_notebook_path()` and `tests/helpers.build_autograde_env()` — helper wrappers around the same notebook-root concept.
- [x] `scripts/build_autograde_payload._normalise_notebooks_dir()` — only permits `notebooks` and `notebooks/solutions`.

#### Authoring, CLI, And Workflow Commands To Keep Under Review

- [x] `python scripts/new_exercise.py exNNN "Title" --slug slug` — current scaffolder command produces legacy root-level paths.
- [x] `template_repo_cli create --construct ...`, `template_repo_cli create --type ...`, `template_repo_cli create --notebooks ...` — selection interface currently relies on path-derived concepts and notebook IDs.
- [x] `template_repo_cli update-repo ...` — same selection contract as `create`.
- [x] `<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks/solutions uv run pytest -q` — current solution verification contract.
- [x] `<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks uv run python scripts/build_autograde_payload.py ...` — current student-mode grading contract used by exported templates.

#### Packaging And Export Contracts That Must Not Be Broken In Phase 1

- [x] `template_repo_files/.github/workflows/classroom.yml` — exported templates run grading with `legacy notebook-root override env var=notebooks`.
- [x] `scripts/template_repo_cli/core/packager.py` — exported templates currently include flat student notebooks and tests only while copying shared runtime helpers out of `tests/`; document how `exercise_runtime_support` should replace that import path and add verification that the exported workspaces continue to include the runtime helpers alongside the flattened files.
- [x] `docs/CLI_README.md` and `README.md` — public documentation promises metadata-free exported template repositories.

### Current Assumptions Being Removed

- [x] Assumption: exercise identity can always be reconstructed safely from a notebook filename alone.
- [x] Assumption: there is only one teacher-doc directory per `exercise_key`.
- [x] Assumption: construct and exercise type can always be inferred reliably from the current folder tree.
- [x] Assumption: every student notebook has a solution notebook with the same stem.
- [x] Assumption: every exercise’s primary pytest file lives only at `tests/test_<exercise_key>.py`.
- [x] Assumption: manual slug registries in helper APIs stay naturally in sync with the filesystem.
- [x] Assumption: placeholder files such as `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` are harmless.

## Implementation Tasks

Break Phase 1 into concrete deliverables. This is inventory and model definition work only.

### Code Changes

- [x] Add a dedicated inventory artefact that records all current exercise identities, physical surfaces, and anomalies.
- [x] Add a path-assumption register mapping every affected module/function/command to one of: filename-based, slug-based, directory-based, or notebook-path-based identity.
- [x] No additional Phase 1 validation script or test module was needed; the inventory was verified with read-only filesystem commands and targeted source inspection.
- [x] Update no resolver code yet. Phase 1 should document the future contract, not implement it.
- [x] Remove nothing from runtime code in Phase 1 unless it is purely dead inventory scaffolding created during execution and not needed afterwards, because the shared helpers are destined for `exercise_runtime_support` and should remain intact.
- [x] Rename or relocate nothing in the live exercise tree during Phase 1.
- [x] Add explicit fail-fast reporting to the inventory artefact for duplicate keys, missing solution mirrors, stale directories, and construct mismatches.

### Canonical Model Definition Tasks

- [x] Write down the canonical identity rule: the only canonical resolver input will be `exercise_key`.
- [x] Write down the canonical authoring location rule: all exercise-specific assets will eventually live under `exercises/<construct>/<exercise_key>/`.
- [x] Write down the future notebook naming rule: `student.ipynb` and `solution.ipynb` inside the canonical exercise directory.
- [x] Write down the future metadata rule: exercise type leaves the folder hierarchy and moves into `exercise.json`.
- [x] Write down the shared-testing rule: shared grading/runtime helpers will move to `exercise_runtime_support`, leaving top-level `tests/` to host only pooled test suites.
- [x] Confirm and write down the export rule: Classroom repositories remain metadata-free and continue to use flattened exported exercise-key paths during the migration transition.
- [x] Write down the public-API deferral rule: notebook/self-check interfaces remain unchanged until later phases prove the replacement execution model.
- [x] Record the canonical target path and canonical identity for every ambiguous exercise or anomaly, and explicitly record when the correct action is deletion rather than migration, including `ex001_sanity` (which must be removed entirely before later phases), `ex006_sequence_modify_casting`, `ex007_sequence_debug_casting`, and `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md`.

### Pilot Suitability Analysis Tasks

- [x] Score every current exercise or sub-tree for pilot suitability using objective criteria: duplicate directories, missing solution mirror, test duplication, manual registry drift, and docs/workflow drift.
- [x] Confirm whether the safest pilot should be a whole construct, a construct subset, or a single exercise.
- [x] Record the rationale if `sequence` is still chosen, and record the rationale if only a subset such as `ex004_sequence_debug_syntax` / `ex005_sequence_debug_logic` is chosen instead.
- [x] Explicitly reject high-risk or obsolete candidates in writing if they remain unsuitable after inventory (`ex001_sanity` must be removed before any later phase can proceed; `ex006_sequence_modify_casting` and `ex007_sequence_debug_casting` are current likely migration rejects).

### Data And Metadata Changes

- [x] `exercise.json` changes: do **not** add files yet; only record the minimal field shortlist that later phases need.
- [x] No machine-readable inventory companion was added; runtime code still does not depend on the Phase 1 artefacts.
- [x] Registry replacement work: identify the current pseudo-registries to replace later (`tests/student_checker/api.py`, `tests/exercise_framework/api.py`, `tests/exercise_expectations/__init__.py`, and the template CLI selector/collector split).
- [x] Migration manifest updates: prepare a provisional list of exercises that will require manual migration handling because of current anomalies, and include the canonical target path each one should resolve to later.

### Test Changes

The unchecked items in this section and the next section are deliberate later-phase backlog captured during Phase 1. They do not block Phase 1 completion.

List both existing tests to update later and any new tests that Phase 1 may add to keep the inventory honest.

- [ ] Update existing unit tests later:
  - `tests/test_new_exercise.py`
  - `tests/test_build_autograde_payload.py`
  - `tests/template_repo_cli/test_collector.py`
  - `tests/template_repo_cli/test_selector.py`
  - `tests/template_repo_cli/test_validation.py`
  - `tests/template_repo_cli/test_filesystem.py`
  - `tests/exercise_framework/test_paths.py`
  - `tests/exercise_framework/test_parity_paths.py`
- [ ] Update existing integration tests later:
  - `tests/template_repo_cli/test_packager.py`
  - `tests/template_repo_cli/test_integration.py`
  - `tests/test_integration_autograding.py`
  - `tests/exercise_framework/test_autograde_parity.py`
  - `tests/exercise_framework/test_parity_autograde_ex002.py`
- [ ] Update packaging/template tests later:
  - `tests/template_repo_cli/conftest.py`
  - `tests/template_repo_cli/test_packager.py`
  - `tests/template_repo_cli/test_integration.py`
- [ ] Update workflow-related tests later:
  - `tests/test_build_autograde_payload.py`
  - `tests/test_autograde_plugin.py`
  - `tests/test_integration_autograding.py`
- [ ] Update exercise-specific anomaly tests later:
  - `tests/test_ex007_sequence_debug_casting.py`
  - `tests/test_ex007_construct_checks.py`
  - `tests/exercise_expectations/__init__.py`
  - `tests/exercise_expectations/ex007_sequence_debug_casting.py`
- [ ] Remove obsolete tests: none in Phase 1 unless a newly added inventory-only test or script is superseded during the same phase.

### New Test Cases Required

Every new test case below should prove a concrete migration fact rather than merely checking that a file exists.

- [ ] Positive case: a repository-inventory test or validation command enumerates all **seven** current student exercise keys and maps each one to its current teacher docs path(s), student notebook, solution notebook, and primary test surface(s).
- [ ] Failure case: duplicate teacher directories for `ex006_sequence_modify_casting` fail with a clear report naming both `exercises/ex006_sequence_modify_casting/` and `exercises/sequence/modify/ex006_sequence_modify_casting/`.
- [ ] Failure case: obsolete exercises such as `ex001_sanity` are reported clearly as removal targets (with explicit blocker wording) rather than being mistaken for canonical migration candidates.
- [ ] Failure case: solution notebook mismatch is reported clearly for `ex007_sequence_debug_casting`, naming `notebooks/solutions/ex007_data_types_debug_casting.ipynb` as the conflicting path.
- [ ] Failure case: placeholder construct path `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` is reported as a non-canonical anomaly.
- [ ] Regression case: the recorded ex002 split test contract remains explicit across the inventory artefact, `tests/template_repo_cli/conftest.py`, `scripts/template_repo_cli/core/collector.py`, and the parity suites that deliberately execute both files.
- [ ] Regression case: manual slug registries in `tests/student_checker/api.py` and `tests/exercise_framework/api.py` are checked against the filesystem inventory so future drift is visible immediately.
- [ ] Export/package case: exported template repos remain metadata-free and do not accidentally retain obsolete exercises such as `ex001_sanity` once they have been removed from the source inventory.
- [ ] Student-mode case: `<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks` grading still resolves notebooks from the student tree and does not depend on yet-to-be-added metadata files.
- [ ] Solution-mode case: `<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks/solutions` grading still resolves solution notebooks and fails clearly when a mirrored slug is missing or renamed.
- [ ] Documentation case: examples in `.github/agents/exercise_generation.md.agent.md`, `docs/exercise-generation-cli.md`, and related docs are checked for stale exercise-name examples such as `ex007_data_types_debug_casting`.

### Docs, Agents, And Workflow Updates

Phase 1 should at least catalogue these updates, even if some wording changes wait until later phases.

- [x] Contributor docs:
  - `README.md`
  - `AGENTS.md`
  - `docs/project-structure.md`
  - `docs/development.md`
  - `docs/setup.md`
  - `docs/testing-framework.md`
  - `docs/exercise-generation.md`
  - `docs/exercise-generation-cli.md`
  - `docs/CLI_README.md`
  - `docs/autograding-cli.md`
  - `docs/exercise-testing.md`
- [x] Teaching docs:
  - `exercises/sequence/OrderOfTeaching.md`
  - `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md`
  - exercise-level `README.md` / `OVERVIEW.md` files only as inventory references, not for content editing in this phase
- [x] Agent docs:
  - `.github/agents/exercise_generation.md.agent.md`
  - `.github/agents/exercise_verifier.md.agent.md`
  - `.github/agents/implementer.md.agent.md`
  - `.github/agents/tidy_code_review.md.agent.md`
  - `docs/agents/tidy_code_review/automated_review.md`
  - `docs/agents/tidy_code_review/manual_review.md`
- [x] Repository workflows:
  - `.github/workflows/tests.yml`
  - `.github/workflows/tests-solutions.yml`
- [x] Export/template workflows and files:
  - `template_repo_files/.github/workflows/classroom.yml`
  - `template_repo_files/README.md.template`
  - `template_repo_files/pyproject.toml`
  - `template_repo_files/pytest.ini`

## Verification Plan

Use the following commands during Phase 1 execution to verify that the written inventory matches the live repository.

### Read-Only Inventory Commands

```bash
source .venv/bin/activate
find exercises -type d -name 'ex*' | sort
find notebooks -maxdepth 2 -type f -name 'ex*.ipynb' | sort
find tests -type f -name 'test_ex*.py' | sort
command -v rg >/dev/null && rg -n "exercise_key|exercise_id|resolve_notebook_path|check_notebook|exercise\.json|notebooks/solutions|tests/test_ex|exercises/" scripts tests docs .github template_repo_files
```

### Baseline Behaviour Commands

These commands do **not** prove the migration, but they document the current contracts that Phase 1 must not accidentally change.

```bash
source .venv/bin/activate
<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks/solutions uv run pytest -q
<LEGACY_NOTEBOOK_ROOT_ENV_VAR>=notebooks uv run python scripts/build_autograde_payload.py --pytest-args=-q --minimal
```

### If Phase 1 Adds Automated Inventory Checks

Prefer a focused command such as one of the following, depending on where the validation is implemented:

```bash
source .venv/bin/activate
uv run pytest -q tests/test_phase1_repository_inventory.py
```

or

```bash
source .venv/bin/activate
uv run python scripts/validate_phase1_inventory.py
```

## Exit Criteria

- [x] A written inventory exists and is easy for later phases to cite.
- [x] Every current exercise key has an explicit location map and anomaly status.
- [x] Duplicate or ambiguous exercise identities are recorded explicitly, not hidden behind recursive search or “best guess” path selection.
- [x] The canonical authoring model is written down and linked back to `ACTION_PLAN.md`.
- [x] A pilot recommendation exists with a short rationale and named non-pilot blockers.
- [x] Any newly discovered blocker or gap has been fed back into `ACTION_PLAN.md`.

## Mandatory Feedback Into `ACTION_PLAN.md`

- [x] If you discover a new blocker, hidden dependency, stale alias, or sequencing problem while carrying out this checklist, add it to `ACTION_PLAN.md` **before** marking Phase 1 complete.
- [x] Record the blocker using concrete paths, symptoms, and impact. Do not write vague notes such as “docs drift exists”. Name the exact files and the exact mismatch.
- [x] State whether the issue blocks pilot selection, blocks canonical identity definition, or can wait for a later phase.
- [x] If the blocker changes any migration rule or sequencing assumption, update the relevant phase wording in `ACTION_PLAN.md` rather than keeping the discovery only in a PR description or commit message.
- [x] Re-run the Phase 1 inventory verification after recording the blocker so the inventory artefact and the action plan remain aligned.

Recommended blocker template for `ACTION_PLAN.md` updates:

```text
Blocker: <short title>
Files: <exact paths>
Why it matters: <impact on canonical identity / pilot / later phases>
Recommended phase: <Phase 1 / 2 / later>
```

## Confirmed Phase 2 Pilot Recommendation

Phase 1 execution confirmed the following pilot decision and non-pilot blockers.

- `ex004_sequence_debug_syntax` — confirmed Phase 2 live pilot. It has clean teacher docs, matching student and solution notebook stems, a single top-level test surface, and no confirmed duplicate artefacts.
- `ex005_sequence_debug_logic` — confirmed reserve backup pilot. It is similarly clean, but it remains the reserve because the plan already names `ex004` and the inventory found no reason to override that choice.
- `ex003_sequence_modify_variables` — low-risk reserve candidate, but not preferred because `ex004` already satisfies the plan’s live-pilot requirement without introducing an alternative proof shape.
- Remove `ex001_sanity` rather than trying to give it a canonical construct/type home; treat it as a blocker that must be deleted before progressing.
- Avoid `ex006_sequence_modify_casting` for the first cut because it has duplicate teacher directories.
- Avoid `ex007_sequence_debug_casting` for the first cut because the solution notebook slug, self-check cell, test import, and registry surfaces are inconsistent.
