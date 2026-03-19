# Phase 13 Migration Checklist — Validation, Cutover, And Cleanup

## Required Migration Rules

These rules are restated from `ACTION_PLAN.md` Phase 13 and apply throughout this checklist:

- Final cleanup must wait for explicit validation across repository student mode, repository solution mode, packaged-template runtime checks, and full test collection.
- Do not treat a green repository CI run as sufficient proof on its own.
- Do not remove remaining legacy support until the canonical contract has been proven across code, tests, packaging, docs, and workflows.
- Any new blocker or missing validation proof discovered here must be recorded back into `ACTION_PLAN.md`.

## Checklist Header

- Checklist title: `Phase 13 Migration Checklist — Validation, Cutover, And Cleanup`
- Related action-plan phase or stream: `Phase 13: Validation, Cutover, And Cleanup`
- Author: `Codex (Implementer Agent)`
- Date: `2026-03-19`
- Status: `in progress`
- Scope summary: Document the minimum Phase 13 validation matrix and close the narrow repository-side mop-up where `tests/test_debug_explanations.py` still assumed the removed top-level `notebooks/` layout.
- Explicitly out of scope:
  - Running the full Phase 13 validation matrix.
  - Removing remaining legacy support.
  - Unrelated Ruff failures or ex004 solution-variant follow-up.

## Objective

Make the remaining Phase 13 validation expectations explicit enough to guide cutover work, while fixing the specific repository test that still pointed at the removed top-level notebook surface.

## Mop-Up Batch Covered Here

- [x] Update `tests/test_debug_explanations.py` to scan canonical student notebooks at `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`.
- [x] Add a focused regression check proving the scan excludes solution notebooks and any removed top-level notebook surface.
- [x] Cross-link the checklist and validation-matrix documentation back into `ACTION_PLAN.md`.

## Minimum Validation Matrix

| Cutover stage | Required proof | Current status |
| --- | --- | --- |
| Repository collection gate | `uv run pytest --collect-only -q` succeeds against the canonical repository layout | Documented earlier in `ACTION_PLAN.md`; not rerun in this mop-up |
| Repository student-mode gate | Focused migrated-construct student-mode validation, then full repository student-mode validation before each cutover stage | Pending |
| Repository solution-mode gate | Focused migrated-construct solution-mode validation, then broader migrated-construct/phase solution-mode coverage | Partial proof exists; broader validation pending |
| Packaged-template gate | At least one migrated exercise passes packaged-template runtime smoke validation | Pending |
| Docs/workflow gate | Maintained docs and workflows reference the canonical exercise-local layout and final `--variant <student|solution>` contract | Partial proof exists; final cleanup gate still pending |
| Legacy-removal gate | Legacy path support is removed only after all rows above are satisfied | Pending |

## Affected Surfaces

- `tests/test_debug_explanations.py` — remove the last hard-coded assumption that repository notebooks live under top-level `notebooks/`.
- `ACTION_PLAN.md` — record this mop-up batch, mark checklist authoring complete, and mark the validation-matrix documentation item complete.
- `PHASE_13_MIGRATION_CHECKLIST.md` — new concise phase checklist and validation matrix for Phase 13.

## Verification Plan

### Commands Run

- [x] `source .venv/bin/activate`
- [x] `python -m pytest -q tests/test_debug_explanations.py`
- [x] `python -m ruff check tests/test_debug_explanations.py`

### Expected Results

- [x] Explanation-content checks only inspect canonical repository student notebooks.
- [x] A regression test protects against drifting back to solution notebooks or the removed top-level notebook layout.
- [x] Phase 13 has a dedicated checklist document that includes the minimum validation matrix.
- [x] `ACTION_PLAN.md` reflects this mop-up batch without overstating broader Phase 13 completion.

## Risks, Ambiguities, And Blockers

### Known Risks

- [x] Broader Phase 13 validation is still incomplete even after this mop-up batch.
- [x] Repository-wide Ruff and solution-variant issues outside this scope remain and should not be treated as Phase 13 closure blockers for this narrow update.

### Open Questions

- [x] Which exact packaged-template smoke command(s) should become the final required Phase 13 gate is still to be confirmed during broader validation.

### Blockers

- [x] No blocker for this narrow mop-up scope.

## Completion Criteria

- [x] The stale repository-side notebook-path assumption in `tests/test_debug_explanations.py` is removed.
- [x] A focused regression test exists for canonical student-notebook targeting.
- [x] The minimum Phase 13 validation matrix is documented in a dedicated checklist file.
- [x] `ACTION_PLAN.md` is updated to reflect this checklist and matrix-documentation work.
- [x] The checklist states clearly that broader validation and legacy-support removal remain for later work.
