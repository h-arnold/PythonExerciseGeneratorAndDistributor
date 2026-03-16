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
| `ex002_sequence_modify_basics` | `exercises/sequence/modify/ex002_sequence_modify_basics/README.md`; `exercises/sequence/modify/ex002_sequence_modify_basics/OVERVIEW.md`; `exercises/sequence/ex002_sequence_modify_basics/exercise.json` | `notebooks/ex002_sequence_modify_basics.ipynb` | `notebooks/solutions/ex002_sequence_modify_basics.ipynb` | `tests/test_ex002_sequence_modify_basics.py`; `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` | Current repo is mid-migration: legacy teacher docs remain under `exercises/sequence/modify/ex002_sequence_modify_basics/`, and a canonical metadata stub already exists at `exercises/sequence/ex002_sequence_modify_basics/`. Current repo state is also an unresolved split test contract: `scripts/template_repo_cli/core/collector.py` and `tests/template_repo_cli/conftest.py` both resolve the top-level file, and ex002 parity suites deliberately execute both live test files. Later migration target: keep the nested exercise-local test surface, retire the top-level duplicate during discovery cutover, and make directory ownership explicit. |
| `ex003_sequence_modify_variables` | `exercises/sequence/modify/ex003_sequence_modify_variables/README.md`; `exercises/sequence/modify/ex003_sequence_modify_variables/OVERVIEW.md`; `exercises/sequence/modify/ex003_sequence_modify_variables/solutions.md`; `exercises/sequence/ex003_sequence_modify_variables/exercise.json` | `notebooks/ex003_sequence_modify_variables.ipynb` | `notebooks/solutions/ex003_sequence_modify_variables.ipynb` | `tests/test_ex003_sequence_modify_variables.py` | Current repo is mid-migration: legacy teacher docs remain under `exercises/sequence/modify/ex003_sequence_modify_variables/`, and a canonical metadata stub already exists at `exercises/sequence/ex003_sequence_modify_variables/`. Keep the legacy source as authoritative until files move. Acceptable but not preferred backup candidate. |
| `ex004_sequence_debug_syntax` | `exercises/sequence/ex004_sequence_debug_syntax/README.md`; `exercises/sequence/ex004_sequence_debug_syntax/OVERVIEW.md`; `exercises/sequence/ex004_sequence_debug_syntax/exercise.json` | `notebooks/ex004_sequence_debug_syntax.ipynb` | `notebooks/solutions/ex004_sequence_debug_syntax.ipynb` | `exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py` | Current repo already includes the canonical exercise directory at `exercises/sequence/ex004_sequence_debug_syntax/`. The flattened top-level notebook contract still exists under `notebooks/` and `notebooks/solutions/`. Recommended Phase 2 live pilot. |
| `ex005_sequence_debug_logic` | `exercises/sequence/debug/ex005_sequence_debug_logic/README.md`; `exercises/sequence/debug/ex005_sequence_debug_logic/OVERVIEW.md`; `exercises/sequence/ex005_sequence_debug_logic/exercise.json` | `notebooks/ex005_sequence_debug_logic.ipynb` | `notebooks/solutions/ex005_sequence_debug_logic.ipynb` | `tests/test_ex005_sequence_debug_logic.py` | Current repo is mid-migration: legacy teacher docs remain under `exercises/sequence/debug/ex005_sequence_debug_logic/`, and a canonical metadata stub already exists at `exercises/sequence/ex005_sequence_debug_logic/`. Reserve backup pilot only after directory ownership is made explicit. |
| `ex006_sequence_modify_casting` | `exercises/sequence/ex006_sequence_modify_casting/README.md`; `exercises/sequence/ex006_sequence_modify_casting/OVERVIEW.md`; `exercises/sequence/ex006_sequence_modify_casting/exercise.json` | `notebooks/ex006_sequence_modify_casting.ipynb` | `notebooks/solutions/ex006_sequence_modify_casting.ipynb` | `tests/test_ex006_sequence_modify_casting.py` | Current repo already includes the canonical exercise directory at `exercises/sequence/ex006_sequence_modify_casting/`. Teacher docs and metadata are co-located there, while the flattened notebook and top-level test contracts still remain under `notebooks/`, `notebooks/solutions/`, and `tests/`. |
| `ex007_sequence_debug_casting` | `exercises/sequence/debug/ex007_sequence_debug_casting/README.md`; `exercises/sequence/debug/ex007_sequence_debug_casting/OVERVIEW.md`; `exercises/sequence/ex007_sequence_debug_casting/exercise.json` | `notebooks/ex007_sequence_debug_casting.ipynb` | `notebooks/solutions/ex007_sequence_debug_casting.ipynb` | `tests/test_ex007_sequence_debug_casting.py`; `tests/test_ex007_construct_checks.py` | Current repo is mid-migration: legacy teacher docs remain under `exercises/sequence/debug/ex007_sequence_debug_casting/`, and a canonical metadata stub already exists at `exercises/sequence/ex007_sequence_debug_casting/`. The current solution notebook already uses the canonical `sequence` stem. |

## Confirmed Anomalies And Canonical Target Decisions

| Issue | Verified evidence | Canonical target decision | Phase impact |
| --- | --- | --- | --- |
| `ex002_sequence_modify_basics` has duplicate test surfaces | Top-level `tests/test_ex002_sequence_modify_basics.py` exists alongside `tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py`, and the live repo still executes both in parity checks | Record the current repo state as a split contract rather than treating either file as the verified canonical current surface. Later migration work may still choose the nested exercise-local surface and retire the top-level file after discovery and collector changes land. | Blocks any claim that ex002 already has a single canonical primary test path |
| `ex002` test ownership is already split across tooling | `tests/template_repo_cli/conftest.py` and `scripts/template_repo_cli/core/collector.py` both point at the top-level ex002 test path, while `tests/exercise_framework/test_autograde_parity.py` plus `tests/exercise_framework/test_parity_autograde_ex002.py` deliberately execute both live test files | Future packaging and selection work must make the target surface explicit instead of inferring authority from today's mixed tooling | Hidden dependency for template CLI migration sequencing |
| Duplicate `ex002_sequence_modify_basics` exercise directories | `exercises/sequence/modify/ex002_sequence_modify_basics/` still holds the legacy README/OVERVIEW authoring docs, and `exercises/sequence/ex002_sequence_modify_basics/exercise.json` now also exists | Keep the legacy docs directory as the current authoring source until later phases either complete the canonical move or delete the stub | Blocks any claim that ex002 is still a single-home exercise while the split test contract remains unresolved |
| Duplicate `ex003_sequence_modify_variables` exercise directories | `exercises/sequence/modify/ex003_sequence_modify_variables/` still holds the legacy README/OVERVIEW authoring docs plus `solutions.md`, and `exercises/sequence/ex003_sequence_modify_variables/exercise.json` now also exists | Keep the legacy docs directory as the current authoring source until later phases either complete the canonical move or delete the stub | Blocks any claim that ex003 is still a single-home low-risk reserve candidate |
| Duplicate `ex005_sequence_debug_logic` exercise directories | `exercises/sequence/debug/ex005_sequence_debug_logic/` still holds the legacy README/OVERVIEW authoring docs, and `exercises/sequence/ex005_sequence_debug_logic/exercise.json` now also exists | Keep the legacy docs directory as the current authoring source until later phases either complete the canonical move or delete the stub | Blocks any claim that ex005 is still a single-home backup pilot |
| Duplicate `ex007_sequence_debug_casting` exercise directories | `exercises/sequence/debug/ex007_sequence_debug_casting/` still holds the legacy README/OVERVIEW authoring docs, `exercises/sequence/ex007_sequence_debug_casting/exercise.json` now also exists, and the current solution notebook is `notebooks/solutions/ex007_sequence_debug_casting.ipynb` | Keep the legacy docs directory as the current authoring source until later phases reconcile the duplicate directories; record the `sequence` solution notebook stem as the current truth | Blocks any claim that ex007 has only one current exercise home, even though the notebook stem mismatch has already been fixed |
| Ex007 is missing from some manual registries | `tests/student_checker/api.py` registers ex007, but `tests/exercise_framework/api.py` stops at ex006 and `tests/exercise_expectations/__init__.py` exports only ex001-ex006 | Later registry replacement work must treat ex007 as already drifting, not as a clean baseline | Hidden dependency for framework-level parity and metadata consolidation |

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
| `tests/notebook_grader.py` | Compatibility wrapper | Re-exports `exercise_runtime_support.notebook_grader` and adds no local notebook-resolution logic | Keep as a thin shim until downstream imports move to the runtime-support package |
| `tests/helpers.py` | Compatibility wrapper | Re-exports `exercise_runtime_support.helpers`; the live variant and notebook-resolution behaviour now lives there | Keep as a thin shim until downstream imports move to the runtime-support package |
| `tests/exercise_framework/paths.py` | Compatibility wrapper | Re-exports `exercise_runtime_support.exercise_framework.paths` path helpers and adds no local exercise-path logic | Keep as a thin shim until downstream imports move to the runtime-support package |
| `tests/student_checker/api.py` | Compatibility wrapper | Re-exports `exercise_runtime_support.student_checker.api` and adds no local exercise-identity logic | Keep as a thin shim until downstream imports move to the runtime-support package |
| `exercise_runtime_support/student_checker/api.py` | Catalogue-backed exercise-key discovery | Uses `get_exercise_catalogue()`, `get_catalogue_entry()`, `get_catalogue_key_for_exercise_id()`, and support-role checks to order and resolve live notebook checks by exercise key | This is now the live student-checker identity contract |
| `tests/exercise_framework/api.py` | Compatibility wrapper | Re-exports `exercise_runtime_support.exercise_framework.api` and adds no local exercise-identity logic | Keep as a thin shim until downstream imports move to the runtime-support package |
| `exercise_runtime_support/exercise_framework/api.py` | Catalogue-backed exercise-key discovery | Uses `get_exercise_catalogue()`, `get_catalogue_entry()`, and support-role checks to build the live framework check set by exercise key | This is now the live exercise-framework identity contract |
| `tests/exercise_expectations/__init__.py` | Manual export registry | Public exports stop at ex006 even though `tests/exercise_expectations/ex007_sequence_debug_casting.py` exists | Hidden dependency for expectation-module migration |
| `tests/test_ex007_sequence_debug_casting.py` | Canonical expectations-module import | Imports `tests.exercise_expectations.ex007_sequence_debug_casting` directly | Confirms the live ex007 test has already normalised its expectations-module name |
| `tests/template_repo_cli/conftest.py` | Fixture-level path choice | Uses the top-level `tests/test_ex002_sequence_modify_basics.py` path in sample data | Confirms template CLI tests currently align with the collector on the top-level ex002 surface, even though parity suites still execute both live files |

### Docs And Workflow Surfaces

| Surface | Verified current assumption | Migration implication |
| --- | --- | --- |
| `README.md`, `AGENTS.md`, `docs/project-structure.md` | Describe the current split layout and the `notebooks/solutions/` contract as normal working practice | Must be rewritten after the resolver and canonical authoring tree are in place |
| `docs/setup.md`, `docs/development.md`, `docs/exercise-generation.md`, `docs/exercise-generation-cli.md`, `docs/exercise-testing.md`, `docs/autograding-cli.md` | Use root-level notebook/test paths and still teach the manual “move the exercise folder afterwards” workflow | Must be updated alongside scaffolding and resolver changes |
| `.github/agents/exercise_generation.md.agent.md`, `.github/agents/exercise_verifier.md.agent.md` | Assume the current split layout and use the canonical `check_notebook('ex007_sequence_debug_casting')` example | Must receive explicit transitional guidance before later phases change the canonical model |
| `docs/agents/tidy_code_review/automated_review.md`, `docs/agents/tidy_code_review/manual_review.md` | Instruct reviewers to use the explicit `uv run python scripts/run_pytest_variant.py --variant solution ...` command guidance | Keep aligned with the shared variant-runner contract during later migration work |
| `.github/workflows/tests.yml`, `.github/workflows/tests-solutions.yml` | Repository CI runs solution verification via `scripts/run_pytest_variant.py --variant solution` | Keep aligned with the shared resolver and explicit variant contract during later migration work |
| `template_repo_files/.github/workflows/classroom.yml` | Exported Classroom workflow assumes a flattened `notebooks/` tree and `PYTUTOR_NOTEBOOKS_DIR=notebooks` | Confirms the current exported student contract is metadata-free and flattened; later packaging changes must preserve that contract deliberately |

## Pilot Suitability Analysis

The following scoring uses the objective criteria called out during Phase 1: duplicate directories, missing solution mirror, duplicate test surfaces, manual registry drift, and exercise-specific docs/workflow drift.

| Exercise key | Duplicate directories | Missing solution mirror | Duplicate test surfaces | Manual registry drift | Exercise-specific docs/workflow drift | Risk score | Pilot judgement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ex002_sequence_modify_basics` | Yes | No | Yes | No | Yes: split test contract across collector, fixture data, and parity suites | 3 | Not suitable for the first live pilot |
| `ex003_sequence_modify_variables` | Yes | No | No | No | No | 1 | Acceptable but not preferred backup candidate |
| `ex004_sequence_debug_syntax` | No | No | No | No | No | 0 | Recommended Phase 2 live pilot |
| `ex005_sequence_debug_logic` | Yes | No | No | No | No | 1 | Backup pilot only after duplicate-directory handling |
| `ex006_sequence_modify_casting` | No | No | No | No | No | 0 | Acceptable but not preferred backup candidate |
| `ex007_sequence_debug_casting` | Yes | No | No | Yes | No | 2 | Reject until duplicate-directory and registry drift are reconciled |

### Recommended Phase 2 Live Pilot

- Recommended live pilot: `ex004_sequence_debug_syntax`
- Reserve backup pilot: `ex005_sequence_debug_logic`
- Acceptable but not preferred backups: `ex003_sequence_modify_variables`, `ex006_sequence_modify_casting`

`ex004_sequence_debug_syntax` remains the best Phase 2 live pilot because the inventory confirmed it already has a coherent canonical exercise directory, matching notebook/test stems, and the pilot status already named in the migration plan. `ex005_sequence_debug_logic` remains the reserve option, but it is no longer equally clean because a canonical metadata stub now coexists with the legacy docs directory. A whole-construct `sequence` pilot is not safe yet because `ex005` and `ex007` still require manual duplicate-directory handling before the resolver layer exists.

## Provisional Manual Migration Handling Set

These entries need explicit handling in a later manifest or migration execution plan.

| Item | Later action |
| --- | --- |
| `ex002_sequence_modify_basics` | Retire the top-level duplicate test and keep the nested exercise-local test surface |
| `ex005_sequence_debug_logic` | Reconcile the legacy docs directory and canonical metadata stub before treating ex005 as a single-home exercise |
| `ex007_sequence_debug_casting` | Reconcile the legacy docs directory and canonical metadata stub before treating ex007 as a single-home exercise |

## Action Plan Feedback Recorded During Phase 1

The following concrete blockers or hidden dependencies were discovered while verifying the live repository and were fed back into `ACTION_PLAN.md` during Phase 1:

- `scripts/template_repo_cli/utils/filesystem.py` contains a bare-filename fallback that silently prepends `notebooks/`, which is a hidden template-tooling dependency outside the main framework modules.
- `ACTION_PLAN.md` previously mixed `exercises/<construct>/<type>/<exercise_key>/` examples with the Phase 1 canonical decision `exercises/<construct>/<exercise_key>/`; Phase 1 corrected that wording so the latter is now the authoritative target contract for later phases.

## Validation Summary

- Filesystem inventory commands matched the six current top-level student notebook stems and the current exercise directories.
- The live repository no longer includes `ex001_sanity`; the current filesystem blockers captured here are duplicated `ex002`, duplicated `ex003`, duplicated `ex005`, and duplicated `ex007` exercise-directory states.
- The inventory also confirmed one material hidden dependency outside the core grader path: `scripts/template_repo_cli/utils/filesystem.py` silently reconstructs notebook paths from filenames.
- Phase 1 completed as inventory and model-definition work only; no runtime behaviour changed.
