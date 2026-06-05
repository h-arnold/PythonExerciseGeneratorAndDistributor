# SPEC — Improve `new_exercise.py` and `verify_exercise_quality.py` with exercise-type scaffolding classes

## Goal

Eliminate three classes of silent exercise-authoring failure and refactor the exercise scaffolder into a class-based design that makes exercise-type cell structure explicit, testable, and extensible.

## Intended Outcome

1. **Scaffolder creates `tests/expectations.py`** — a minimal skeleton so authors know where to put expected outputs.
2. **Scaffolder creates `tests/student_checker_support.py`** — a placeholder that follows the established pattern so the self-checker does not silently fall back to lenient execution-only checks.
3. **Solution notebook self-checker sets `PYTUTOR_ACTIVE_VARIANT`** — so `run_notebook_checks()` reads from `solution.ipynb`, not `student.ipynb`.
4. **Student notebook self-checker explicitly sets `PYTUTOR_ACTIVE_VARIANT`** — defensive explicit-is-better-than-implicit.
5. **Verifier gains new gates** — detection of missing student checker support, missing expectations, and incorrect solution variant in self-checker cells.
6. **Verifier gains a runtime self-check gate (Gate I)** — actually runs the student checker against the solution variant and reports whether it passes.
7. **Exercise scaffolding logic is refactored into classes** — `scripts/exercise_scaffolder/` package with a base class and one subclass per exercise type.

## Current State

### `scripts/new_exercise.py`

- ~675-line monolithic module with per-type functions: `_make_debug_cells()`, `_make_standard_cells()` (shared by modify and make), `_make_gaps_cells()`.
- `_make_check_answers_cell()` generates a self-checker cell that does **not** set `PYTUTOR_ACTIVE_VARIANT` — student and solution notebooks get identical cells.
- The `main()` function writes 6 files: `__init__.py`, `README.md`, `exercise.json`, `student.ipynb`, `solution.ipynb`, `test_<key>.py`.
- Does **not** create `tests/expectations.py` or `tests/student_checker_support.py`.

### `scripts/verify_exercise_quality.py`

- ~900-line module with gates A–E: canonical structure, notebook structure, student/solution parity, OrderOfTeaching, progression scanning.
- Does **not** check for `student_checker_support.py`, `expectations.py`, or solution notebook variant override.
- No runtime self-check.

### The three silent failures (from issue #66)

| # | Failure | Root cause |
|---|---------|-----------|
| 1 | ~~Exercise not in manifest~~ | No longer applicable (manifest removed) |
| 2 | Missing `student_checker_support.py` → lenient fallback | `has_exercise_checks()` returns `False`; `run_notebook_checks()` falls back to execution-only check |
| 3 | Solution notebook reads `student.ipynb` | `_exercise_check_variant_context()` defaults to `"student"`; solution notebook doesn't override |

## Approach Comparison

### Current approach (per-type functions in `new_exercise.py`)

| Pros | Cons |
|------|------|
| Simple, low ceremony | Type-specific logic scattered across ~5 functions |
| No new files or abstractions | Adding a type requires touching multiple conditional branches |
| Already working | Hard to test per-type cell generation in isolation |
| Zero refactoring risk | Cell structure, test generation, and README generation not co-located by type |

### Approach A — Class hierarchy (`ExerciseScaffold` base + subclasses)

| Pros | Cons |
|------|------|
| Each type is a single cohesive class | More files and abstractions |
| Shared cells (header, scratch, self-check) in base class | Slight contributor learning curve |
| Clear override points for type-specific cells | Refactoring risk in the scaffolder |
| Easy to add a new type: add one subclass | |
| Testable per-type in isolation | |
| Cell structure, test generation, and supporting files co-located by type | |

### Approach B — Dataclass / config-driven

| Pros | Cons |
|------|------|
| Very lightweight | Less flexible for fundamentally different cell patterns (debug needs explanation cells, gaps uses `# YOUR CODE HERE`) |
| Declarative, easy to read | Complex conditional logic still needed for test generation |
| Minimal code | Hard to cleanly encapsulate type-specific behaviour |

### Decision

**Approach A** (class hierarchy) chosen. Introduces a new `scripts/exercise_scaffolder/` package. The current functions in `new_exercise.py` become thin callers that delegate to the appropriate scaffold class. Existing CLI behaviour (args, file paths, output) is preserved unchanged.

**Subclass granularity**: Each exercise type (`debug`, `modify`, `make`, `gaps`) gets its own direct subclass of `ExerciseScaffold` — even though `modify` and `make` currently share the same cell structure. Keeping separate subclasses is intentional: it avoids coupling types that may diverge later, makes type-specific behaviour explicit, and improves readability. A docstring comment in both subclasses explains this to prevent future reviewers from suggesting they be merged.

**expectations.py naming**: Uses exercise-ID-prefixed names (e.g., `EX014_EXPECTED_OUTPUTS`), matching the existing ex012 pattern. This eliminates ambiguity when multiple exercise support modules are loaded in the same process.

## Scope

### In scope

1. New `scripts/exercise_scaffolder/` package with base class + 4 type subclasses.
2. Update `scripts/new_exercise.py` to delegate cell generation and supporting file generation to the scaffold classes.
3. Scaffold `tests/expectations.py` (minimal skeleton with empty exercise-ID-prefixed dict, e.g. `EX014_EXPECTED_OUTPUTS: dict[int, str] = {}`, keyed by exercise number).
4. Scaffold `tests/student_checker_support.py` (placeholder following ex012 pattern).
5. Set `PYTUTOR_ACTIVE_VARIANT` explicitly in **both** student and solution self-checker cells.
6. Add verification gates F–I to `scripts/verify_exercise_quality.py`.
7. Update existing tests for both scripts.
8. New tests for the `exercise_scaffolder` package (per-type).
9. New tests for verification gates F–I.

### Out of scope

- Changing the CLI interface of `new_exercise.py`.
- Changing exported classroom repository behaviour.
- Changing the student checker runtime (`exercise_runtime_support/student_checker/`).
- Retrofitting existing exercises with missing `expectations.py` / `student_checker_support.py` / variant overrides.
- Adding new exercise types beyond the existing four (debug, modify, make, gaps).
- Refactoring `verify_exercise_quality.py` beyond adding the new gates.

### `tests/expectations.py` scaffold contract

The scaffolded file must be syntactically valid and importable. Exact content:

```python
"""Exercise-local expectations for {exercise_key}."""
from __future__ import annotations

from typing import Final

{expectations_var}: Final[dict[int, str]] = {
    {comma_separated_keys}
}
```

Where `{expectations_var}` is the exercise-ID-prefixed name (e.g. `EX014_EXPECTED_OUTPUTS`) and `{comma_separated_keys}` is `1: "", 2: "", …, N: ""` for parts 1..N.

### `tests/student_checker_support.py` scaffold contract

The scaffolded file must be syntactically valid and importable at creation time (Gate F verifies import). Exact content:

```python
"""Exercise-local student checker definitions for {exercise_key}."""
from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.student_checker.checks.base import (
    ExerciseCheckDefinition,
    build_exercise_check,
    exercise_tag,
)

_EXERCISE_KEY = "{exercise_key}"
{expectations_var} = load_exercise_test_module(_EXERCISE_KEY, "expectations")

# TODO: Define check functions and build the CHECKS list.
# See exercises/sequence/ex012_sequence_modify_maths_operators/tests/student_checker_support.py for an example.
CHECKS: list[ExerciseCheckDefinition] = []
```

## Constraints & Invariants

1. CLI contract unchanged: `python scripts/new_exercise.py <id> <title> --construct X --type Y [--slug Z] [--parts N]`.
2. Canonical output paths unchanged: `exercises/<construct>/<exercise_key>/`.
3. All existing tests in `tests/test_new_exercise.py` and `tests/test_verify_exercise_quality.py` must continue to pass.
4. Ruff linting must pass.
5. No new third-party dependencies.
6. Student variant tests may fail; solution variant tests must pass.
7. `exercise_runtime_support/student_checker/checks/__init__.py` (the `_exercise_check_variant_context` default) is NOT changed — the fix is in the notebook cell, not in the runtime.

## Relevant Docs & Files

- `AGENTS.md`
- `docs/developers/project-structure.md`
- `docs/developers/execution-model.md`
- `docs/developers/testing-framework.md`
- `docs/exercise-agents/exercise-generation-cli.md`
- `docs/exercise-agents/exercise-types/debug.md`, `gaps.md`, `make.md`, `modify.md`
- `scripts/new_exercise.py`
- `scripts/verify_exercise_quality.py`
- `exercise_runtime_support/student_checker/checks/__init__.py`
- `exercise_runtime_support/student_checker/checks/base.py`
- `exercise_runtime_support/exercise_test_support.py`
- `exercise_runtime_support/execution_variant.py`
- `exercises/sequence/ex012_sequence_modify_maths_operators/tests/student_checker_support.py`
- `exercises/sequence/ex012_sequence_modify_maths_operators/tests/expectations.py`
- `tests/test_new_exercise.py`
- `tests/test_verify_exercise_quality.py`

## Acceptance Criteria

### Scaffolder changes

- [ ] Running `new_exercise.py` with `--type debug|modify|make|gaps` produces `tests/expectations.py` with an empty expected-outputs dict keyed 1..parts.
- [ ] Running `new_exercise.py` produces `tests/student_checker_support.py` following the ex012 pattern (load exercise-ID-prefixed expectations, build `CHECKS` list, TODO for author).
- [ ] Student notebook self-checker cell sets `PYTUTOR_ACTIVE_VARIANT="student"`.
- [ ] Solution notebook self-checker cell sets `PYTUTOR_ACTIVE_VARIANT="solution"`.
- [ ] Student and solution notebooks are NOT identical after scaffolding (the variant override differs).
- [ ] `scripts/exercise_scaffolder/` exists with base class and 4 direct subclasses (no intermediate shared base for modify/make).
- [ ] `new_exercise.py` delegates cell generation to `exercise_scaffolder`.
- [ ] All existing `test_new_exercise.py` tests pass.

### Verifier changes

- [ ] Gate F: `tests/student_checker_support.py` exists, imports without error, and exposes non-empty `CHECKS`.
- [ ] Gate G: `tests/expectations.py` exists and defines non-empty expected outputs for all exercise numbers from `exercise.json`. An empty dict is an ERROR (it means the self-checker will silently pass everything).
- [ ] Gate H: Student notebook self-checker cell sets `PYTUTOR_ACTIVE_VARIANT="student"` (WARN if missing — default already correct, but explicit is defensive). Solution notebook self-checker cell sets `PYTUTOR_ACTIVE_VARIANT="solution"` (ERROR if missing or wrong).
- [ ] Gate I: Runtime self-check — import `run_exercise_checks()` from `exercise_runtime_support.student_checker.checks` (canonical submodule import path), set `PYTUTOR_ACTIVE_VARIANT="solution"` using the public `configure_variant_environment()` from `exercise_runtime_support.execution_variant`, and inspect the returned `list[ExerciseCheckResult]` for any `.passed == False`. Save and restore the original env-var value around the check. Produces ERROR on failure (a solution that doesn't pass its own self-checker is a genuine defect).
- [ ] All existing `test_verify_exercise_quality.py` tests pass.
- [ ] New test coverage for gates F–I.

### General

- [ ] `ruff check .` passes.
- [ ] `uv run pytest -q` passes (student variant failures are expected; solution variant passes).
- [ ] `uv run python scripts/run_pytest_variant.py --variant solution -q` passes.

## Open Questions & Risks

1. **Risk**: Gate I (runtime self-check) executes arbitrary notebook code. Mitigation: run in a subprocess or sandboxed context; only run against solution variant where code is trusted.
**Decision** Not a risk no sensitive data is being handled and this is excuted locally in an isolated container only.
2. **Risk**: The class refactor could break subtle edge cases in test generation. Mitigation: preserve all existing test assertions; add new focused tests for each scaffold class before refactoring.
**Decisions** this is only a risk if we attempt to refactor the existing exercises. Those will be being left as is.
3. **Deferred**: Retrofitting existing exercises. The scaffolder will generate the new files and variant overrides for *new* exercises only. Existing exercises must be updated manually or via a follow-up migration script.
