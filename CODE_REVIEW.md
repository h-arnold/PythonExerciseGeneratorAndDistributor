# Tidy Code Review — `h-arnold/issue73-progression-fix` vs `main`

**Review date**: 2026-06-08
**Reviewer**: Tidy Code Reviewer (automated + manual trace)
**Branch**: `h-arnold/issue73-progression-fix`
**Base**: `main`

---

## Files changed (10 files, +479 / −495)

| File | Change type | Lines |
|---|---|---|
| `scripts/verify_exercise_quality.py` | Modified | +29 / −4 |
| `tests/test_verify_exercise_quality.py` | Modified | +326 / −25 |
| `.github/agents/exercise_generation.md.agent.md` | Modified | +1 / −1 |
| `.github/agents/exercise_reviewer.md.agent.md` | Modified | +4 / −4 |
| `docs/developers/development.md` | Modified | +2 / −1 |
| `docs/developers/setup.md` | Modified | +2 / −0 |
| `docs/exercise-agents/exercise-generation-cli.md` | Modified | +1 / −1 |
| `docs/teachers/exercise-generation.md` | Modified | +7 / −1 |
| `ACTION_PLAN.md` | Rewritten | −185 net |
| `SPEC.md` | Deleted | −204 |

---

## What changed — summary

Two features, both in `scripts/verify_exercise_quality.py`:

### Feature 1 — Progression scan filtering (Section 1)

Modifies `_collect_code_cell_text()` to only include source from `exerciseN`-tagged code cells. Untagged infrastructure cells (self-checker, scratch, variant-setup) are excluded, eliminating false-positive progression warnings.

### Feature 2 — `--skip-empty-checks` flag (Section 2)

Adds a `--skip-empty-checks` CLI flag that suppresses the Gate F error when `student_checker_support.py` has an empty `CHECKS` list. This allows the quality verifier to pass during Phase 1 (notebook authoring) before checker definitions are written. All other Gate F errors (missing file, unimportable module, non-list CHECKS) are still reported.

### Documentation

Updated 6 files (4 agent docs + 2 developer docs) to reference `--skip-empty-checks`. Also added a solution-variant test command to the teacher-facing guide.

### Housekeeping

- `ACTION_PLAN.md` rewritten from the old Issue #66 plan to the Issue #73 plan.
- `SPEC.md` deleted (no longer relevant to current scope).

---

## Validation performed

| Check | Command | Result |
|---|---|---|
| Lint | `uv run ruff check` | All checks passed |
| Format | `uv run ruff format --check` | Already formatted |
| Tests (affected) | `uv run pytest tests/test_verify_exercise_quality.py -q` | 32 passed |
| Tests (solution, full) | `uv run python scripts/run_pytest_variant.py --variant solution -q` | All passed |
| Type checking | `uv run --with pyright pyright scripts/verify_exercise_quality.py tests/test_verify_exercise_quality.py` | No new regressions |

### Safe edits applied

- `ruff format` on both `scripts/verify_exercise_quality.py` and `tests/test_verify_exercise_quality.py` (trailing commas, line wrapping only).

---

## Manual trace findings

### Feature 1 — Control/data flow

`_collect_progression_findings()` → `_collect_code_cell_text(nb_student)` → iterates notebook cells → filters by `cell_type == "code"` → filters by `any(_EXERCISE_TAG_RE.match(tag) for tag in tags)` → joins sources.

The cell-tag helper `_cell_tags(cell)` returns `set[str]` (empty set when no metadata/tags present). The regex `^exercise(?P<n>\d+)$` strictly matches `exerciseN` — case-sensitive, no prefix variations. This is correct: the repo's notebook convention uses exact `exercise1`, `exercise2`, etc. tags.

**Key insight**: Self-checker cells contain `import os`, `os.environ["PYTUTOR_ACTIVE_VARIANT"] = ...`, and `run_notebook_checks(...)`. These were contributing to the collected text and triggering heuristic progression warnings. Excluding them is correct — they are infrastructure, not student exercise code.

### Feature 2 — Control/data flow

CLI `argparse` → `args.skip_empty_checks` → `main()` passes `skip_empty_checks=args.skip_empty_checks` to `_check_student_checker_support()`. Inside that function, only the `elif not checks and not skip_empty_checks:` branch is affected. All other error paths (missing file, import failure, non-list CHECKS) always fire regardless of the flag.

The flag is keyword-only (`*`, `skip_empty_checks: bool = False`) — good API hygiene.

### DRY improvement

The diff extracts the inline `_make_exercise_dir` logic from `TestGateFStudentCheckerSupport` into a module-level `_make_checker_test_exercise_dir` helper function. Both `TestGateFStudentCheckerSupport._make_exercise_dir` and `TestSection2SkipEmptyChecks._make_exercise_dir` now delegate to it. Clean extraction.

### Correctness

All 11 new/modified tests pass. Solution-variant regression suite passes. No false-negative risk: the progression filter is strictly additive (excludes cells) and the flag suppresses only one specific error condition.

---

## Remaining issues (low severity, pre-existing or cosmetic)

1. **`TestGateGExpectationsModule._make_exercise_dir`** (line 433) still duplicates the `_make_checker_test_exercise_dir` logic inline. Could delegate to the shared helper. Outside diff scope.

2. **`test_main_respects_skip_empty_checks_flag` docstring** says "returns exit code 0" but the test doesn't assert the return value. The captured-output assertions are sufficient for the behaviour under test; the docstring is slightly misleading.

3. **`docs/developers/setup.md`** has `--skip-empty-checks` in a comment above the command rather than on the command line, unlike other docs. Acceptable since the flag may not always apply in a walkthrough context, but mildly inconsistent.

4. **`scripts/verify_exercise_quality.py` (1248 lines)** and **`tests/test_verify_exercise_quality.py` (1042 lines)** both exceed the 500-line threshold. This is pre-existing and outside diff scope; splitting would be a separate refactoring effort.

---

## Documentation coverage

| Doc | Status |
|---|---|
| `docs/developers/project-structure.md` | Read — no conflicts |
| `docs/developers/execution-model.md` | Read — changes don't violate execution model |
| `docs/developers/testing-framework.md` | Read — no conflicts |
| `docs/developers/development.md` | Updated correctly |
| `docs/developers/setup.md` | Updated with comment (see remaining issue #3) |
| `.github/agents/exercise_generation.md.agent.md` | Updated correctly |
| `.github/agents/exercise_reviewer.md.agent.md` | Updated correctly |
| `docs/exercise-agents/exercise-generation-cli.md` | Updated correctly |
| `docs/teachers/exercise-generation.md` | Updated correctly |
| `docs/agents/tidy_code_review/automated_review.md` | Read — followed as workflow |
| `docs/agents/tidy_code_review/manual_review.md` | Read — followed as workflow |

---

## Verdict

**✅ Approved.** The changes are correct, well-tested (11 tests covering both features with unit and integration coverage), and documentation is updated across 6 files. No regressions in the solution-variant suite. The two features work together to enable the quality verifier in Phase 1 without sacrificing rigour in Phase 2.
