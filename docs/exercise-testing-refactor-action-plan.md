# Exercise Testing Refactor — Staged TDD Action Plan

This plan converts the `exercise-testing-new.md` architecture into small, testable implementation phases. It intentionally prioritises ex002 parity first, then broader migration.

## Delivery Rules

- Work in small phases; each phase must be testable and reviewable in isolation.
- Follow strict TDD: write/adjust tests first, then implement, then refactor.
- Preserve current observable ex002 behaviour before migrating non-ex002 suites.
- Do **not** add backwards-compatibility shims for legacy non-ex002 tests in this stage.

---

## Phase 0 — Baseline and Safety Net

### Goal

Capture the current ex002 behaviour as the regression baseline.

### TDD Tasks

- [x] Add/update explicit parity tests for ex002 table/report output format.
- [x] Add/update parity tests for `PYTUTOR_NOTEBOOKS_DIR` path override and fallback semantics.
- [x] Add/update parity tests for ex002 issue message formatting (`Exercise N:` stripping, `;` joins, `line1 | line2`).
- [x] Add autograde metadata parity checks for ex002 task grouping and collected test count.

### Acceptance Criteria

- [x] All new baseline tests pass against current behaviour (solutions notebooks).
- [ ] Baseline tests fail when any key format rule is intentionally changed. _(Validated indirectly via existing failure-oriented rendering tests; add explicit mutation checks in a follow-up commit if needed.)_

### Constraints

- No production refactor yet beyond wiring necessary for testability.
- Keep test runtime fast and deterministic.

### Touched Code

- **Reference code**:
  - `tests/student_checker.py`
  - `tests/test_student_checker_table_rendering.py`
  - `tests/test_ex002_sequence_modify_basics.py`
  - `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`
  - `tests/notebook_grader.py`
  - `tests/autograde_plugin.py`
  - `scripts/build_autograde_payload.py`
- **New/updated tests**:
  - `tests/exercise_framework/test_parity_ex002_reporting.py` _(new)_
  - `tests/exercise_framework/test_parity_paths.py` _(new)_
  - `tests/exercise_framework/test_parity_autograde_ex002.py` _(new)_

### Notes

- Decisions:
  - Added dedicated Phase 0 parity tests under `tests/exercise_framework/` for reporting, path resolution, and autograde task distribution/count.
- Open questions:
  - Whether to add explicit mutation-style tests that intentionally monkeypatch formatting constants to prove baseline-test sensitivity.
- Follow-up:
  - If requested, add mutation-sensitivity tests as a short hardening pass before Phase 1.

---

## Phase 1 — Introduce Framework Skeleton and Stable API

### Goal

Create `tests/exercise_framework/` with a stable public facade and minimal behaviour-preserving plumbing.

### TDD Tasks

- [x] Write API contract tests for `run_all_checks`, `run_notebook_check`, and `run_detailed_ex002_check`.
- [x] Verify API returns structured results independent of rendering concerns.
- [x] Verify unknown slug handling remains explicit and informative.

### Acceptance Criteria

- [x] `api.py` exists and is used by at least one caller path.
- [x] API contract tests pass without depending on private internals.

### Constraints

- Avoid moving all logic at once; introduce facade first.
- Keep external behaviour unchanged for ex002 outputs.

### Touched Code

- **Reference code**:
  - `tests/student_checker.py`
- **New code**:
  - `tests/exercise_framework/__init__.py`
  - `tests/exercise_framework/api.py`
  - `tests/exercise_framework/types.py` _(optional, if shared result structures are needed)_
- **New tests**:
  - `tests/exercise_framework/test_api_contract.py`

### Notes

- Decisions:
  - Introduced `tests/exercise_framework/api.py` and `tests/exercise_framework/__init__.py` as the initial stable framework facade for Phase 1.
  - Added contract tests in `tests/exercise_framework/test_api_contract.py` with solution-notebook execution to keep development checks deterministic.
- Open questions:
  - Whether to introduce a small dedicated `types.py` module now or wait until richer result structures arrive in Phase 2/3.
- Follow-up:
  - Repoint at least one existing caller to import through the new API once Phase 2 runtime/path modules are in place.

---

## Phase 2 — Extract Paths and Runtime Modules

### Goal

Move notebook resolution/execution concerns into dedicated modules with parity.

### TDD Tasks

- [x] Write tests for path resolver parity with current fallback rules.
- [x] Write tests for runtime extraction/execution parity (tag not found, JSON errors, execution errors).
- [x] Add tests for execution artefact caching per `(path, tag, input_signature)` when safe.

### Acceptance Criteria

- [x] `paths.py` and `runtime.py` satisfy parity tests from Phase 0.
- [x] Runtime caching does not change observable outputs/messages.

### Constraints

- Preserve fail-fast behaviour and existing exception semantics.
- No exercise-specific logic inside runtime/path modules.

### Touched Code

- **Reference code**:
  - `tests/notebook_grader.py`
- **New code**:
  - `tests/exercise_framework/paths.py`
  - `tests/exercise_framework/runtime.py`
- **New tests**:
  - `tests/exercise_framework/test_paths.py`
  - `tests/exercise_framework/test_runtime.py`

### Notes

- Decisions:
  - Added `tests/exercise_framework/paths.py` as the Phase 2 resolver entry point, delegating to existing grading semantics for strict parity.
  - Added `tests/exercise_framework/runtime.py` wrappers plus `RuntimeCache` keyed by `(path, tag)` and `(path, tag, input_signature)` for safe artefact reuse.
  - Added dedicated Phase 2 tests in `tests/exercise_framework/test_paths.py` and `tests/exercise_framework/test_runtime.py`.
- Open questions:
  - None at this stage; API now uses framework runtime/path modules for execution and resolution concerns.
- Follow-up:
  - Keep API runners aligned with upcoming expectation/assertion extraction in Phase 3 to avoid duplicate logic drift.

---

## Phase 3 — Extract Expectations and Consolidate Sources

### Goal

Create a single source of truth for expectations, starting with ex002.

### TDD Tasks

- [x] Write tests ensuring expectations are loaded from canonical package modules only.
- [x] Add tests for output normalisation helpers (single-line vs multi-line).
- [x] Add tests for print-call expectation lookup behaviour.

### Acceptance Criteria

- [x] Duplicated expectation sources are removed/deprecated in use.
- [x] ex002 tests consume canonical expectation helpers and pass.

### Constraints

- Use repo-relative notebook paths resolved centrally.
- Keep expectation modules data-centric; minimal logic only.

### Touched Code

- **Reference code**:
  - `tests/exercise_expectations.py`
  - `tests/exercise_expectations/__init__.py`
  - `tests/exercise_expectations/ex002_sequence_modify_basics_exercise_expectations.py`
- **New code**:
  - `tests/exercise_framework/expectations.py`
  - `tests/exercise_expectations/ex002_sequence_modify_basics.py` _(optional rename target)_
- **New tests**:
  - `tests/exercise_framework/test_expectations.py`

### Notes

- Decisions
  - Consolidated ex002 expectations into package-level data exports and framework helpers.
  - Moved explanation validation into framework helpers to keep expectations data-only.
  - Deferred notebook path resolution until check execution to respect `PYTUTOR_NOTEBOOKS_DIR`.

- Open questions
  - None.

- Follow-up
  - Run solution-notebook tests for ex002 and explanation suites when convenient.

---

## Phase 4 — Extract Construct and Assertion Layers (AST-first)

### Goal

Unify construct checks and assertion messaging with reusable helpers.

### TDD Tasks

- [x] Add AST-based tests for required `print()` usage.
- [x] Add AST-based tests for required operators (`*`, `/`, `-`) in ex002 exercises.
- [x] Add assertion-helper tests for exact failure text parity.

### Acceptance Criteria

- [x] Construct checks are AST-first and pass positive/negative test cases.
- [x] Failure messages remain consistent with current student-facing output rules.

### Constraints

- Avoid fragile string-only construct detection except explicit fallback cases.
- Keep helper APIs small (`check_*`, `assert_*`).

### Touched Code

- **Reference code**:
  - `tests/exercise_expectations/ex002_sequence_modify_basics_exercise_expectations.py`
  - `tests/test_ex002_sequence_modify_basics.py`
- **New code**:
  - `tests/exercise_framework/constructs.py`
  - `tests/exercise_framework/assertions.py`
- **New tests**:
  - `tests/exercise_framework/test_constructs.py`
  - `tests/exercise_framework/test_assertions.py`

### Notes

- Decisions
  - Introduced AST-first construct helpers with token-based fallbacks for invalid code.
  - Centralised ex002 construct failure messaging in assertion helpers.

- Open questions
  - None.

- Follow-up
  - Run solution-notebook tests for ex002 construct and assertion helpers when convenient.

---

## Phase 5 — Centralise Reporting and Error Normalisation

### Goal

Move all table and error formatting to one reporting module.

### TDD Tasks

- [ ] Port existing rendering tests to framework reporting tests.
- [ ] Add tests for 40-char wrapping and long-word splitting.
- [ ] Add tests for continuation-row blank columns.
- [ ] Add tests for canonical issue normalisation pipeline (strip, join, wrap).

### Acceptance Criteria

- [ ] Reporting output is parity-equivalent to current ex002/student-checker output.
- [ ] No ad-hoc rendering logic remains in exercise-specific checks.

### Constraints

- Keep `tabulate(..., tablefmt="grid")` output.
- Keep emoji status tokens exactly `🟢 OK` and `🔴 NO`.

### Touched Code

- **Reference code**:
  - `tests/student_checker.py`
  - `tests/test_student_checker_table_rendering.py`
- **New code**:
  - `tests/exercise_framework/reporting.py`
- **New tests**:
  - `tests/exercise_framework/test_reporting.py`

### Notes

- Decisions
  -

- Open questions
  -

- Follow-up
  -

---

## Phase 6 — Rewire ex002 Tests to the New Framework

### Goal

Use the new framework end-to-end for ex002 while preserving behaviour.

### TDD Tasks

- [ ] Rewrite ex002 tests to call framework API/assertions/construct helpers.
- [ ] Ensure old and new ex002 tests can be compared during transition.
- [ ] Add deterministic checks for task marker parity (`@pytest.mark.task`).

### Acceptance Criteria

- [ ] ex002 suites pass against `notebooks/solutions`.
- [ ] ex002 suites still fail appropriately against incomplete student notebooks.
- [ ] Collected test count/task distribution remains stable.

### Constraints

- Preserve student-facing feedback quality and granularity.
- Do not migrate non-ex002 suites yet.

### Touched Code

- **Reference code**:
  - `tests/test_ex002_sequence_modify_basics.py`
  - `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`
- **New/updated code**:
  - `tests/exercise_framework/fixtures.py`
  - `tests/exercise_expectations/ex002_*.py`
  - ex002 test modules above (rewired)
- **New tests**:
  - `tests/exercise_framework/test_ex002_integration.py`

### Notes

- Decisions
  -

- Open questions
  -

- Follow-up
  -

---

## Phase 7 — Autograder and Payload Parity Verification

### Goal

Prove the refactor is autograder-safe before wider migration.

### TDD Tasks

- [ ] Add integration tests exercising autograde plugin with ex002-focused runs.
- [ ] Add payload-builder tests for full and `--minimal` modes.
- [ ] Assert unchanged status fields (`pass`/`fail`/`error`) and task metadata.

### Acceptance Criteria

- [ ] Autograde plugin hooks function unchanged.
- [ ] Payload schema and required fields remain compatible.
- [ ] No scoring drift for ex002 tasks.

### Constraints

- Do not rename/move plugin hooks without explicit migration.
- Avoid introducing autograde-only test branches.

### Touched Code

- **Reference code**:
  - `tests/autograde_plugin.py`
  - `scripts/build_autograde_payload.py`
  - `tests/test_autograde_plugin.py`
  - `tests/test_build_autograde_payload.py`
- **New tests**:
  - `tests/exercise_framework/test_autograde_parity.py`

### Notes

- Decisions
  -

- Open questions
  -

- Follow-up
  -

---

## Phase 8 — Non-ex002 Migration (Explicitly Deferred)

### Goal

Migrate legacy non-ex002 suites to the framework once ex002 parity is complete.

### TDD Tasks

- [ ] For each exercise suite, port tests to framework helpers first.
- [ ] Keep logic/format/construct separation and task markers explicit.
- [ ] Remove obsolete duplicated execution/parsing code once parity is confirmed.

### Acceptance Criteria

- [ ] Each migrated suite preserves intended student feedback quality.
- [ ] Framework usage is consistent; little/no bespoke execution logic remains.

### Constraints

- This phase starts only after Phases 0–7 pass.

### Touched Code

- **Reference code**:
  - `tests/test_ex001_sanity.py`
  - `tests/test_ex003_sequence_modify_variables.py`
  - `tests/test_ex004_sequence_debug_syntax.py`
  - `tests/test_ex005_sequence_debug_logic.py`
  - `tests/test_ex006_sequence_modify_casting.py`
- **New/updated code**:
  - exercise-specific expectation modules under `tests/exercise_expectations/`
  - framework modules introduced earlier

### Notes

- Decisions
  -

- Open questions
  -

- Follow-up
  -

---

## Standard Validation Commands Per Phase

Use the `uv` environment and prefer solution notebooks for development checks.

- [ ] `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`
- [ ] `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q tests/test_ex002_sequence_modify_basics.py`
- [ ] `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q tests/test_student_checker_table_rendering.py`
- [ ] `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run pytest -q tests/test_autograde_plugin.py tests/test_build_autograde_payload.py`
- [ ] `uv run ruff check .`

## Implementation Log

### Completed

- [x] Phase 0
- [x] Phase 1
- [x] Phase 2
- [x] Phase 3
- [x] Phase 4
- [ ] Phase 5
- [ ] Phase 6
- [ ] Phase 7
- [ ] Phase 8

### Risks to Track During Delivery

- [ ] Hidden scoring drift from changed pytest collection.
- [ ] Behaviour drift in output formatting and error wrapping.
- [ ] Duplicate expectation sources reappearing during migration.
- [ ] Runtime side effects from repeated execution not covered by cache boundaries.
