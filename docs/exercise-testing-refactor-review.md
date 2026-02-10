# Review Feedback: `docs/exercise-testing-new.md`

This review identifies likely implementation risks and gaps between the proposed architecture and the current codebase behaviour.

## 1) Backwards-compatibility gap for notebook entry points (high risk)

Current notebooks directly import and run `tests.student_checker` functions (`check_exercises()` or `check_ex002_notebook()`).

If the refactor moves or renames these without keeping compatibility shims, notebook check cells will break immediately.

**Recommendation**: keep `tests/student_checker.py` as a thin compatibility layer that delegates to the new framework (`reporting` + runner/harness API), at least for one migration cycle.

## 2) No explicit migration plan for existing tests that import private helpers (high risk)

There are direct tests for private rendering helpers (`_render_grouped_table_with_errors`, `_strip_exercise_prefix`, `_wrap_text_to_width`).

The plan says to centralise table rendering in `reporting.py`, but it does not define whether these tests should be migrated, aliased, or replaced. Without a plan, the refactor is likely to cause avoidable breakage.

**Recommendation**: either:
- preserve these helper names temporarily as wrappers, or
- migrate tests in the same commit and publish a clear compatibility boundary.

## 3) Duplication already exists in expectations modules (medium risk)

The repository currently contains both:
- `tests/exercise_expectations.py`, and
- `tests/exercise_expectations/__init__.py`

Both define overlapping constants/functions. The current proposal adds more per-exercise expectations modules, but does not specify how to eliminate this existing duplication. Leaving this unresolved will make the new structure harder to reason about and easier to desynchronise.

**Recommendation**: define one canonical import path and deprecate/remove the duplicate module.

## 4) ex002 checks currently rerun notebook code repeatedly; plan does not cover execution caching (medium risk)

For ex002, logic and formatting checks both call runtime execution separately for the same exercise cell. This repeats execution and can amplify side effects in exercises that read input or mutate state.

The new architecture describes separation of concerns, but not whether execution results/output should be cached per exercise run.

**Recommendation**: add an explicit execution model (e.g., one execution per `(notebook, tag)` per check pass, with reusable captured output/code snapshots).

## 5) Construct checking API in the proposal is too weak unless AST-based checks are mandated (medium risk)

Current construct checks in ex002 use string containment (`"print("`, operator character checks). This can pass on comments/strings and miss structurally incorrect code.

The proposal suggests reusable construct helpers but does not require AST-based implementation.

**Recommendation**: specify AST-backed construct checks as the default for Python syntax constructs, with clear fallback rules when parsing fails.

## 6) Error normalisation scope is underspecified for non-ex002 exercises (medium risk)

The spec defines strict error text/formatting behaviour for ex002 (prefix stripping, join with `; `, 40-char wrapping), but the proposed `reporting.py` is general-purpose.

Without a policy for other exercises, different callers may emit inconsistent error styles.

**Recommendation**: define a canonical error normalisation pipeline in `reporting.py` and require all student-facing checks to use it.

## 7) Autograder compatibility section is good, but missing a hard constraint on test cardinality (medium risk)

Autograding is one point per collected test, and this repo already contains two ex002 suites (`tests/test_ex002_sequence_modify_basics.py` and `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`).

A refactor that accidentally duplicates/renames collected tests can silently change scoring.

**Recommendation**: add a compatibility check that verifies expected collected test counts/task distribution before and after migration.

## 8) Path-handling consistency is not addressed (low-to-medium risk)

Current expectations use mixed path styles (relative strings in shared expectations, absolute `Path(...).resolve()` in ex002 expectations). The resolver supports overrides, but mixed conventions increase maintenance overhead and can create subtle path assumptions.

**Recommendation**: standardise notebook path declarations (prefer relative notebook paths resolved only through a single resolver API).

## 9) Proposed module list misses an explicit public facade/harness (low-to-medium risk)

The plan lists modules, but not a single orchestrator API that external callers (scripts, notebooks, tests, agents) should depend on.

Without this, callers are likely to import internals directly, recreating coupling.

**Recommendation**: add a small public harness module (for example, `exercise_framework/api.py`) exposing stable entry points for:
- run all checks
- run one notebook
- run detailed exercise checks
- render student-facing output

## 10) Migration sequencing does not include parity gates at each step (low risk, high value)

The migration steps are sensible, but they do not require measurable parity checkpoints between steps.

**Recommendation**: after each major extraction step, run parity checks for:
- summary table format,
- ex002 grouped table format,
- `PYTUTOR_NOTEBOOKS_DIR` fallback behaviour,
- autograde payload schema and status mapping.

This will reduce debugging time and prevent regressions from stacking.
