# Phase 10 Migration Checklist — Docs, Agents, Workflows, And Contributor Guidance

## Required Migration Rules

These rules are restated from `ACTION_PLAN.md` and apply throughout Phase 10:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless `ACTION_PLAN.md` is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into `ACTION_PLAN.md`.

## Checklist Header

- Checklist title: `Phase 10 Migration Checklist — Docs, Agents, Workflows, And Contributor Guidance`
- Related action-plan phase or stream: `Phase 10: Docs, Agents, Workflows, And Contributor Guidance`
- Author: `Codex (Implementer Agent)`
- Date: `2026-03-12`
- Status: `ready`
- Scope summary: Align maintained contributor docs, teacher docs, agent instructions, repository workflows, template workflow guidance, and docs-backed tests with the migrated exercise-centric authoring structure and the settled resolver/execution/export contracts.
- Explicitly out of scope:
  - Moving notebooks, tests, or exercise folders as part of this checklist alone.
  - Implementing the resolver, execution-model, packaging, or registry migrations described in earlier phases.
  - Editing `ACTION_PLAN.md` as part of this planning task.
  - Editing `.ipynb` files directly.
  - Broad tidy-up of unrelated docs or workflows.

## Objective

When this checklist is complete, the repository should have one authoritative story for contributors and agents:

- the authoring repository’s canonical home for exercise-specific assets is under `exercises/`
- the agreed resolver contract is documented consistently as `exercise_key`-based
- contributor guidance clearly distinguishes the authoring repository from exported Classroom repositories
- repository and template workflows describe the same execution model that the code actually implements
- agent prompts no longer teach the legacy split layout as the canonical model
- transitional warnings are present wherever the migration is still incomplete

This phase is documentation and guidance cutover work, not a substitute for the earlier code migration phases.

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [ ] Required decisions from `ACTION_PLAN.md` are settled.
- [ ] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly.

Notes:

- Decisions relied on:
  - The post-migration canonical authoring path has been fixed and implemented enough to document confidently.
  - The replacement execution model for student versus solution verification has been defined.
  - The export contract for Classroom repositories has been defined and proven.
  - The agent cutover sequence has been chosen: update in place first, or replace then archive.
- Open assumptions:
  - The `sequence` construct remains the best pilot/example set because the live repo already contains `ex002` to `ex007` there.
  - Phase 10 should not invent a new manifest path, resolver API, or workflow contract; it should document whichever contract earlier phases settled.
  - If the `PYTUTOR_NOTEBOOKS_DIR` replacement is not ready, the docs must stay explicitly transitional rather than pretending the cutover is complete.

## Affected Surfaces Inventory

List every surface this migration unit touches. This inventory is based on the current repository state as verified on `2026-03-12`.

### Files And Paths To Update

- [ ] Source files:
  - `scripts/new_exercise.py` — review and update user-facing help text, generated README text, and printed output if the scaffold contract has already changed before Phase 10 lands.
  - `scripts/verify_exercise_quality.py` — review CLI help text and path-assumption messaging if canonical exercise paths are no longer `exercises/<construct>/<type>/<exercise_key>/`.
  - `scripts/build_autograde_payload.py` — review help text and environment guidance if the execution model no longer hinges on `PYTUTOR_NOTEBOOKS_DIR`.
  - `scripts/template_repo_cli/cli.py` — update command help or examples if CLI selection or export guidance changes.
  - `scripts/template_repo_cli/core/collector.py` — update only if its public contract or error messages still teach top-level notebook/test paths after earlier migration phases.
  - `scripts/template_repo_cli/core/selector.py` — update only if selection should no longer be notebook-name-first or type-folder-first.
  - `scripts/template_repo_cli/core/packager.py` — update comments/help/output only if export mapping text changes.
- [ ] Test files:
  - `tests/test_exercise_type_docs.py` — currently asserts content in `docs/exercise-types/*.md` and `.github/agents/exercise_generation.md.agent.md`; will need extension for new canonical guidance and migration warnings.
  - `tests/test_new_exercise.py` — update only if scaffolded README/help text or file-path messaging changes.
  - `tests/exercise_framework/test_paths.py` — update if Phase 10 lands after the path/execution contract changes.
  - `tests/test_build_autograde_payload.py` — update if workflow-facing environment or output messaging changes.
  - `tests/test_integration_autograding.py` — update if contributor and workflow guidance changes around student/solution execution.
  - `tests/template_repo_cli/test_packager.py` — ensure packaging still matches the documented metadata-free export contract.
  - `tests/template_repo_cli/test_integration.py` — ensure end-to-end template creation/update flows still match the documented contract.
  - `tests/template_repo_cli/test_selector.py` — update if selector guidance moves from notebook-pattern selection towards resolver-driven `exercise_key` selection.
  - `tests/template_repo_cli/test_collector.py` — update if collector inputs/outputs change.
  - `tests/template_repo_cli/test_filesystem.py` — update if notebook-path resolution examples are no longer valid.
  - `tests/template_repo_cli/test_validation.py` — update if validation rules for notebook patterns or selector inputs change.
- [ ] Docs:
  - `README.md` — repository overview, quick-start testing commands, workflow summary, and structure explanation.
  - `AGENTS.md` — repo structure, notebook/testing patterns, common commands, grading-system guidance.
  - `docs/project-structure.md` — canonical folder tree and path descriptions.
  - `docs/setup.md` — student/teacher setup, testing commands, development workflow, workflow descriptions, troubleshooting.
  - `docs/development.md` — repository architecture, grader workflow, generator workflow, CI/CD maintenance, troubleshooting.
  - `docs/exercise-generation.md` — exercise authoring workflow, verifier guidance, example paths.
  - `docs/exercise-generation-cli.md` — scaffold outputs, move/rename instructions, notebook/test examples.
  - `docs/testing-framework.md` — framework responsibilities, runtime helper examples, CI notes.
  - `docs/exercise-testing.md` — testing examples, runtime helper examples, environment variable guidance.
  - `docs/autograding-cli.md` — local dry-run commands, workflow excerpts, output interpretation.
  - `docs/github-classroom-autograding-guide.md` — `classroom.yml` guidance and workflow wiring.
  - `docs/CLI_README.md` — template CLI behaviour, exported file list, usage examples.
  - `docs/agents/tidy_code_review/automated_review.md` — reviewer workflow currently tells contributors to use `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
  - `docs/agents/tidy_code_review/manual_review.md` — reviewer guidance still refers to `tests/test_exNNN_*.py` and `PYTUTOR_NOTEBOOKS_DIR`.
- [ ] Workflows:
  - `.github/workflows/tests.yml` — currently runs pytest with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`; needs alignment with the final contributor/CI contract.
  - `.github/workflows/tests-solutions.yml` — currently duplicates the solution-run behaviour and needs an explicit role after cutover.
  - `.github/workflows/docker-build.yml` — review only if workflow listings or contributor docs describe it inaccurately after the Phase 10 rewrite.
- [ ] Agent instructions:
  - `.github/agents/exercise_generation.md.agent.md` — currently teaches `notebooks/` and `notebooks/solutions/` as the core model.
  - `.github/agents/exercise_verifier.md.agent.md` — currently expects notebook-path input and solution verification via `PYTUTOR_NOTEBOOKS_DIR`.
  - `.github/agents/implementer.md.agent.md` — update with migration warning/cross-links if the shared contributor contract changes materially.
  - `.github/agents/tidy_code_review.md.agent.md` — update scope descriptions and ensure linked reviewer docs follow the new contract.
- [ ] Template/export files:
  - `template_repo_files/.github/workflows/classroom.yml` — exported Classroom workflow must stay aligned with the documented export contract.
  - `template_repo_files/README.md.template` — review if exported README wording should distinguish student-facing export from authoring repo guidance.
  - `template_repo_files/pytest.ini` — review only if the documented test-discovery contract changes.
- [ ] Exercise directories:
  - `exercises/ex001_sanity/` — current root-level exercise directory; treat as a migration example/blocker, not a canonical layout example.
  - `exercises/ex006_sequence_modify_casting/` — duplicate legacy root-level copy; must not be shown as canonical in docs.
  - `exercises/sequence/modify/ex002_sequence_modify_basics/`
  - `exercises/sequence/modify/ex003_sequence_modify_variables/`
  - `exercises/sequence/modify/ex006_sequence_modify_casting/`
  - `exercises/sequence/debug/ex004_sequence_debug_syntax/`
  - `exercises/sequence/debug/ex005_sequence_debug_logic/`
  - `exercises/sequence/debug/ex007_sequence_debug_casting/`
  - `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` — stray construct-like directory discovered during checklist preparation; treat as a blocker until explained.
  - `notebooks/` and `notebooks/solutions/` — still present in the live repo and heavily referenced in current docs; Phase 10 must describe them correctly as either transitional authoring inputs or export-only surfaces, depending on the settled contract.

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
  - `tests.notebook_grader` — current notebook runtime helpers and path redirection.
  - `tests.exercise_framework.paths` — framework-level notebook path resolver.
  - `scripts.new_exercise` — scaffolding workflow and generated instructions.
  - `scripts.verify_exercise_quality` — teacher-verification workflow and exercise-directory inference.
  - `scripts.build_autograde_payload` — workflow-facing autograding wrapper.
  - `scripts.template_repo_cli.cli` — CLI commands exposed to contributors.
  - `scripts.template_repo_cli.core.collector` — exercise file collection.
  - `scripts.template_repo_cli.core.selector` — exercise selection rules.
  - `scripts.template_repo_cli.core.packager` — export packaging rules.
- [ ] Public functions or methods:
  - `tests.notebook_grader.resolve_notebook_path` — currently uses `PYTUTOR_NOTEBOOKS_DIR`; docs must only describe it in its post-migration form.
  - `tests.notebook_grader.extract_tagged_code` — current examples use top-level notebook paths and will need path examples updated.
  - `tests.notebook_grader.exec_tagged_code` — same as above.
  - `tests.exercise_framework.paths.resolve_notebook_path` — contributor docs and framework docs must match its final contract.
  - `scripts.new_exercise.main` — currently scaffolds into `exercises/exNNN_slug/`, `notebooks/`, `notebooks/solutions/`, and `tests/`.
  - `scripts.new_exercise._check_exercise_not_exists` — currently hard-codes old locations.
  - `scripts.new_exercise._build_readme_lines` — currently tells authors to open the matching notebook in `notebooks/`.
  - `scripts.verify_exercise_quality.main` — currently accepts a notebook path under `notebooks/` and infers `construct`/`type` from the old directory shape.
  - `scripts.verify_exercise_quality._find_exercise_dir` — currently expects `exercises/<construct>/<type>/<exercise_key>/`.
  - `scripts.verify_exercise_quality._infer_construct_and_type` — same assumption.
  - `scripts.verify_exercise_quality._check_order_of_teaching` — currently checks for notebook links such as `notebooks/<notebook_name>`.
  - `scripts.build_autograde_payload.validate_environment` — currently allows only `notebooks` or `notebooks/solutions`.
  - `scripts.build_autograde_payload._normalise_notebooks_dir` — tied to the same contract.
  - `scripts.build_autograde_payload._should_zero_scores_on_failure` — tied to student-versus-solution mode handling.
  - `scripts.template_repo_cli.cli.create_command` — contributor-facing template creation command.
  - `scripts.template_repo_cli.cli.update_repo_command` — contributor-facing repo update command.
  - `scripts.template_repo_cli.cli.list_command` — contributor-facing discovery command.
  - `scripts.template_repo_cli.cli.validate_command` — contributor-facing validation command.
  - `scripts.template_repo_cli.core.collector.FileCollector.collect_files` — currently collects `notebooks/<exercise>.ipynb` and `tests/test_<exercise>.py`.
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.get_all_notebooks` — currently scans the top-level `notebooks/` directory.
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_pattern` — currently validates notebook-name glob patterns rather than canonical resolver inputs.
  - `scripts.template_repo_cli.core.packager.TemplatePackager.copy_exercise_files` — currently flattens selected notebooks/tests into export paths.
- [ ] CLI commands or flags:
  - `uv run python scripts/new_exercise.py exNNN "Title" --slug slug --type <debug|modify|make>` — examples and output text must match the final canonical layout.
  - `uv run python scripts/verify_exercise_quality.py <notebook-path> --construct <construct> --type <type>` — update command examples only after the tool contract changes.
  - `uv run ./scripts/verify_solutions.sh` — update or retire once the replacement solution-verification model is settled.
  - `template_repo_cli list` — update examples if selection is no longer notebook-name driven.
  - `template_repo_cli validate` — same.
  - `template_repo_cli create` — update packaged-file examples and README wording.
  - `template_repo_cli update-repo` — update maintenance guidance if export behaviour changes.
  - `uv run python scripts/build_autograde_payload.py --pytest-args=... --output ... --summary ... --minimal` — docs/workflows must match the final wrapper contract.
- [ ] Environment variables:
  - `PYTUTOR_NOTEBOOKS_DIR` — currently the dominant contributor-facing switch in docs, tests, agents, and workflows; either document it as transitional or replace it consistently.
  - `GITHUB_OUTPUT` — used by the autograding CLI in workflow contexts; keep docs accurate if step outputs change.
  - `PYTEST_RESULTS` — set in the Classroom workflow for the grading reporter.
- [ ] Workflow jobs or steps:
  - `.github/workflows/tests.yml` → `pytest` job → `Run tests` step.
  - `.github/workflows/tests-solutions.yml` → `pytest_solutions` job → `Run tests against solution notebooks` step.
  - `template_repo_files/.github/workflows/classroom.yml` → `autograding` job → `Build autograde payload`, `Prepare reporter payload`, and `Report results to Classroom` steps.
- [ ] Packaging/export contracts:
  - Exported Classroom repositories stay metadata-free and must not ship `exercise.json` or the full authoring `exercises/` tree.
  - Template exports must continue to contain the exact workflow/runtime files the docs promise.
  - Contributor docs must distinguish authoring paths from exported paths instead of conflating them.
- [ ] Notebook self-check contracts:
  - The generated check-answers cell produced by `scripts.new_exercise._make_check_answers_cell` currently points at `notebooks/<exercise_key>.ipynb`; docs and agent guidance must not contradict the actual self-check path contract.

### Current Assumptions Being Removed

- [ ] Assumption 1: The canonical authoring home for exercise-specific content is the legacy split layout across `exercises/`, `notebooks/`, and top-level `tests/`.
- [ ] Assumption 2: Contributor guidance should always tell people to verify solutions with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
- [ ] Assumption 3: New exercises begin in `exercises/exNNN_slug/` and are then moved manually into `exercises/CONSTRUCT/TYPE/exNNN_slug/`.
- [ ] Assumption 4: Agent inputs should be notebook-path-first rather than `exercise_key`-first.
- [ ] Assumption 5: It is acceptable for docs to blur the authoring repository contract and the exported Classroom repository contract.

## Implementation Tasks

Break work into concrete tasks. Group by concern, not by person.

### Code Changes

- [ ] Add:
  - Add docs-consistency tests that guard against reintroducing legacy canonical-layout wording once the cutover lands.
  - Add agent-consistency tests that verify all maintained agent specs carry the same resolver/execution guidance and any required migration warning block.
  - Add workflow-consistency tests that parse or inspect `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml`, and `template_repo_files/.github/workflows/classroom.yml` against the documented contract.
- [ ] Update:
  - Update help text, examples, and generated strings in `scripts/new_exercise.py` only if earlier phases have already changed its contract.
  - Update help text in `scripts/verify_exercise_quality.py` only if earlier phases have changed canonical exercise paths and verifier inputs.
  - Update help/output wording in `scripts/build_autograde_payload.py` and `scripts/template_repo_cli` only if the documented workflow contract has changed.
  - Update every in-scope Markdown document and agent spec listed above.
  - Update workflow YAML comments, step names, and environment handling where the workflow itself still encodes legacy guidance.
- [ ] Remove:
  - Remove statements that describe top-level `notebooks/` and `tests/test_exNNN_*.py` as the canonical authoring model.
  - Remove instructions that tell contributors to move scaffolded folders into `exercises/CONSTRUCT/TYPE/` once the scaffolder no longer requires it.
  - Remove stale examples that still pass notebook paths as the primary exercise identity when the resolver contract has moved to `exercise_key`.
- [ ] Rename or relocate:
  - Archive superseded `.github/agents/*.agent.md` files with a suffix such as `.old` only after replacement guidance exists, every reference has been updated, and the new files are confirmed authoritative.
  - Do not archive agent files during the same change that merely adds transitional warnings.
- [ ] Fail-fast behaviour to add:
  - Add tests that fail if any maintained contributor doc still claims the old split layout is canonical.
  - Add tests that fail if the agent files disagree on the canonical resolver input.
  - Add tests that fail if the workflow docs and workflow YAML disagree about student-versus-solution execution.

### Data And Metadata Changes

- [ ] `exercise.json` changes:
  - No schema expansion is expected in Phase 10.
  - Update docs only to reflect the minimal metadata fields already agreed earlier.
- [ ] Derived-data/index changes:
  - Document the chosen metadata-derived index/manifest only if it already exists from an earlier phase.
  - Do not create a new index format as part of Phase 10 documentation work.
- [ ] Registry replacement work:
  - Update docs to stop telling contributors to maintain any hard-coded exercise registry that earlier phases have already removed.
- [ ] Migration manifest updates:
  - If a migration manifest exists by Phase 10, document exactly when contributors must update it.
  - If no manifest exists but the docs cannot explain layout state cleanly without one, record that as a blocker in `ACTION_PLAN.md` before marking Phase 10 complete.

### Test Changes

List both existing tests to update and new tests to add.

- [ ] Update existing unit tests:
  - `tests/test_exercise_type_docs.py` — broaden coverage from exercise-type guides to canonical-layout and agent-warning expectations.
  - `tests/test_new_exercise.py` — adjust only if generated README/help text changes.
  - `tests/template_repo_cli/test_selector.py` — adjust if selection UX changes away from notebook/glob-first language.
  - `tests/template_repo_cli/test_filesystem.py` — adjust only if notebook-path resolution examples are no longer part of the public contract.
  - `tests/exercise_framework/test_paths.py` — adjust if the path-resolution contract changes.
- [ ] Update integration tests:
  - `tests/test_build_autograde_payload.py` — align expected environment validation and printed messages with the settled workflow contract.
  - `tests/test_integration_autograding.py` — align end-to-end expectations for student versus solution modes.
  - `tests/template_repo_cli/test_integration.py` — ensure template creation/update still matches the newly documented contract.
- [ ] Update packaging/template tests:
  - `tests/template_repo_cli/test_packager.py` — verify exported contents and workflow files still match the documented metadata-free export contract.
  - `tests/template_repo_cli/test_collector.py` — update only if file collection semantics change.
  - `tests/template_repo_cli/test_validation.py` — update only if validation rules change.
- [ ] Update workflow-related tests:
  - Add new tests for `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml`, and `template_repo_files/.github/workflows/classroom.yml` because the repo currently has no dedicated workflow-consistency test surface.
- [ ] Remove obsolete tests:
  - Remove or rewrite assertions that hard-code legacy contributor guidance, such as “move the exercise folder into `exercises/sequence/modify/`” or “solution verification always uses `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`”, but only after replacement assertions are in place.

### New Test Cases Required

Every checklist should spell out the behaviour that must be proved, not just the files to edit.

- [ ] Positive case:
  - Maintained contributor docs (`README.md`, `AGENTS.md`, `docs/project-structure.md`, `docs/setup.md`, `docs/development.md`) all describe the same canonical authoring structure and the same resolver/execution contract.
- [ ] Failure case:
  - A docs-consistency test fails if any maintained doc still says the legacy split layout is the canonical authoring model after cutover.
- [ ] Regression case:
  - All four `.github/agents/*.agent.md` files either contain the same migration warning block plus `ACTION_PLAN.md` cross-link, or all four have fully cut over to the replacement guidance with no stale legacy references.
- [ ] Export/package case:
  - `template_repo_files/.github/workflows/classroom.yml` and `tests/template_repo_cli/test_packager.py` prove that exported repos remain metadata-free and that the docs do not claim otherwise.
- [ ] Student-mode case:
  - Classroom-facing docs and workflow snippets describe the student execution path that the template export actually uses.
- [ ] Solution-mode case:
  - Contributor-facing docs and workflows describe the solution verification path that the repository actually uses after the execution-model cutover.
- [ ] Additional explicit cases to add:
  - The docs no longer tell contributors to move `exercises/exNNN_slug/` into `exercises/CONSTRUCT/TYPE/exNNN_slug/` unless the scaffold still genuinely requires that move.
  - The docs no longer present notebook-path input as the canonical resolver interface if the codebase has migrated to `exercise_key` input.
  - The workflow docs explain the difference between authoring-repo paths and exported Classroom-repo paths.
  - Any retained reference to `PYTUTOR_NOTEBOOKS_DIR` is explicitly marked transitional and confined to surfaces that still truly depend on it.

### Docs, Agents, And Workflow Updates

- [ ] Contributor docs:
  - Rewrite the repository tree and quick-start sections in `README.md`.
  - Rewrite `docs/project-structure.md` to show the post-migration canonical tree rather than the live mixed legacy tree.
  - Rewrite `docs/setup.md` and `docs/development.md` commands and troubleshooting sections to match the final execution model.
  - Update `docs/CLI_README.md` so template CLI examples describe the correct source and export contracts.
- [ ] Teaching docs:
  - Update `docs/exercise-generation.md` and `docs/exercise-generation-cli.md` to match the post-migration scaffold and verification workflow.
  - Update any examples that name current live exercises such as `ex002_sequence_modify_basics` or `ex006_sequence_modify_casting` so they use the correct canonical paths.
  - Update `docs/testing-framework.md` and `docs/exercise-testing.md` helper examples so they no longer hard-code stale notebook paths or stale environment-variable guidance.
- [ ] Agent docs:
  - Update `AGENTS.md` first because it is the shared contributor contract for Codex/Copilot-style work.
  - Update `.github/agents/exercise_generation.md.agent.md` and `.github/agents/exercise_verifier.md.agent.md` so they request/accept the right exercise identity and canonical file locations.
  - Update `.github/agents/implementer.md.agent.md` and `.github/agents/tidy_code_review.md.agent.md` with migration warnings and cross-links where needed.
  - Update `docs/agents/tidy_code_review/automated_review.md` and `docs/agents/tidy_code_review/manual_review.md` so the linked reviewer workflow does not reintroduce stale path guidance.
- [ ] Repository workflows:
  - Decide whether `.github/workflows/tests.yml` remains the primary CI workflow, becomes student-mode, or remains solution-mode only.
  - Decide whether `.github/workflows/tests-solutions.yml` stays as a separate manual workflow, becomes redundant, or needs renaming.
  - Update workflow comments and job names so contributors can understand the difference without reading the YAML twice.
- [ ] Template workflows:
  - Update `template_repo_files/.github/workflows/classroom.yml` comments and any env wiring so it matches the final Classroom export contract.
  - Ensure docs referencing `classroom.yml` match the actual file contents exactly.
- [ ] CLI examples:
  - Update commands in `README.md`, `docs/setup.md`, `docs/development.md`, `docs/exercise-generation.md`, `docs/exercise-generation-cli.md`, `docs/autograding-cli.md`, and `docs/CLI_README.md`.
  - Remove examples that depend on stale mixed-layout quirks discovered in the current repo.

## Verification Plan

State exactly how this migration unit will be verified.

### Commands To Run

- [ ] Command:

```bash
source .venv/bin/activate
```

- [ ] Command:

```bash
rg -n "PYTUTOR_NOTEBOOKS_DIR|notebooks/solutions|exercises/CONSTRUCT/TYPE|move .*exercises/.*/modify|tests/test_exNNN|legacy split layout" README.md docs AGENTS.md .github/agents docs/agents
```

- [ ] Command:

```bash
uv run pytest tests/test_exercise_type_docs.py -q
```

- [ ] Command:

```bash
uv run pytest tests/test_new_exercise.py tests/template_repo_cli/test_packager.py tests/template_repo_cli/test_integration.py -q
```

- [ ] Command:

```bash
uv run pytest tests/test_build_autograde_payload.py tests/test_integration_autograding.py tests/exercise_framework/test_paths.py -q
```

- [ ] Command:

```bash
uv run pytest -q
```

Only include broader commands after the focused tests pass.

### Expected Results

- [ ] Expected passing behaviour:
  - The updated docs/agents/workflows all describe the same canonical authoring and export contracts.
  - All updated and new tests pass.
- [ ] Expected failure behaviour:
  - Docs/agent/workflow consistency tests fail if legacy canonical-layout wording or stale environment guidance is reintroduced.
- [ ] Expected packaging/export behaviour:
  - Template exports remain metadata-free and continue to include the workflow/runtime files the docs promise.
- [ ] Expected docs/workflow outcome:
  - A contributor reading `README.md`, `AGENTS.md`, `docs/setup.md`, and `.github/workflows/tests.yml` receives one coherent story rather than mixed legacy assumptions.

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old canonical-layout wording is gone where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model
- [ ] Explicit proof that every maintained agent file either contains the agreed migration warning or has fully cut over to the new contract

## Risks, Ambiguities, And Blockers

This section is mandatory. Do not leave it out just because nothing is blocked yet.

### Known Risks

- [ ] Risk: Docs are updated before the code migration lands, leaving contributors with instructions that do not match the executable repository.
- [ ] Risk: Transitional warnings get added but never removed, leaving the repo in a permanently ambiguous state.
- [ ] Risk: Authoring-repo guidance and exported-Classroom guidance are conflated again during review.
- [ ] Risk: Workflow names remain misleading even if commands are corrected.

### Open Questions

- [x] Decision: contributor-facing commands should use the final explicit `variant` CLI flag rather than `PYTUTOR_NOTEBOOKS_DIR`.
- [x] Decision: the final canonical authoring path is `exercises/<construct>/<exercise_key>/`, with no retained `type/` path segment.
- [x] Decision: docs for exported repositories should continue to show flattened exercise-key notebook names rather than `student.ipynb` and `solution.ipynb`.
- [x] Decision: repo workflows should validate the authoring-repository contract, while the exported Classroom workflow validates the metadata-free student export contract.
- [x] Decision: current `.github/agents/*.agent.md` files should only be archived after replacement guidance exists and references have been switched.

### Blockers

- [ ] Blocker: The live repo still contains mixed exercise layouts, including `exercises/ex001_sanity/`, `exercises/ex006_sequence_modify_casting/`, and nested `exercises/sequence/...` exercise folders, so docs cannot honestly present the migration as complete without calling out the transitional state.
- [ ] Blocker: `.github/workflows/tests.yml` and `.github/workflows/tests-solutions.yml` currently both run solution-mode tests with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`, so the intended workflow split is unclear.
- [ ] Blocker: `notebooks/solutions/ex007_data_types_debug_casting.ipynb` does not match `tests/test_ex007_sequence_debug_casting.py` or `exercises/sequence/debug/ex007_sequence_debug_casting/`, which is a concrete naming mismatch that could leak into docs/examples if not resolved.
- [ ] Blocker: `scripts/new_exercise.py` and `scripts/verify_exercise_quality.py` still encode legacy path assumptions, so documentation cannot fully cut over until the earlier implementation phases land.
- [ ] Blocker: `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` appears to be a stray construct-like directory and should be explained or removed by an earlier phase before final structure docs are declared authoritative.

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue:
  - Phase 10 depends on earlier resolution of mixed-layout reality in the live repo; the duplicate `ex006` directories, root-level `ex001`, and stray `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` should be tracked explicitly if they are not already.
- [ ] New affected surface:
  - `docs/CLI_README.md`
  - `docs/agents/tidy_code_review/automated_review.md`
  - `docs/agents/tidy_code_review/manual_review.md`
  - `template_repo_files/README.md.template`
- [ ] Incorrect assumption in current plan:
  - The plan currently treats repository workflow updates at a high level, but the live repo already has two solution-mode workflows (`tests.yml` and `tests-solutions.yml`) whose overlap should be called out explicitly.
- [ ] Missing acceptance criterion:
  - Phase 10 should require automated tests that guard docs/agent/workflow consistency, not just manual review.
- [ ] Missing migration stream:
  - Add a small “docs/workflow consistency guardrails” stream if the existing phases do not already cover new regression tests for docs and agent prompts.

### Follow-Up Action

- [ ] Update `ACTION_PLAN.md` before marking this checklist complete
- [ ] Cross-link this checklist from the relevant phase in `ACTION_PLAN.md` if useful
- [ ] Feed every newly discovered blocker or gap from implementation back into `ACTION_PLAN.md`; do not treat this checklist as complete until that feedback loop has happened

## Completion Criteria

Do not mark the checklist complete until all of the following are true.

- [ ] In-scope code changes are complete
- [ ] In-scope tests are updated
- [ ] New required test cases are added
- [ ] Verification commands have been run or explicitly deferred with a reason
- [ ] Docs/agents/workflows in scope are updated
- [ ] Known blockers and risks are recorded
- [ ] New action-plan feedback has been folded into `ACTION_PLAN.md`, or confirmed unnecessary
- [ ] The checklist states clearly what remains for later phases

## Checklist Notes

- This checklist was prepared by reviewing `MIGRATION_CHECKLIST_TEMPLATE.md`, `ACTION_PLAN.md`, the current docs, the current agent files, the repository workflows, the template workflow, and the current test/code surfaces that those docs describe.
- This planning task intentionally did not edit `ACTION_PLAN.md`; future implementation work must still push newly discovered blockers and sequencing problems back into it.
- The current repo state is visibly transitional. Phase 10 should therefore be treated as a cutover-and-guardrails phase, not as a prose-only tidy-up.
- Where a code contract is still unsettled, prefer explicit transitional wording plus an `ACTION_PLAN.md` update over speculative documentation.
