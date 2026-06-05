# ACTION PLAN — Issue #66 + Exercise Scaffolder Refactor

## Summary

A 7-stage TDD plan. Tests are written or updated **before** implementation in each stage. Stages 1 → 2 → 3 are sequential; Stage 4 can run in parallel with Stages 1–3. Stages 3 and 5 converge at Stage 6; Stages 6 → 7 are sequential.

---

## Stage 1 — `exercise_scaffolder` package: base class + tests

**Objective**: Create the `scripts/exercise_scaffolder/` package with an abstract base class defining the shared scaffold contract. No existing code changes yet.

**Files**:
- `scripts/exercise_scaffolder/__init__.py` — re-exports public API
- `scripts/exercise_scaffolder/base.py` — `ExerciseScaffold` base class with:
  - `__init__(title, exercise_key, parts, test_target, exercise_id: int)`
  - `build_notebook(variant: str) -> dict` — assembles header + type-specific cells + scratch + self-check. Threads `test_target` and `exercise_type` to `_build_header_cells()`.
  - `_build_header_cells(exercise_type: str, test_target: str) -> list[dict]` — orientation markdown with "How to work" instructions (shared; instructions vary by `exercise_type` — gaps uses "YOUR CODE HERE" language, debug uses explanation cell language, others use standard test-target language). `test_target` is the relative path to the exercise-local test file (e.g. `exercises/sequence/ex014_.../tests/test_ex014_....py`), embedded in the notebook header so students know which pytest command to run.
  - `_build_exercise_cells() -> list[dict]` — abstract, overridden per type
  - `_build_scratch_cell() -> dict` — shared
  - `_build_check_answers_cell(variant: str) -> dict` — sets `PYTUTOR_ACTIVE_VARIANT` per variant
  - `build_readme_lines(created_date: str) -> list[str]` — shared with type-specific hook `_readme_type_hook()`
  - `build_test_lines() -> list[str]` — **concrete in base class**: emits shared imports, `_EXERCISE_KEY`, `_NOTEBOOK_PATH`, `_CACHE`, `_run_and_capture` helper. Calls abstract `_build_exercise_body_test_lines()` and `_build_type_specific_test_lines()` for type-specific portions.
  - `_build_exercise_body_test_lines() -> list[str]` — abstract; subclasses return placeholder assertions
  - `_build_type_specific_test_lines() -> list[str]` — hook for debug explanation checks etc.; returns `[]` by default
  - `build_expectations_module() -> str` — shared (exercise-ID-prefixed dict keyed 1..parts, e.g. `EX014_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: "", 2: "", 3: ""}`)
  - `build_student_checker_support() -> str` — shared (importable skeleton with `CHECKS: list[ExerciseCheckDefinition] = []`, TODO comment, and reference to ex012 example; see SPEC for exact content)
- `tests/test_exercise_scaffolder_base.py` — test shared behaviour (header, scratch, self-check with variant, expectations skeleton, student checker skeleton)

**Acceptance criteria**:
- [ ] `ExerciseScaffold` cannot be instantiated directly (ABC).
- [ ] `_build_check_answers_cell("student")` produces `os.environ["PYTUTOR_ACTIVE_VARIANT"] = "student"`.
- [ ] `_build_check_answers_cell("solution")` produces `os.environ["PYTUTOR_ACTIVE_VARIANT"] = "solution"`.
- [ ] `build_expectations_module()` with `exercise_id=14, parts=3` produces `EX014_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: "", 2: "", 3: ""}`.
- [ ] `build_student_checker_support()` produces a module with `CHECKS` list, TODO comment, and references the exercise-ID-prefixed expectations name.
- [ ] `ruff check` passes on new files.

**Review point**: Base class API review before subclasses are written.

**Dependency note**: Stage 1 must be minimally complete (ABC with all method signatures defined) before Stage 2 subclasses can be implemented, since subclasses inherit from `ExerciseScaffold`. Stage 2 can be *designed* in parallel but not *coded* until Stage 1's base class exists.

---

## Stage 2 — `exercise_scaffolder` subclasses: one per exercise type + tests

**Objective**: Implement the four concrete subclasses. Each encapsulates type-specific cell generation, test generation, and README hooks. Shared test boilerplate stays in the base class; subclasses only override type-specific portions.

**Files**:
- `scripts/exercise_scaffolder/debug.py` — `DebugScaffold(ExerciseScaffold)`
- `scripts/exercise_scaffolder/modify.py` — `ModifyScaffold(ExerciseScaffold)` (docstring notes intentional separation from MakeScaffold despite current cell-structure similarity)
- `scripts/exercise_scaffolder/make.py` — `MakeScaffold(ExerciseScaffold)` (docstring notes intentional separation from ModifyScaffold despite current cell-structure similarity)
- `scripts/exercise_scaffolder/gaps.py` — `GapsScaffold(ExerciseScaffold)`
- `tests/test_exercise_scaffolder_debug.py`
- `tests/test_exercise_scaffolder_modify.py`
- `tests/test_exercise_scaffolder_make.py`
- `tests/test_exercise_scaffolder_gaps.py`

Each subclass overrides:
- `_build_exercise_cells() -> list[dict]` — type-specific tagged cells
- `_build_exercise_body_test_lines() -> list[str]` — type-specific placeholder assertions (TODO guards for gaps vs standard)
- `_build_type_specific_test_lines() -> list[str]` — e.g. debug explanation checks; returns `[]` for modify/make/gaps
- `_readme_type_hook() -> list[str]` — optional type-specific README lines (e.g. debug adds explanation cell note, gaps adds YOUR CODE HERE note)

**Acceptance criteria**:
- [ ] `DebugScaffold` produces exerciseN + explanationN cell pairs matching current `_make_debug_cells()` output.
- [ ] `ModifyScaffold` produces standard code cells matching current `_make_standard_cells()` output.
- [ ] `MakeScaffold` produces standard code cells matching current `_make_standard_cells()` output.
- [ ] `GapsScaffold` produces `# YOUR CODE HERE` cells matching current `_make_gaps_cells()` output.
- [ ] All subclass test scaffolds match current `_build_test_lines()` output for their type.
- [ ] `ruff check` passes on new files.

**Review point**: Verify each subclass generates identical notebook cells and test files to the current implementation.

---

## Stage 3 — Wire `new_exercise.py` to use `exercise_scaffolder`

**Objective**: Update `scripts/new_exercise.py` to delegate to the scaffold classes. The CLI, args, file paths, and output format are unchanged.

**Files**:
- `scripts/new_exercise.py` — replace `_make_debug_cells`, `_make_standard_cells`, `_make_gaps_cells`, `_make_check_answers_cell`, `_make_notebook_with_parts`, `_build_readme_lines`, `_build_test_lines` with delegation to the scaffold class.
- `tests/test_new_exercise.py` — update tests that reference removed private functions; add assertions for new scaffolded files (expectations.py, student_checker_support.py, variant overrides).

**Acceptance criteria**:
- [ ] `new_exercise.py` main() now writes `tests/expectations.py` and `tests/student_checker_support.py`.
- [ ] Student notebook self-checker cell contains `os.environ["PYTUTOR_ACTIVE_VARIANT"] = "student"`.
- [ ] Solution notebook self-checker cell contains `os.environ["PYTUTOR_ACTIVE_VARIANT"] = "solution"`.
- [ ] Student and solution notebooks are no longer byte-identical (variant differs).
- [ ] All existing `test_new_exercise.py` tests pass (adapted where they referenced removed internals).
- [ ] New test assertions verify the variant override in both notebooks.
- [ ] New test assertions verify expectations.py and student_checker_support.py are created.
- [ ] `ruff check` passes.

**Review point**: Full integration test — scaffold a real exercise and verify the self-checker works.

---

## Stage 4 — New verification gates: tests first

**Objective**: Write tests for the four new verification gates (F–I) before implementing them.

**Files**:
- `tests/test_verify_exercise_quality.py` — add parametrised tests for gates F–I.

**Tests to add**:

**Gate F — Student checker support module**:
- Missing `student_checker_support.py` → ERROR.
- `student_checker_support.py` with empty `CHECKS` → ERROR.
- `student_checker_support.py` with non-empty `CHECKS` → no finding.

**Gate G — Expectations module**:
- Missing `expectations.py` → ERROR.
- `expectations.py` with empty dict → ERROR (empty dict means the self-checker silently passes everything — a genuine defect).
- `expectations.py` with non-empty expected outputs for all exercise numbers → no finding.

**Gate H — Notebook variant overrides**:
- Student self-checker cell missing `PYTUTOR_ACTIVE_VARIANT` or not set to `"student"` → WARN (the default is already `"student"`, but the scaffolder sets it explicitly).
- Solution self-checker cell missing `PYTUTOR_ACTIVE_VARIANT` → ERROR.
- Solution self-checker cell sets wrong variant → ERROR.
- Solution self-checker cell sets `"solution"` → no finding.

**Gate I — Runtime self-check**:
- Valid solution with matching expectations → no finding.
- Mismatched expectations → ERROR (solution doesn't pass its own self-checker).
- Missing student checker support → WARN (can't run).

**Test development note**: Before writing Stage 4 tests, add skeleton gate functions to `verify_exercise_quality.py` that return `[]` (empty finding list). This ensures tests fail on assertion mismatch rather than `AttributeError` at import time, giving a clean red→green TDD cycle.

**Acceptance criteria**:
- [ ] All new tests fail before implementation (red phase) — on assertion mismatch, not import error.
- [ ] Tests cover positive and edge cases for each gate.
- [ ] `ruff check` passes on test file.

**Review point**: Confirm test coverage before moving to implementation.

---

## Stage 5 — Implement verification gates F–I

**Objective**: Implement the four new gates in `scripts/verify_exercise_quality.py`.

**Files**:
- `scripts/verify_exercise_quality.py` — add gate functions and wire into `main()`.

**Gate F implementation**:
- Check `tests/student_checker_support.py` exists.
- Attempt to import it via `load_exercise_test_module()`.
- Verify `CHECKS` is a non-empty list.

**Gate G implementation**:
- Check `tests/expectations.py` exists.
- Attempt to import it.
- Verify it defines expected outputs for all exercise numbers declared in `exercise.json` parts.

**Gate H implementation**:
- Parse both student and solution notebooks' self-checker cells.
- Student: verify `PYTUTOR_ACTIVE_VARIANT` is set to `"student"` → WARN if missing (default already correct).
- Solution: verify `PYTUTOR_ACTIVE_VARIANT` is set to `"solution"` → ERROR if missing or wrong.

**Gate I implementation**:
- Verify `student_checker_support.py` is importable (already checked by Gate F).
- Import `run_exercise_checks()` from `exercise_runtime_support.student_checker.checks` (this is the canonical import path for the structured check API; it intentionally reaches past the package `__init__` into the submodule).
- Save the original `PYTUTOR_ACTIVE_VARIANT` value, then set it to `"solution"` using the public `configure_variant_environment(os.environ, "solution")` helper from `exercise_runtime_support.execution_variant`. Restore the original value after the check completes.
- Call `run_exercise_checks(exercise_key)` — returns `list[ExerciseCheckResult]` with `.passed` booleans (structured API, not print-based).
- Any `.passed == False` is an ERROR finding (a solution that fails its own self-checker is a defect).
- If `student_checker_support.py` is missing (shouldn't happen after Gate F), produce WARN.

**Acceptance criteria**:
- [ ] All tests from Stage 4 pass (green phase).
- [ ] Existing `test_verify_exercise_quality.py` tests still pass.
- [ ] `ruff check` passes.

**Review point**: Run verifier against existing exercises to see realistic gate output.

---

## Stage 6 — Integration validation

**Objective**: End-to-end validation of the full pipeline.

**Steps**:
1. Run full test suite: `uv run pytest -q`
2. Run solution variant: `uv run python scripts/run_pytest_variant.py --variant solution -q`
3. Scaffold a test exercise with each type and run the verifier against it.
4. Confirm lint: `ruff check .`

**Acceptance criteria**:
- [ ] Full test suite passes.
- [ ] Solution variant tests pass.
- [ ] Scaffolded exercise passes all verification gates.
- [ ] Zero lint errors.

**Review point**: Final review before handoff.

---

## Stage 7 — Cleanup & documentation

**Objective**: Remove dead code, update docs if needed.

**Files**:
- `scripts/new_exercise.py` — remove orphaned private functions replaced by the scaffold classes: `_make_debug_cells`, `_make_standard_cells`, `_make_gaps_cells`, `_make_check_answers_cell`, `_make_notebook_with_parts`, `_build_readme_lines`, `_build_test_lines`, `_build_exercise_body_test_lines`, `_build_debug_explanation_test_lines`. Keep `_slugify`, `_make_meta`, `_build_exercise_key`, `_build_exercise_metadata`, `_validate_and_parse_args`, `_check_exercise_not_exists` (still used by `main()`).
- `docs/exercise-agents/exercise-generation-cli.md` — update scaffolded file list to include `tests/expectations.py` and `tests/student_checker_support.py`.
- `AGENTS.md` — no change needed unless quick reference changes.

**Acceptance criteria**:
- [ ] No dead code remains in `new_exercise.py`.
- [ ] No existing tests import removed functions (check `tests/test_new_exercise.py`).
- [ ] Doc update reflects new scaffolded files.
- [ ] `ruff check .` passes.

---

## Dependency Order

```
Stage 1 (base class) ──> Stage 2 (subclasses) ──> Stage 3 (wire new_exercise.py) ──> Stage 6 (integration) ──> Stage 7 (cleanup)
Stage 4 (verifier tests) ──────────────────────────> Stage 5 (verifier impl) ──────────┘
```

Stage 1 must be complete before Stage 2. Stage 4 can run in parallel with Stages 1–2. Stages 3 and 5 converge at Stage 6.
