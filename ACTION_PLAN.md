# ACTION_PLAN — Pyright Typing Cleanup

**Branch**: `fix/template_repo_cli-update-repo_command`
**Goal**: Eliminate all 143 pyright errors across the codebase with minimal, safe changes.

---

## Global Constraints

- **No functional changes**: Only type annotations, re-exports, and compatibility wrapper changes.
- **Tests must remain green**: `uv run pytest` and `uv run ./scripts/verify_solutions.sh` must pass after each batch.
- **Student notebooks untouched**: Only infrastructure code.
- **pyright must pass clean**: `uv run pyright` must show 0 errors, 0 warnings.

---

## Error Overview (143 total)

| Category | Count | Root Cause |
|----------|-------|-----------|
| `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` / `reportUnknownParameterType` / `reportUnknownLambdaType` | 96 | Compatibility wrappers use `importlib` + `globals()` runtime injection; pyright cannot statically resolve symbols |
| `reportPrivateUsage` | 24 | Private (`_prefixed`) functions accessed across module boundaries |
| `reportAttributeAccessIssue` | 18 | Same as unknown types — wrappers hide the real exports |
| `reportUnsupportedDunderAll` | 15 | `__all__ = getattr(...)` is not statically analyzable |
| `reportArgumentType` | 3 | Type incompatibilities in exercise test code |
| `reportMissingParameterType` | 1 | Missing annotation in test helper |
| `reportImportCycles` | 1 | TBD |
| `reportConstantRedefinition` | 1 | `_PYTEST_FATAL_TYPES` redefined |

---

## Section 1: Fix Compatibility Wrappers (~126 errors)

### Objective
Replace the `importlib` + `globals()` runtime injection pattern in wrapper modules with static `from ... import *` re-exports, matching the pattern already used by `tests/exercise_framework/__init__.py`.

### Files to change (8 wrapper modules):
1. `tests/exercise_framework/api.py`
2. `tests/exercise_framework/assertions.py`
3. `tests/exercise_framework/constructs.py`
4. `tests/exercise_framework/expectations_helpers.py`
5. `tests/exercise_framework/fixtures.py`
6. `tests/exercise_framework/reporting.py`
7. `tests/exercise_framework/runtime.py`
8. `tests/notebook_grader.py`

### Acceptance criteria
- All wrappers use `from <source_module> import *` with `# noqa: F403`
- `tests/exercise_framework/test_reporting.py`: 0 pyright errors (was 62)
- `tests/exercise_framework/test_constructs.py`: 0 pyright errors (was 16)
- `tests/exercise_framework/test_assertions.py`: 0 pyright errors (was 9)
- `reportUnsupportedDunderAll` errors: 0 (was 15)
- `reportAttributeAccessIssue` errors: 0 (was 18)
- `uv run pytest` passes
- `uv run ./scripts/verify_solutions.sh` passes

### Implementation notes
- The `__getattr__` fallback in `api.py` should be preserved if the source module has one; otherwise drop it.
- Each wrapper simply becomes: `from <real_module> import *  # noqa: F403`

---

## Section 2: Fix Private Member Access (~24 errors)

### Objective
Make intentionally-public-but-underscore-prefixed functions publicly accessible, or suppress pyright where the private access is legitimate test access.

### Files to change

**2a. `_make_meta` (8 errors across 4 source + 4 test files)**
- Source: `scripts/exercise_scaffolder/debug.py`, `gaps.py`, `make.py`, `modify.py`
- Tests: `tests/test_exercise_scaffolder_debug.py`, `test_exercise_scaffolder_gaps.py`, `test_exercise_scaffolder_make.py`, `test_exercise_scaffolder_modify.py`
- Fix: Rename `_make_meta` to `make_meta` in the source module and update all callers.

**2b. `_readme_type_hook` (5 errors across test files)**
- Tests: `tests/test_exercise_scaffolder_debug.py`, `test_exercise_scaffolder_gaps.py`, `test_exercise_scaffolder_make.py`, `test_exercise_scaffolder_modify.py`
- Fix: Add `# pyright: ignore[reportPrivateUsage]` at the call sites (tests legitimately access protected class members).

**2c. `pytest_collection_guard` private functions (7 errors)**
- Source: `exercise_runtime_support/pytest_collection_guard.py` (`_exercise_key_for_path`, `_is_canonical_test_path`, `_is_top_level_test_path`)
- Test: `tests/test_pytest_collection_guard.py`
- Fix: Rename to public (`exercise_key_for_path`, `is_canonical_test_path`, `is_top_level_test_path`) and update all callers.

**2d. Student checker private functions (12 errors)**
- Test: `tests/exercise_runtime_support/test_student_checker_notebook_runtime.py`
- Fix: Add `# pyright: ignore[reportPrivateUsage]` at call sites (tests legitimately access private internals).

### Acceptance criteria
- `reportPrivateUsage` errors: 0 (was 24)
- `uv run pytest` passes
- `uv run ./scripts/verify_solutions.sh` passes

---

## Section 3: Fix Remaining Type Issues (~13 errors)

### Objective
Add explicit type annotations to resolve remaining partially-unknown and argument-type errors.

### Files to change

**3a. `scripts/template_repo_cli/core/packager.py` (5 errors)**
- Fix: Add explicit type annotations for `construct` and `title` variables from `metadata.get()`.

**3b. `scripts/migrate_exercise_data.py` (2 errors)**
- Fix: Add return type annotation `dict[str, object]` to the function.

**3c. `exercises/sequence/ex008_sequence_make_consolidation/tests/test_ex008_sequence_make_consolidation.py` (7 errors)**
- Fix: Add `cast()` or explicit type annotations for `range()` calls being passed where `Iterable` is expected.

**3d. `tests/autograde_plugin.py` (2 errors)**
- Fix: Rename `_PYTEST_FATAL_TYPES` to `_pytest_fatal_types` (lowercase) to avoid constant redefinition complaint.

**3e. `tests/exercise_runtime_support/test_build_autograde_env.py` (4 errors)**
- Fix: Add type annotation for `monkeypatch` parameter and resolve unknown types.

**3f. `tests/test_verify_exercise_quality.py` (3 errors)**
- Fix: Add type annotations for lambda parameter.

**3g. `exercise_runtime_support/exercise_framework/__init__.py` (10 errors)**
- Fix: TBD after reading full file context.

**3h. `exercise_runtime_support/exercise_framework/api.py` (1 error)**
- Fix: TBD after reading full context.

### Acceptance criteria
- All pyright errors: 0
- `uv run pytest` passes
- `uv run ./scripts/verify_solutions.sh` passes

---

## Section Checklist

### Section 1: Compatibility Wrappers ✅ COMPLETED
- [x] Green implementation complete — 10 wrappers deleted, ~18 call sites updated
- [x] Green review clean — Tidy Code Reviewer approved (3 minor docs findings fixed)
- [x] pyright: 51 errors remaining (all from Sections 2 & 3)
- [x] pytest passes — 100%
- [x] Action plan updated
- [x] Commit: `5089711` — "Section 1: Delete compatibility wrappers, update all call sites to canonical imports"
- [x] Push: branch `fix/template_repo_cli-update-repo_command`

**Implementation notes:**
- Deleted all 10 wrapper files; no more `tests.exercise_framework` re-export package
- All call sites now import directly from `exercise_runtime_support.exercise_framework.*`
- Packager and its tests updated to remove `notebook_grader.py` references
- AGENTS.md updated to reference canonical `exercise_runtime_support/notebook_grader.py`
- Known benign warning: `PytestAssertRewriteWarning` for `fixtures` module (import order)

### Section 2: Private Member Access
- [ ] Red tests added (N/A)
- [ ] Red review clean
- [ ] Green implementation complete
- [ ] Green review clean
- [ ] pyright: 0 errors in affected categories
- [ ] pytest passes
- [ ] Action plan updated
- [ ] Commit created
- [ ] Push completed

### Section 3: Remaining Type Issues
- [ ] Red tests added (N/A)
- [ ] Red review clean
- [ ] Green implementation complete
- [ ] Green review clean
- [ ] pyright: 0 errors total
- [ ] pytest passes
- [ ] Action plan updated
- [ ] Commit created
- [ ] Push completed
