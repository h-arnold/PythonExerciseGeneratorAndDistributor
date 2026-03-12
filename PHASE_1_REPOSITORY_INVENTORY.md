# Phase 1 Repository Inventory

This artefact records the verified repository state for Phase 1 on 2026-03-12.
It is intentionally concrete and repository-specific so later phases can cite it directly rather than re-discovering legacy paths ad hoc.

## Validation Basis

- Activated the repository virtual environment and confirmed the workspace uses Python 3.11.15 from `.venv`.
- Verified current exercise directories with `find exercises -type d -name 'ex*' | sort`.
- Verified current student and solution notebooks with `find notebooks -maxdepth 2 -type f -name 'ex*.ipynb' | sort`.
- Verified current test surfaces with `find tests -type f -name 'test_ex*.py' | sort`.
- Verified identity and path assumptions with targeted source inspection across `scripts/`, `tests/`, `docs/`, `.github/workflows/`, `.github/agents/`, `template_repo_files/`, `README.md`, and `AGENTS.md`.
- `rg` was not available in the shell in this container, so equivalent repository searches were performed with the workspace search tooling.
- Phase 1 made no runtime, resolver, notebook, or filesystem-move changes.

## Confirmed Phase 1 Canonical Model

The following decisions are fixed for later phases and were re-confirmed against the live repository state:

- Canonical resolver input will be `exercise_key` only.
- Canonical authoring location will be `exercises/<construct>/<exercise_key>/`.
- Exercise type leaves the directory hierarchy and moves into `exercise.json`.
- Canonical notebook filenames will be `student.ipynb` and `solution.ipynb` inside the canonical exercise directory.
- Shared grading and runtime helpers will move into `exercise_runtime_support`, leaving top-level `tests/` for executed test suites only.
- Exported Classroom repositories remain metadata-free and keep the current flattened export contract during the transition.
- Public notebook-facing interfaces, including self-check entry points, remain unchanged until a replacement execution model is proved in a later phase.

During the current legacy layout, the authoritative source for each exercise remains the current teacher-doc directory listed below. The canonical target path is a later migration move and is not implemented in Phase 1.

## Current Exercise Inventory

| Exercise key | Current teacher docs path(s) | Current student notebook | Current solution notebook | Current primary test surface(s) | Phase 1 canonical target decision |
| --- | --- | --- | --- | --- | --- |
| `ex001_sanity` | `exercises/ex001_sanity/README.md` | `notebooks/ex001_sanity.ipynb` | `notebooks/solutions/ex001_sanity.ipynb` | `tests/test_ex001_sanity.py` | Removal target only. Do not migrate. There is no canonical target under `exercises/` for this exercise. |
| `ex002_sequence_modify_basics` | `exercises/sequence/modify/ex002_sequence_modify_basics/README.md`; `exercises/sequence/modify/ex002_sequence_modify_basics/OVERVIEW.md` | `notebooks/ex002_sequence_modify_basics.ipynb` | `notebooks/solutions/ex002_sequence_modify_basics.ipynb` | `tests/test_ex002_sequence_modify_basics.py`; `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` | Keep `exercises/sequence/modify/ex002_sequence_modify_basics/` as the authoritative legacy source until files move. Current repo state is an unresolved split test contract: `scripts/template_repo_cli/core/collector.py` resolves the top-level file, `tests/template_repo_cli/conftest.py` uses the nested file, and ex002 parity suites deliberately execute both. Later migration target: keep the nested exercise-local test surface and retire the top-level duplicate during discovery cutover. |
| `ex003_sequence_modify_variables` | `exercises/sequence/modify/ex003_sequence_modify_variables/README.md`; `exercises/sequence/modify/ex003_sequence_modify_variables/OVERVIEW.md`; `exercises/sequence/modify/ex003_sequence_modify_variables/solutions.md` | `notebooks/ex003_sequence_modify_variables.ipynb` | `notebooks/solutions/ex003_sequence_modify_variables.ipynb` | `tests/test_ex003_sequence_modify_variables.py` | Keep the current legacy source as authoritative until files move. Later canonical target: `exercises/sequence/ex003_sequence_modify_variables/`. Low-risk candidate, but not the preferred live pilot. |
| `ex004_sequence_debug_syntax` | `exercises/sequence/debug/ex004_sequence_debug_syntax/README.md`; `exercises/sequence/debug/ex004_sequence_debug_syntax/OVERVIEW.md` | `notebooks/ex004_sequence_debug_syntax.ipynb` | `notebooks/solutions/ex004_sequence_debug_syntax.ipynb` | `tests/test_ex004_sequence_debug_syntax.py` | Keep the current legacy source as authoritative until files move. Later canonical target: `exercises/sequence/ex004_sequence_debug_syntax/`. Recommended Phase 2 live pilot. |
| `ex005_sequence_debug_logic` | `exercises/sequence/debug/ex005_sequence_debug_logic/README.md`; `exercises/sequence/debug/ex005_sequence_debug_logic/OVERVIEW.md` | `notebooks/ex005_sequence_debug_logic.ipynb` | `notebooks/solutions/ex005_sequence_debug_logic.ipynb` | `tests/test_ex005_sequence_debug_logic.py` | Keep the current legacy source as authoritative until files move. Later canonical target: `exercises/sequence/ex005_sequence_debug_logic/`. Reserve backup pilot. |
| `ex006_sequence_modify_casting` | `exercises/ex006_sequence_modify_casting/README.md`; `exercises/sequence/modify/ex006_sequence_modify_casting/README.md`; `exercises/sequence/modify/ex006_sequence_modify_casting/OVERVIEW.md` | `notebooks/ex006_sequence_modify_casting.ipynb` | `notebooks/solutions/ex006_sequence_modify_casting.ipynb` | `tests/test_ex006_sequence_modify_casting.py` | Current authoritative legacy source is `exercises/sequence/modify/ex006_sequence_modify_casting/`. Later canonical target: `exercises/sequence/ex006_sequence_modify_casting/`. Delete the root-level duplicate `exercises/ex006_sequence_modify_casting/` during the migration move. |
| `ex007_sequence_debug_casting` | `exercises/sequence/debug/ex007_sequence_debug_casting/README.md`; `exercises/sequence/debug/ex007_sequence_debug_casting/OVERVIEW.md` | `notebooks/ex007_sequence_debug_casting.ipynb` | `notebooks/solutions/ex007_data_types_debug_casting.ipynb` | `tests/test_ex007_sequence_debug_casting.py`; `tests/test_ex007_construct_checks.py` | Current authoritative legacy source is `exercises/sequence/debug/ex007_sequence_debug_casting/`. Later canonical target: `exercises/sequence/ex007_sequence_debug_casting/`. Before that move, rename the mismatched solution notebook and normalise every remaining `ex007_data_types_debug_casting` alias to the canonical `sequence` key. |

## Confirmed Anomalies And Canonical Target Decisions

| Issue | Verified evidence | Canonical target decision | Phase impact |
| --- | --- | --- | --- |
| Obsolete `ex001_sanity` tree | `exercises/ex001_sanity/`, `notebooks/ex001_sanity.ipynb`, `notebooks/solutions/ex001_sanity.ipynb`, `tests/test_ex001_sanity.py` all still exist | Delete it; do not create a canonical `sequence` or metadata-backed target for it | Blocks later phases from treating every `exNNN_*` tree as a valid migration candidate |
| Duplicate `ex006_sequence_modify_casting` teacher-doc homes | `exercises/ex006_sequence_modify_casting/` and `exercises/sequence/modify/ex006_sequence_modify_casting/` both exist | Treat `exercises/sequence/modify/ex006_sequence_modify_casting/` as the authoritative legacy source, then move to `exercises/sequence/ex006_sequence_modify_casting/` and delete the root duplicate | Blocks any future resolver or manifest from assuming a single teacher-doc home today |
| `ex002_sequence_modify_basics` has duplicate test surfaces | Top-level `tests/test_ex002_sequence_modify_basics.py` exists alongside `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`, and the live repo still executes both in parity checks | Record the current repo state as a split contract rather than treating either file as the verified canonical current surface. Later migration work may still choose the nested exercise-local surface and retire the top-level file after discovery and collector changes land. | Blocks any claim that ex002 already has a single canonical primary test path |
| `ex002` test ownership is already split across tooling | `tests/template_repo_cli/conftest.py` points at the nested ex002 test, `scripts/template_repo_cli/core/collector.py` synthesises the top-level test path, and `tests/exercise_framework/test_autograde_parity.py` plus `tests/exercise_framework/test_parity_autograde_ex002.py` deliberately execute both files | Future packaging and selection work must make the target surface explicit instead of inferring authority from today's mixed tooling | Hidden dependency for template CLI migration sequencing |
| `ex007` solution notebook does not mirror the student notebook stem | Student notebook: `notebooks/ex007_sequence_debug_casting.ipynb`; solution notebook: `notebooks/solutions/ex007_data_types_debug_casting.ipynb` | Rename the solution notebook to the canonical `sequence` key before relying on variant resolution | Blocks trustworthy pilot use of ex007 and later variant-aware resolution |
| `ex007` self-check still uses the legacy `data_types` key | `notebooks/ex007_sequence_debug_casting.ipynb` and `notebooks/solutions/ex007_data_types_debug_casting.ipynb` both call `check_notebook('ex007_data_types_debug_casting')` | Normalise self-check calls to `check_notebook('ex007_sequence_debug_casting')` | Hidden dependency for student-checker and notebook identity consistency |
| `ex007` live test imports a legacy expectations alias | `tests/test_ex007_sequence_debug_casting.py` imports `tests.exercise_expectations.ex007_data_types_debug_casting`, but only `tests/exercise_expectations/ex007_sequence_debug_casting.py` exists | Normalise the test import to the canonical expectations module name | Concrete blocker for clean ex007 identity normalisation |
| Ex007 is missing from some manual registries | `tests/student_checker/api.py` registers ex007, but `tests/exercise_framework/api.py` stops at ex006 and `tests/exercise_expectations/__init__.py` exports only ex001-ex006 | Later registry replacement work must treat ex007 as already drifting, not as a clean baseline | Hidden dependency for framework-level parity and metadata consolidation |
| Stray repository-level teaching-order tree exists under `exercises/` | `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` explicitly says it is a placeholder to satisfy verifier checks | Remove or relocate it; do not treat it as a construct tree | Blocks final structure documentation from claiming the current `exercises/` tree is trustworthy |

## Path-Assumption Inventory

### Code And Test Surfaces

| Surface | Identity model in use today | Verified current assumption | Migration implication |
| --- | --- | --- | --- |
| `scripts/new_exercise.py` | Filename-based plus root-level directory scaffold | Scaffolds `exercises/<exercise_key>/`, `notebooks/<exercise_key>.ipynb`, `notebooks/solutions/<exercise_key>.ipynb`, and `tests/test_<exercise_key>.py` | Later scaffolding must create the canonical exercise directory directly and stop teaching manual moves |
| `scripts/verify_exercise_quality.py` | Directory-based plus notebook filename assumptions | `_find_exercise_dir()` recursively searches for a directory name and prefers the deeper match; `_infer_construct_and_type()` infers metadata from parent folders; `_check_order_of_teaching()` looks for `exercises/<construct>/OrderOfTeaching.md` and notebook mentions | Must move to the metadata/resolver contract and stop using recursive best-guess discovery |
| `scripts/build_autograde_payload.py` | Notebook-path plus environment override | `_normalise_notebooks_dir()` and `validate_environment()` only allow `notebooks` and `notebooks/solutions` | Later variant selection must replace `PYTUTOR_NOTEBOOKS_DIR` as the layout contract |
| `scripts/template_repo_cli/core/collector.py` | Filename-based | `collect_files()` synthesises `notebooks/<exercise_id>.ipynb` and `tests/test_<exercise_id>.py` | Must stop inferring exercise ownership from flat filenames |
| `scripts/template_repo_cli/core/selector.py` | Mixed notebook-stem and directory-hierarchy discovery | `get_all_notebooks()` scans `notebooks/ex*.ipynb`; construct/type selection walks `exercises/<construct>/<type>/<exercise_key>/` | Must move fully to metadata-backed exercise discovery |
| `scripts/template_repo_cli/core/packager.py` | Flattened export contract plus top-level `tests` runtime | Copies notebooks to `workspace/notebooks/<exercise_id>.ipynb`, tests to `workspace/tests/test_<exercise_id>.py`, and runtime helpers out of the live `tests/` package | Later packaging must explicitly map canonical authoring assets onto the flattened export contract |
| `scripts/template_repo_cli/utils/filesystem.py` | Bare-filename notebook fallback | `resolve_notebook_path()` treats a single filename as implicitly living under `notebooks/` | Hidden dependency already fed back into `ACTION_PLAN.md`; later template tooling must not bypass canonical exercise identity this way |
| `scripts/template_repo_cli/utils/validation.py` | Construct/type enum and notebook-pattern validation | Validates construct names, type names, and notebook patterns with no path separators | Must be updated once selection no longer revolves around notebook IDs and type directories |
| `tests/notebook_grader.py` | Notebook-path input plus `PYTUTOR_NOTEBOOKS_DIR` override | `resolve_notebook_path()` accepts a notebook path and falls back to the filename when the input is not under `notebooks/` | Later resolver work must reject path-shaped inputs rather than adapting them |
| `tests/helpers.py` | Wrapper around notebook-path semantics | Re-exports path-based helpers and defaults `PYTUTOR_NOTEBOOKS_DIR` to `notebooks` for autograding helpers | Must move onto the shared resolver and variant contract |
| `tests/exercise_framework/paths.py` | Notebook-path input plus environment override | Mirrors the same override behaviour as `tests/notebook_grader.py` | Must stay in sync during migration, then converge on the same canonical resolver |
| `tests/student_checker/api.py` | Manual slug registry | Registers `_EX001_SLUG` through `_EX007_SLUG` manually in `_NOTEBOOK_ORDER` and `_get_checks()` | Must be replaced by metadata-driven discovery later |
| `tests/exercise_framework/api.py` | Manual slug registry with ex007 drift | Registers `EX001_SLUG` through `EX006_SLUG` only; ex007 is absent | Hidden dependency for later parity and resolver cutover |
| `tests/exercise_expectations/__init__.py` | Manual export registry | Public exports stop at ex006 even though `tests/exercise_expectations/ex007_sequence_debug_casting.py` exists | Hidden dependency for expectation-module migration |
| `tests/test_ex007_sequence_debug_casting.py` | Legacy alias import | Imports `tests.exercise_expectations.ex007_data_types_debug_casting` | Confirms that ex007 naming drift is not limited to notebook filenames |
| `tests/template_repo_cli/conftest.py` | Fixture-level path choice | Treats the nested ex002 test path as canonical sample data | Confirms template CLI tests already depend on a different ex002 test surface than the collector |

### Docs And Workflow Surfaces

| Surface | Verified current assumption | Migration implication |
| --- | --- | --- |
| `README.md`, `AGENTS.md`, `docs/project-structure.md` | Describe the current split layout and the `notebooks/solutions/` contract as normal working practice | Must be rewritten after the resolver and canonical authoring tree are in place |
| `docs/setup.md`, `docs/development.md`, `docs/exercise-generation.md`, `docs/exercise-generation-cli.md`, `docs/exercise-testing.md`, `docs/autograding-cli.md` | Use root-level notebook/test paths and still teach the manual “move the exercise folder afterwards” workflow | Must be updated alongside scaffolding and resolver changes |
| `.github/agents/exercise_generation.md.agent.md`, `.github/agents/exercise_verifier.md.agent.md` | Assume the current split layout and still use stale examples such as `check_notebook('ex007_data_types_debug_casting')` | Must receive explicit transitional guidance before later phases change the canonical model |
| `docs/agents/tidy_code_review/automated_review.md`, `docs/agents/tidy_code_review/manual_review.md` | Continue to instruct reviewers to use `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` and top-level `tests/test_exNNN_*.py` patterns | Must be updated once the runtime and discovery model changes |
| `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml` | Repository CI runs all tests with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` | Later CI must follow the shared resolver and explicit variant contract |
| `template_repo_files/.github/workflows/classroom.yml` | Exported Classroom workflow assumes a flattened `notebooks/` tree and `PYTUTOR_NOTEBOOKS_DIR=notebooks` | Confirms the current exported student contract is metadata-free and flattened; later packaging changes must preserve that contract deliberately |

## Pilot Suitability Analysis

The following scoring uses the objective criteria called out during Phase 1: duplicate directories, missing solution mirror, duplicate test surfaces, manual registry drift, and exercise-specific docs/workflow drift.

| Exercise key | Duplicate directories | Missing solution mirror | Duplicate test surfaces | Manual registry drift | Exercise-specific docs/workflow drift | Risk score | Pilot judgement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ex001_sanity` | No | No | No | No | Yes: obsolete removal-only asset | Removal target | Reject |
| `ex002_sequence_modify_basics` | No | No | Yes | No | Yes: split test contract across collector, fixture data, and parity suites | 2 | Not suitable for the first live pilot |
| `ex003_sequence_modify_variables` | No | No | No | No | No | 0 | Low-risk reserve candidate |
| `ex004_sequence_debug_syntax` | No | No | No | No | No | 0 | Recommended Phase 2 live pilot |
| `ex005_sequence_debug_logic` | No | No | No | No | No | 0 | Backup pilot |
| `ex006_sequence_modify_casting` | Yes | No | No | No | No | 1 | Reject for first live pilot because directory ownership is still duplicated |
| `ex007_sequence_debug_casting` | No | Yes | No | Yes | Yes: stale self-check and stale docs/agent examples | 3 | Reject until naming normalisation is complete |

### Recommended Phase 2 Live Pilot

- Recommended live pilot: `ex004_sequence_debug_syntax`
- Reserve backup pilot: `ex005_sequence_debug_logic`
- Acceptable but not preferred backup: `ex003_sequence_modify_variables`

`ex004_sequence_debug_syntax` remains the best Phase 2 live pilot because the inventory confirmed it is clean on all Phase 1 risk criteria, its teacher docs and notebook/test stems already match, and it is the pilot already named in the migration plan. `ex005_sequence_debug_logic` is equally clean but remains the simpler reserve option. A whole-construct `sequence` pilot is not safe yet because `ex006` and `ex007` would force manual anomaly handling before the resolver layer exists.

## Provisional Manual Migration Handling Set

These entries need explicit handling in a later manifest or migration execution plan.

| Item | Later action |
| --- | --- |
| `ex001_sanity` | Delete rather than migrate |
| `ex002_sequence_modify_basics` | Retire the top-level duplicate test and keep the nested exercise-local test surface |
| `ex006_sequence_modify_casting` | Delete `exercises/ex006_sequence_modify_casting/` after moving the authoritative legacy source to `exercises/sequence/ex006_sequence_modify_casting/` |
| `ex007_sequence_debug_casting` | Rename the solution notebook, fix self-check calls, normalise the live test import, and remove ex007 `data_types` aliases from docs and registries |
| `exercises/PythonExerciseGeneratorAndDistributor/OrderOfTeaching.md` | Remove or relocate the placeholder tree before structure documentation is finalised |

## Action Plan Feedback Recorded During Phase 1

The following concrete blockers or hidden dependencies were discovered while verifying the live repository and were fed back into `ACTION_PLAN.md` during Phase 1:

- `scripts/template_repo_cli/utils/filesystem.py` contains a bare-filename fallback that silently prepends `notebooks/`, which is a hidden template-tooling dependency outside the main framework modules.
- `tests/test_ex007_sequence_debug_casting.py` still imports the legacy expectations alias `tests.exercise_expectations.ex007_data_types_debug_casting`, while `tests/exercise_framework/api.py` and `tests/exercise_expectations/__init__.py` both stop short of a clean ex007 registry surface.
- `ACTION_PLAN.md` previously mixed `exercises/<construct>/<type>/<exercise_key>/` examples with the Phase 1 canonical decision `exercises/<construct>/<exercise_key>/`; Phase 1 corrected that wording so the latter is now the authoritative target contract for later phases.

## Validation Summary

- Filesystem inventory commands matched the seven current student notebook stems and the current exercise directories.
- The live repository confirmed three primary identity blockers before Phase 2: obsolete `ex001`, duplicated `ex006`, and drifted `ex007` naming/registry surfaces.
- The inventory also confirmed one material hidden dependency outside the core grader path: `scripts/template_repo_cli/utils/filesystem.py` silently reconstructs notebook paths from filenames.
- Phase 1 completed as inventory and model-definition work only; no runtime behaviour changed.
