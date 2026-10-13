# Execution Model Contract

This document is the canonical contract for test discovery, runtime imports, variant selection, and source-to-export mapping in this repository.

All related contributor guidance must align with this document.

## 1) Repository pytest discovery model

### Canonical discovery roots

Repository pytest discovery uses configured roots in `pyproject.toml` via `testpaths = ["tests", "exercises"]`.

The exercise test contract is:

- Canonical authoring identity lives under `exercises/<construct>/<exercise_key>/`.
- Canonical exercise-specific tests must live in the exercise-scoped tests subfolder (`exercises/<construct>/<exercise_key>/tests/`).
- Top-level flattened exercise tests under `tests/test_exNNN_slug.py` are transitional export compatibility artefacts only.
- New or changed exercise-specific test logic must be implemented in the canonical exercise-scoped tests folder, then mapped/exported as needed.

### Fail-fast rules

- **Duplicate collection is a hard error**: if both top-level flattened tests and canonical nested tests for the same exercise are collected in one run, tooling must fail immediately.
- **Missing canonical files are a hard error**: if an exercise is treated as canonical but required canonical files are missing (metadata, notebook source, or mapped test source), tooling must fail immediately.
- **Unsupported legacy entry points are a hard error**: legacy entry points that are outside the documented compatibility surface must terminate with a clear error message and non-zero exit code.
- **Canonical location violations are a hard error**: any new exercise-specific test implementation added only to top-level flattened `tests/test_exNNN_slug.py` without its canonical counterpart in `exercises/<construct>/<exercise_key>/tests/` must fail validation.

## 2) Shared runtime import model (`exercise_runtime_support`)

All notebook execution and grading helpers shared across repository code and exported classroom templates are imported from `exercise_runtime_support`.

Contract:

- `exercise_runtime_support.exercise_framework` is the public runtime facade for test execution helpers.
- `exercise_runtime_support.notebook_grader` is the lower-level notebook parsing and execution layer.
- Repository tests and exported template tests must import runtime helpers through this shared package, not via ad hoc relative copies.

Rationale: one import contract keeps local development and exported classroom repositories behaviourally aligned.

## 3) Variant selection contract (`PYTUTOR_ACTIVE_VARIANT` and `--variant`)

Variant selection chooses which notebook surface (`student` or `solution`) is executed.

Contract:

- Preferred interface: explicit `--variant <student|solution>` on repository scripts that invoke pytest orchestration (for example `scripts/run_pytest_variant.py`).
- Runtime propagation: orchestrators expose the active value through the `PYTUTOR_ACTIVE_VARIANT` environment variable for downstream runtime resolution.
- Default variant is `solution` when no variant is provided to a repository orchestration script. The Classroom 50 bundle grader is the exception: it defaults to `student` in both of its modes, as §5 records.
- The runtime helper `exercise_runtime_support.execution_variant::get_active_variant` defaults to `solution`, and `run_exercise_checks` (behind `run_notebook_checks`) deliberately overrides that default to `student` when the variable is unset. That override is why a student notebook self-check cell needs no explicit assignment, while a solution self-check cell must set `'solution'`. See [exercise-quality-verifier.md](exercise-quality-verifier.md) for the Gate H severities.
- `active_variant_context()` defaults to `student`, unlike the standalone `get_active_variant()` helper. It temporarily sets the selected value and restores the prior environment value when the context exits.

### Notebook self-check readability

`run_notebook_checks('<exercise_key>')` retains its `None` return and combines
functional results with required per-task readability results. Its self-check
variant defaults to `student` when `PYTUTOR_ACTIVE_VARIANT` is unset; explicit
`student` and `solution` values select the same notebook for functional execution
and readability analysis. The previous environment value is restored after the
call. The full Ruff policy is documented in
[testing-framework.md](testing-framework.md); this is a notebook self-check
contract, not a change to functional-only grading APIs.

Deprecated note:

- `legacy notebook-root override env var` is not part of the supported execution contract. New tooling must ignore or clear it rather than using it for notebook selection.

## 4) Source-to-export mapping contract

Canonical authoring and export surfaces are intentionally different.

Contract:

- Authoring source of truth: `exercises/<construct>/<exercise_key>/`.
- Packaged runtime contract: exported Classroom repositories include `exercise_metadata/`, `exercises/<construct>/<exercise_key>/exercise.json`, `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`, and `exercises/<construct>/<exercise_key>/tests/`.
- Mapping from canonical source to export must be deterministic and reproducible, so the same exercise key resolves to the same exported metadata, notebook, and test paths.
- Flattened notebook/test mirrors are forbidden in packaged outputs.
- Resolution and packaging failures must remain fail-fast and preserve these message fragments (asserted by `tests/test_exercise_metadata.py`):
  - missing or invalid `exercise.json` -> `exercise.json is missing or invalid`
  - missing canonical notebook -> `expected notebook is missing`

The mapping layer must preserve exercise identity by `exercise_key` and must not redefine identity from flattened path names.

## 5) Classroom 50 grading-bundle contract

Teacher-side grading uses a teacher-built bundle, not the exported student template:

- `scripts/build_classroom50_bundle.py` copies hidden exercise tests and a bundle-local `exercise_runtime_support/` copy into `<bundle>/`, plus the generic `autograder.py` at the bundle root.
- The bundle is the grader's only discovery root: tests are collected solely from `<bundle>/exercises/<construct>/<exercise_key>/tests/`, never from the student checkout's `exercises/.../tests/`.
- The bundle root is prepended to `sys.path` ahead of the student checkout, so `exercise_runtime_support` resolves to the bundle copy while `exercise_metadata` resolves to the student checkout. The grader verifies these package origins before grading.
- The grader has two invocation modes. Classroom 50 mode takes no arguments: the current working directory is the student root, the bundle root is the grader script's own parent directory, the result is `./result.json` in the working directory, and the identity fields come from the runner environment. The local dry run requires `--student-root` and `--result` as a pair.
- Both modes force `PYTUTOR_ACTIVE_VARIANT=student` by default; the solution variant is reserved for the local dry run.

See [classroom50-autograder.md](classroom50-autograder.md) for the scoring rule, CLI interfaces, and result contract, and [exercise-quality-verifier.md](exercise-quality-verifier.md) for the authoring-time quality gate set that enforces these contracts.

## Current status

- **Canonical now**: exercise identity, exercise-local notebooks and tests, metadata-backed runtime catalogue resolution, variant semantics (`--variant`, `PYTUTOR_ACTIVE_VARIANT`), and shared runtime import contract.
- **Packaged runtime now**: exported repositories include the metadata package, per-exercise `exercise.json`, canonical student notebooks, and canonical exercise-local tests.
- **Teacher-side grading now**: a separately built bundle (generic `autograder.py` plus hidden test copies and a bundle-local `exercise_runtime_support/` copy) is the graded surface. Exported templates ship starter code only and contain no grading sources or hidden tests.
- **Removed from the supported contract**: `legacy notebook-root override env var` must not be relied on for notebook selection.
- **Template CLI contract**: The template CLI follows a canonical-only exercise-local contract with no legacy compatibility paths. Test-only helpers and fixtures belong under `tests/` and are not part of the runtime surface.
- **Notebook readability self-check**: Ruff checks saved task-cell source in the
  native managed Python/Jupyter environment. The canonical policy, feedback
  states and teacher-grading boundary are specified in
  [testing-framework.md](testing-framework.md). The student guide source is
  `template_repo_files/RUFF_GUIDE.md`; packaging maps it to root-level
  `RUFF_GUIDE.md` in exported repositories and the generated README links to it.
  Normal checker output is the header and task-grouped table only, without a
  footer or guide lookup. Readability labels omit physical cell numbers; the
  Exercise column identifies the task. Feedback wraps at the shared reporting
  default of 40 characters without truncation or a line-count limit; other columns
  remain content-sized, rather than adapting to the viewport.
  Syntax-blocked readability rows show neutral
  `⚪ NOT CHECKED` with `Not checked - make sure your code runs first`; valid-syntax
  cells are assessed independently of functional outcomes.

**Construct-level resources**: When packaging, the CLI preserves construct-level `additional-resources/` directories (e.g. `exercises/sequence/additional-resources/`) in the exported output. These are optional reference materials for students and are not part of the grading contract.

Key runtime contract checks are enforced by direct file-based tests, without a consumer matrix table.
