# SLOP REVIEW — Issue #66 + Exercise Scaffolder Refactor

**Date**: 2026-06-05
**Scope**: `scripts/exercise_scaffolder/`, `scripts/new_exercise.py`, `scripts/verify_exercise_quality.py` (Gates F–I), and their test suites

---

## Summary: **Needs Improvement**

The refactor is well-structured and the TDD discipline is evident. However, there is **one confirmed bug** (gaps scaffold producing literal `{i}` in notebooks), **significant code duplication** between Make/Modify classes and their test suites, and a few smaller dead-parameter and inconsistency issues. No dead imports or unused functions were found — the Stage 7 cleanup was effectively done during Stage 3 wiring.

---

## 🔴 Critical

### 1. Gaps scaffold emits literal `{i}` instead of exercise number

- **Location**: `scripts/exercise_scaffolder/gaps.py`, lines ~48–49 (inside `_build_exercise_cells()`)
- **Evidence**: The source string is a plain string, not an f-string:

  ```python
  "source": [
      "# Exercise {i} — replace this scaffold with the real "
      "partially-written program.\n",
      ...
  ],
  ```

  Running the scaffolder confirms the output:
  ```
  '# Exercise {i} — replace this scaffold with the real partially-written program.\n'
  ```

- **Why it matters**: This is a **bug**, not a style issue. Every scaffolded gaps notebook will contain the literal text `{i}` instead of the actual exercise number (e.g., `Exercise 1`). Students will see confusing placeholder text in their notebooks.

- **Recommended fix**: Change to an f-string:

  ```python
  f"# Exercise {i} — replace this scaffold with the real "
  f"partially-written program.\n",
  ```

- **Note**: No test caught this because:
  - `test_exercise_scaffolder_gaps.py` tests for `"# YOUR CODE HERE"` content but does not check that the exercise number is rendered correctly in the source text.
  - The `test_new_exercise.py` integration tests focus on debug/make/modify types, not gaps.

---

## 🟡 Improvement

### 2. `MakeScaffold` and `ModifyScaffold` are line-for-line identical **IGNORE - THIS IS INTENTIONAL PER ACTION_PLAN**

- **Location**: `scripts/exercise_scaffolder/make.py` vs `scripts/exercise_scaffolder/modify.py`
- **Evidence**: `diff` shows only docstrings and class names differ. All method bodies (`_build_exercise_cells`, `_build_exercise_body_test_lines`, `_readme_type_hook`) are identical byte-for-byte.
- **Why it matters**: Two separate modules exist purely to hold a class name each. The `exercise_type` argument already selects the scaffold class in `new_exercise.py:main()`. Both classes always resolve to the same behaviour. The docstrings claim "kept as separate classes intentionally — may diverge in future" — this is the canonical "speculative generality" smell.
- **Recommended fix**: Either:
  1. Collapse into a single `StandardScaffold` (or rename one to a shared base and make both trivial subclasses), or
  2. If the team insists on keeping them separate, at minimum extract the shared implementation into a private mixin or module-level helper so the duplication is eliminated.
- **Counterargument from ACTION_PLAN**: The plan explicitly calls this out as intentional. Even so, the current implementation provides zero behavioural difference, and the "future divergence" argument has already cost: two files to maintain, two test files to maintain, and every change to the standard exercise type must be made in two places.

### 3. `test_exercise_scaffolder_make.py` and `test_exercise_scaffolder_modify.py` are near-identical **IGNORE - THIS IS INTENTIONAL PER ACTION_PLAN**

- **Location**: `tests/test_exercise_scaffolder_make.py` vs `tests/test_exercise_scaffolder_modify.py`
- **Evidence**: `diff` shows only the import (`MakeScaffold` vs `ModifyScaffold`) and the `exercise_type` string (`"make"` vs `"modify"`) differ across ~200 lines. All 6 test classes (`TestCellStructure`, `TestExerciseCellTags`, `TestTodoPlaceholder`, `TestNoDebugSpecificLines`, `TestTodoGuardInTestLines`, `TestReadmeHook`) are identical in structure.
- **Why it matters**: This is the test-side mirror of finding #2. If Make/Modify diverge, the tests should diverge too. But right now they test identical behaviour with duplicated assertions. Every test change must be made in two files.
- **Recommended fix**: If Make/Modify classes are collapsed, collapse the tests too. If they stay separate, at minimum use a parametrised test class or shared base test class to eliminate the duplicated test methods.

### 4. `nb_solution` parameter is unused in `_check_runtime_self_check`

- **Location**: `scripts/verify_exercise_quality.py`, line 1044–1045
- **Evidence**: The function signature declares `nb_solution: NotebookDocument` but the body never references it. The function only uses `ex_dir`, `exercise_key`, and the `student_checker_support.py` file.
- **Why it matters**: Dead parameter suggests the function was designed to do something with the solution notebook (e.g., read it, check it, pass it to the runtime) but that logic was either never implemented or removed. It's misleading to future readers and creates a false dependency at the call site (line ~1178 in `main()`).
- **Recommended fix**: Remove the `nb_solution` parameter from the signature and update the call site in `main()`.

### 5. `build_notebook` default `exercise_type="modify"` is misleading

- **Location**: `scripts/exercise_scaffolder/base.py`, line ~44
- **Evidence**: The signature is `def build_notebook(self, variant: str, exercise_type: str = "modify")`. All production call sites in `new_exercise.py:main()` pass the explicit exercise type. The only callers that rely on the default are base-class tests in `test_exercise_scaffolder_base.py` (lines 363–421), which use `_ConcreteScaffold` and call `build_notebook("student")` without the second argument.
- **Why it matters**: The default `"modify"` controls which header instructions appear (via `_build_header_cells`). If a future scaffold subclass forgets to pass `exercise_type`, the notebook silently gets "modify"-style instructions even if it's a debug or gaps exercise. The base class tests don't validate the header content, so they wouldn't catch it.
- **Recommended fix**: Either:
  1. Remove the default entirely (require the caller to be explicit), or
  2. Document why `"modify"` is the safe default and add a test that verifies header content for each exercise_type.

### 6. Duplicate `source_text` helpers across test files

- **Location**: `tests/test_exercise_scaffolder_base.py` line 29 (`_source_text`) vs `tests/_scaffold_test_helpers.py` line 8 (`source_text`)
- **Evidence**: Both functions do exactly the same thing: `return "".join(cell["source"])`. The base test file defines its own private `_source_text` while all subclass test files import `source_text` from `tests._scaffold_test_helpers`.
- **Why it matters**: Minor maintenance burden. If the cell source format changes, two functions must be updated. The shared helper was created in Stage 2 but the base test (Stage 1) was never updated to use it.
- **Recommended fix**: Update `test_exercise_scaffolder_base.py` to import `source_text` from `tests._scaffold_test_helpers` instead of defining its own.

---

## ⚪ Nitpick

### 7. Magic number `# noqa: PLR2004` suppressions are repetitive

- **Location**: All four subclass test files (`test_exercise_scaffolder_{debug,modify,make,gaps}.py`)
- **Evidence**: Cell-count assertions like `assert len(cells) == 9  # noqa: PLR2004` appear in every `test_cell_count_for_parts_*` test. The cell counts (5, 6, 7, 9, 12) are documented in comments.
- **Why it matters**: Low priority, but defining module-level constants (e.g., `_DEBUG_CELLS_FOR_3_PARTS = 12`) would eliminate the suppressions and make the tests self-documenting.
- **Recommended fix**: Extract constants at the top of each test module.

### 8. `_build_exercise_cells` return type annotation inconsistency

- **Location**: `scripts/exercise_scaffolder/base.py` line ~127
- **Evidence**: The abstract method is annotated as `-> list[dict[str, Any]]` while some subclass overrides annotate more specifically or identically. This is consistent and functional, but the `Any` key value could be narrowed.
- **Why it matters**: Cosmetic; only worth addressing if the team wants stricter type annotations across the board.

---

## Cleanup Performed

None yet — this is a review-only pass. The report identifies issues for the implementer to address.

If the team wants me to apply fixes, the priority order is:

1. Fix the gaps `{i}` bug (🔴 #1) — one-line change in `gaps.py`
2. Remove unused `nb_solution` parameter (🟡 #4) — signature change + call site update
3. Consolidate `source_text` helper (🟡 #6) — import change in base test file
4. Decide on Make/Modify consolidation (🟡 #2, #3) — requires team discussion

---

## Validation

- **Full test suite**: `uv run pytest -q` — all tests pass (100%)
- **Ruff lint**: `uv run ruff check .` — no errors (verified on scaffolder, verifier, and new_exercise.py)
- **Not verified**: Running the verifier against existing exercises (requires a registered exercise; Gate I integration depends on runtime imports)

---

## Areas Not Reviewed

- `docs/` updates (Stage 7 documentation changes were not applied; the ACTION_PLAN checkbox is unchecked)
- `exercise_runtime_support/` package (touched only via imports in Gate I; not in the ACTION_PLAN scope)
- Existing exercises under `exercises/sequence/` (out of scope for this review)
- `scripts/template_repo_cli/` (unchanged by this refactor)
