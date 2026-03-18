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
- Status: `in progress`
- Scope summary: Track the intentional public-interface breaking changes that move repository-facing exercise tooling from notebook-path inputs to canonical `exercise_key` inputs.
- Explicitly out of scope:
  - Broad docs/workflow rewrites beyond directly coupled command examples.
  - Template CLI redesign or export-contract changes.
  - Exercise moves, notebook rewrites, or broader repository cleanup.

## Objective

Phase 10 is the repository public-interface cutover. The goal is to make public entry points clearly exercise-key-first, remove notebook-path-driven invocation from those interfaces, and update the narrow set of docs/tests that would otherwise immediately become misleading.

## Current Phase 10 Streams

### Batch 1 — Verifier CLI Cutover

- [x] Update `scripts/verify_exercise_quality.py` so the public CLI accepts `exercise_key` as the canonical positional input.
- [x] Remove notebook-path-driven CLI inference from the verifier public entry point.
- [x] Keep verifier internals checking canonical files under `exercises/<construct>/<exercise_key>/`.
- [x] Update focused verifier tests to assert the new `exercise_key` contract.
- [x] Update directly coupled verifier command examples in maintained docs.

### Remaining Known Phase 10 Batches

- [ ] Template CLI and selector public-interface cutover to `exercise_key`-first invocation, including any required docs/tests updates.
- [ ] `scripts/new_exercise.py` and notebook self-check public-surface review so generated guidance no longer teaches notebook-path-first identity once that stream is ready.
- [ ] Final Phase 10 docs pass for remaining public examples after the rest of the interface cutovers land.
- [ ] Pointer-list review for interface pain points called out in `ACTION_PLAN.md`: `docs/CLI_README.md`, `scripts/template_repo_cli/core/selector.py`, `scripts/verify_exercise_quality.py`, and `scripts/new_exercise.py`.

## Affected Surfaces For Batch 1

- `scripts/verify_exercise_quality.py`
- `tests/test_verify_exercise_quality.py`
- `docs/setup.md`
- `docs/development.md`
- `docs/exercise-generation.md`
- `docs/exercise-generation-cli.md`

## Implementation Tasks

### Code And Test Changes

- [x] Change the verifier CLI positional argument from notebook path to `exercise_key`.
- [x] Resolve the canonical exercise directory via metadata-backed exercise resolution.
- [x] Load `student.ipynb` and `solution.ipynb` from the canonical exercise directory after resolution succeeds.
- [x] Keep legacy notebook-path input unsupported with no compatibility wrapper.
- [x] Add or update tests proving `exercise_key` succeeds and notebook-path input is no longer the public contract.

### Focused Docs Changes

- [x] Replace stale verifier command examples that passed notebook paths.
- [x] Update nearby wording where needed so the command is described in terms of `exercise_key`.
- [ ] Do broader contributor/workflow documentation rewrites only in later Phase 10 batches.

## Verification Plan

### Commands To Run

- [x] `source .venv/bin/activate`
- [x] `python -m pytest tests/test_verify_exercise_quality.py -q`
- [x] `python -m ruff check scripts/verify_exercise_quality.py tests/test_verify_exercise_quality.py`

### Expected Results

- [x] `scripts/verify_exercise_quality.py <exercise_key>` validates the canonical exercise notebooks and scaffold.
- [x] Passing a notebook path to the verifier no longer works as a supported interface.
- [x] Updated docs show `exercise_key`-based verifier invocation.

## Risks, Ambiguities, And Blockers

### Known Risks

- [ ] Other public interfaces listed in `ACTION_PLAN.md` still use notebook-path-oriented inputs and remain for later batches.
- [ ] Some wider docs and workflow surfaces may still describe pre-cutover interfaces until their own Phase 10 batches land.

### Open Questions

- [x] Decision: the verifier public CLI should break cleanly to `exercise_key` rather than carrying a notebook-path alias.
- [ ] Decision pending: exact Phase 10 cutover order for template CLI, scaffold guidance, and notebook self-check surfaces.

### Blockers

- [ ] No blocker for Batch 1 identified beyond environment setup if `.venv` is absent and must be recreated with `uv sync`.

## Completion Criteria

- [x] In-scope verifier code changes are complete.
- [x] In-scope verifier tests are updated.
- [x] Directly coupled verifier docs are updated.
- [x] Verification commands have been run or explicitly deferred with a reason.
- [x] Remaining Phase 10 batches are listed for follow-up.
