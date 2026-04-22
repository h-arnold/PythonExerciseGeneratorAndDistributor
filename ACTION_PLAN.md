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
- any other touched template CLI contributor doc that still describes removed fixtures, helpers, or legacy-layout compatibility

**Acceptance criteria**
- Repo and agent docs say the steady-state template CLI is canonical-only.
- Repo and agent docs say helpers kept only for tests belong under `tests/` and are not part of the runtime surface.
- Docs no longer recommend `tests/template_repo_cli/conftest.py` fixtures or `scripts/template_repo_cli/utils/filesystem.py::resolve_notebook_path` as stable public surfaces if they are being removed or relocated.
- The documentation slice is reviewable on its own and gives the implementer unambiguous direction.

**Checks or validation**
- `rg` confirms stale references to removed legacy compatibility and test-only runtime helpers have been updated in the touched docs.
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
- an explicit helper-ownership inventory for `scripts/template_repo_cli/core/github.py` and `scripts/template_repo_cli/utils/filesystem.py`

**Acceptance criteria**
- No dead config module remains in the runtime surface without a caller.
- Helpers that exist only for tests are either moved under `tests/` with a justified helper role or deleted.
- Filesystem and GitHub helpers kept in runtime modules are demonstrably used by production flow.
- The runtime/test ownership boundary for `core/github.py` and `utils/filesystem.py` is explicit enough that Stage 4 can reuse the remaining runtime-supported helpers safely.
- Unused shared fixtures are removed.

**Checks or validation**
- `rg` confirms removed helpers are no longer referenced from runtime modules.
- Run the affected template CLI tests.

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
- GitHub permission/auth classification is centralised and reused by both retry and hint paths.

**Checks or validation**
- Run focused CLI/GitHub tests.
- Spot-check dry-run create/validate flows for unchanged user-visible success behaviour.

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
- Broad `BaseException` catches are removed or replaced with a narrowly justified alternative.
- Integration tests assert current canonical/runtime wording where relevant.
- Repo-wide stale wording and path-assumption checks are updated wherever the canonical contract has replaced legacy terminology.

**Checks or validation**
- `uv run pytest tests/template_repo_cli -q`

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

**Checks or validation**
- `uv run pytest tests/template_repo_cli/test_github.py tests/template_repo_cli/test_integration.py -q`
- `uv run pytest tests/template_repo_cli -q`
- `uv run pytest --collect-only -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- `uv run ruff check .`

**Review point**
Hand off only once the template CLI clean-up is verified against both local targeted tests and the repository-wide authoring contract.
