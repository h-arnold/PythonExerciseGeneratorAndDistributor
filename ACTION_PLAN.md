# Feature Delivery Plan (TDD-First)

## Read-First Context

Before writing or executing this plan:

1. Read the current `SPEC.md`.
2. Read any related workflow or companion planning doc.
3. Treat those documents as the source of truth for product behaviour, contracts, and layout rules.
4. Use this action plan to sequence delivery and testing; do not restate or redefine material already settled in the spec or layout docs.

## Scope and assumptions

### Scope

- Implement README exercise-list rendering in template packaging with construct headings and numbered links.
- Use metadata-backed `title` text and canonical student notebook links.
- Preserve sorted exercise-key ordering.
- Add and update packager unit tests covering the new rendering contract and error behaviour.

### Out of scope

- Changes to exercise selection API or CLI option set.
- Changes to canonical package layout and runtime variant semantics.
- Introducing alternative ordering schemes (for example, exercise-id ordering).

### Assumptions

1. Selected exercises provided to packager are already validated as known exercise keys.
2. Canonical metadata remains available at `exercises/<construct>/<exercise_key>/exercise.json`.
3. Existing README placeholders (`{TEMPLATE_NAME}`, `{EXERCISE_LIST}`) remain the rendering interface.

---

## Global constraints and quality gates

### Engineering constraints

- Keep API/entry points thin and delegate behaviour to services or controllers.
- Fail fast on invalid inputs and persistence failures.
- Avoid defensive guards that hide wiring issues.
- Keep changes minimal, localised, and consistent with repository conventions.
- Use British English in comments and documentation.

### TDD workflow (mandatory per section)

For each section below:

1. Red: write failing tests for the section's acceptance criteria.
2. Green: implement the smallest change needed to pass.
3. Refactor: tidy implementation with all tests still green.
4. Run section-level verification commands.

### Delegation mandatory-read gate (mandatory for sub-agent execution)

When a section is delegated to sub-agents, the plan must define and enforce mandatory documentation reads.

For each delegated phase (Testing Specialist, Implementation, Code Reviewer, Docs, De-Sloppification, or planning agents when used):

1. list required documentation file paths under that phase before delegation
2. require the sub-agent handoff to include Files read with explicit file paths
3. verify every mandatory file is listed before accepting the handoff
4. if any mandatory file is missing, return the work to the same sub-agent and block progression to the next phase

### Shared-helper planning gate (mandatory when helper changes are expected)

When a section is likely to introduce helper reuse, helper extension, or new shared helpers:

1. record helper decisions in that section before implementation
2. include: decision (`reuse` | `extend` | `new` | `keep local`), owning path, and call-site rationale
3. add planned helper entries to the relevant canonical docs with status `Not implemented`
4. during documentation pass, reconcile planned entries against actual implementation and update status/details accordingly

### Validation commands hierarchy

- Lint: `uv run ruff check .`
- Format check (if used): `uv run ruff format --check .`
- Type checks (if touched): `uv run pyright`
- Tests: `uv run pytest -q`
- Solution variant checks (when relevant): `uv run python scripts/run_pytest_variant.py --variant solution -q`

---

## Section 1 — Red tests for README rendering contract

### Objective

- Define failing tests for construct grouping, numbered links, sorted-key ordering, and packager-specific `ValueError` wrapping.

### Constraints

- Tests must target observable README behaviour, not implementation details.
- Keep assertions robust against unrelated whitespace changes.
- Preserve existing package validation test intent.

### Delegation mandatory reads (when sub-agents are used)

Testing Specialist mandatory docs:

- `SPEC.md`
- `docs/testing-framework.md`
- `docs/execution-model.md`
- `tests/template_repo_cli/test_packager.py`

Implementation mandatory docs:

- `SPEC.md`
- `scripts/template_repo_cli/core/packager.py`
- `template_repo_files/README.md.template`

Code Reviewer mandatory docs:

- `SPEC.md`
- `ACTION_PLAN.md`
- `tests/template_repo_cli/test_packager.py`
- `scripts/template_repo_cli/core/packager.py`

Other delegated agents (if used) mandatory docs:

- `docs/development.md`

### Shared helper plan (when helper changes are expected)

Helper decision entries:

1. Helper: README exercise-entry formatter in packager
   - Decision: `extend`
   - Owning module/path: `scripts/template_repo_cli/core/packager.py`
   - Call-site rationale: keeps README rendering logic local to packager ownership boundary
   - Relevant canonical doc target: `docs/development.md`
   - Planned doc status: `Implemented`

### Acceptance criteria

- Existing README test coverage is extended with failing tests for grouped numbered links and metadata title usage.
- Failing test coverage exists for wrapped `ValueError` behaviour with exercise-key context.
- Failing test coverage explicitly verifies wrapped exceptions preserve root cause via chaining.
- Tests encode sorted exercise-key ordering expectation.

### Required test cases (Red first)

Backend model tests:

1. None.

Backend controller tests:

1. None.

API layer tests:

1. None.

Integration tests:

1. Add/update `test_generate_readme` assertions for grouped numbered links and canonical student notebook hrefs.
2. Add failure-path test where metadata loading/title access fails and packager raises `ValueError` with exercise-key context.
3. Assert failure-path wrapping preserves root-cause chaining (for example, `exc_info.value.__cause__ is not None`).
4. Add ordering test with multi-construct input to confirm sorted-key-derived output order.

### Section checks

- `uv run pytest -q tests/template_repo_cli/test_packager.py -k readme`
- Mandatory-read evidence gate passed for all delegated handoffs in this section.
- Shared-helper planning entries are present when helper changes are expected.
- Planned helper entries were added to relevant canonical docs with status `Not implemented` before implementation starts.

### Optional documentation follow-through

- None.

### Implementation notes / deviations / follow-up

- Implementation notes: Completed red phase. Added failing README contract tests in tests/template_repo_cli/test_packager.py for construct headings, numbered markdown links, metadata title text, canonical student notebook hrefs, sorted exercise-key ordering, and ValueError wrapping with cause chaining.
- Deviations from plan: None.
- Follow-up implications for later sections: Section 2 must implement metadata-backed README rendering and error wrapping so these tests pass.
- Section checklist status:
   - red tests added: complete
   - red review clean: complete
   - green implementation complete: deferred to Section 2
   - green review clean: deferred to Section 2
   - checks passed: red check executed with expected failures
   - action plan updated: complete
   - commit created: complete (b087512, test(packager): add red README rendering contract tests (section 1))
   - push completed: complete (branch feat/READMELinks)

---

## Section 2 — Green implementation in packager and template

### Objective

- Implement the smallest packager/template changes that satisfy Section 1 tests.

### Constraints

- Preserve existing `generate_readme(...)` call flow from CLI.
- Keep placeholder replacement contract unchanged.
- Maintain canonical packaged path rules.

### Delegation mandatory reads (when sub-agents are used)

Testing Specialist mandatory docs:

- `SPEC.md`
- `tests/template_repo_cli/test_packager.py`

Implementation mandatory docs:

- `SPEC.md`
- `scripts/template_repo_cli/core/packager.py`
- `scripts/template_repo_cli/cli.py`
- `template_repo_files/README.md.template`

Code Reviewer mandatory docs:

- `SPEC.md`
- `ACTION_PLAN.md`
- `scripts/template_repo_cli/core/packager.py`
- `template_repo_files/README.md.template`
- `tests/template_repo_cli/test_packager.py`

Other delegated agents (if used) mandatory docs:

- `docs/development.md`
- `docs/project-structure.md`

### Shared helper plan (when helper changes are expected)

Helper decision entries:

1. Helper: construct display normaliser (snake_case to title-case words)
   - Decision: `new`
   - Owning module/path: `scripts/template_repo_cli/core/packager.py`
   - Call-site rationale: required for deterministic construct-heading rendering
   - Relevant canonical doc target: `docs/development.md`
   - Planned doc status: `Implemented`
2. Helper: grouped README list composer
   - Decision: `new`
   - Owning module/path: `scripts/template_repo_cli/core/packager.py`
   - Call-site rationale: isolates formatting from I/O path and improves testability
   - Relevant canonical doc target: `docs/development.md`
   - Planned doc status: `Implemented`

### Acceptance criteria

- README output contains construct headings and numbered links using metadata titles.
- Link hrefs point to canonical student notebook export paths.
- Ordering remains sorted by exercise key.
- Failures in metadata/render path are wrapped in packager-specific `ValueError` with exercise-key context.

### Required test cases (Red first)

Backend model tests:

1. None.

Backend controller tests:

1. None.

API layer tests:

1. None.

Integration tests:

1. Section 1 tests pass without weakening assertions.

### Section checks

- `uv run pytest -q tests/template_repo_cli/test_packager.py -k readme`
- Mandatory-read evidence gate passed for all delegated handoffs in this section.
- Shared-helper planning entries are present when helper changes are expected.
- Planned helper entries were added to relevant canonical docs with status `Not implemented` before implementation starts.

### Optional documentation follow-through

- If helper methods are introduced, add concise docstrings to capture grouping and ordering rules.

### Implementation notes / deviations / follow-up

- Implementation notes: Implemented metadata-backed README rendering in scripts/template_repo_cli/core/packager.py with sorted exercise-key iteration, construct grouping, title-based numbered markdown links, canonical student notebook hrefs, and ValueError wrapping with exercise-key context and chained cause.
- Deviations from plan: None.
- Follow-up implications for later sections: Section 3 may only refactor for clarity with no behaviour drift.
- Section checklist status:
   - red tests added: complete in Section 1
   - red review clean: complete in Section 1
   - green implementation complete: complete
   - green review clean: complete
   - checks passed: complete (uv run pytest -q tests/template_repo_cli/test_packager.py -k readme; uv run ruff check scripts/template_repo_cli/core/packager.py tests/template_repo_cli/test_packager.py)
   - action plan updated: complete
   - commit created: complete (ff7eea7, feat(packager): render README grouped numbered notebook links (section 2))
   - push completed: complete (branch feat/READMELinks)

---

## Section 3 — Refactor and local hardening

### Objective

- Refine implementation for readability and maintainability without changing behaviour.

### Constraints

- No behavioural drift from SPEC contract.
- Keep public packager interface stable unless strictly necessary.

### Delegation mandatory reads (when sub-agents are used)

Testing Specialist mandatory docs:

- `SPEC.md`
- `tests/template_repo_cli/test_packager.py`

Implementation mandatory docs:

- `SPEC.md`
- `scripts/template_repo_cli/core/packager.py`

Code Reviewer mandatory docs:

- `SPEC.md`
- `ACTION_PLAN.md`
- `scripts/template_repo_cli/core/packager.py`
- `tests/template_repo_cli/test_packager.py`

Other delegated agents (if used) mandatory docs:

- `docs/development.md`

### Shared helper plan (when helper changes are expected)

Helper decision entries:

1. Helper: README list composition helpers from Section 2
   - Decision: `reuse`
   - Owning module/path: `scripts/template_repo_cli/core/packager.py`
   - Call-site rationale: keep behaviour centralised and avoid duplicate formatting logic
   - Relevant canonical doc target: `docs/development.md`
   - Planned doc status: `Implemented`

### Acceptance criteria

- Implementation remains minimal and clear.
- Section 1 and Section 2 behaviour stays green after refactor.

### Required test cases (Red first)

Backend model tests:

1. None.

Backend controller tests:

1. None.

API layer tests:

1. None.

Integration tests:

1. Re-run README-focused packager tests.

### Section checks

- `uv run pytest -q tests/template_repo_cli/test_packager.py -k readme`
- `uv run ruff check scripts/template_repo_cli/core/packager.py tests/template_repo_cli/test_packager.py`
- Mandatory-read evidence gate passed for all delegated handoffs in this section.
- Shared-helper planning entries are present when helper changes are expected.
- Planned helper entries were added to relevant canonical docs with status `Not implemented` before implementation starts.

### Optional documentation follow-through

- None unless refactor introduces non-obvious helper interactions.

### Implementation notes / deviations / follow-up

- Implementation notes: Refactored README generation by extracting helper methods in scripts/template_repo_cli/core/packager.py: _load_readme_template, _readme_entry_from_exercise_key, and _render_grouped_readme_sections. Behaviour is unchanged from Section 2.
- Deviations from plan: None.
- Follow-up implications for later sections: Regression checks should confirm broad packager stability beyond the readme-focused subset.
- Section checklist status:
   - red tests added: complete in Section 1
   - red review clean: complete in Section 1
   - green implementation complete: complete
   - green review clean: complete
   - checks passed: complete (uv run pytest -q tests/template_repo_cli/test_packager.py -k readme; uv run ruff check scripts/template_repo_cli/core/packager.py tests/template_repo_cli/test_packager.py)
   - action plan updated: complete
   - commit created: complete (16a2b7b, refactor(packager): extract README rendering helpers (section 3))
   - push completed: complete (branch feat/READMELinks)

---

## Regression and contract hardening

### Objective

- Confirm the README feature and packaging contract remain stable across affected test surfaces.

### Constraints

- Prefer focused tests first, then broader checks if needed.

### Acceptance criteria

- README behaviour tests and touched lint checks pass.
- Existing package integrity tests remain green for affected surfaces.

### Required test cases/checks

1. Run touched packager tests.
2. Run related template integration checks if README assertions are present.
3. Run lint checks for touched files.
4. Verify mandatory-read evidence (Files read) is complete for every delegated regression handoff.

### Section checks

- `uv run pytest -q tests/template_repo_cli/test_packager.py`
- Optional: `uv run pytest -q tests/template_repo_cli/test_integration.py -k readme`
- `uv run ruff check scripts/template_repo_cli/core/packager.py tests/template_repo_cli/test_packager.py`

### Implementation notes / deviations / follow-up

- Implementation notes: Completed regression checks for the touched surfaces. Command results: uv run pytest -q tests/template_repo_cli/test_packager.py passed; uv run ruff check scripts/template_repo_cli/core/packager.py tests/template_repo_cli/test_packager.py passed; optional uv run pytest -q tests/template_repo_cli/test_integration.py -k readme reported no selected tests (38 deselected).
- Deviations from plan: None.

---

## Documentation and rollout notes

### Objective

- Keep documentation and comments aligned with implemented README behaviour.

### Constraints

- Only modify docs relevant to touched packager/template surfaces.

### Acceptance criteria

- Documentation accurately reflects grouped numbered README rendering and error semantics.
- Any deviations or caveats are documented.

### Required checks

1. Verify packager docstrings and comments reflect grouped numbered rendering.
2. Verify notes/deviations fields are filled during implementation.
3. Verify mandatory-read evidence (Files read) is complete for delegated docs/review handoffs.
4. Reconcile planned shared-helper entries in canonical docs: keep `Not implemented` where still pending, and update implemented entries where delivered.

### Optional documentation review

- Confirm whether construct-heading formatting and ordering rationale needs preserving in inline comments/docstrings.

### Implementation notes / deviations / follow-up

- Implementation notes: Updated docs/development.md to reflect delivered grouped numbered README rendering semantics, sorted exercise-key ordering, canonical student notebook href targets, and wrapped ValueError error semantics with exercise-key context and chained causes. Reconciled helper tracker status against implementation in scripts/template_repo_cli/core/packager.py: `_readme_entry_from_exercise_key` and `_render_grouped_readme_sections` are implemented; construct display normalisation remains inlined rather than extracted as a standalone helper.
- Deviations from plan: The planned standalone construct display normaliser helper was not introduced; equivalent behaviour is implemented inline in `_readme_entry_from_exercise_key`.
- Follow-up implications: If construct display rules grow beyond current title-casing, extract a dedicated normaliser helper to keep rendering concerns isolated.

---

## Suggested implementation order

1. Section 1 (Red tests for README rendering contract)
2. Section 2 (Green implementation in packager and template)
3. Section 3 (Refactor and local hardening)
4. Regression and contract hardening
5. Documentation and rollout notes
