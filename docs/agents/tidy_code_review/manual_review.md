# Tidy Code Reviewer — Manual Review (KISS & DRY)

This document contains the manual review instructions for the Tidy Code Reviewer. Invoke it after the automated phase finishes and a human-style reasoning pass is required.

## KISS & DRY (overview)

- KISS (Simplicity checks):
  - Cyclomatic complexity per function — flag when CC > 8 (too many branches or conditional paths).
  - Function length — flag when > 120 lines (likely multiple responsibilities).
  - Nesting depth — flag when > 3 (control flow becoming hard to follow).
  - Look for repeated conditionals, nested loops, or complex boolean expressions that could be simplified.
  - Check for functions that mix data retrieval, transformation, and output — suggest extraction of concerns.

- DRY (Duplication checks):
  - Manually scan for repeated logic patterns across files, especially helper functions or validation logic.
  - Flag duplicated blocks >= 5 LOC present in >= 2 files by default.
  - Suggest extraction targets (e.g., new utility in `scripts/` or `tests/helpers.py`) and refactor strategy.

## Tidy code principles (prompt for reviewer)

- KISS (Keep It Simple): prefer simple, explicit logic. Check CC, nesting depth, and long functions; flag complex functions for refactor.
- DRY (Don't Repeat Yourself): detect duplicated blocks (>= duplication_min_lines); suggest extraction to utils/helpers.
- Readability & naming: meaningful names, consistent formatting, short expressions. Flag unclear/one-letter names and long inline expressions.
- Single Responsibility: functions/classes should do one thing. Flag multi-responsibility functions for extraction.
- Small functions & modules: prefer short functions (< max_function_length) and small modules; suggest splitting where appropriate.
- If a function needs more than 5 parameters, refactor to use a configuration object or class.
- Explicit error handling: no silent excepts; ensure clear exceptions and helpful messages.
- Deterministic, fast tests: require unit tests for changed code, cover edge cases, avoid randomness/time/network in tests.
- No dead code or commented-out code: remove unused imports, variables, and unreachable statements.
- No magic numbers/strings: replace with named constants or enums with clear names.
- Minimise side effects & global state: prefer pure functions or clearly documented side effects; flag implicit global mutation.
- Minimal/explicit dependencies: avoid unnecessary third-party libs; prefer stdlib or documented, pinned dependencies.
- Documentation & docstrings: public APIs documented; update docs and README when behaviour or CLI/options change.
- Security & input validation: validate external inputs, sanitize data, avoid insecure patterns.
- Performance when measured: don't preoptimize; add micro-benchmarks for hotspots and document trade-offs.
- Consistent style & linting: run and fix ruff/formatting rules; ensure CI lints pass.
- Type hints for public APIs: prefer modern annotations; check mismatches with tests or usage.
- Type guards must be in a separate file near the main module to avoid cluttering business logic.
- Backwards compatibility & deprecation: document breaking changes, provide migration notes or deprecation warnings.
- Commit quality & scope: small, focused commits with clear messages and tests; include CHANGELOG or PR description for notable changes.
- Testability & observability: code should be easily unit-testable; include logs/metrics where helpful for debugging.
- Respect licences & third-party code: do not modify vendored/third-party code; check license compatibility.

For each principle: note a concise rationale, an automated detection heuristic (tool/metric), and an actionable suggestion (fix, refactor, or docs).
Defaults and thresholds are configurable via `agent-config.yml`.

## Naming and folder organisation

- File and module naming
  - Use snake_case for module and file names (e.g., `my_module.py`, `string_utils.py`).
  - Use CamelCase for classes (e.g., `HtmlParser`) and UPPER_SNAKE for constants.
  - Keep module surface area small and explicit: prefer small modules with a clear single responsibility.

- Packages and splitting modules
  - When a module grows or has distinct responsibilities, convert it to a package:
    - Create a folder `my_module/` with `__init__.py`.
    - Split parts into cohesive submodules (e.g., `my_module/core.py`, `my_module/_helpers.py`, `my_module/cli.py`).
    - Keep truly internal pieces prefixed with an underscore (e.g., `_helpers.py`).
    - Re-export the public API from `__init__.py` so callers use `from my_module import X`.
  - Aim for shallow, focused packages. If a package becomes complex, consider further subpackages.

- Type hints, guards and shared types
  - Put type guard helpers adjacent to the code they protect:
    - Prefer `module_typeguards.py`.
  - For cross-cutting TypedDicts or widely used type definitions, use a small `types/` package at repo root (e.g., `types/__init__.py`).
  - Keep type-only modules small and documented; avoid circular imports by placing shared TypedDicts in `types/` if necessary.

- Tests organisation
  - Mirror the package/module layout under `tests/`. Examples:
    - `my_module.py` -> `tests/test_my_module.py`
    - `my_module/` package -> `tests/test_my_module_api.py`, `tests/test_my_module_core.py`
  - Use pytest naming conventions: files `test_*.py`, functions `test_*`.
  - Keep tests fast and deterministic (no network, sleep, or randomness).
  - Each public behaviour should have positive and edge-case tests (follow repository testing standards).
  - For notebooks and exercises, continue to use the existing notebook test patterns: `tests/test_exNNN_*.py` and `PYTUTOR_NOTEBOOKS_DIR` as described elsewhere.

- Practical rules of thumb
  - Small, well-documented modules are easier to test and review; prefer composition over monoliths.
  - Keep type guards and tiny helpers close to the code they protect to reduce cognitive overhead and avoid import cycles.
  - When splitting code, update and add tests at the same time and expose only the intended public API from packages.

## Workflow (MUST do vs OPTIONAL) - manual steps

### MUST do (manual steps)

1. Review the automated phase summary (change list, diagnostics, tests run). Capture follow-up actions in the calling agent's task list if available; otherwise record them in the review notes.
2. Ensure the uv-managed environment is used for any commands that must be rerun (for example, `uv run pytest -q` with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`). Only rerun tooling if additional evidence is needed.
3. **Trace code execution**: For each changed file, manually trace inputs → outputs. Identify assumptions, edge cases, and data flow. Check for simpler implementations or reuse of existing helpers.
4. **Validate no re-implementation**: Ensure changes do not duplicate existing functionality elsewhere in the codebase. Flag opportunities to consolidate or reuse.
5. **Check separation of concerns**: Verify functions/classes have clear single responsibilities. Flag functions handling multiple concerns for potential extraction.
6. **Review code duplication**: Manually scan for repeated logic patterns, especially across module boundaries. Suggest extraction to shared utilities.
7. **Verify adherence to standards**: Check that changed code follows the repo's coding conventions, naming patterns, and architectural principles outlined in the docs.
   1. Focus particularly hard on unnessecary defensive guards that result in silent failures or obscure error handling. Code **must** fail fast and loudly with clear exceptions bubbled up.
8. **Compare docs against the code**: Ensure any behavioural changes are reflected in documentation, README, or docstrings. Flag discrepancies for update.
9. **Check the total length of files**: If a file exceeds 500 lines, suggest splitting into smaller modules when sensible.
10. **Prepare findings report**: Document control/data flow observations, suggested refactors requiring human judgement, and patches for non-trivial changes. Recommend draft PRs where extensive follow-up work is needed.

### OPTIONAL (manual)

- If a manual trace was deferred due to many changes, suggest a scoped follow-up review focusing solely on control/data flow and code duplication patterns.

## Output to calling agent (expanded)

Return a concise summary containing:

- **Verification**: list files confirmed with what changed.
- **Edits made**: all safe changes you applied (file + short reason).
- **Manual trace & reuse check**: brief notes on control/data flow, any simpler implementation identified, and whether existing helpers could replace new code.
- **Trace status**: state whether the manual trace was performed or deferred; if deferred, note that a follow-up pass is required.
- **KISS findings**: list of functions flagged with CC, MI, length, nesting, and suggested refactors.
- **DRY findings**: list of duplicated regions with file ranges and suggested extraction/merge locations.
- **Docs findings**: which docs were checked and any discrepancies found.
- **Suggested patches/PRs**: list of non-automated refactors with a short diff or PR URL (if created).
- **Remaining issues**: anything you did not fix (reason + suggestion).
- **Lint results**: summary of remaining diagnostics.

### Exit criteria

The manual review should finish when the following are satisfied:

1. Completed all MUST do manual steps (trace, duplication check, separation of concerns, standards adherence)
2. Documented control/data flow observations and suggested refactors
3. Generated patch files or draft PRs for non-trivial refactors with clear rationale
4. Return findings to calling agent for final report assembly (see main agent instructions for report format)

## Quick reference card

- **Inputs**: Outputs from Phase 1 (automated review findings and issue count)
- **Guardrails**: No notebook/vendor/generated file edits. Focus on code tracing and higher-level concerns.
- **Manual steps**: (1) trace code execution, (2) check duplication, (3) verify separation of concerns, (4) verify standards adherence
- **Coverage**: All changed files receive manual trace; prioritise complex interactions
- **Output**: Return detailed findings (control/data flow notes, KISS/DRY findings, suggested patches/PRs) to calling agent
- **Report format**: Handled by main agent (see main agent instructions for structure)
