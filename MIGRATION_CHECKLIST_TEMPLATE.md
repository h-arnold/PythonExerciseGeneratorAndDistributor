# Migration Checklist Template

Use this template when creating a detailed migration checklist for a phase, stream, or bounded piece of migration work from [ACTION_PLAN.md](./ACTION_PLAN.md).

The goal is consistency. Each checklist should make it obvious:

- what is in scope
- what must change
- which files, paths, modules, methods, docs, workflows, and tests are affected
- how success will be verified
- which blockers or new risks must be fed back into [ACTION_PLAN.md](./ACTION_PLAN.md)

## How To Use This Template

1. Copy this file to a new checklist document in the repo root or an agreed migration-planning location.
2. Replace placeholders with concrete details.
3. Keep the checklist narrowly scoped to one phase, stream, or coherent migration unit.
4. Prefer explicit file paths, functions, classes, CLI commands, workflows, and tests over vague summaries.
5. If new blockers, hidden coupling, or sequencing problems appear, add them to [ACTION_PLAN.md](./ACTION_PLAN.md) before treating the checklist as complete.

## Required Migration Rules

These rules come from [ACTION_PLAN.md](./ACTION_PLAN.md) and should be restated in each detailed checklist where relevant:

- Canonical exercise resolver input is `exercise_key` only.
- Do not add compatibility wrappers, fallback resolution, or dual path-based interfaces unless [ACTION_PLAN.md](./ACTION_PLAN.md) is updated explicitly.
- Legacy callers should fail clearly until they are refactored.
- Exported Classroom repositories remain metadata-free.
- `exercise.json` stays intentionally small and must not absorb convention-based data.
- Public interface breaking changes should only happen after the replacement execution model is defined and proven.
- Any newly discovered blocker or gap must be recorded back into [ACTION_PLAN.md](./ACTION_PLAN.md).

## Checklist Header

- Checklist title:
- Related action-plan phase or stream:
- Author:
- Date:
- Status: `draft` / `in progress` / `ready` / `done`
- Scope summary:
- Explicitly out of scope:

## Objective

Describe the exact migration outcome this checklist is intended to deliver.

Example prompts:

- What will be true when this checklist is complete?
- Which old assumptions should no longer exist?
- What new contract should be in place?

## Preconditions

- [ ] Dependencies from earlier phases are complete or explicitly waived.
- [ ] Required decisions from [ACTION_PLAN.md](./ACTION_PLAN.md) are settled.
- [ ] Scope boundaries are clear enough to avoid accidental spill into later phases.
- [ ] Any pilot construct or target exercise(s) for this checklist are named explicitly.

Notes:

- Decisions relied on:
- Open assumptions:

## Affected Surfaces Inventory

List every surface this migration unit touches. Be concrete.

### Files And Paths To Update

- [ ] Source files:
- [ ] Test files:
- [ ] Docs:
- [ ] Workflows:
- [ ] Agent instructions:
- [ ] Template/export files:
- [ ] Exercise directories:

Recommended format:

- `path/to/file.py` — why it is affected
- `path/to/file.md` — what must change

### Modules, Functions, Classes, Commands, And Contracts

- [ ] Python modules:
- [ ] Public functions or methods:
- [ ] CLI commands or flags:
- [ ] Environment variables:
- [ ] Workflow jobs or steps:
- [ ] Packaging/export contracts:
- [ ] Notebook self-check contracts:

Recommended format:

- `module.function_name` — current behaviour, required change
- `script.py --flag` — current interface, target interface
- `WORKFLOW_NAME` — current assumption, required update

### Current Assumptions Being Removed

List the exact assumptions this checklist is meant to remove.

- [ ] Assumption 1:
- [ ] Assumption 2:
- [ ] Assumption 3:

## Implementation Tasks

Break work into concrete tasks. Group by concern, not by person.

### Code Changes

- [ ] Add:
- [ ] Update:
- [ ] Remove:
- [ ] Rename or relocate:
- [ ] Fail-fast behaviour to add:

### Data And Metadata Changes

- [ ] `exercise.json` changes:
- [ ] Derived-data/index changes:
- [ ] Registry replacement work:
- [ ] Migration manifest updates:

### Test Changes

List both existing tests to update and new tests to add.

- [ ] Update existing unit tests:
- [ ] Update integration tests:
- [ ] Update packaging/template tests:
- [ ] Update workflow-related tests:
- [ ] Remove obsolete tests:

### New Test Cases Required

Every checklist should spell out the behaviour that must be proved, not just the files to edit.

- [ ] Positive case:
- [ ] Failure case:
- [ ] Regression case:
- [ ] Export/package case:
- [ ] Student-mode case:
- [ ] Solution-mode case:

Use explicit statements such as:

- `resolve_exercise("ex006_sequence_modify_casting")` returns the canonical exercise directory
- path-based resolver input fails with a clear error
- packaged template excludes `exercise.json`
- migrated exercise tests are collected from `exercises/**/tests/`

### Docs, Agents, And Workflow Updates

- [ ] Contributor docs:
- [ ] Teaching docs:
- [ ] Agent docs:
- [ ] Repository workflows:
- [ ] Template workflows:
- [ ] CLI examples:

## Verification Plan

State exactly how this migration unit will be verified.

### Commands To Run

- [ ] Command:
- [ ] Command:
- [ ] Command:

Recommended format:

```bash
source .venv/bin/activate
uv run pytest -q
```

Only include commands that are relevant to this checklist’s scope.

### Expected Results

- [ ] Expected passing behaviour:
- [ ] Expected failure behaviour:
- [ ] Expected packaging/export behaviour:
- [ ] Expected docs/workflow outcome:

### Evidence To Capture

- [ ] Tests updated and passing
- [ ] New tests added for the new contract
- [ ] Explicit proof that old path-based behaviour fails where intended
- [ ] Explicit proof that packaged exports still match the agreed contract
- [ ] Explicit proof that docs and workflows no longer teach the old model

## Risks, Ambiguities, And Blockers

This section is mandatory. Do not leave it out just because nothing is blocked yet.

### Known Risks

- [ ] Risk:
- [ ] Risk:

### Open Questions

- [ ] Question:
- [ ] Question:

### Blockers

- [ ] Blocker:
- [ ] Blocker:

## Action Plan Feedback

Record anything discovered while preparing or executing this checklist that should change the high-level plan.

### Must Be Added Or Updated In `ACTION_PLAN.md`

- [ ] New blocker or sequencing issue:
- [ ] New affected surface:
- [ ] Incorrect assumption in current plan:
- [ ] Missing acceptance criterion:
- [ ] Missing migration stream:

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

## Checklist Notes

Use this space for working notes, references, sequencing reminders, or links to related checklists.
