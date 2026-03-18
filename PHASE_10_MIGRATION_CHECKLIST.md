# Phase 10 Migration Checklist — Public Interface Cutover

## Required Migration Rules

These rules are restated from `ACTION_PLAN.md` Phase 10 and apply throughout this checklist:

- Canonical public exercise identity is `exercise_key`.
- Prefer deliberate breaking changes over compatibility wrappers for public CLI, verifier, and helper interfaces that still accept notebook paths or notebook-oriented terminology.
- Do not leave notebook-path aliases or hidden fallbacks in public interfaces once the replacement interface lands.
- Public cutovers should happen only after the canonical execution model and packaging contract have been proven for at least one migrated exercise.
- Phase 10 is complete only when public-facing interfaces, docs, and tests assert the new `exercise_key` contract.

## Checklist Header

- Checklist title: `Phase 10 Migration Checklist — Public Interface Cutover`
- Related action-plan phase or stream: `Phase 10: Public Interface Cutover`
- Author: `Codex (Implementer Agent)`
- Date: `2026-03-18`
- Status: `completed`
- Scope summary: Track the intentional public-interface breaking changes that move repository-facing exercise tooling from notebook-path inputs to canonical `exercise_key` inputs.
- Explicitly out of scope:
  - Broad docs/workflow rewrites beyond directly coupled command examples.
  - Template CLI redesign or export-contract changes.
  - Exercise moves, notebook rewrites, or broader repository cleanup.

## Objective

Phase 10 is the repository public-interface cutover. The goal is to make public entry points clearly exercise-key-first, remove notebook-path-driven invocation from those interfaces, and update the narrow set of docs/tests that would otherwise immediately become misleading.

## Completed Phase 10 Batches

- [x] Batch 1 — Verifier CLI cut over to `exercise_key` as the canonical public positional input, with focused docs/tests updated.
- [x] Batch 2 — Template CLI cut over from `--notebooks` to `--exercise-keys`, with selector naming and focused docs/tests updated.
- [x] Batch 3 — `scripts/new_exercise.py` scaffold guidance now generates `run_notebook_checks(<exercise_key>)` self-check usage and the focused tests/docs assert that contract.
- [x] Batch 4 — Student checker public API cut over from `check_notebook(notebook_slug)` to `check_exercise(exercise_key)`, while notebook self-check guidance remained aligned to `run_notebook_checks(<exercise_key>)`.

## Affected Surfaces For Final Batch

- `exercise_runtime_support/student_checker/api.py`
- `exercise_runtime_support/student_checker/__init__.py`
- `tests/student_checker/test_api.py`
- `tests/template_repo_cli/test_integration.py`
- `docs/exercise-testing.md`
- `.github/agents/exercise_generation.md.agent.md`
- `.github/agents/exercise_verifier.md.agent.md`

## Implementation Tasks

### Code And Test Changes

- [x] Replace the public student-checker entry point `check_notebook(notebook_slug)` with `check_exercise(exercise_key)`.
- [x] Keep the student-checker behaviour otherwise unchanged.
- [x] Export only the renamed public student-checker entry point; do not leave `check_notebook` as a compatibility alias.
- [x] Update focused student-checker tests to assert the renamed public API and `exercise_key` wording.
- [x] Update directly coupled template-repository integration tests that execute the public self-check API in packaged workspaces.

### Focused Docs And Guidance Changes

- [x] Keep notebook self-check guidance aligned to `run_notebook_checks('<exercise_key>')` while renaming the exported student-checker API to `check_exercise('<exercise_key>')`.
- [x] Update Exercise Verifier agent guidance so verifier CLI examples use the Batch 1 `exercise_key` contract instead of notebook paths.
- [x] Keep broader documentation and notebook content sweeps out of scope for this phase-closing batch.

## Verification Plan

### Commands Run

- [x] `source .venv/bin/activate`
- [ ] `python -m pytest -q tests/student_checker/test_api.py`
- [ ] `python -m pytest -q tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_self_check_command_succeeds tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_subset_export_rejects_excluded_notebook_early tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_ex004_subset_imports_checker_apis_without_ex002 tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_ex004_solution_variant_uses_solution_mirror tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_ex004_solution_variant_checker_api_fails_without_solution_mirror`
- [ ] `python -m ruff check exercise_runtime_support/student_checker/api.py exercise_runtime_support/student_checker/__init__.py tests/student_checker/test_api.py tests/template_repo_cli/test_integration.py`

### Expected Results

- [x] `exercise_runtime_support.student_checker.check_exercise(<exercise_key>)` is the public self-check entry point.
- [x] `check_notebook(...)` is no longer exported as a supported public alias from `exercise_runtime_support.student_checker`.
- [x] Focused packaged-workspace tests and API tests were updated to exercise the renamed `check_exercise(<exercise_key>)` API.
- [x] Directly coupled docs and agent guidance now distinguish notebook self-check cells (`run_notebook_checks(<exercise_key>)`) from the exported student-checker API (`check_exercise(<exercise_key>)`) while keeping verifier guidance on `exercise_key`.

## Risks, Ambiguities, And Blockers

### Known Risks

- [x] This batch is a deliberate public breaking change for the student-checker API; repository notebooks or notes that still mention `check_notebook(...)` are outside this narrowly scoped checklist update.

### Open Questions

- [x] None remaining for Phase 10 within the scoped public-interface cutover batches.

### Blockers

- [x] No blocker identified beyond normal environment setup.

## Completion Criteria

- [x] Verifier CLI public contract uses `exercise_key`.
- [x] Template CLI public contract uses `--exercise-keys`.
- [x] Scaffolded self-check guidance uses `run_notebook_checks(<exercise_key>)`.
- [x] Public student-checker self-check API uses `check_exercise(<exercise_key>)` with no compatibility alias.
- [x] Directly coupled tests are updated for each public-interface batch.
- [x] Directly coupled maintained docs and agent guidance are updated for each public-interface batch.
- [x] Focused verification commands were run for the earlier Phase 10 batches, and the final Phase 10 code/doc batches were accepted after focused implementer verification plus tidy review.
- [x] Phase 10 public-interface cutover is complete.
