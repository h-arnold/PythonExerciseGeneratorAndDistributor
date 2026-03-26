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

Rationale: one import contract keeps local development, CI, and exported classroom repositories behaviourally aligned.

## 3) Variant selection contract (`PYTUTOR_ACTIVE_VARIANT` and `--variant`)

Variant selection chooses which notebook surface (`student` or `solution`) is executed.

Contract:

- Preferred interface: explicit `--variant <student|solution>` on repository scripts that invoke pytest orchestration (for example `scripts/run_pytest_variant.py` and `scripts/build_autograde_payload.py`).
- Runtime propagation: orchestrators expose the active value through the `PYTUTOR_ACTIVE_VARIANT` environment variable for downstream runtime resolution.
- Default variant is `solution` when no variant is provided.

Deprecated note:

- `legacy notebook-root override env var` is not part of the supported execution contract. New tooling must ignore or clear it rather than using it for notebook selection.

## 4) Source-to-export mapping contract

Canonical authoring and export surfaces are intentionally different.

Contract:

- Authoring source of truth: `exercises/<construct>/<exercise_key>/`.
- Export surfaces: flattened `notebooks/`, `notebooks/solutions/`, and top-level `tests/` inside packaged Classroom repositories.
- Mapping from canonical source to flattened export must be deterministic and reproducible, so the same exercise key resolves to the same exported notebook and test paths.

The mapping layer must preserve exercise identity by `exercise_key` and must not redefine identity from flattened path names.

## Current status

- **Canonical now**: exercise identity, exercise-local notebooks and tests, variant semantics (`--variant`, `PYTUTOR_ACTIVE_VARIANT`), and shared runtime import contract.
- **Export-only**: flattened notebooks and top-level flattened exercise tests used in packaged Classroom repositories.
- **Removed from the supported contract**: `legacy notebook-root override env var` must not be relied on for notebook selection.


## 5) Consumer matrix (definitive migration tracker)

The following matrix records each active consumer surface, its current entry point, and the target entry point for the shared execution contract.

| Surface | Current entry point | Target entry point |
| --- | --- | --- |
| runtime/grading wrapper | tests.notebook_grader wrapper | exercise_runtime_support.notebook_grader |
| framework API wrapper | tests.exercise_framework.runtime wrapper | exercise_runtime_support.exercise_framework.* |
| packager and collector CLI | scripts/template_repo_cli/core/* imports and packaging surfaces | exercise_runtime_support package copied and referenced |
| exercise scaffolder | emitted import from exercise_runtime_support.exercise_framework.runtime | emitted import from exercise_runtime_support.exercise_framework.runtime |
| repository workflows | scripts/run_pytest_variant.py --variant solution | scripts/run_pytest_variant.py --variant solution |
| classroom template workflow | scripts/build_autograde_payload.py --variant student | scripts/build_autograde_payload.py --variant student |
| contributor documentation | legacy and transition guidance scattered across docs and AGENTS.md | single contract documented in docs/execution-model.md |

Maintenance note: `tests/exercise_runtime_support/test_consumer_matrix.py` validates this matrix, checks listed files exist, and guards against regressions that bypass the shared contract.
