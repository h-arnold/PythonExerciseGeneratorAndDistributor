# ACTION PLAN — Issue #73: False-positive progression warnings in `verify_exercise_quality.py`

## Summary

A 3-section TDD plan. Tests are written or updated **before** implementation in each section. Sections are sequential but Section 3 (documentation) can run in parallel with Sections 1–2 once the CLI flag exists.

## Root cause

`_collect_code_cell_text()` concatenates **all** code cells — including untagged infrastructure cells (scratch cell, self-check cell with `import os` / `from ... import ...`) — and passes them to `_scan_for_progression_violations()`. This means:
- The `lists` pattern (`\[[^\]]*\]`) matches `list[ExerciseCheckDefinition]` in `student_checker_support.py` and markdown `[⌨️: value]` in notebook cells.
- The `libraries` pattern (`^\s*import\b`) matches `import os` / `from ... import ...` in the auto-appended checker cell.

**Secondary problem**: `_check_student_checker_support()` (Gate F) always errors on freshly scaffolded exercises because the `CHECKS` list is still empty. During Phase 1 (notebook authoring) this is expected, so a `--skip-empty-checks` flag is needed.

---

## Section 1 — Filter progression scanning to only `exerciseN` tagged cells

**Objective**: Modify `_collect_code_cell_text()` (and any other scan entry points) to skip cells that do not have an `exerciseN` tag. Infrastructure cells (scratch cell, self-check cell, explanation cells) are not student code and should not be scanned for progression violations.

**Files**:
- `scripts/verify_exercise_quality.py` — modify `_collect_code_cell_text()` to filter by `exerciseN` tags
- `tests/test_verify_exercise_quality.py` — add tests for the new filtering behaviour

**Acceptance criteria**:
- [ ] `_collect_code_cell_text()` only includes cells with an `exerciseN` tag (e.g. `exercise1`, `exercise2`)
- [ ] Untagged code cells (scratch cell, self-check cell) are excluded from the concatenated text
- [ ] Markdown cells with `explanationN` tags are excluded (not code, already excluded by cell_type filter, but confirm)
- [ ] Non-notebook files (e.g. `student_checker_support.py`) are not scanned for progression violations (they are not notebooks, so `_collect_code_cell_text` is never called on them, but confirm the scan path)
- [ ] `_scan_for_progression_violations()` is only called via `_collect_progression_findings()`, which calls `_collect_code_cell_text()` — if that function filters correctly, the fix is complete
- [ ] Existing tests still pass

**Required test cases**:

1. **`test_collect_code_cell_text_excludes_untagged_cells`**: Create a notebook with tagged exercise1 code cell, an untagged scratch code cell, and an untagged self-check code cell. Assert `_collect_code_cell_text()` only returns the exercised tagged cell's source.
2. **`test_collect_code_cell_text_includes_all_exerciseN_cells`**: Create a notebook with exercise1, exercise2, exercise3 tagged cells plus untagged cells. Assert all three exerciseN cells are included.
3. **`test_collect_code_cell_text_excludes_explanationN_cells`**: Create a notebook with an explanation1 markdown cell (already excluded by cell_type filter, but verify). Assert it's not in the result.
4. **`test_progression_scan_ignores_self_check_imports`**: Create a notebook with only an untagged self-check cell containing `import os` / `from ... import ...`. Assert `_collect_progression_findings()` returns empty (no `libraries` progression violation).
5. **`test_progression_scan_still_detects_real_violations`**: Create a notebook with an exercise1 cell containing a later-construct pattern (e.g. `def foo():` in a `sequence` exercise). Assert the violation is still detected — this guards against over-filtering.

**Section checks**:
- All 6 new tests pass
- All existing `test_verify_exercise_quality.py` tests pass
- `ruff check` passes

**Review point**: Confirm the filter is correct and no real violations are missed.

---

## Section 2 — Add `--skip-empty-checks` flag

**Objective**: Add a `--skip-empty-checks` CLI flag to `verify_exercise_quality.py` that suppresses the Gate F error when `CHECKS` list in `student_checker_support.py` is empty. This allows the verifier to be used during Phase 1 (notebook authoring) when tests and checker support have not yet been written.

**Files**:
- `scripts/verify_exercise_quality.py` — add `--skip-empty-checks` to the argument parser and modify `_check_student_checker_support()` (or its call site) to respect the flag
- `tests/test_verify_exercise_quality.py` — add tests for the new flag

**Acceptance criteria**:
- [ ] `--skip-empty-checks` flag is accepted by the CLI
- [ ] Without `--skip-empty-checks`, empty `CHECKS` still produces an ERROR (existing behaviour preserved)
- [ ] With `--skip-empty-checks`, empty `CHECKS` produces no finding
- [ ] With `--skip-empty-checks`, missing `student_checker_support.py` still produces an ERROR (file must exist regardless)
- [ ] With `--skip-empty-checks`, unimportable `student_checker_support.py` still produces an ERROR (file must be valid regardless)
- [ ] With `--skip-empty-checks`, non-empty `CHECKS` still produces no finding (same as without flag)
- [ ] Existing tests still pass

**Required test cases**:

1. **`test_skip_empty_checks_suppresses_empty_checks`**: With `--skip-empty-checks`, verify that empty `CHECKS` produces no finding.
2. **`test_skip_empty_checks_does_not_suppress_missing_file`**: With `--skip-empty-checks`, verify that missing `student_checker_support.py` still produces an ERROR.
3. **`test_skip_empty_checks_does_not_suppress_unimportable_file`**: With `--skip-empty-checks`, verify that unimportable `student_checker_support.py` still produces an ERROR.
4. **`test_skip_empty_checks_non_empty_checks_still_pass`**: With `--skip-empty-checks` and non-empty `CHECKS`, verify no finding.
5. **`test_main_respects_skip_empty_checks_flag`**: Integration test — run `main()` with the flag and verify exit code 0 when only Gate F would have failed.

**Implementation notes**:
- Add `--skip-empty-checks` as a `store_true` action in `_build_parser()`.
- Pass the flag value through `main()` to `_check_student_checker_support()` (or use a module-level/function-level parameter).
- Modify `_check_student_checker_support()` to accept an optional `skip_empty_checks: bool = False` parameter.
- When `skip_empty_checks=True` and `CHECKS` is an empty list, return `[]` instead of the ERROR finding.

**Section checks**:
- All 5 new tests pass
- All existing `test_verify_exercise_quality.py` tests pass
- `ruff check` passes

**Review point**: Confirm the flag does not suppress legitimate errors (missing file, unimportable file).

---

## Section 3 — Documentation updates

**Objective**: Update the exercise generation and reviewer agent instructions to include the `--skip-empty-checks` flag in their `verify_exercise_quality.py` commands.

**Files**:
- `.github/agents/exercise_generation.md.agent.md` — add `--skip-empty-checks` to the quality verifier command in the Phase 1 workflow
- `.github/agents/exercise_reviewer.md.agent.md` — add `--skip-empty-checks` to the automation helper commands in Gates B, C, and F

**Acceptance criteria**:
- [ ] Exercise generation agent's Phase 1 quality gate command includes `--skip-empty-checks`
- [ ] Exercise reviewer agent's Gate B command includes `--skip-empty-checks`
- [ ] Exercise reviewer agent's Gate C command includes `--skip-empty-checks`
- [ ] Exercise reviewer agent's Gate F command includes `--skip-empty-checks`
- [ ] All references to `verify_exercise_quality.py` in both agent files use the flag when running during Phase 1

**Required test cases**: None (documentation only — review manually or with a structural grep).

**Section checks**:
- Grep both agent files for `verify_exercise_quality.py` — each occurrence should either include `--skip-empty-checks` or have a justification for not including it
- `ruff check` passes (agent files are markdown, not Python, so this is a no-op)

**Review point**: Ensure the flag is added to Phase 1 commands only (not Phase 2 commands where the checker should be populated).

---

## Cross-cutting checks

- [ ] All sections complete
- [ ] All new tests pass
- [ ] All existing tests pass (run `uv run pytest tests/test_verify_exercise_quality.py -q`)
- [ ] Full suite passes: `uv run pytest -q`
- [ ] `ruff check . --fix` passes
- [ ] Commits are clean and well-scoped
