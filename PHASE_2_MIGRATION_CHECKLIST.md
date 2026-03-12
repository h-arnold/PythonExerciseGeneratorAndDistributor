# Phase 2 Migration Checklist — Metadata And Resolution Layer

Use this checklist for the implementation work described in [ACTION_PLAN.md](./ACTION_PLAN.md) under **Phase 2: Metadata And Resolution Layer**.

This checklist is intentionally concrete and repository-specific. It is based on the current codebase state on **12 March 2026** and must be kept aligned with later discoveries.

## Required Migration Rules

These rules are restated from [ACTION_PLAN.md](./ACTION_PLAN.md) and are mandatory for this phase:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless [ACTION_PLAN.md](./ACTION_PLAN.md) is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into [ACTION_PLAN.md](./ACTION_PLAN.md).
- **Mandatory for future agents:** if implementation uncovers a missing dependency, hidden coupling, or naming ambiguity, update [ACTION_PLAN.md](./ACTION_PLAN.md) before marking Phase 2 complete.

## Checklist Header

- Checklist title: `PHASE_2_MIGRATION_CHECKLIST.md`
- Related action-plan phase or stream: `Phase 2: Metadata And Resolution Layer`
- Author: `OpenAI Codex (Implementer role)`
- Date: `2026-03-12`
- Status: `draft`
- Scope summary: Introduce the shared metadata and resolver layer, define the minimal metadata schema in code, add an explicit migration manifest, prove canonical resolution from `exercise_key`, and prove that legacy path-based resolver inputs fail hard without silent fallback.
- Explicitly out of scope: moving all live exercises into the canonical tree, rewriting `scripts/new_exercise.py`, cutting grading/autograding over to the new execution model, changing Classroom export layout, moving exercise-local tests into `exercises/**/tests/`, and rewriting all contributor docs and workflows to the final model.

## Objective

When this phase is complete, the repository has a single shared metadata/resolution layer that can:

- load minimal exercise metadata from `exercise.json`
- load an explicit migration manifest that states whether an exercise is still legacy or has reached the canonical layout
- resolve a canonical exercise directory from `exercise_key`
- resolve the canonical student or solution notebook path from `exercise_key` plus an explicit variant selector
- reject notebook paths, test paths, filenames, and other legacy path-shaped inputs with a clear error
- fail hard when an exercise is marked as migrated but the canonical files are missing

What must no longer be true after Phase 2:

- resolver logic is duplicated across `tests/`, `scripts/`, and template tooling
- `PYTUTOR_NOTEBOOKS_DIR` is treated as part of the target resolver contract
- canonical resolution depends on scanning `notebooks/`, `notebooks/solutions/`, or `tests/` as the source of truth
- canonical resolution quietly adapts path-based callers instead of forcing them onto `exercise_key`

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [ ] Required decisions from [ACTION_PLAN.md](./ACTION_PLAN.md) are settled.
- [ ] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly.

Notes:

- Decisions relied on:
  - Canonical layout is `exercises/<construct>/<exercise_key>/`.
  - Exercise type moves into metadata and is **not** part of the canonical path.
  - Notebook filenames inside canonical exercise folders are `student.ipynb` and `solution.ipynb`.
  - `exercise.json` fields are limited to `schema_version`, `exercise_key`, `exercise_id`, `slug`, `title`, `construct`, `exercise_type`, and `parts`.
  - Exported repositories must remain metadata-free even after authoring-side metadata is introduced.
- Open assumptions:
  - The shared module/package name for this phase is `exercise_metadata/`.
  - Phase 2 must prove canonical behaviour with isolated fixtures and one live migrated pilot exercise.
  - If a live pilot is required in this phase, do **not** choose `ex006_sequence_modify_casting` or `ex007_sequence_debug_casting` until the blockers in this checklist have been resolved and fed back into [ACTION_PLAN.md](./ACTION_PLAN.md).
  - The Phase 2 live pilot exercise is `ex004_sequence_debug_syntax`; start with that clean example when proving canonical resolver behaviour.

## Affected Surfaces Inventory

List every surface this migration unit touches. Be concrete.

### Files And Paths To Update

- [ ] Source files:
  - `pyproject.toml` — add the new shared metadata/resolver package to the installed package list if a new top-level package is introduced.
  - `tests/notebook_grader.py` — currently owns a path-based `resolve_notebook_path()` helper and silently falls back from solution paths to the original notebook path.
  - `tests/exercise_framework/paths.py` — duplicates notebook-resolution semantics and depends on `PYTUTOR_NOTEBOOKS_DIR`.
  - `tests/exercise_framework/runtime.py` — re-exports path-based grading helpers and may need to import the shared resolver later without changing the public execution API prematurely.
  - `tests/helpers.py` — wraps `tests.notebook_grader.resolve_notebook_path()` and therefore inherits legacy path semantics.
  - `tests/student_checker/notebook_runtime.py` — resolves notebooks from a filename/path input and is part of the student self-check path.
  - `tests/student_checker/api.py` — exposes notebook-slug-based public entry points and hard-coded notebook ordering.
  - `tests/student_checker/__init__.py` — exports `run_notebook_checks`, which currently remains notebook-shaped.
  - `tests/student_checker/checks/ex001.py` — imports `EX001_NOTEBOOK_PATH`.
  - `tests/student_checker/checks/ex003.py` — resolves notebook paths from expectation constants.
  - `tests/student_checker/checks/ex004.py` — resolves notebook paths from expectation constants.
  - `tests/student_checker/checks/ex005.py` — resolves notebook paths from expectation constants.
  - `tests/student_checker/checks/ex006.py` — resolves notebook paths from expectation constants.
  - `tests/student_checker/checks/ex007.py` — resolves notebook paths from expectation constants and is already affected by the ex007 naming mismatch.
  - `tests/exercise_expectations/__init__.py` and the per-exercise expectation modules under `tests/exercise_expectations/` — currently store notebook-path constants such as `EX004_NOTEBOOK_PATH = "notebooks/ex004_sequence_debug_syntax.ipynb"`.
  - `scripts/build_autograde_payload.py` — validates `PYTUTOR_NOTEBOOKS_DIR` against `notebooks` and `notebooks/solutions`; this is a live coupling to the legacy layout.
  - `scripts/template_repo_cli/utils/filesystem.py` — contains a third notebook-path resolver implementation that accepts absolute paths, relative paths, and bare filenames.
  - `scripts/verify_exercise_quality.py` — currently infers exercise directories by recursively searching `exercises/` and prefers the existing `exercises/<construct>/<type>/<exercise_key>/` shape, which conflicts with the canonical action-plan layout.
- [ ] Test files:
  - `tests/exercise_framework/test_paths.py` — asserts parity with the current path-based notebook grader.
  - `tests/exercise_framework/test_parity_paths.py` — asserts notebook-path parity under `PYTUTOR_NOTEBOOKS_DIR`.
  - `tests/exercise_framework/test_runtime.py` — exercises the current runtime wrappers against path inputs.
  - `tests/exercise_framework/test_api_contract.py` — validates notebook-slug-based public framework behaviour.
  - `tests/exercise_framework/test_autograde_parity.py` — assumes solution-mode execution via `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
  - `tests/student_checker/test_notebook_runtime.py` — exercises path-based notebook runtime behaviour.
  - `tests/template_repo_cli/test_filesystem.py` — currently tests `resolve_notebook_path()` for absolute, relative, filename-only, and nonexistent notebook inputs.
  - `tests/template_repo_cli/test_selector.py` — currently assumes exercise selection from the existing `exercises/<construct>/<type>/<exercise_key>/` tree and notebook-pattern selection from top-level `notebooks/`.
  - `tests/template_repo_cli/test_packager.py` — packages notebooks from top-level `notebooks/` and excludes `notebooks/solutions/`.
  - `tests/test_build_autograde_payload.py` — validates strict allowed values for `PYTUTOR_NOTEBOOKS_DIR`.
  - `tests/test_integration_autograding.py` — exercises real autograding flow with `PYTUTOR_NOTEBOOKS_DIR`.
  - `tests/test_new_exercise.py` — not a Phase 2 implementation target, but its generated self-check contract currently passes a notebook filename to `run_notebook_checks()` and must be tracked as a downstream caller.
  - New tests to add for this phase should live alongside the new shared package, for example `tests/test_exercise_metadata_resolver.py` and `tests/test_exercise_metadata_manifest.py`, or mirrored package tests if a package directory is created.
- [ ] Docs:
  - `README.md` — teaches `notebooks/` plus `notebooks/solutions/` as the canonical model.
  - `AGENTS.md` — repeatedly instructs agents to use `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` and the current split layout.
  - `docs/project-structure.md` — must eventually describe the shared metadata/resolution layer and the canonical exercise tree.
  - `docs/testing-framework.md` — currently documents `resolve_notebook_path()` as a notebook-path redirector.
  - `docs/development.md` — should eventually describe the new resolver contract and verification commands.
  - `docs/setup.md` — currently includes solution-mode test commands tied to `PYTUTOR_NOTEBOOKS_DIR`.
  - `docs/exercise-generation-cli.md` — downstream consumer; do not rewrite in Phase 2 unless the shared resolver becomes a hard dependency for scaffolded files.
  - `docs/github-classroom-autograding-guide.md` — downstream documentation for exported repos and autograding.
- [ ] Workflows:
  - `.github/workflows/tests.yml` — currently runs `uv run pytest -q` with `PYTUTOR_NOTEBOOKS_DIR: notebooks/solutions`.
  - `.github/workflows/tests-solutions.yml` — same legacy solution-layout assumption.
  - `template_repo_files/.github/workflows/classroom.yml` — exported workflow still uses `PYTUTOR_NOTEBOOKS_DIR: notebooks`.
- [ ] Agent instructions:
  - `.github/agents/exercise_generation.md.agent.md` — instructs authors to create student notebooks under `notebooks/` and solutions under `notebooks/solutions/`.
  - `.github/agents/exercise_verifier.md.agent.md` — verifies exercises via notebook-path commands and the current solution mirror.
  - `AGENTS.md` — contributor-level instructions will need a later-phase cutover once the resolver model is proven.
- [ ] Template/export files:
  - `template_repo_files/.github/workflows/classroom.yml` — keep metadata-free export assumptions explicit.
  - `scripts/template_repo_cli/core/collector.py` — still collects only top-level notebooks and top-level tests.
  - `scripts/template_repo_cli/core/packager.py` — still copies top-level notebooks and top-level tests into exported workspaces.
  - `scripts/template_repo_cli/core/selector.py` — still selects via notebooks and type-segmented exercise directories.
- [ ] Exercise directories:
  - `exercises/ex001_sanity/` — legacy root-level exercise directory with no construct parent and no `exercise.json`.
  - `exercises/ex006_sequence_modify_casting/` — legacy root-level exercise directory that duplicates the `ex006` identity; should be removed after `exercises/sequence/modify/ex006_sequence_modify_casting/` is confirmed as the canonical home.
  - `exercises/sequence/modify/ex002_sequence_modify_basics/` — current teacher-material directory in the old construct/type/exercise shape.
  - `exercises/sequence/modify/ex003_sequence_modify_variables/` — same old construct/type/exercise shape.
  - `exercises/sequence/debug/ex004_sequence_debug_syntax/` — same old construct/type/exercise shape.
  - `exercises/sequence/debug/ex005_sequence_debug_logic/` — same old construct/type/exercise shape.
  - `exercises/sequence/modify/ex006_sequence_modify_casting/` — duplicate `ex006` identity in the old construct/type/exercise shape.
  - `exercises/sequence/debug/ex007_sequence_debug_casting/` — old construct/type/exercise shape and the canonical `ex007` home; all `data_types` references should be normalised to this key family.
  - `exercises/sequence/OrderOfTeaching.md` — currently links to `./modify/...` and `./debug/...` directories and notebook paths under `notebooks/`.

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
  - New shared package, recommended as `exercise_metadata/` with modules such as:
    - `exercise_metadata/__init__.py` — public exports.
    - `exercise_metadata/metadata.py` — `exercise.json` loading and schema validation.
    - `exercise_metadata/manifest.py` — migration manifest loading and validation.
    - `exercise_metadata/resolver.py` — `exercise_key`-based resolution helpers.
    - `exercise_metadata/errors.py` — explicit resolver/metadata exception types for later call-site migration.
    - `exercise_metadata/_typeguards.py` or `exercise_metadata/types.py` — TypeGuards and small shared types.
  - Existing duplicated-resolver modules to converge later:
    - `tests.notebook_grader`
    - `tests.exercise_framework.paths`
    - `scripts.template_repo_cli.utils.filesystem`
    - `tests.helpers`
- [ ] Public functions or methods:
  - New shared functions to add:
    - `load_exercise_metadata(exercise_key: str, repo_root: Path | None = None)`
    - `load_migration_manifest(repo_root: Path | None = None)`
    - `resolve_exercise_dir(exercise_key: str, repo_root: Path | None = None)`
    - `resolve_notebook_variant(exercise_key: str, variant: Literal["student", "solution"], repo_root: Path | None = None)`
  - New fail-fast helper to add:
    - `validate_exercise_key(value: str)` or equivalent — reject path-like inputs such as `notebooks/ex001_sanity.ipynb`, `ex001_sanity.ipynb`, `tests/test_ex001_sanity.py`, and strings containing `/`, `\\`, or `.ipynb`.
  - Existing functions whose current contract must be inventoried, but not necessarily broken in Phase 2:
    - `tests.notebook_grader.resolve_notebook_path()`
    - `tests.exercise_framework.paths.resolve_notebook_path()`
    - `scripts.template_repo_cli.utils.filesystem.resolve_notebook_path()`
    - `tests.student_checker.notebook_runtime.run_notebook_checks()`
    - `tests.student_checker.api.check_notebook()`
- [ ] CLI commands or flags:
  - `uv run python scripts/build_autograde_payload.py` — current environment validation assumes only legacy notebook roots.
  - `uv run python scripts/verify_exercise_quality.py notebooks/exNNN_slug.ipynb --construct ... --type ...` — currently notebook-path-shaped and depends on old exercise-directory conventions.
  - `template-repo-cli` and `template_repo_cli` — current selection logic still scans `notebooks/` and the old exercise directory shape.
- [ ] Environment variables:
  - `PYTUTOR_NOTEBOOKS_DIR` — current legacy variant selector. Phase 2 must prove that the **new shared resolver does not read this variable**.
- [ ] Workflow jobs or steps:
  - `tests.yml::pytest`
  - `tests-solutions.yml::pytest_solutions`
  - `template_repo_files/.github/workflows/classroom.yml::grade`
- [ ] Packaging/export contracts:
  - Exported workspaces must continue to exclude `exercise.json`, any migration manifest, `solution.ipynb`, and the full authoring-side `exercises/` tree.
- [ ] Notebook self-check contracts:
  - `scripts/new_exercise.py::_make_check_answers_cell()` currently generates `run_notebook_checks('ex001_dummy.ipynb')`.
  - `tests/student_checker/api.check_notebook()` currently accepts a notebook slug such as `ex007_sequence_debug_casting`.
  - `notebooks/ex007_sequence_debug_casting.ipynb` currently calls `check_notebook('ex007_data_types_debug_casting')`, which must be normalised to `check_notebook('ex007_sequence_debug_casting')`.

### Current Assumptions Being Removed

- [ ] Notebook paths such as `notebooks/ex002_sequence_modify_basics.ipynb` are treated as canonical exercise identity.
- [ ] `PYTUTOR_NOTEBOOKS_DIR` is allowed to stand in for a proper variant-aware resolver contract.
- [ ] Resolver helpers may silently fall back to the original path when an override candidate does not exist.
- [ ] Canonical exercise discovery can be inferred reliably from the current mixed directory shapes under `exercises/`.
- [ ] Exercise type belongs in the canonical path instead of metadata.
- [ ] It is acceptable for multiple modules to implement their own notebook-path resolution logic.
- [ ] Duplicate exercise-specific test surfaces like `tests/test_ex002_sequence_modify_basics.py` versus `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` must be resolved: the nested path is the canonical exercise-local test and the top-level copy should not be part of the canonical discovery contract.

## Implementation Tasks

Break work into concrete tasks. Group by concern, not by person.

### Code Changes

- [ ] Add:
  - Create the shared metadata/resolution package in a location importable by `tests/`, `scripts/`, and future export-aware code. Preferred home: `exercise_metadata/` at repo root.
  - Add strict loader(s) for `exercise.json` and the migration manifest.
  - Add explicit exception types for invalid `exercise_key`, unknown exercise, legacy-only exercise, duplicate exercise identity, invalid metadata schema, and missing canonical files.
  - Add TypeGuards for JSON payload validation instead of `cast()`-heavy parsing.
- [ ] Update:
  - Update `pyproject.toml` so the shared package is installed in the `uv` environment.
  - Update only the minimum internal call sites needed to prove the new resolver layer; do **not** force a full public API cutover in this phase.
  - Where existing modules must import the new resolver for tests or internal use, keep the resolver input contract strictly `exercise_key`-based.
  - Add repository-root discovery once, centrally, instead of repeating `Path(__file__).resolve().parents[...]` patterns across new resolver modules.
- [ ] Remove:
  - Remove any temptation to add helper overloads that accept `Path`, notebook filename, notebook relative path, or test path as resolver inputs.
  - Remove any new fallback logic that checks top-level `notebooks/` when canonical files are missing for a migrated exercise.
- [ ] Rename or relocate:
  - If a live pilot exercise is migrated in this phase, relocate it directly to `exercises/<construct>/<exercise_key>/`; do **not** preserve the `/<type>/` path segment in the canonical target.
  - Do not use the existing `exercises/sequence/modify/...` or `exercises/sequence/debug/...` directories as the final canonical shape.
- [ ] Fail-fast behaviour to add:
  - `resolve_exercise_dir('notebooks/ex001_sanity.ipynb')` fails with an error that explicitly says resolver input must be an `exercise_key`.
  - `resolve_exercise_dir('ex001_sanity.ipynb')` fails clearly rather than stripping the extension.
  - `resolve_notebook_variant('ex001_sanity', variant='student')` fails clearly if the manifest still marks `ex001_sanity` as `legacy`.
  - `resolve_notebook_variant('ex999_missing', variant='student')` fails clearly for unknown exercise identity.
  - A manifest entry marked `migrated` fails immediately if `exercise.json`, `notebooks/student.ipynb`, or `notebooks/solution.ipynb` is missing.
  - Duplicate discovered directories or duplicate manifest entries for the same `exercise_key` fail immediately.

### Data And Metadata Changes

- [ ] `exercise.json` changes:
  - Add the loader and schema validation in code first.
  - Create `exercise.json` only in the live pilot canonical directory and use the exact minimal field set from [ACTION_PLAN.md](./ACTION_PLAN.md).
  - Do **not** add notebook paths, test paths, tag names, ordering, self-check flags, or other convention-based data to `exercise.json`.
- [ ] Derived-data/index changes:
  - Add a single migration manifest, recommended path: `exercises/migration_manifest.json`.
  - Recommended manifest responsibility: map each known `exercise_key` to a layout state such as `legacy` or `migrated` without storing notebook/test paths.
  - Initial real-repo manifest should list at least: `ex001_sanity`, `ex002_sequence_modify_basics`, `ex003_sequence_modify_variables`, `ex004_sequence_debug_syntax`, `ex005_sequence_debug_logic`, `ex006_sequence_modify_casting`, and `ex007_sequence_debug_casting`.
- [ ] Registry replacement work:
  - Phase 2 should **not** replace every existing notebook-path constant or framework registry yet.
  - Phase 2 should create the new source of truth and prove it with tests so later phases can cut over deliberately.
- [ ] Migration manifest updates:
  - The manifest must make legacy-vs-migrated state explicit.
  - The manifest must not auto-discover layout state by scanning for files.
  - Update only the nominated live pilot entry to `migrated` once the canonical files exist.

### Test Changes

List both existing tests to update and new tests to add.

- [ ] Update existing unit tests:
  - `tests/template_repo_cli/test_filesystem.py` — update or quarantine the existing path-resolution tests so they do not accidentally become the canonical resolver contract.
  - `tests/exercise_framework/test_paths.py` — update expectations if any shared internals are introduced, while keeping legacy notebook-path behaviour explicit and clearly temporary.
  - `tests/exercise_framework/test_parity_paths.py` — same as above.
  - `tests/student_checker/test_notebook_runtime.py` — update only if internal resolution is deliberately threaded into notebook runtime; do not expand the public interface here by accident.
  - `tests/test_build_autograde_payload.py` — update only if Phase 2 deliberately narrows or documents environment validation boundaries.
- [ ] Update integration tests:
  - `tests/test_integration_autograding.py` — keep as a watchlist file; update only if the shared resolver becomes part of the executed autograding path in this phase.
  - `tests/exercise_framework/test_autograde_parity.py` — watchlist for later cutover; update only if runtime wiring changes in Phase 2.
- [ ] Update packaging/template tests:
  - `tests/template_repo_cli/test_selector.py` — do not let this suite continue to define the future canonical layout by default; add comments or follow-up tasks if it remains on the legacy model.
  - `tests/template_repo_cli/test_packager.py` — add protective tests only if the shared package or manifest could affect exported contents.
- [ ] Update workflow-related tests:
  - No mandatory workflow-test rewrite in Phase 2, but capture any changed commands or assumptions in test helpers and docs if a resolver smoke test is added.
- [ ] Remove obsolete tests:
  - Remove no existing tests until equivalent fail-fast shared-resolver coverage is in place.
  - Once the shared resolver tests exist, mark the legacy path-resolution tests as legacy-contract coverage rather than canonical-behaviour coverage.

### New Test Cases Required

Every checklist should spell out the behaviour that must be proved, not just the files to edit.

- [ ] Positive case:
  - `resolve_exercise_dir("ex002_sequence_modify_basics")` returns `exercises/sequence/ex002_sequence_modify_basics/` in a canonical fixture repository.
  - `resolve_notebook_variant("ex002_sequence_modify_basics", variant="student")` returns `exercises/sequence/ex002_sequence_modify_basics/notebooks/student.ipynb` in a canonical fixture repository.
  - `resolve_notebook_variant("ex002_sequence_modify_basics", variant="solution")` returns the corresponding `solution.ipynb` path.
  - `load_exercise_metadata("ex002_sequence_modify_basics")` returns the expected minimal metadata object and nothing path-based.
- [ ] Failure case:
  - Path-shaped inputs such as `"notebooks/ex002_sequence_modify_basics.ipynb"`, `"ex002_sequence_modify_basics.ipynb"`, `"tests/test_ex002_sequence_modify_basics.py"`, and `"exercises/sequence/modify/ex002_sequence_modify_basics"` are rejected with a clear error.
  - A manifest entry marked `migrated` but missing `exercise.json` fails hard.
  - A manifest entry marked `migrated` but missing `notebooks/student.ipynb` or `notebooks/solution.ipynb` fails hard.
  - Metadata containing disallowed convention-based keys such as `student_notebook`, `solution_notebook`, `test_path`, or `tags` is rejected.
- [ ] Regression case:
  - The new shared resolver ignores `PYTUTOR_NOTEBOOKS_DIR` entirely.
  - Duplicate exercise identities fail, using a fixture that mirrors the live `ex006` ambiguity.
  - The ex007 identity mismatch is captured by at least one failing fixture or validation test so it cannot be forgotten during later phases.
  - A real-repo manifest entry marked `legacy` does **not** silently resolve to `notebooks/<exercise_key>.ipynb`.
- [ ] Export/package case:
  - If a shared resolver package is added, exported template packaging still excludes `exercise.json`, `exercises/migration_manifest.json`, `solution.ipynb`, and the full `exercises/` authoring tree.
  - If Phase 2 does not touch packaging code, add at least one protective test or explicit deferred note so this contract is not lost.
- [ ] Student-mode case:
  - Explicitly prove that canonical `variant="student"` resolution works without consulting `PYTUTOR_NOTEBOOKS_DIR`.
  - Explicitly prove that a legacy exercise marked `legacy` does not pretend to have a canonical student notebook.
- [ ] Solution-mode case:
  - Explicitly prove that canonical `variant="solution"` resolution works without consulting `PYTUTOR_NOTEBOOKS_DIR`.
  - Explicitly prove that solution resolution fails cleanly for a legacy-only exercise rather than falling back to `notebooks/solutions/<exercise_key>.ipynb`.

### Docs, Agents, And Workflow Updates

- [ ] Contributor docs:
  - Add a short contributor-facing note in `docs/development.md` or `docs/project-structure.md` explaining the new shared resolver package and the migration manifest **if** the code lands in this phase.
  - Do not rewrite all contributor guidance to the final end-state until later phases complete the cutover.
- [ ] Teaching docs:
  - No student-facing documentation rewrite is required in Phase 2.
  - Keep a watchlist entry for `exercises/sequence/OrderOfTeaching.md` because it currently links to the old `debug/` and `modify/` directory layout.
- [ ] Agent docs:
  - Do not update all agent prompts in Phase 2 unless the new resolver package becomes a required daily workflow.
  - If a new verification command is introduced, add a minimal contributor/agent note and leave the wider layout rewrite for later phases.
- [ ] Repository workflows:
  - No mandatory `.github/workflows/*.yml` change in Phase 2.
  - If a new dedicated resolver unit-test file is added, ensure existing workflow commands run it automatically via the normal `pytest` collection.
- [ ] Template workflows:
  - No exported workflow change in Phase 2.
  - Record any future dependency on the shared resolver package as a blocker if exported packaging would break without it.
- [ ] CLI examples:
  - If implementation introduces a small internal verification command or code example, document it in `docs/development.md` only.
  - Do not rewrite `docs/exercise-generation-cli.md` or the template CLI README in this phase unless the shared resolver is wired into those commands immediately.

## Verification Plan

State exactly how this migration unit will be verified.

### Commands To Run

- [ ] Command:
```bash
source .venv/bin/activate
uv run pytest -q tests/test_exercise_metadata_resolver.py tests/test_exercise_metadata_manifest.py
```
- [ ] Command:
```bash
source .venv/bin/activate
uv run pytest -q tests/exercise_framework/test_paths.py tests/exercise_framework/test_parity_paths.py tests/student_checker/test_notebook_runtime.py
```
- [ ] Command:
```bash
source .venv/bin/activate
uv run pytest -q tests/test_build_autograde_payload.py tests/template_repo_cli/test_filesystem.py
```
- [ ] Command:
```bash
source .venv/bin/activate
uv run ruff check .
```

Only include broader suites if Phase 2 implementation actually touches those surfaces.

### Expected Results

- [ ] Expected passing behaviour:
  - New shared resolver tests pass for canonical fixture repositories.
  - Existing legacy-path tests still pass unless deliberately rewritten in-scope.
  - Manifest validation and metadata validation tests pass.
- [ ] Expected failure behaviour:
  - Shared resolver rejects path-like inputs with clear, user-facing error text.
  - Shared resolver raises explicit errors for `legacy` exercises, unknown exercises, duplicate identities, and missing canonical files.
- [ ] Expected packaging/export behaviour:
  - No authoring metadata files appear in exported template workspaces.
  - No canonical `solution.ipynb` leaks into the exported student repository.
- [ ] Expected docs/workflow outcome:
  - Any new contributor note describes the shared resolver without claiming that the full repository layout migration is complete.
  - Workflows continue to pass without introducing hidden dependency on path-based compatibility.

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old path-based behaviour fails where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model where this phase intentionally changes them

## Risks, Ambiguities, And Blockers

This section is mandatory. Do not leave it out just because nothing is blocked yet.

### Known Risks

- [ ] Risk: Introducing a new shared package without planning how exported templates will import it could create a hidden packaging dependency before Phase 7 is ready.
- [ ] Risk: Updating any existing public grading helper too early could violate the action-plan rule that public interface breaking changes should wait until the replacement execution model is proven.
- [ ] Risk: Fixture-only proof of canonical resolution may be technically sufficient for Phase 2, but later phases could stall if no real pilot exercise is nominated soon afterwards.
- [ ] Risk: The current `scripts/verify_exercise_quality.py` logic still encodes the old `exercises/<construct>/<type>/<exercise_key>/` structure and could mislead future work if left untracked.

### Decisions

- [x] Decision: The shared package name for this phase is `exercise_metadata`.
- [x] Decision: Phase 2 should prove canonical behaviour with isolated fixtures and one live migrated pilot exercise.
- [x] Decision: The manifest lives at `exercises/migration_manifest.json`.
- [x] Decision: The shared resolver exposes explicit errors for invalid `exercise_key`, unknown exercise, legacy-only exercise, duplicate exercise identity, invalid metadata schema, and missing canonical files.

### Blockers

- [ ] Blocker: The current repository contains duplicate `ex006_sequence_modify_casting` exercise directories at `exercises/ex006_sequence_modify_casting/` and `exercises/sequence/modify/ex006_sequence_modify_casting/`; the nested `sequence/modify` path is canonical, and the root-level duplicate must be removed before identity is trusted.
- [ ] Blocker: The current repository contains mixed exercise directory shapes (`exercises/<exercise_key>/` and `exercises/<construct>/<type>/<exercise_key>/`) that do not match the target canonical layout `exercises/<construct>/<exercise_key>/`.
- [ ] Blocker: `ex007` has inconsistent identity strings — the canonical key is `ex007_sequence_debug_casting`, and the solution notebook stem, self-check code, expectation imports, and test targets must all be normalised to that key with `data_types` references removed.
- [ ] Blocker: No `exercise.json` files currently exist anywhere in the repository, so any live migrated exercise must be created deliberately rather than inferred.
- [ ] Blocker: `scripts/verify_exercise_quality.py` currently prefers the old construct/type/exercise directory layout, which conflicts with the target canonical design and must not become the accidental resolver model.
- [ ] Blocker: a live pilot exercise must be nominated from Phase 1 outputs before Phase 2 implementation starts; do not improvise the pilot during implementation.

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue:
  - Record the duplicate `ex006_sequence_modify_casting` identity across `exercises/ex006_sequence_modify_casting/` and `exercises/sequence/modify/ex006_sequence_modify_casting/`.
  - Record that no current live exercise directory matches the target canonical path `exercises/<construct>/<exercise_key>/`.
  - Record the `ex007_sequence_debug_casting` versus `ex007_data_types_debug_casting` naming mismatch as a blocker before choosing any pilot exercise.
- [ ] New affected surface:
  - Add `tests/helpers.py` to the high-level affected-surface list because it wraps notebook-path resolution.
  - Add `scripts/verify_exercise_quality.py` to the high-level affected-surface list because it already encodes the old exercise-directory shape.
- [ ] Incorrect assumption in current plan:
  - If the plan currently implies the inventory is already unambiguous, correct it. The current codebase still has duplicate and conflicting exercise identities.
- [ ] Missing acceptance criterion:
  - Add an explicit acceptance criterion if needed stating that the new shared resolver must ignore `PYTUTOR_NOTEBOOKS_DIR` entirely.
  - Add an explicit acceptance criterion if needed stating that fixture-only canonical proof is acceptable only if the live manifest records every real exercise as `legacy` until a real pilot is chosen.
- [ ] Missing migration stream:
  - If maintainers decide the `verify_exercise_quality.py` directory-shape migration deserves its own stream, add it to the action plan rather than hiding it inside another phase.

### Follow-Up Action

- [ ] Update [ACTION_PLAN.md](./ACTION_PLAN.md) before marking this checklist complete
- [ ] Cross-link this checklist from the relevant phase in [ACTION_PLAN.md](./ACTION_PLAN.md) if useful

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
- [ ] The implementation record says explicitly whether canonical behaviour was proved with a live pilot exercise, fixture-only repositories, or both

## Checklist Notes

- Current live notebook inventory remains legacy and split-brain:
  - student notebooks live under `notebooks/`
  - solution notebooks live under `notebooks/solutions/`
  - exercise-specific tests still live under top-level `tests/`
- Current live exercise-directory state is mixed:
  - `ex001` exists only in a root-level legacy directory under `exercises/`
  - `ex002` to `ex007` largely exist under the old construct/type/exercise shape
  - `ex006` exists in both legacy root-level and old construct/type paths
- No `exercise.json` files currently exist.
- The existing workflows still use `PYTUTOR_NOTEBOOKS_DIR` and should be treated as legacy execution surfaces until later phases.
- `tests/template_repo_cli` currently defines much of the packaging and selection contract around the old layout; keep those suites on the watchlist but avoid widening Phase 2 scope unless necessary.
- If implementation chooses a fixture-only proof strategy in Phase 2, record that explicitly in the final implementation notes so later agents do not mistake the live repository for already migrated content.
