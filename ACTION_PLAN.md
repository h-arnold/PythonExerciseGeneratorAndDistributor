# ACTION_PLAN: template_repo_cli slop clean-up

## Stage 1 — Update docs before implementation
**Objective**
Write down the new expected behaviour first so contributors and sub-agents implement the canonical-only template CLI contract instead of preserving stale compatibility paths or test-only runtime helpers.

**Files or surfaces**
- `AGENTS.md`
- `.github/agents/planner.agent.md`
- `.github/agents/planner-reviewer.agent.md`
- `.github/agents/implementer.md.agent.md`
- `docs/testing-framework.md`
- `docs/project-structure.md`
- `docs/execution-model.md`
- `docs/exercise-generation-cli.md`
- `docs/development.md`
- `SLOP_REVIEW.md`

**Acceptance criteria**
- Repo and agent docs say the steady-state template CLI is canonical-only.
- Repo and agent docs say helpers kept only for tests belong under `tests/` and are not part of the runtime surface.
- Docs no longer recommend `tests/template_repo_cli/conftest.py` fixtures (`sample_exercises`, `mock_gh_*`) or `scripts/template_repo_cli/utils/filesystem.py::resolve_notebook_path` as stable public surfaces.
- `docs/testing-framework.md` updated to reflect new test-only helper locations and removed fixtures.
- `docs/execution-model.md` updated to reflect canonical-only contract.
- `docs/exercise-generation-cli.md` updated to reflect new helper organization.
- `docs/development.md` updated with new contributor guidelines for helper placement.
- `.github/agents/planner-reviewer.agent.md` updated to expect canonical-only exercise layouts and enforce new contract.
- `.github/agents/implementer.md.agent.md` updated with implementation guidelines for canonical-only contract.
- `.github/agents/planner.agent.md` updated with planning expectations for canonical-only template CLI.
- Documentation includes guidance on removing any legacy compatibility paths found during implementation.
- The documentation slice is reviewable on its own and gives the implementer unambiguous direction.

**Checks or validation**
- `rg` confirms stale references to removed legacy compatibility and test-only runtime helpers have been updated in all touched docs.
- `rg` confirms no documentation references removed fixtures (`sample_exercises`, `mock_gh_*`) or helpers (`resolve_notebook_path`).
- `rg` confirms agent documentation includes canonical-only expectations and new helper placement guidelines.
- `rg` confirms no legacy compatibility paths remain in documentation.
- Manual review confirms the docs align with `SPEC.md` and the execution model.

**Review point**
Confirm the docs now describe the intended canonical-only behaviour before any production refactor begins.

## Stage 2 — Remove dead runtime-surface utilities
**Objective**
Remove persisted-config plumbing, dead fixtures, and test-only utility helpers that have no live template CLI caller.

**Files or surfaces**
- `scripts/template_repo_cli/utils/config.py`
- `scripts/template_repo_cli/utils/filesystem.py`
- `scripts/template_repo_cli/core/github.py`
- `tests/template_repo_cli/conftest.py`
- `tests/template_repo_cli/test_filesystem.py`
- `tests/template_repo_cli/test_github.py`
- any new helper module created under `tests/template_repo_cli/` or `tests/typeguards/`

**Acceptance criteria**
- No dead config module remains in the runtime surface without a caller.
- Helpers that exist only for tests are either moved under `tests/` with a justified helper role or deleted.
- Filesystem and GitHub helpers kept in runtime modules are demonstrably used by production flow.
- The runtime/test ownership boundary for `core/github.py` and `utils/filesystem.py` is clear for Stage 4 reuse.
- Unused shared fixtures are removed.
- Test-only helpers `is_command_sequence()`, `check_authentication()`, `parse_json_output()` are relocated to `tests/` or deleted if no valid purpose.
- `rg` confirms relocated helpers are imported by at least one test file.
- `rg` confirms no runtime modules import from new test helper locations.

**Checks or validation**
- `rg` confirms removed helpers are no longer referenced from runtime modules.
- `rg` confirms relocated test-only helpers are only referenced in test files.
- `rg` confirms any relocated helpers are properly documented in their new location.
- Run the affected template CLI tests: `uv run pytest tests/template_repo_cli -q`
- Verify tests using relocated helpers continue to pass.

**Review point**
Confirm the shipped module surface now matches actual runtime use before simplifying deeper workflow code.

## Stage 3 — Simplify collector, selector, and packager to the canonical contract
**Objective**
Remove obsolete legacy-layout branches from exercise selection, file collection, and packaging.

**Files or surfaces**
- `scripts/template_repo_cli/core/collector.py`
- `scripts/template_repo_cli/core/selector.py`
- `scripts/template_repo_cli/core/packager.py`
- `tests/template_repo_cli/test_collector.py`
- `tests/template_repo_cli/test_packager.py`

**Acceptance criteria**
- Canonical exercise-local notebooks/tests are the only steady-state path through collector/packager logic.
- All legacy-layout compatibility is removed rather than preserved behind dormant or synthetic branches.
- Unreachable `Path("tests")` export handling is removed.
- Tests cover canonical behaviour and fail-fast conditions, not synthetic legacy directory behaviour that the live repo no longer uses.

**Checks or validation**
- Run focused collector/packager tests.
- Verify packaging still places notebooks and tests under `exercises/<construct>/<exercise_key>/...`.
- Verify removal of legacy-layout branches does not break any existing tests.

**Review point**
Confirm no legacy-layout compatibility remains anywhere in the steady-state template CLI/package path.

## Stage 4 — Deduplicate CLI selection and GitHub auth classification
**Objective**
Consolidate duplicated decision logic so selection and auth failure handling each have one source of truth.

**Files or surfaces**
- `scripts/template_repo_cli/cli.py`
- `scripts/template_repo_cli/core/github.py`
- related template CLI tests

**Acceptance criteria**
- `create` and `validate` share one exercise-selection implementation.
- GitHub permission/auth classification is centralised in `github.py` and reused by both retry and hint paths.
- `_github_permission_hint()`, `_is_integration_permission_error()`, `_should_retry_with_reauth()` from `cli.py` are merged into `github.py`.
- `GitHubClient._should_retry_with_fresh_auth()` remains as central logic.
- `should_retry_with_fresh_auth()` remains as public wrapper.
- Duplicate marker constants and classification functions are removed.

**Checks or validation**
- Run focused CLI/GitHub tests.
- Spot-check dry-run create/validate flows for unchanged user-visible success behaviour.
- `rg` confirms no duplicate auth classification logic remains.
- Verify consolidated logic does not introduce new dependencies or circular imports.

**Review point**
Verify the new single-source helpers do not change the supported CLI contract except where the spec explicitly intends alignment.

## Stage 5 — Narrow workflow error handling and align tests with the current contract
**Objective**
Stop masking internal defects as generic CLI failures and bring tests in line with the documented exercise-key contract.

**Files or surfaces**
- `scripts/template_repo_cli/cli.py`
- `tests/template_repo_cli/test_integration.py`
- a repo-wide sweep for stale legacy wording and old path assumptions
- any related template CLI tests

**Acceptance criteria**
- Broad `BaseException` catches are removed or replaced with specific exceptions (`FileNotFoundError`, `ValueError`, `RuntimeError`).
- Fatal control-flow exceptions (`GeneratorExit`, `KeyboardInterrupt`, `SystemExit`) are allowed to propagate.
- Integration tests assert current canonical/runtime wording where relevant.
- Repo-wide stale wording and path-assumption checks are updated wherever the canonical contract has replaced legacy terminology.

**Checks or validation**
- `uv run pytest tests/template_repo_cli -q`
- Verify updated exception handling does not mask critical errors.

**Review point**
Confirm failure messages now distinguish expected user/input problems from programmer defects.

## Stage 6 — Final repository validation
**Objective**
Prove the clean-up is stable for the touched repository tooling surface.

**Files or surfaces**
- All modified template CLI files and tests
- All documentation updated in Stage 1

**Acceptance criteria**
- Targeted template CLI tests pass.
- Repository collection and solution-variant validation still pass for the wider tree.
- Updated docs remain aligned with the execution model and final implementation.
- Solution variants continue to pass after all changes.

**Checks or validation**
- `uv run pytest tests/template_repo_cli/test_github.py tests/template_repo_cli/test_integration.py -q`
- `uv run pytest tests/template_repo_cli -q`
- `uv run pytest --collect-only -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- `uv run ./scripts/verify_solutions.sh -q`
- `uv run ruff check .`
- Final validation includes review of updated documentation for accuracy and completeness.

**Review point**
Hand off only once the template CLI clean-up is verified against both local targeted tests and the repository-wide authoring contract.
