# Execution Model Contract

This document is the canonical contract for test discovery, runtime imports, variant selection, and source-to-export mapping in this repository.

All related contributor guidance must align with this document.

## 1) Repository pytest discovery model

### Canonical discovery roots

Repository pytest discovery is rooted at `tests/`.

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

Rationale: one import contract keeps local development, CI, and exported classroom repositories behaviourally aligned.

## 3) Variant selection contract (`PYTUTOR_ACTIVE_VARIANT` and `--variant`)

Variant selection chooses which notebook surface (`student` or `solution`) is executed.

Contract:

- Preferred interface: explicit `--variant <student|solution>` on repository scripts that invoke pytest orchestration (for example `scripts/run_pytest_variant.py` and `scripts/build_autograde_payload.py`).
- Runtime propagation: orchestrators expose the active value through `PYTUTOR_ACTIVE_VARIANT` for downstream runtime resolution.
- Default variant is `student` when no variant is provided.

Compatibility note:

- `PYTUTOR_NOTEBOOKS_DIR` may still exist for transitional compatibility in some paths, but it is no longer the long-term public contract.

## 4) Source-to-export mapping contract

Canonical authoring and export surfaces are intentionally different.

Contract:

- Authoring source of truth: `exercises/<construct>/<exercise_key>/`.
- Export/runtime surfaces during migration: flattened `notebooks/`, `notebooks/solutions/`, and top-level `tests/`.
- Mapping from canonical source to flattened export must be deterministic and reproducible, so the same exercise key resolves to the same exported notebook and test paths.

The mapping layer must preserve exercise identity by `exercise_key` and must not redefine identity from flattened path names.

## Migration status

- **Canonical now**: exercise identity, variant semantics (`--variant`, `PYTUTOR_ACTIVE_VARIANT`), and shared runtime import contract.
- **Transitional**: flattened notebooks and top-level flattened exercise tests used for export compatibility, plus limited legacy path-based resolution.
- **Planned removal**: undocumented legacy entry points and long-term dependency on `PYTUTOR_NOTEBOOKS_DIR`.
