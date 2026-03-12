# Phase 11 Migration Checklist — Validation, Cutover, And Cleanup

Use this checklist for the final migration phase that proves the new canonical exercise model works end to end, cuts the repository over to that model, and removes the remaining legacy top-level exercise-specific sources.

This checklist has been prepared against the current repository state on `2026-03-12`.

## Required Migration Rules

These rules come from [ACTION_PLAN.md](./ACTION_PLAN.md) and remain mandatory during Phase 11:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless [ACTION_PLAN.md](./ACTION_PLAN.md) is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into [ACTION_PLAN.md](./ACTION_PLAN.md).

## Checklist Header

- Checklist title: `Phase 11 Migration Checklist — Validation, Cutover, And Cleanup`
- Related action-plan phase or stream: `Phase 11: Validation, Cutover, And Cleanup`
- Author: `OpenAI Codex`
- Date: `2026-03-12`
- Status: `draft`
- Scope summary: Final repository-wide validation of the canonical `exercise_key` model, final cutover of runtime/workflow/template selection to the agreed post-migration contract, and removal or repurposing of legacy top-level exercise-specific notebooks and tests once they are no longer sources of truth.
- Explicitly out of scope: Designing the canonical resolver, inventing the final variant-selection mechanism, migrating individual exercises for the first time, editing notebooks by hand, or changing [ACTION_PLAN.md](./ACTION_PLAN.md) as part of this planning task.

## Objective

When this checklist is complete:

- The repository validates the migrated exercise layout in both repository mode and packaged-template mode using the final execution contract.
- The final variant-selection mechanism has replaced the transitional `PYTUTOR_NOTEBOOKS_DIR` contract everywhere it was only intended as an interim implementation detail.
- The CLI `--variant <student|solution>` flag is listed in the validation commands and workflows as the sole literal for selecting student versus solution runs so that cutover proofs use the same syntax every time.
- Packaging and autograding are proven to export the correct flattened Classroom structure from canonical authoring sources under `exercises/`.
- Repository workflows, template workflows, docs, and agent guidance all describe the same canonical model.
- The old top-level exercise-specific notebooks under `notebooks/` and top-level exercise-specific tests under `tests/test_ex*.py` (for example `tests/test_ex002_sequence_modify_basics.py`) are deleted or repurposed only after their canonical nested counterparts (such as `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`) prove the new discovery contract.

Old assumptions that should no longer exist:

- Top-level `notebooks/*.ipynb` files are the authoritative authoring source.
- Top-level `tests/test_ex*.py` files are the authoritative exercise-test source.
- Resolver inputs may be notebook paths, test paths, or filenames as a permanent public contract.
- `PYTUTOR_NOTEBOOKS_DIR` is the long-term way to switch between student and solution variants.

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [ ] Required decisions from [ACTION_PLAN.md](./ACTION_PLAN.md) are settled.
- [ ] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly (Phase 2 live pilot = `ex004_sequence_debug_syntax`).

Notes:

- Decisions relied on:
  - Phase 2 has defined the canonical resolver and the agreed migration manifest/registry location.
  - Phase 4 has defined the replacement execution model and the final source-to-export mapping.
  - Phase 8 has defined the public cutover point and the final variant-selection mechanism.
  - Phase 9 has migrated every in-scope exercise to the canonical layout.
  - Phase 10 has already updated maintained docs, workflows, and agent guidance.
- Open assumptions:
  - Exported Classroom repositories still flatten exercise outputs to top-level `notebooks/` and `tests/` paths even though authoring moves under `exercises/`.
  - `ex001_sanity` is obsolete, reserved for removal, and must be deleted before the final canonical validation set is defined.
  - The canonical exercise set to validate after that removal is: `ex002_sequence_modify_basics`, `ex003_sequence_modify_variables`, `ex004_sequence_debug_syntax` (the Phase 2 pilot), `ex005_sequence_debug_logic`, `ex006_sequence_modify_casting`, and `ex007_sequence_debug_casting`.
  - Resolving duplicate test surfaces for exercises such as `ex002_sequence_modify_basics` (the nested `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` file versus the legacy `tests/test_ex002_sequence_modify_basics.py`) is part of proving this canonical set before discovery cutover.

## Affected Surfaces Inventory

List every surface this migration unit touches. This section is intentionally explicit so the final implementation agent can work from a checked inventory rather than inference.

### Files And Paths To Update

- [ ] Source files:
  - `tests/notebook_grader.py` — current `resolve_notebook_path()` redirects through `PYTUTOR_NOTEBOOKS_DIR` and still accepts non-`notebooks/` inputs via filename fallback.
  - `tests/exercise_framework/paths.py` — mirrors the legacy path-override behaviour and must align with the final resolver contract.
  - `tests/exercise_framework/runtime.py` — wraps `tests.notebook_grader` and must stop exposing legacy path semantics once cutover is complete.
  - `tests/helpers.py` — `build_autograde_env()` currently defaults `PYTUTOR_NOTEBOOKS_DIR` to `notebooks`; update once the final selector exists.
  - `tests/student_checker/api.py` — hard-coded slug registry and `_NOTEBOOK_ORDER` must match canonical `exercise_key` values exactly.
  - `tests/student_checker/notebook_runtime.py` — notebook self-check runtime must use the final source/execution contract, not ad hoc notebook paths.
  - `scripts/build_autograde_payload.py` — `validate_environment()` currently only accepts `notebooks` and `notebooks/solutions`; this must change at final cutover.
  - `scripts/template_repo_cli/core/collector.py` — still collects source material from top-level `notebooks/` and `tests/`.
  - `scripts/template_repo_cli/core/selector.py` — still discovers exercises by scanning `notebooks/*.ipynb` and uses notebook-name selection as a primary interface.
  - `scripts/template_repo_cli/core/packager.py` — still copies `notebooks/<exercise_id>.ipynb` and `tests/test_<exercise_id>.py` from legacy top-level sources.
  - `scripts/template_repo_cli/utils/filesystem.py` — `resolve_notebook_path()` still assumes a top-level `notebooks/` authoring location.
  - `scripts/template_repo_cli/cli.py` — `create`, `validate`, `list`, and `update-repo` flows must reflect the final canonical source model.
  - `pyproject.toml` — repository pytest and console entrypoint expectations must match the post-cutover layout.
  - `pytest.ini` — duplicated pytest config must match the post-cutover discovery rules.
- [ ] Test files:
  - `tests/exercise_framework/test_runtime.py` — parity checks currently compare helpers under the old path model.
  - `tests/exercise_framework/test_api_contract.py` — API contract tests assume current notebook selection behaviour.
  - `tests/exercise_framework/test_autograde_parity.py` — autograde parity currently uses `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
  - `tests/exercise_framework/test_parity_paths.py` — explicitly tests current override/fallback path semantics.
  - `tests/student_checker/test_notebook_runtime.py` — exercises runtime selection and interactive execution assumptions.
  - `tests/template_repo_cli/test_selector.py` — asserts notebook discovery from the current top-level layout.
  - `tests/template_repo_cli/test_collector.py` — asserts collection from the current top-level `notebooks/` and `tests/` layout.
  - `tests/template_repo_cli/test_packager.py` — validates the current packaging contract and the current packaged workspace smoke test.
  - `tests/template_repo_cli/test_integration.py` — exercises end-to-end CLI behaviour and workspace validation.
  - `tests/test_build_autograde_payload.py` — explicitly validates `PYTUTOR_NOTEBOOKS_DIR` handling.
  - `tests/test_integration_autograding.py` — verifies the end-to-end autograding flow.
  - `tests/test_autograde_plugin.py` — plugin-facing contract must remain valid after cutover.
  - `tests/test_ex002_sequence_modify_basics.py`
  - `tests/test_ex003_sequence_modify_variables.py`
  - `tests/test_ex004_sequence_debug_syntax.py`
  - `tests/test_ex005_sequence_debug_logic.py`
  - `tests/test_ex006_sequence_modify_casting.py`
  - `tests/test_ex007_construct_checks.py`
  - `tests/test_ex007_sequence_debug_casting.py` — legacy top-level exercise-specific tests that should be removed or relocated only after equivalent canonical coverage exists and is proven.
- [ ] Docs:
  - `README.md`
  - `AGENTS.md`
  - `docs/project-structure.md`
  - `docs/setup.md`
  - `docs/testing-framework.md`
  - `docs/exercise-testing.md`
  - `docs/autograding-cli.md`
  - `docs/development.md`
  - `docs/github-classroom-autograding-guide.md`
  - `docs/exercise-generation.md`
  - `docs/exercise-generation-cli.md`
  - `docs/CLI_README.md`
  - `docs/agents/tidy_code_review/automated_review.md`
  - `docs/agents/tidy_code_review/manual_review.md`
- [ ] Workflows:
  - `.github/workflows/tests.yml` — currently runs repository tests with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
  - `.github/workflows/tests-solutions.yml` — duplicate solution-mode workflow that also depends on `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`.
  - `template_repo_files/.github/workflows/classroom.yml` — exported template workflow currently sets `PYTUTOR_NOTEBOOKS_DIR: notebooks` before running `scripts/build_autograde_payload.py`.
- [ ] Agent instructions:
  - `.github/agents/exercise_generation.md.agent.md`
  - `.github/agents/exercise_verifier.md.agent.md`
  - `.github/agents/implementer.md.agent.md`
  - `.github/agents/tidy_code_review.md.agent.md`
- [ ] Template/export files:
  - `template_repo_files/README.md.template`
  - `template_repo_files/pyproject.toml`
  - `template_repo_files/pytest.ini`
  - `template_repo_files/.github/workflows/classroom.yml`
- [ ] Exercise directories:
  - `exercises/sequence/modify/ex002_sequence_modify_basics/`
  - `exercises/sequence/modify/ex003_sequence_modify_variables/`
  - `exercises/sequence/modify/ex006_sequence_modify_casting/`
  - `exercises/sequence/debug/ex004_sequence_debug_syntax/`
  - `exercises/sequence/debug/ex005_sequence_debug_logic/`
  - `exercises/sequence/debug/ex007_sequence_debug_casting/`
  - `exercises/ex001_sanity/` — obsolete directory that is explicitly reserved for removal; it must be removed before the final cutover proceeds.
  - `exercises/ex006_sequence_modify_casting/` — duplicate or partially migrated home that must not survive into final cutover unnoticed.
  - `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` — placeholder path that may need repurposing or removal once verifier expectations are updated.
  - `notebooks/` — current legacy top-level student notebook source location.
  - `notebooks/solutions/` — current legacy top-level solution mirror location.

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
  - `tests.notebook_grader` — path resolution, tagged-cell execution, notebook explanation lookup.
  - `tests.exercise_framework.paths`
  - `tests.exercise_framework.runtime`
  - `tests.student_checker.api`
  - `tests.student_checker.notebook_runtime`
  - `tests.helpers`
  - `scripts.build_autograde_payload`
  - `scripts.template_repo_cli.cli`
  - `scripts.template_repo_cli.core.collector`
  - `scripts.template_repo_cli.core.selector`
  - `scripts.template_repo_cli.core.packager`
  - `scripts.template_repo_cli.utils.filesystem`
- [ ] Public functions or methods:
  - `tests.notebook_grader.resolve_notebook_path()` — current behaviour: redirect by environment variable, with filename fallback; required change: use the final resolver/variant contract only.
  - `tests.notebook_grader.extract_tagged_code()` — required change: continue to work after cutover without relying on legacy notebook source paths.
  - `tests.notebook_grader.exec_tagged_code()` — same requirement as above.
  - `tests.notebook_grader.run_cell_and_capture_output()`
  - `tests.notebook_grader.run_cell_with_input()`
  - `tests.notebook_grader.get_explanation_cell()`
  - `tests.exercise_framework.paths.resolve_notebook_path()` — must stop mirroring deprecated override behaviour once cutover is final.
  - `tests.exercise_framework.runtime.resolve_notebook_path()`
  - `tests.exercise_framework.runtime.extract_tagged_code()`
  - `tests.exercise_framework.runtime.exec_tagged_code()`
  - `tests.student_checker.api.check_exercises()` — must enumerate exercises from the canonical source of truth.
  - `tests.student_checker.api.check_notebook()` — must fail clearly for obsolete or mismatched slugs.
  - `tests.student_checker.notebook_runtime.run_notebook_checks()` — must work with the final selector and exported paths.
  - `tests.helpers.build_autograde_env()` — must no longer smuggle in obsolete defaults once cutover is complete.
  - `scripts.build_autograde_payload.validate_environment()` — must validate the final selector instead of the transitional `PYTUTOR_NOTEBOOKS_DIR` contract.
  - `scripts.build_autograde_payload.run_pytest()` and `scripts.build_autograde_payload.main()` — must continue to produce correct payloads for both student and solution runs after cutover.
  - `scripts.template_repo_cli.core.collector.FileCollector.collect_files()` — must collect from canonical authoring paths, not top-level authoring paths.
  - `scripts.template_repo_cli.core.collector.FileCollector.collect_multiple()`
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.get_all_notebooks()` — likely rename or repurpose if selection becomes `exercise_key` based.
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_notebooks()` — must not remain a hidden compatibility path if public cutover has moved to `exercise_key`.
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_pattern()`
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_construct()`
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_type()`
  - `scripts.template_repo_cli.core.selector.ExerciseSelector.select_by_construct_and_type()`
  - `scripts.template_repo_cli.core.packager.TemplatePackager.copy_exercise_files()` — currently copies from the legacy top-level source locations.
  - `scripts.template_repo_cli.core.packager.TemplatePackager.copy_template_base_files()`
  - `scripts.template_repo_cli.core.packager.TemplatePackager.validate_package()`
  - `scripts.template_repo_cli.cli.create_command()`
  - `scripts.template_repo_cli.cli.validate_command()`
  - `scripts.template_repo_cli.cli.list_command()`
  - `scripts.template_repo_cli.cli.update_repo_command()`
- [ ] CLI commands or flags:
  - `python -m scripts.template_repo_cli create --construct ... --type ... --notebooks ... --repo-name ... [--dry-run] [--output-dir ...] [--template-repo ...]`
  - `python -m scripts.template_repo_cli validate --construct ... --type ... --notebooks ...`
  - `python -m scripts.template_repo_cli list --construct ... --type ... --format ...`
  - `python -m scripts.template_repo_cli update-repo --repo-name ...`
  - `python scripts/build_autograde_payload.py --pytest-args ... --output ... --summary ... --minimal`
  - `--variant <student|solution>` — verify the final validation commands and workflow steps all pass this literal flag to the resolver and that any other values are rejected before final cutover.
- [ ] Environment variables:
  - `PYTUTOR_NOTEBOOKS_DIR` — transitional and currently widely used; Phase 11 should remove it from the canonical public contract rather than preserving it conditionally.
  - `PYTHONPATH` — injected by `tests.helpers.build_autograde_env()` for autograding helper runs.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD` — part of the current autograde test harness.
- [ ] Workflow jobs or steps:
  - `pytest` job in `.github/workflows/tests.yml`
  - `pytest_solutions` job in `.github/workflows/tests-solutions.yml`
  - `autograding` job in `template_repo_files/.github/workflows/classroom.yml`
  - `Build autograde payload` step in `template_repo_files/.github/workflows/classroom.yml`
- [ ] Packaging/export contracts:
  - Exported repositories remain metadata-free.
  - Exported repositories include the grading support files under `tests/` plus `scripts/build_autograde_payload.py`.
  - Exported repositories still present flattened Classroom-facing paths even when source authoring is exercise-local.
- [ ] Notebook self-check contracts:
  - `check_notebook('<slug>')` calls embedded in notebooks must use the canonical `exercise_key` exactly.
  - Notebook self-check helpers must not reference obsolete notebook stems after cutover.

### Current Assumptions Being Removed

- [ ] Assumption 1: Top-level `notebooks/` and `notebooks/solutions/` are the permanent source of truth for authoring and validation.
- [ ] Assumption 2: Top-level exercise-specific tests under `tests/test_ex*.py` are the permanent home for exercise tests.
- [ ] Assumption 3: Path-based notebook selection and filename fallback are acceptable long-term resolver inputs.
- [ ] Assumption 4: Template packaging may discover exercises by scanning top-level notebooks rather than canonical exercise metadata or resolver-backed inventories.
- [ ] Assumption 5: Docs and workflows may continue to teach `PYTUTOR_NOTEBOOKS_DIR` as the canonical variant switch.

## Implementation Tasks

Break this phase into explicit validation, cutover, and cleanup work. Keep the order deliberate so cleanup never happens before proof.

### Code Changes

- [ ] Add: a documented validation matrix command set that future agents can run repeatedly during cutover.
- [ ] Update: `tests/notebook_grader.py`, `tests/exercise_framework/paths.py`, `tests/exercise_framework/runtime.py`, `tests/helpers.py`, and `scripts/build_autograde_payload.py` to use the final selector contract and fail clearly on obsolete path-based inputs.
- [ ] Update: `scripts/template_repo_cli/core/collector.py`, `scripts/template_repo_cli/core/selector.py`, and `scripts/template_repo_cli/core/packager.py` so packaging and selection use canonical authoring sources under `exercises/`.
- [ ] Update: `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml`, and `template_repo_files/.github/workflows/classroom.yml` to use the final variant-selection mechanism and final source-to-export contract.
- [ ] Update: notebook self-check entry points in `tests/student_checker/api.py` and `tests/student_checker/notebook_runtime.py` so they validate canonical identities consistently.
- [ ] Remove: any remaining top-level source lookup logic that treats `notebooks/<exercise>.ipynb` or `tests/test_<exercise>.py` as authoritative inputs.
- [ ] Remove: transitional env-var validation that hard-codes `PYTUTOR_NOTEBOOKS_DIR` to `notebooks` or `notebooks/solutions`.
- [ ] Rename or relocate: any legacy exercise-specific tests moved under exercise-local test directories, once pytest discovery is already proven.
- [ ] Rename or relocate: top-level notebook mirrors only if they still serve a clearly documented export fixture purpose; otherwise delete them after validation.
- [ ] Fail-fast behaviour to add: explicit errors when callers pass legacy notebook paths, legacy test paths, or mismatched slugs instead of canonical `exercise_key` inputs.

### Data And Metadata Changes

- [ ] `exercise.json` changes: none beyond verifying that the agreed minimal schema is sufficient; do not expand metadata in Phase 11 just to paper over unresolved path conventions.
- [ ] Derived-data/index changes: ensure any runtime index or derived registry introduced earlier reflects that all exercises are now canonical and none remain in a legacy state.
- [ ] Registry replacement work: remove or update hard-coded registries that still point at legacy paths, especially `_NOTEBOOK_ORDER` in `tests/student_checker/api.py` and any legacy notebook-name inventories in `scripts/template_repo_cli/core/selector.py`.
- [ ] Migration manifest updates: set every exercise to its final post-migration state in `exercises/migration_manifest.json`.

### Test Changes

List both existing tests to update and new tests to add.

- [ ] Update existing unit tests:
  - `tests/exercise_framework/test_parity_paths.py`
  - `tests/exercise_framework/test_runtime.py`
  - `tests/exercise_framework/test_api_contract.py`
  - `tests/student_checker/test_notebook_runtime.py`
  - `tests/template_repo_cli/test_selector.py`
  - `tests/template_repo_cli/test_collector.py`
- [ ] Update integration tests:
  - `tests/exercise_framework/test_autograde_parity.py`
  - `tests/template_repo_cli/test_integration.py`
  - `tests/test_integration_autograding.py`
  - `tests/test_autograde_plugin.py`
- [ ] Update packaging/template tests:
  - `tests/template_repo_cli/test_packager.py`
  - `tests/test_build_autograde_payload.py`
- [ ] Update workflow-related tests:
  - `tests/test_build_autograde_payload.py`
  - any workflow smoke harnesses added in earlier phases for `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml`, and `template_repo_files/.github/workflows/classroom.yml`
- [ ] Remove obsolete tests:
  - `tests/test_ex002_sequence_modify_basics.py`
  - `tests/test_ex003_sequence_modify_variables.py`
  - `tests/test_ex004_sequence_debug_syntax.py`
  - `tests/test_ex005_sequence_debug_logic.py`
  - `tests/test_ex006_sequence_modify_casting.py`
  - `tests/test_ex007_construct_checks.py`
  - `tests/test_ex007_sequence_debug_casting.py`
  - remove them only after equivalent exercise-local tests are discovered and passing under the new pytest contract.

### New Test Cases Required

Every checklist should spell out the behaviour that must be proved, not just the files to edit.

- [ ] Positive case: `resolve_exercise("ex002_sequence_modify_basics")` (or the agreed equivalent API) resolves the canonical exercise directory under `exercises/sequence/modify/ex002_sequence_modify_basics/` without consulting top-level `notebooks/` or `tests/` sources.
- [ ] Positive case: packaging `ex002_sequence_modify_basics` from canonical sources produces the flattened export pair `notebooks/ex002_sequence_modify_basics.ipynb` and `tests/test_ex002_sequence_modify_basics.py` in the temporary workspace.
- [ ] Failure case: passing a legacy notebook path such as `notebooks/ex002_sequence_modify_basics.ipynb` into the final resolver fails with a clear `exercise_key`-only error.
- [ ] Failure case: passing a legacy test path such as `tests/test_ex002_sequence_modify_basics.py` into the final resolver or packager contract fails clearly rather than silently adapting.
- [ ] Regression case: `ex006_sequence_modify_casting` packages from exactly one canonical source and cannot accidentally pull from both `exercises/ex006_sequence_modify_casting/` and `exercises/sequence/modify/ex006_sequence_modify_casting/`.
- [ ] Regression case: the `ex007` identity is fully normalised so the notebook stem, solution notebook stem, self-check slug, expectation module import, and test target all agree on one canonical `exercise_key`.
- [ ] Export/package case: packaged workspaces do not include `exercise.json`, migration manifests, or any other repository-only metadata files.
- [ ] Export/package case: packaged workspaces still include `tests/notebook_grader.py`, `tests/autograde_plugin.py`, `tests/helpers.py`, `tests/exercise_framework/`, `tests/exercise_expectations/`, `tests/student_checker/`, and `scripts/build_autograde_payload.py` if those remain part of the agreed export contract.
- [ ] Student-mode case: running the final student-mode validation against an intentionally incomplete notebook fails in the expected grading way (non-zero exit or reduced score) and does not fail because of missing paths, mismatched slugs, or selector confusion.
- [ ] Solution-mode case: running the same exercise in solution mode passes end to end under the final selector and yields a full-score autograde payload.
- [ ] Solution-mode case: repository solution-mode tests for all migrated exercises pass without `PYTUTOR_NOTEBOOKS_DIR` if that variable has been retired.

### Docs, Agents, And Workflow Updates

- [ ] Contributor docs: verify and, if needed, update `README.md`, `AGENTS.md`, `docs/project-structure.md`, `docs/setup.md`, and `docs/development.md` so none of them describe the legacy split layout as canonical authoring.
- [ ] Teaching docs: verify and, if needed, update `docs/testing-framework.md`, `docs/exercise-testing.md`, `docs/autograding-cli.md`, `docs/github-classroom-autograding-guide.md`, `docs/exercise-generation.md`, and `docs/exercise-generation-cli.md`.
- [ ] Agent docs: verify and, if needed, update `.github/agents/*.md.agent.md` and `docs/agents/tidy_code_review/*.md` so future agents do not reintroduce legacy path guidance.
- [ ] Runtime helper reference: document that the shared grading/runtime helpers live in `exercise_runtime_support` and instruct exercise code (and exported templates) to import from or ship that package rather than from top-level `tests`.
- [ ] Repository workflows: finalise `.github/workflows/tests.yml` and `.github/workflows/tests-solutions.yml` against the agreed post-cutover selector.
- [ ] Template workflows: finalise `template_repo_files/.github/workflows/classroom.yml` so the exported Classroom repo uses the final contract and no longer depends on transitional assumptions.
- [ ] CLI examples: update examples in `README.md`, `docs/setup.md`, `docs/CLI_README.md`, and any template README text so commands point at the canonical model and the final validation steps.

## Verification Plan

State exactly how this migration unit will be verified.

### Commands To Run

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/exercise_framework/test_runtime.py \
  tests/exercise_framework/test_api_contract.py \
  tests/exercise_framework/test_autograde_parity.py \
  tests/exercise_framework/test_parity_paths.py \
  tests/student_checker/test_notebook_runtime.py
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q \
  tests/template_repo_cli/test_selector.py \
  tests/template_repo_cli/test_collector.py \
  tests/template_repo_cli/test_packager.py \
  tests/template_repo_cli/test_integration.py \
  tests/test_build_autograde_payload.py \
  tests/test_integration_autograding.py \
  tests/test_autograde_plugin.py
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m scripts.template_repo_cli validate --notebooks ex002_sequence_modify_basics ex003_sequence_modify_variables
python -m scripts.template_repo_cli create \
  --notebooks ex002_sequence_modify_basics ex003_sequence_modify_variables \
  --repo-name phase11-smoke \
  --dry-run \
  --output-dir /tmp/phase11-template
```

- [ ] Command:

```bash
source .venv/bin/activate
cd /tmp/phase11-template
python -m pytest -q
python scripts/build_autograde_payload.py \
  --pytest-args="-p tests.autograde_plugin" \
  --output tmp/autograde/payload.txt \
  --summary tmp/autograde/results.json \
  --minimal
```

- [ ] Command:

```bash
source .venv/bin/activate
rg -n "PYTUTOR_NOTEBOOKS_DIR|notebooks/solutions|tests/test_ex[0-9]|notebooks/ex[0-9]" \
  README.md AGENTS.md docs .github/workflows template_repo_files .github/agents
```

- [ ] Command:

```bash
source .venv/bin/activate
python -m pytest -q
python -m pytest -q <STUDENT_MODE_SMOKE_TARGETS> --variant student
python -m pytest -q --variant solution
```

Only include commands that remain relevant once the earlier-phase execution-model decisions are final. If the final support-package location or final CLI flag syntax is still not implemented in code, Phase 11 cannot be executed safely.

### Expected Results

- [ ] Expected passing behaviour:
  - All repository validation suites pass against the canonical model.
  - Packaged workspace smoke tests pass from canonical authoring sources.
  - Solution-mode autograding produces a passing payload with full score.
- [ ] Expected failure behaviour:
  - Legacy path-based resolver inputs fail clearly and mention the canonical `exercise_key` contract.
  - Student-mode validation of intentionally incomplete notebooks fails in the expected grading manner rather than with infrastructure/path errors.
- [ ] Expected packaging/export behaviour:
  - Packaged templates contain the agreed flattened notebook/test outputs, required runtime helpers, and no repository-only metadata.
  - No solution notebooks are leaked into the exported template.
- [ ] Expected docs/workflow outcome:
  - No maintained doc, workflow, agent instruction, or template file teaches `PYTUTOR_NOTEBOOKS_DIR`, `notebooks/solutions`, or top-level `tests/test_ex*.py` as the canonical authoring model.

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old path-based behaviour fails where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model
- [ ] A saved tree or file listing of the packaged `/tmp/phase11-template` workspace
- [ ] A sample autograde payload from the packaged workspace
- [ ] CI run identifiers or screenshots for repository and template workflow smoke runs

## Risks, Ambiguities, And Blockers

This section is mandatory. Do not leave it out just because nothing is blocked yet.

### Known Risks

- [ ] Risk: hidden coupling to top-level `notebooks/` and `tests/test_ex*.py` may still exist in scripts, notebooks, docs, or self-check cells and could be missed by unit tests alone.
- [ ] Risk: deleting legacy sources too early could break packaging, discovery, or contributor workflows before the final source-to-export mapping is fully proven.
- [ ] Risk: exported template workflows may appear healthy while repository-mode student/solution switching is still inconsistent.
- [ ] Risk: mixed exercise identities and duplicate homes could cause the wrong source notebook or wrong test module to be packaged even if smoke tests only cover one exercise.

### Open Questions

- [x] Decision: the final variant-selection mechanism is an explicit `variant` argument in Python APIs plus a matching CLI flag for scripts, workflows, and local tooling.
- [x] Decision: shared grading helpers now live in `exercise_runtime_support` rather than top-level `tests`, and packaging/docs/workflows must document and verify that import path.
- [x] Decision: student-mode validation uses the full suite before each cutover stage.
- [x] Decision: the manifest path is `exercises/migration_manifest.json`.

### Blockers

- [ ] Blocker: the obsolete `exercises/ex001_sanity/` tree must be removed before final cleanup proceeds; treat it as a reserved removal-only asset rather than a migration candidate.
- [ ] Blocker: the root-level `exercises/ex006_sequence_modify_casting/` duplicate must be removed so that `exercises/sequence/modify/ex006_sequence_modify_casting/` is the only surviving `ex006` source.
- [ ] Blocker: the current `ex007` identity is inconsistent across source files. Everything must be normalised to `ex007_sequence_debug_casting`, and all `ex007_data_types_debug_casting` references must be removed.
- [ ] Blocker: Phase 11 cannot execute safely until the final selector and manifest decisions from earlier phases are written down in code and docs, not just implied.
- [ ] Blocker: Phase 11 cannot execute safely until `exercise_runtime_support` is implemented, `pyproject.toml` installs it, packaging/docs/workflows reference it, and exported workspaces plus exercises import or delegate to it instead of top-level `tests`.

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue: add an explicit blocker for the current `ex007` identity split (`sequence` versus `data_types`) because it already breaks `tests/test_ex007_sequence_debug_casting.py` during test collection.
- [ ] New affected surface: add `tests/helpers.py` to the list of modules that need variant-selection cutover, because `build_autograde_env()` currently injects `PYTUTOR_NOTEBOOKS_DIR` by default.
- [ ] New affected surface: add the placeholder path `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` to the migration inventory so final cleanup decides whether it stays, moves, or disappears.
- [ ] Incorrect assumption in current plan: Phase 11 should explicitly require a full test-collection pass, not just “CI is green”, because the current repository already has a collection-time identity mismatch in `tests/test_ex007_sequence_debug_casting.py`.
- [ ] Missing acceptance criterion: duplicate exercise homes must be resolved deterministically before packaging and cleanup; `ex006_sequence_modify_casting` is the verified example in the current tree.
- [ ] Missing migration stream: if earlier phases do not already own exercise-identity normalisation, add a small stream for slug/stem/self-check reconciliation before final cutover.

### Follow-Up Action

- [ ] Update [ACTION_PLAN.md](./ACTION_PLAN.md) before marking this checklist complete
- [ ] Cross-link this checklist from the relevant phase in [ACTION_PLAN.md](./ACTION_PLAN.md) if useful
- [ ] Tell future agents explicitly to feed every newly discovered blocker, stale path reference, or identity mismatch back into [ACTION_PLAN.md](./ACTION_PLAN.md) before they mark Phase 11 done

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
- [ ] The final variant-selection mechanism is the only supported selector in the cutover contract, unless [ACTION_PLAN.md](./ACTION_PLAN.md) explicitly says otherwise
- [ ] Legacy top-level `notebooks/` and legacy top-level exercise-specific `tests/test_ex*.py` sources are deleted or explicitly documented as non-authoritative artefacts only

## Checklist Notes

- Current repository facts verified while preparing this checklist:
  - `notebooks/` currently contains seven student notebooks: `ex001_sanity` (obsolete removal target), `ex002_sequence_modify_basics`, `ex003_sequence_modify_variables`, `ex004_sequence_debug_syntax`, `ex005_sequence_debug_logic`, `ex006_sequence_modify_casting`, and `ex007_sequence_debug_casting`.
  - `notebooks/solutions/` currently contains six matching solution stems plus the mismatched `ex007_data_types_debug_casting.ipynb`.
  - Top-level exercise-specific tests currently still exist under `tests/test_ex*.py`.
  - `tests/template_repo_cli/core/collector.py` and `scripts/template_repo_cli/core/packager.py` still treat top-level notebooks and tests as source inputs.
- Light verification run completed during planning:
  - Passing command: `python -m pytest -q tests/exercise_framework/test_parity_paths.py tests/template_repo_cli/test_packager.py::TestPackageIntegrity::test_packaged_workspace_pytest_smoke tests/test_build_autograde_payload.py::test_cli_notebook_dir_validation tests/student_checker/test_notebook_runtime.py`
  - Failing command exposing a real blocker: `python -m pytest -q tests/test_ex007_sequence_debug_casting.py`
- Keep this checklist narrow: if later work discovers unresolved resolver design, metadata schema questions, or source-to-export mapping gaps, stop and update the earlier-phase checklist and [ACTION_PLAN.md](./ACTION_PLAN.md) rather than improvising Phase 11 workarounds.
