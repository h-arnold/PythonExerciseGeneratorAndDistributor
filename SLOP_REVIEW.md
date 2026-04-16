# SLOP_REVIEW

## Purpose

This document records an in-depth slop review of the `exercise_runtime_support` package.

It is intended to be actionable for a follow-up cleanup agent that does not have the benefit of the original investigation. It therefore includes:

- scope
- method
- commands run
- confirmed findings with evidence
- weak hypotheses that need verification before cleanup
- suggested cleanup order
- validation requirements

The focus is not generic style commentary. The focus is concrete AI-slop or maintenance slop:

- dead code
- duplicated logic
- misleading abstractions
- stale compatibility branches
- documentation encoded as code that has drifted
- validation layers that look safer than they are


## Scope

Reviewed package:

- `exercise_runtime_support/`

Reviewed direct tests and nearby consumers:

- `tests/exercise_runtime_support/`
- `tests/exercise_framework/`
- `tests/test_pytest_collection_guard.py`
- selected direct consumers under `scripts/`, `exercises/`, and `docs/`

Key files inspected during the review:

- `exercise_runtime_support/helpers.py`
- `exercise_runtime_support/notebook_grader.py`
- `exercise_runtime_support/execution_variant.py`
- `exercise_runtime_support/exercise_catalogue.py`
- `exercise_runtime_support/exercise_test_support.py`
- `exercise_runtime_support/consumer_matrix.py`
- `exercise_runtime_support/support_matrix.py`
- `exercise_runtime_support/pytest_collection_guard.py`
- `exercise_runtime_support/exercise_framework/__init__.py`
- `exercise_runtime_support/exercise_framework/api.py`
- `exercise_runtime_support/exercise_framework/paths.py`
- `exercise_runtime_support/exercise_framework/runtime.py`
- `exercise_runtime_support/exercise_framework/expectations.py`
- `exercise_runtime_support/student_checker/notebook_runtime.py`
- `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py`
- `exercise_runtime_support/student_checker/reporting.py`


## Standards And Contracts Consulted

Repository instructions and docs reviewed before making any judgments:

- `AGENTS.md`
- `docs/project-structure.md`
- `docs/testing-framework.md`
- `docs/execution-model.md`

Important repository constraints that materially affected the review:

- Canonical authoring layout is now `exercises/<construct>/<exercise_key>/`.
- Variant selection is explicit and uses `PYTUTOR_ACTIVE_VARIANT`.
- Shared runtime import contract is `exercise_runtime_support`.
- The source repository is now canonical-first, while packaged classroom exports remain metadata-free and student-focused.
- Fail-fast is preferred over defensive fallback logic unless the repository explicitly needs the fallback.


## Method

The review used the following process:

1. Read the package structure and the repo-level standards.
2. Read the implementation files most likely to accumulate slop.
3. Read nearby tests and consumers before judging whether a helper or branch was actually needed.
4. Use repository-wide searches to distinguish real public surface from dead or pseudo-public surface.
5. Validate assumptions with targeted test runs.
6. Separate confirmed findings from weaker hypotheses.

This review deliberately avoided proposing cleanups that were not grounded in:

- actual callers
- actual tests
- current repo status
- current runtime contract


## Commands Run

These commands were used to establish and validate the findings:

```bash
sed -n '1,220p' .codex/agents/de-sloppifier.toml
sed -n '1,260p' AGENTS.md
sed -n '1,240p' docs/testing-framework.md
sed -n '1,260p' docs/project-structure.md
sed -n '1,260p' docs/execution-model.md

find exercise_runtime_support -maxdepth 3 -type f | sort
wc -l exercise_runtime_support/*.py exercise_runtime_support/exercise_framework/*.py \
  exercise_runtime_support/student_checker/*.py \
  exercise_runtime_support/student_checker/checks/*.py

rg -n "..." exercise_runtime_support tests/exercise_runtime_support tests/exercise_framework
rg -n "exercise_runtime_support\.helpers" .
rg -n "load_exercise_test_module\(" .
rg -n "CONSUMER_MATRIX" .
rg -n "iter_exercise_ids_for_role\(" .

uv run pytest tests/exercise_runtime_support tests/exercise_framework \
  tests/test_pytest_collection_guard.py -q

uv run python - <<'PY'
from collections import Counter
from exercise_runtime_support.exercise_catalogue import get_exercise_catalogue
print(Counter(entry.layout for entry in get_exercise_catalogue()))
PY
```

Observed validation results:

- `uv run pytest tests/exercise_runtime_support tests/exercise_framework tests/test_pytest_collection_guard.py -q`
  - passed
- layout check
  - current catalogue result: `Counter({'canonical': 7})`


## High-Level Assessment

Overall rating: **Needs Improvement**

The package is not a mess. Most of the runtime support code is coherent, and the focused test slices pass. The slop is concentrated in a few predictable areas:

- leftover compatibility surfaces from the canonical-layout migration
- pseudo-public helper APIs with no real consumers
- metadata/documentation tracking encoded in Python instead of being derived from real sources
- weak validation layers that add indirection without adding meaningful protection

This is not a “rewrite the package” situation. The cleanup should be local and removal-heavy.


## What Appears Clean

These areas were inspected and are not primary slop targets:

- `exercise_runtime_support/notebook_grader.py`
  - This is the real low-level runtime layer and has direct consumers.
  - Some internals are mildly defensive, but most of the code is clearly in active use.

- `exercise_runtime_support/exercise_test_support.py`
  - This is a real shared boundary.
  - `load_exercise_test_module()` is used widely across canonical exercise-local tests and support modules.

- `exercise_runtime_support/pytest_collection_guard.py`
  - This is narrow, tested, and tied to a concrete discovery contract.
  - It does not appear over-abstracted.

- `exercise_runtime_support/support_matrix.py`
  - Small, direct, and actually consumed by `exercise_framework/api.py` and tests.
  - One helper is underused, but the module itself is not obviously slop.

- `exercise_runtime_support/exercise_catalogue.py`
  - The metadata-backed and snapshot-backed dual path is still justified by source-vs-packaged repo behavior.
  - This does not currently look like stale compatibility logic.


## Confirmed Findings

The items below are confirmed from code, callers, and current repository contracts.

### 1. `helpers.py` is mostly dead compatibility cargo

Severity: **Critical**

Primary files:

- `exercise_runtime_support/helpers.py`
- `tests/helpers.py`

Direct evidence:

- Repo-wide usage only hits `build_autograde_env()`.
- Searches found no external callers for:
  - `resolve_notebook_path()` at `exercise_runtime_support/helpers.py:27`
  - `run_tagged_cell_output()` at `exercise_runtime_support/helpers.py:36`
  - `load_notebook()` at `exercise_runtime_support/helpers.py:49`
  - `_find_code_cell()` at `exercise_runtime_support/helpers.py:57`
  - `assert_code_cell_present()` at `exercise_runtime_support/helpers.py:67`
  - `get_explanation_cell()` at `exercise_runtime_support/helpers.py:90`

Concrete caller evidence:

- `exercise_runtime_support.helpers` is only imported directly in:
  - `exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py:16`
  - `tests/helpers.py:1`
- The real consumer is `build_autograde_env()`:
  - `exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py:34`
  - `tests/test_build_autograde_payload.py:15`
  - `tests/test_integration_autograding.py:14`

Why this counts as slop:

- The module presents itself as a general helper surface, but almost all of it is unconsumed.
- Several functions duplicate runtime/grader accessors rather than adding a new boundary.
- `load_notebook()` uses `use_solution: bool` at `exercise_runtime_support/helpers.py:49`, which reflects an older boolean toggle design rather than the current explicit variant contract.
- The wrapper module `tests/helpers.py` keeps this surface alive in exported test space, which increases the chance of future accidental coupling to dead APIs.

Why it matters:

- Dead helper surfaces create false affordances.
- Future contributors or agents can easily import the wrong thing because it exists and looks supported.
- The stale boolean-mode API does not match the canonical runtime contract the rest of the repo is moving toward.

Recommended simplification:

Option A, preferred:

- Reduce `exercise_runtime_support/helpers.py` to `build_autograde_env()` only.
- Keep `tests/helpers.py` as a thin compatibility wrapper only if packaged tests still need it.

Option B:

- Move `build_autograde_env()` closer to the autograde CLI or shared autograde test helpers.
- Delete `exercise_runtime_support/helpers.py` entirely.
- Update `tests/helpers.py` and direct imports accordingly.

Do not do this cleanup blindly:

- Confirm whether packaged classroom tests still expect `tests/helpers.py`.
- If they do, keep only the minimum surface needed for that packaging contract.

Suggested edit set:

1. Remove unused helper functions from `exercise_runtime_support/helpers.py`.
2. Update `tests/helpers.py` if necessary.
3. Re-run autograde-related tests.

Required validation after cleanup:

```bash
uv run pytest tests/test_build_autograde_payload.py tests/test_integration_autograding.py -q
uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py -q
```


### 2. `consumer_matrix.py` is code-as-documentation that has already drifted

Severity: **Critical**

Primary files:

- `exercise_runtime_support/consumer_matrix.py`
- `tests/exercise_runtime_support/test_consumer_matrix.py`
- `docs/execution-model.md`

Direct evidence of drift:

- `exercise_runtime_support/consumer_matrix.py:47-52` describes the scaffolder row as:
  - current entry point: `emitted import from exercise_runtime_support.exercise_framework.runtime`
- Actual scaffolder code in `scripts/new_exercise.py:382-408` imports from:
  - `exercise_runtime_support.exercise_framework`
  - not `exercise_runtime_support.exercise_framework.runtime`

- `exercise_runtime_support/consumer_matrix.py:32-37` describes the framework API wrapper surface as only:
  - `tests/exercise_framework/runtime.py`
- But parallel wrappers also exist, for example:
  - `tests/exercise_framework/api.py`
  - `tests/exercise_framework/reporting.py`
  - `tests/exercise_framework/assertions.py`
  - `tests/exercise_framework/constructs.py`
  - `tests/exercise_framework/expectations_helpers.py`
  - `tests/exercise_framework/fixtures.py`
  - `tests/exercise_framework/paths.py`

- The validating test at `tests/exercise_runtime_support/test_consumer_matrix.py:34-40` only checks that the docs repeat the matrix strings.
- That means a stale matrix and stale docs can agree with each other and still pass.

Why this counts as slop:

- The module claims to be “definitive” but is not derived from real imports or real consumers.
- It duplicates repo knowledge in a form that is cheaper to update superficially than to keep accurate.
- The test validates text consistency, not actual correctness.

Why it matters:

- This module can mislead cleanup work.
- It creates the appearance of strong contract tracking without actually enforcing the contract.
- Drift has already happened, so this is not hypothetical.

Recommended simplification:

Option A, preferred:

- Remove `consumer_matrix.py`.
- Replace it with direct tests against actual consumer files and imports.
- Keep the human-oriented explanation in `docs/execution-model.md`.

Suggested edit set:

1. Decide whether the matrix remains as code or moves fully into docs.
2. If removing it:
   - delete `exercise_runtime_support/consumer_matrix.py`
   - replace the matrix test with real consumer-contract tests
3. If keeping it:
   - update the matrix rows
   - strengthen tests so they assert on actual imports and emitted scaffold text

Required validation after cleanup:

```bash
uv run pytest tests/exercise_runtime_support/test_consumer_matrix.py -q
uv run pytest tests/test_new_exercise.py -q
```


### 3. `exercise_framework.paths` still carries a stale source-legacy branch

Severity: **Critical**

Primary file:

- `exercise_runtime_support/exercise_framework/paths.py`

Relevant code:

- `_resolve_source_legacy_notebook_path()` at `exercise_runtime_support/exercise_framework/paths.py:67-81`
- the branch that still uses it at `exercise_runtime_support/exercise_framework/paths.py:131-136`

Supporting evidence:

- Current repo status in `AGENTS.md` and project docs says canonical layout is the source-repo standard.
- `exercise_metadata/resolver.py:154-159` already hard-fails on non-canonical exercise layouts.
- Live catalogue check result:
  - `Counter({'canonical': 7})`
- No current source-repo exercise in the live catalogue requires that source-legacy branch.

Why this counts as slop:

- It is compatibility branching for a source-layout state that no longer exists in this repository.
- The branch is in the core path resolver, which makes the most important runtime path harder to reason about.
- The name `_resolve_source_legacy_notebook_path()` is especially misleading because it still returns exercise-local notebook paths rather than old root-level notebook paths.

Why it matters:

- Resolver code is central infrastructure. Unused branches here are disproportionately expensive.
- The branch suggests live support for a source-repo state that the metadata resolver already rejects.
- It makes future cleanup around `execution_variant.py` and canonical path handling harder.

Recommended simplification:

Keep only two active modes in `resolve_exercise_notebook_path()`:

1. metadata-backed canonical source resolution
2. metadata-free packaged-export resolution

Delete:

- `_resolve_source_legacy_notebook_path()`
- the corresponding source-legacy branch in `resolve_exercise_notebook_path()`

Do not delete packaged-export handling:

- The metadata-free packaged-export path is still justified.
- This review does not support removing the snapshot/export branch.

Suggested edit set:

1. Remove `_resolve_source_legacy_notebook_path()`.
2. Remove the branch that calls it.
3. Update or remove any tests that were only preserving source-legacy behavior.
4. Re-read the error text in related resolver tests to ensure the contract remains consistent.

Required validation after cleanup:

```bash
uv run pytest tests/exercise_framework/test_paths.py tests/exercise_framework/test_parity_paths.py -q
uv run pytest tests/exercise_runtime_support/test_exercise_catalogue.py -q
```


### 4. The student notebook runtime type-guard layer adds ceremony without real protection

Severity: **Improvement**

Primary files:

- `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py`
- `exercise_runtime_support/student_checker/notebook_runtime.py`

Direct evidence:

- `is_notebook_cell()` at `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py:20-22`
  - only checks `isinstance(value, dict)`
- `is_notebook_metadata()` at `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py:25-27`
  - only checks `isinstance(value, dict)`
- `is_notebook_json()` at `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py:12-17`
  - only checks that the top-level object is a `dict` with string keys
- `_load_notebook_json()` at `exercise_runtime_support/student_checker/notebook_runtime.py:55-65`
  - returns `{}` on notebook shape mismatch rather than failing fast

Resulting behavior:

- malformed notebook JSON can degrade into:
  - empty cells list semantics
  - “No exercise tags found in ...”
- rather than surfacing as a real structure error

Why this counts as slop:

- The extra file and TypeGuard names imply meaningful validation.
- In reality, most of the checks are just renamed `isinstance(..., dict)` calls.
- The code still needs field-by-field inspection after the guards, so the indirection is not buying much.

Why it matters:

- This is classic “validation theater” slop.
- It makes the code feel safer than it is.
- It also conflicts with the repo’s fail-fast bias.

Recommended simplification:

Option A, preferred:

- Inline the few trivial `dict`/`list` checks directly into `notebook_runtime.py`.
- Remove `notebook_runtime_typeguards.py`.

Option B:

- Keep the module, but make the guards real.
- For example:
  - require `cells` to be a list when validating notebook JSON
  - require metadata to be a `dict[str, object]`
  - raise `NotebookGradingError` when the notebook shape is invalid

Important caution:

- If you tighten notebook validation, update user-facing messages deliberately.
- Some tests may implicitly rely on soft failure paths.

Suggested edit set:

1. Decide whether the file stays or goes.
2. Change `_load_notebook_json()` to fail fast on invalid notebook structure.
3. Update tests to assert on explicit malformed-notebook failure if needed.

Required validation after cleanup:

```bash
uv run pytest tests/exercise_runtime_support/test_student_checker_notebook_runtime.py -q
uv run pytest tests/exercise_runtime_support/test_student_checker_reporting.py -q
```


### 5. Shared expectation helpers are duplicated in ex002 framework support

Severity: **Improvement**

Primary files:

- `exercise_runtime_support/exercise_framework/expectations.py`
- `exercises/sequence/ex002_sequence_modify_basics/tests/framework_support.py`

Direct evidence:

Shared helpers in package:

- `expected_output_lines()` at `exercise_runtime_support/exercise_framework/expectations.py:13-26`
- `expected_output_text()` at `exercise_runtime_support/exercise_framework/expectations.py:29-44`

Exercise-local duplicates:

- `_expected_output_lines()` at `exercises/sequence/ex002_sequence_modify_basics/tests/framework_support.py:23-32`
- `_expected_output_text()` at `exercises/sequence/ex002_sequence_modify_basics/tests/framework_support.py:35-46`

Additional context:

- Repo-side ex002 tests already use the shared helpers directly:
  - `exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py:82`

Why this counts as slop:

- The shared abstraction exists, but its closest detailed-check consumer still duplicates the logic.
- This is the kind of duplication that survives because the abstraction was introduced after local code already existed.

Why it matters:

- Any future change to output normalization rules risks splitting behavior.
- It weakens the value proposition of `exercise_framework/expectations.py`.

Recommended simplification:

Option A, preferred:

- Update `framework_support.py` to use the shared helpers from `exercise_runtime_support.exercise_framework.expectations`.

Option B:

- If `framework_support.py` intentionally owns this logic, stop exporting the generic helpers from the package.

The first option is more consistent with the rest of the runtime package.

Suggested edit set:

1. Import shared expectation helpers into `framework_support.py`.
2. Remove the duplicated local implementations.
3. Re-run ex002 tests and framework API tests.

Required validation after cleanup:

```bash
uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests -q
uv run pytest tests/exercise_framework/test_expectations.py tests/exercise_framework/test_api_contract.py -q
```


### 6. `exercise_framework.api` looks more generic than it really is

Severity: **Improvement**

Primary file:

- `exercise_runtime_support/exercise_framework/api.py`

Direct evidence:

- `_get_check_runners()` at `exercise_runtime_support/exercise_framework/api.py:85-96`
  - maps any `FRAMEWORK_DETAILED` exercise to `_check_ex002_summary`
- `_check_ex002_summary()` at `exercise_runtime_support/exercise_framework/api.py:75-77`
  - is explicitly ex002-specific
- The module then makes multiple catalogue passes:
  - `_get_check_runners()`
  - `_get_check_definitions()`
  - `_get_supported_catalogue()`

Why this counts as slop:

- The API is written as if there were a general detailed-check registry.
- In reality, detailed behavior is still effectively “special case ex002.”
- The abstraction surface overstates the current generality of the feature.

Why it matters:

- Over-general APIs increase maintenance cost and hide the true shape of the system.
- Another agent might incorrectly assume that adding a second detailed exercise is already modeled cleanly.

Recommended simplification:

Option A, preferred for now:

- Make the detailed-check path explicitly ex002-specific until there is a second real detailed consumer.

Option B:

- Introduce a real per-exercise detailed runner registry only when at least one more detailed exercise exists.

If choosing Option A, an acceptable cleanup would be:

- collapse the multiple catalogue passes
- make the detailed path explicit
- keep the smoke path data-driven

If choosing Option B, do not build another layer of abstraction unless a second detailed exercise is actually being added.

Required validation after cleanup:

```bash
uv run pytest tests/exercise_framework/test_api_contract.py -q
uv run pytest tests/exercise_runtime_support/test_support_matrix.py -q
```


### 7. Duplicate `ExerciseCheckResult` models create avoidable glue code

Severity: **Nitpick**

Primary files:

- `exercise_runtime_support/exercise_framework/api.py`
- `exercise_runtime_support/student_checker/models.py`
- `exercise_runtime_support/student_checker/reporting.py`

Direct evidence:

- `exercise_framework/api.py:35-42` defines `ExerciseCheckResult`
- `student_checker/models.py:19-26` defines another `ExerciseCheckResult`
- `student_checker/reporting.py:24-41` introduces `_ExerciseCheckResult` as a protocol to paper over the duplicate shape

Why this counts as slop:

- This is not a bug, but it is duplicated model structure.
- The reporting code has to become structural rather than nominal because the same concept exists twice.

Why it matters:

- Small duplicated models are often how package boundaries start to rot.
- It makes future refactors or serializer logic more awkward.

Recommended simplification:

- Share one result dataclass if the semantic concept is truly the same.
- If the concepts are intentionally separate, keep one side private and stop pretending they are interchangeable.

This is a cleanup-of-opportunity item, not a priority driver.


## Follow-Up Confirmations

These items were initially left as hypotheses during the first pass. They are now confirmed cleanup targets based on follow-up direction and should be treated as part of the main removal plan.

### A. Legacy top-level notebook rewriting in `execution_variant.py` should be removed

Severity: **Critical**

File:

- `exercise_runtime_support/execution_variant.py`

Relevant code:

- `resolve_variant_notebook_path()` at `exercise_runtime_support/execution_variant.py:44-61`
- `_resolve_legacy_notebook_path()` at `exercise_runtime_support/execution_variant.py:69-92`
- `_relative_legacy_path()` at `exercise_runtime_support/execution_variant.py:94-107`

Confirmed rationale:

- The framework layer already rejects source-repo `notebooks/...` path inputs.
- Packaged notebook layout is exercise-local, not top-level `notebooks/`.
- The current repo state is canonical-only for source exercises.
- The cleanup policy for this area is now explicit: if removing legacy notebook path rewriting breaks something, that breakage is preferable to silently preserving obsolete behavior.

Why this counts as slop:

- This is stale compatibility logic in a shared runtime path helper.
- It keeps legacy path rewriting alive even though the repository contract has moved away from top-level notebook resolution.
- It hides unsupported entry points behind silent path rewriting rather than surfacing them as failures.

Recommended simplification:

- Remove `_resolve_legacy_notebook_path()`.
- Remove `_relative_legacy_path()`.
- Simplify `resolve_variant_notebook_path()` so it only:
  - anchors relative paths when requested
  - switches canonical `student.ipynb` and `solution.ipynb` filenames when appropriate
- Let unsupported legacy inputs fail rather than auto-rewriting them.

Required follow-up:

- If this breaks callers, treat that as a discovery step.
- Fix the callers to use canonical exercise keys or canonical exercise-local paths rather than preserving the rewrite branch.


### B. The package-level lazy facade in `exercise_framework.__init__` should be simplified

Severity: **Improvement**

File:

- `exercise_runtime_support/exercise_framework/__init__.py`

Relevant code:

- `_ATTRIBUTE_MODULES`
- `_MODULE_CACHE`
- `_load_module()`
- `__getattr__()`

Confirmed rationale:

- There is no strong project-level requirement for lazy loading here.
- The strongest evidence found during the review was only that laziness helps defer ex002 support loading.
- The current direction is explicit: lazy loading is not assumed necessary for this project, and removal/simplification is the correct default.

Why this counts as slop:

- The package root uses a large dynamic re-export mechanism for a relatively small codebase.
- It makes the public surface harder to trace and reason about.
- It adds import indirection that can conceal real dependencies and delay obvious failures.

Recommended simplification:

Option A, preferred:

- Replace the dynamic facade with direct imports and a normal `__all__`.
- Keep the package root explicit and static.

Option B:

- If one specific lazy path still proves necessary, keep laziness only for that path and remove it for everything else.

Important principle for this cleanup:

- Prefer eager import failures over hidden import machinery.
- If simplifying the facade exposes real dependency problems, fix those problems directly.


## Cleanup Order

A less powerful cleanup agent should work in this order.

This order is important because some later decisions become easier once earlier dead surfaces are removed.

### Phase 1: Remove dead helper surface

Targets:

- `exercise_runtime_support/helpers.py`
- `tests/helpers.py`
- any imports that still reference removed helpers

Goal:

- reduce the public surface to real consumers only

Why first:

- this is the clearest confirmed dead code
- it shrinks the search space for the rest of the cleanup


### Phase 2: Remove or replace `consumer_matrix.py`

Targets:

- `exercise_runtime_support/consumer_matrix.py`
- `tests/exercise_runtime_support/test_consumer_matrix.py`
- possibly `docs/execution-model.md`

Goal:

- eliminate drift-prone code-as-documentation

Why second:

- the matrix is already stale
- future cleanup should not depend on misleading tracking metadata


### Phase 3: Simplify canonical path resolution

Targets:

- `exercise_runtime_support/exercise_framework/paths.py`

Goal:

- remove source-legacy branching that the current repo no longer needs

Why third:

- path resolution is core runtime behavior
- changes here affect several tests, so it is best to do after dead-surface cleanup but before weaker cleanup items


### Phase 4: Remove legacy notebook path rewriting from `execution_variant.py`

Targets:

- `exercise_runtime_support/execution_variant.py`

Goal:

- stop silently rewriting unsupported top-level legacy notebook paths

Why fourth:

- this is now a confirmed cleanup item
- it is tightly related to the resolver cleanup from Phase 3
- the repository direction is to fail fast if something still depends on the old path model


### Phase 5: Tighten notebook runtime validation

Targets:

- `exercise_runtime_support/student_checker/notebook_runtime.py`
- `exercise_runtime_support/student_checker/notebook_runtime_typeguards.py`

Goal:

- reduce fake validation layers and restore fail-fast behavior

Why fifth:

- this is useful cleanup, but behavior-sensitive
- it should happen after the highest-confidence removal work


### Phase 6: Simplify the package-root lazy facade

Targets:

- `exercise_runtime_support/exercise_framework/__init__.py`

Goal:

- replace dynamic re-export machinery with a simpler explicit package surface

Why sixth:

- this is now a confirmed cleanup direction
- it is easier to judge once the path and runtime cleanup has removed the biggest stale branches
- eager failures are preferable here, but this still touches package import behavior and should be done deliberately


### Phase 7: Remove duplicated expectation logic

Targets:

- `exercise_runtime_support/exercise_framework/expectations.py`
- `exercises/sequence/ex002_sequence_modify_basics/tests/framework_support.py`

Goal:

- unify output expectation normalization

Why seventh:

- lower risk than the path/runtime changes
- straightforward once the surrounding runtime surfaces are already clearer


### Phase 8: Reassess remaining abstraction cleanup

Targets:

- `exercise_runtime_support/exercise_framework/api.py`

Goal:

- only after the concrete slop is removed, decide whether the remaining API indirection is still worth it

Why last:

- `exercise_framework/api.py` is the remaining abstraction-heavy area that is still more generic-looking than the current feature set
- some of the abstraction may become easier to judge after earlier cleanup


## Validation Matrix

Use the smallest relevant test slice after each phase, then run a broader slice at the end.

### After Phase 1

```bash
uv run pytest tests/test_build_autograde_payload.py tests/test_integration_autograding.py -q
uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py -q
```

### After Phase 2

```bash
uv run pytest tests/exercise_runtime_support/test_consumer_matrix.py -q
uv run pytest tests/test_new_exercise.py -q
```

### After Phase 3

```bash
uv run pytest tests/exercise_framework/test_paths.py tests/exercise_framework/test_parity_paths.py -q
uv run pytest tests/exercise_runtime_support/test_exercise_catalogue.py -q
```

### After Phase 4

```bash
uv run pytest tests/exercise_runtime_support/test_execution_variant.py -q
uv run pytest tests/exercise_framework/test_paths.py tests/exercise_framework/test_parity_paths.py -q
```

### After Phase 5

```bash
uv run pytest tests/exercise_runtime_support/test_student_checker_notebook_runtime.py -q
uv run pytest tests/exercise_runtime_support/test_student_checker_reporting.py -q
```

### After Phase 6

```bash
uv run pytest tests/exercise_framework/test_api_contract.py tests/exercise_framework/test_expectations.py -q
uv run pytest tests/test_new_exercise.py -q
```

### After Phase 7

```bash
uv run pytest exercises/sequence/ex002_sequence_modify_basics/tests -q
uv run pytest tests/exercise_framework/test_expectations.py tests/exercise_framework/test_api_contract.py -q
```

### Final broad pass

```bash
uv run pytest tests/exercise_runtime_support tests/exercise_framework tests/test_pytest_collection_guard.py -q
uv run python scripts/run_pytest_variant.py --variant solution -q
```

Important note:

- Do not interpret failing student-variant behavior as a defect.
- The repository contract is that solution-variant notebook tests pass and student-variant notebook tests fail.


## Risks And Non-Goals

### Do not “clean up” these things without new evidence

- `exercise_runtime_support/exercise_catalogue.py` metadata-vs-snapshot split
  - this still matches source-repo vs packaged-export behavior

- `exercise_runtime_support/exercise_test_support.py`
  - this is a real shared boundary used by many canonical exercise-local test modules

- `exercise_runtime_support/pytest_collection_guard.py`
  - this is tied to an explicit repo discovery contract and already has focused tests


### Do not silently change runtime contracts while removing slop

Examples:

- Do not reintroduce boolean variant toggles in place of explicit variants.
- Do not weaken fail-fast resolver errors.
- Do not replace current import contracts with new abstractions unless they remove proven duplication.


### Be cautious around packaged/exported behavior

This review was grounded in the source repository. It did not directly execute an exported classroom repository. That means:

- packaged runtime expectations still need to be validated after cleanup
- branches that look stale in-source may still be supporting exported consumers

That caution especially applies to:

- `tests/helpers.py`


## Minimal Cleanup Checklist

If another agent needs a compressed execution checklist, use this:

1. Remove dead helpers from `exercise_runtime_support/helpers.py`, preserving only what has real callers.
2. Either delete `consumer_matrix.py` or make its tests assert real facts instead of prose parity.
3. Remove the source-legacy branch from `exercise_framework/paths.py`.
4. Simplify or replace `student_checker/notebook_runtime_typeguards.py`.
5. Deduplicate ex002 expectation normalization between package helpers and `framework_support.py`.
6. Remove legacy notebook path rewriting from `exercise_runtime_support/execution_variant.py` and fix any callers that break.
7. Replace the dynamic package-root lazy facade in `exercise_runtime_support/exercise_framework/__init__.py` with an explicit surface.
8. Re-run the focused validation matrix and then the broader solution-variant pass.


## Final Conclusion

`exercise_runtime_support` does not need a redesign. It needs a disciplined removal pass.

The highest-value cleanup is:

- delete dead helper surface
- delete or de-power drift-prone code-as-documentation
- delete source-legacy resolver branches that the repo no longer uses

After that, the remaining improvement work is smaller and more judgment-sensitive:

- tighten notebook validation
- remove duplicate expectation logic
- simplify the package-root facade
- only then reconsider the remaining API abstraction layer

This package is close enough to clean that the wrong next step would be adding more abstraction. The right next step is targeted deletion.
