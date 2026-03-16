# Phase 6 Migration Checklist — Exercise Test Migration Preparation And Verification

Use this checklist for the preparation work described in [ACTION_PLAN.md](./ACTION_PLAN.md) under **Phase 6: Exercise Test Migration Preparation And Verification**.

This checklist is intentionally concrete and repository-specific. It captures the current repository-side `test_exNNN*.py` surfaces that still live outside `exercises/<construct>/<exercise_key>/tests/` as of **2026-03-16** so the remaining Phase 6 work can proceed without guessing.

## Required Migration Rules

These Phase 6 guardrails are restated from [ACTION_PLAN.md](./ACTION_PLAN.md) and remain mandatory while this checklist is being executed:

- Do not treat the Phase 4 `ex004_sequence_debug_syntax` migration as permission to move all remaining exercise-specific tests early; it is the pilot proof only.
- Do not move exercise-specific tests in bulk until the broader exercise-file migration phase, where notebooks, local docs links, and exercise tests move together.
- Use this phase to eliminate known structural blockers, prove the canonical test layout works, and make the later broad migration safer.
- The phase is only complete once the remaining repository-side `test_exNNN*.py` surfaces have been inventoried, `ex002` has been refactored into the same canonical test structure as the other exercises, and the repository has a clear verified path for migrating the remaining exercise tests alongside the wider exercise-file moves.
- Any exercise or test file that cannot yet move with its wider exercise files must be recorded as an explicit migration blocker rather than left as a silent exception.

## Checklist Header

- Checklist title: `Phase 6 Migration Checklist — Exercise Test Migration Preparation And Verification`
- Related action-plan phase or stream: `Phase 6: Exercise Test Migration Preparation And Verification`
- Author: `Codex Implementer Agent`
- Date: `2026-03-16`
- Status: `completed`
- Scope summary: Inventory every remaining repository-side `test_exNNN*.py` file that still sits outside canonical exercise-local test directories, record the current ownership or naming blockers attached to those files, and anchor the next clean-up step on `ex002_sequence_modify_basics`.
- Explicitly out of scope: bulk relocation of the remaining exercise tests; moving notebooks or exercise-local docs for `ex003`, `ex005`, `ex006`, or `ex007`; implementing the final repository guard; or treating any non-`ex002` move as an approved early migration.

## Objective

When the inventory portion of Phase 6 is complete, the repository should have one verified answer to these questions:

- Which `test_exNNN*.py` files still remain outside `exercises/<construct>/<exercise_key>/tests/`?
- Which of those files are straightforward legacy top-level exercise tests versus transition-only or shared-support repo-side tests?
- Which remaining files are blocked by unresolved ownership or naming drift rather than simple sequencing?
- Which exercise should be used as the dedicated Phase 6 clean-up target before any broader relocation work is attempted?

The current canonical proof remains `ex004_sequence_debug_syntax`; this checklist does **not** widen that proof to the rest of the repository.

## Phase 6 Progress Snapshot

- [x] Inventory every remaining repository-side `test_exNNN*.py` file that still lives outside `exercises/<construct>/<exercise_key>/tests/`.
- [x] Refactor the `ex002` exercise tests into the canonical exercise-local layout and naming pattern.
- [x] Update imports, fixtures, helper references, and collection configuration needed for canonical exercise-local tests to run cleanly.
- [x] Run the relevant repository-side exercise tests after the `ex002` clean-up work.
- [ ] Resolve or explicitly document the remaining blocker-class repo-side `test_exNNN*.py` files before the later repository guard is introduced.
- [x] Define the audit or repository guard that should fail once any `test_exNNN*.py` file still remains outside canonical exercise-local tests after the broad migration completes.

## Current Canonical Proof

- `exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py` remains the full notebook-and-test canonical proof.
- `exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py` now provides the canonical repository-side ex002 test surface while `ex002` notebooks remain legacy.

## Verification Evidence

- `uv run python scripts/run_pytest_variant.py --variant solution exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py -q` -> passed (`30 passed`).
- `uv run pytest tests/template_repo_cli/test_collector.py tests/template_repo_cli/test_packager.py tests/exercise_framework/test_ex002_integration.py tests/exercise_framework/test_autograde_parity.py tests/exercise_framework/test_parity_autograde_ex002.py tests/test_run_pytest_variant.py tests/test_pytest_collection_guard.py -q` -> passed (`54 passed`), with one existing `PytestAssertRewriteWarning` for `tests.exercise_framework.fixtures`.

## Remaining Repository-Side `test_exNNN*.py` Inventory

Inventory result: **6** repository-side `test_exNNN*.py` files still live outside canonical exercise-local test directories.

| File | Exercise or scope | Current role | Known blocker or reason it still sits outside canonical exercise-local tests | Phase 6 handling note |
| --- | --- | --- | --- | --- |
| `tests/exercise_framework/test_ex002_integration.py` | `ex002_sequence_modify_basics` task-metadata follow-up | Repo-side support test that validates the canonical ex002 task-mark distribution and naming | This is not a canonical exercise-local notebook test. It still carries a `test_exNNN*.py` name outside the exercise-local tree, so it would violate the future guard if left in place. | Keep repo-side for now, then rename, relocate, or retire it before the final repository guard is introduced. |
| `tests/test_ex003_sequence_modify_variables.py` | `ex003_sequence_modify_variables` | Legacy top-level exercise test surface | `ex003` still has split ownership between the legacy docs directory `exercises/sequence/modify/ex003_sequence_modify_variables/` and the canonical metadata stub `exercises/sequence/ex003_sequence_modify_variables/`. No separate naming drift is evident in the live test file. | Keep repo-side until the wider ex003 notebooks, docs links, and tests can move together. |
| `tests/test_ex005_sequence_debug_logic.py` | `ex005_sequence_debug_logic` | Legacy top-level exercise test surface | `ex005` still has split ownership between the legacy docs directory `exercises/sequence/debug/ex005_sequence_debug_logic/` and the canonical metadata stub `exercises/sequence/ex005_sequence_debug_logic/`. | Keep repo-side until the wider ex005 notebooks, docs links, and tests can move together. |
| `tests/test_ex006_sequence_modify_casting.py` | `ex006_sequence_modify_casting` | Legacy top-level exercise test surface | The live inventory no longer shows a duplicate-home or naming blocker for `ex006`; its test remains top-level because Phase 6 deliberately avoids broad one-off moves outside the dedicated ex002 clean-up. | Leave repo-side for now. `ex006` is a sequencing hold, not the next clean-up target. |
| `tests/test_ex007_sequence_debug_casting.py` | `ex007_sequence_debug_casting` | Legacy top-level exercise test surface | The older `data_types` naming drift no longer appears in the live repo-side test file, but `ex007` still has split ownership between `exercises/sequence/debug/ex007_sequence_debug_casting/` and `exercises/sequence/ex007_sequence_debug_casting/`. The aggregated expectations export surface in `tests/exercise_expectations/__init__.py` also still stops at `ex006`, so `ex007` is not yet a fully tidy baseline. | Keep repo-side until the wider ex007 exercise files move together and the remaining export/ownership drift is resolved. |
| `tests/test_ex007_construct_checks.py` | `ex007_sequence_debug_casting` shared construct-helper coverage | Repo-side shared-helper test for `tests.exercise_framework.ex007_construct_checks` and `exercise_runtime_support.exercise_framework.ex007_construct_checks` | This is not a canonical exercise-local notebook test. It targets shared construct-check helper behaviour, so it cannot simply move with the ex007 notebook files. It will also violate the future `test_exNNN*.py` guard if it keeps this name outside the canonical exercise-local tree. | Treat as an explicit blocker-class file. Decide later whether it belongs under shared runtime-support tests or needs a non-`test_exNNN*.py` name. |

## Known Blockers And Sequencing Notes

- `ex002_sequence_modify_basics` no longer has a split repository-side exercise test contract. Its remaining repo-side blocker is `tests/exercise_framework/test_ex002_integration.py`, which should be renamed, relocated, or retired before the final `test_exNNN*.py` guard lands.
- `ex003_sequence_modify_variables` and `ex005_sequence_debug_logic` still have split legacy-docs versus canonical-stub ownership. Their tests should remain repo-side until notebooks, docs links, and tests can move together.
- `ex006_sequence_modify_casting` is no longer blocked by a live duplicate-home or naming mismatch in the current inventory. Its remaining top-level test is a sequencing hold only.
- `ex007_sequence_debug_casting` is no longer blocked by the older `data_types` naming drift in the live repository-side test inventory, but it still has split exercise-home ownership and a repo-side construct-helper test that does not map 1:1 to canonical exercise-local notebook coverage.
- The future repository guard must account for blocker-class repo-side files such as `tests/exercise_framework/test_ex002_integration.py` and `tests/test_ex007_construct_checks.py`; they cannot remain as silent `test_exNNN*.py` exceptions outside canonical exercise-local tests.

## Explicit Migration Blockers

- `ex003_sequence_modify_variables`: blocked for wider test migration because teacher-doc ownership is still split between `exercises/sequence/modify/ex003_sequence_modify_variables/` and `exercises/sequence/ex003_sequence_modify_variables/`.
- `ex005_sequence_debug_logic`: blocked for wider test migration because teacher-doc ownership is still split between `exercises/sequence/debug/ex005_sequence_debug_logic/` and `exercises/sequence/ex005_sequence_debug_logic/`.
- `ex007_sequence_debug_casting`: blocked for wider test migration because exercise ownership is still split between `exercises/sequence/debug/ex007_sequence_debug_casting/` and `exercises/sequence/ex007_sequence_debug_casting/`, and the shared expectations/export surface is still not fully tidy for `ex007`.
- `tests/exercise_framework/test_ex002_integration.py`: explicit blocker-class repo-side file that must be renamed, relocated, or retired before the final `test_exNNN*.py` guard is enforced.
- `tests/test_ex007_construct_checks.py`: explicit blocker-class repo-side file that must be renamed, relocated, or moved under shared runtime-support coverage before the final `test_exNNN*.py` guard is enforced.
- `ex006_sequence_modify_casting` is intentionally not listed as a blocker here. Its remaining top-level test is a sequencing hold only, not an unresolved ownership or naming problem.

## Future Guard Definition

- Guard helper: `exercise_runtime_support.pytest_collection_guard.find_noncanonical_exercise_test_sources()`.
- Detection rule: any repository-side `test_exNNN*.py` path that does not live under `exercises/<construct>/<exercise_key>/tests/` is an offender, including top-level exercise tests, nested parity leftovers, and blocker-class repo-side helper tests such as `tests/exercise_framework/test_ex002_integration.py`.
- Proof surface: `tests/test_pytest_collection_guard.py` now includes focused unit tests that distinguish canonical exercise-local tests from future-guard offenders.
- Planned enforcement point after the blocker register is cleared: extend the repository collection guard to raise a clear `pytest.UsageError` if `find_noncanonical_exercise_test_sources()` returns any paths during repository test discovery.
- Current repository state: the helper is defined and tested now, but live enforcement remains deferred until the explicit blocker register above has been resolved.

## Next Step Anchor

- The dedicated `ex002_sequence_modify_basics` clean-up step is complete for the exercise-specific pytest surface.
- The next Phase 6 implementation step should decide the final home and name for blocker-class repo-side files such as `tests/exercise_framework/test_ex002_integration.py` and `tests/test_ex007_construct_checks.py`.
- Do **not** treat this update as approval to start broad `ex003`, `ex005`, `ex006`, or `ex007` test relocation ahead of the later wider exercise-file migration.

## Action Plan Feedback

- The inventory confirmed the expected exercise-ownership drift and also surfaced blocker-class repo-side `test_exNNN*.py` files that will need explicit rename, relocation, or retirement before the final repository guard can be enforced.
- This checklist now records `ex002_sequence_modify_basics` as the completed dedicated clean-up target for Phase 6.
- The explicit Phase 6 blocker register now identifies which exercises and repo-side files still prevent broader test migration, so later phases do not have to treat them as silent exceptions.
- The future noncanonical-test guard is now defined in code and tests, ready to be enforced once the blocker register has been cleared.
