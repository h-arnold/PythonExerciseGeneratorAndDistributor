# SPEC: template_repo_cli canonical clean-up

## Goal and intended outcome
Reduce confirmed maintenance-only code in `scripts/template_repo_cli/` so the template CLI reflects the repository's current canonical exercise-local model and exposes only runtime-supported behaviour.

The intended outcome is a smaller, clearer CLI/package surface with:
- no dead persisted-config plumbing
- no test-only helpers shipped as production utilities
- no legacy-layout compatibility in the live template CLI/package path
- one selection path for CLI commands
- one auth-error classification path for GitHub retry and hint logic
- narrower failure handling that does not hide internal defects behind generic CLI errors
- contributor and agent-facing docs updated first so implementation follows the new canonical-only contract

## Current state
`SLOP_REVIEW.md` confirms a second-pass clean-up target concentrated in `scripts/template_repo_cli/` and `tests/template_repo_cli/`.

A narrow hypothesis was checked before drafting this spec:
- **Hypothesis:** the flagged slop is mostly obsolete compatibility and test-only surface, not live runtime behaviour required by the canonical repository state.
- **Cheap disconfirmation check:** search current symbol usage with `rg` and inspect `exercises/migration_manifest.json`.
- **Result:** the manifest currently contains only `canonical` layouts, and several flagged helpers are referenced only by tests or by their own module.

The current docs also create drift risk for implementation:
- `docs/testing-framework.md` still presents `tests/template_repo_cli/conftest.py` fixtures such as `sample_exercises` and `mock_gh_*` as intentionally reusable.
- `docs/testing-framework.md` still documents `scripts/template_repo_cli/utils/filesystem.py::resolve_notebook_path` as a live CLI utility.
- Agent guidance does not yet explicitly tell implementers and plan reviewers to update template CLI docs first when canonical-only behaviour is the intended outcome.

## Scope
This work covers the template repository CLI, its tests, and the directly-related docs that define the intended behaviour:

1. Update docs and agent guidance first so the canonical-only contract is explicit before code changes begin.
2. Remove dead configuration plumbing with no runtime caller.
3. Investigate test-only helper functions currently shipped under runtime module paths; move any helper with a legitimate test-only role under `tests/`, and delete any helper with no valid purpose.
4. Remove all legacy-layout compatibility from collector, selector, and packager flow; if a behaviour must survive, refactor it to the canonical exercise-local contract rather than preserving a legacy branch.
5. Deduplicate CLI selection logic shared by `create` and `validate` flows.
6. Centralise GitHub auth-error classification so retry decisions and user hints use the same rule.
7. Replace broad defensive `BaseException` catches in template CLI workflows with narrower expected failure handling.
8. Remove dead shared pytest fixtures in `tests/template_repo_cli/conftest.py`.
9. Update affected tests so they assert the current canonical/runtime contract rather than preserved legacy behaviour.

## Non-goals
- No change to the canonical authoring layout: `exercises/<construct>/<exercise_key>/` remains the source of truth.
- No change to notebook-variant semantics (`--variant`, `PYTUTOR_ACTIVE_VARIANT`).
- No change to exported student-facing packaging shape beyond removing unreachable or obsolete implementation branches.
- No unrelated refactors outside the flagged template CLI surface and the docs needed to describe its new behaviour.

## Constraints and invariants
- The execution model in `docs/execution-model.md` remains authoritative.
- Exercise identity is the canonical `exercise_key`, not a flattened notebook path.
- Canonical exercise tests remain exercise-local under `exercises/<construct>/<exercise_key>/tests/`.
- Packaged outputs remain metadata-free, student-facing, and exercise-local.
- Shared notebook/runtime imports must continue to come from `exercise_runtime_support`.
- Fail-fast rules remain in force for missing canonical files and duplicate test sources.
- Legacy-layout compatibility must not remain in the steady-state template CLI path after this clean-up.
- Any helper kept only for tests must live under `tests/` and be documented as test-only.
- Any intentional change to visible CLI errors must be aligned with the documented current contract, not legacy wording.

## Relevant docs and file evidence
### Source-of-truth docs
- `AGENTS.md`
- `docs/project-structure.md`
- `docs/execution-model.md`
- `docs/testing-framework.md`
- `docs/development.md`
- `docs/exercise-generation.md`
- `docs/exercise-generation-cli.md`
- `docs/pedagogy.md`

### Agent guidance likely to require alignment
- `.github/agents/planner.agent.md`
- `.github/agents/planner-reviewer.agent.md`
- `.github/agents/implementer.md.agent.md`

### Review input
- `SLOP_REVIEW.md`

### Current code evidence
- `exercises/migration_manifest.json` contains only canonical layouts.
- `scripts/template_repo_cli/utils/config.py` defines persisted-config helpers with no runtime caller outside the module.
- `scripts/template_repo_cli/utils/filesystem.py` exposes `resolve_notebook_path()` and `create_directory_structure()` that are exercised only by `tests/template_repo_cli/test_filesystem.py`.
- `scripts/template_repo_cli/core/collector.py` still branches on legacy layout and flat test fallback even though the live manifest is canonical-only.
- `scripts/template_repo_cli/core/selector.py` still scans legacy construct/type directory shapes when manifest-backed metadata is absent.
- `scripts/template_repo_cli/core/packager.py` retains a `Path("tests")` branch that current collector output does not produce.
- `scripts/template_repo_cli/cli.py` duplicates exercise-selection logic between `_select_exercises()` and `_select_exercises_for_validation()`.
- `scripts/template_repo_cli/cli.py` and `scripts/template_repo_cli/core/github.py` both classify GitHub integration/auth failures.
- `scripts/template_repo_cli/core/github.py` exposes helpers such as `check_authentication()` and `parse_json_output()` that are exercised only by tests.
- `tests/template_repo_cli/conftest.py` includes unused shared fixtures.
- `tests/template_repo_cli/test_integration.py` should keep its assertions aligned with the current `Unknown exercise key ...` contract rather than any older notebook-oriented wording.

## Acceptance criteria
1. Repo docs and agent guidance are updated first so contributors and sub-agents are told to implement the canonical-only template CLI behaviour and to keep any retained test-only helpers under `tests/`.
2. `scripts/template_repo_cli/` no longer contains dead persisted-config plumbing without a runtime consumer.
3. Runtime modules under `scripts/template_repo_cli/` expose only helpers needed by the live CLI/package flow; helpers used only by tests are either moved under `tests/` with a justified test-helper role or deleted.
4. `FileCollector`, `ExerciseSelector`, and `TemplatePackager` follow a canonical exercise-local path through selection, collection, and packaging, with no remaining legacy-layout compatibility branches in the steady-state flow.
5. The packager copies exercise tests to exercise-local export paths only, with no dead special-case branch for `Path("tests")`.
6. The CLI uses a single exercise-selection helper shared by create/validate paths, with command-specific messaging added only at the boundary.
7. GitHub auth/integration error detection is defined once and reused by retry and hint logic so both layers stay in sync.
8. Template CLI workflow wrappers handle expected operational errors explicitly and allow unexpected programmer defects to surface instead of collapsing them into `Unexpected error: ...`.
9. Dead fixtures in `tests/template_repo_cli/conftest.py` are removed, and any retained test helpers are documented in their new test-only location.
10. The template CLI test suite is updated to the canonical contract, including current exercise-key error wording where applicable.
11. The resulting code passes targeted template CLI tests and repository-level validation required by the touched surfaces.

## Open questions and risks
- No open questions remain after clarification: all legacy-layout compatibility should be removed, and test-only helpers should either move under `tests/` with a justified role or be deleted.
- **Documentation drift risk:** several current docs still describe helpers and fixtures likely to be removed or relocated. If these are not updated first, implementers may preserve obsolete surfaces to satisfy stale guidance.
- **Baseline mismatch risk:** `tests/template_repo_cli/test_integration.py` previously mixed exercise-key and notebook-oriented expectation wording. That inconsistency has been aligned with the documented runtime contract, so future cleanups should keep the exercise-key wording consistent.
