# Action Plan

## Goal

Move the repository towards an exercise-centric layout where each exercise has a single canonical home under `exercises/`, while shared infrastructure remains in the existing top-level `tests/`, `scripts/`, and `docs/` directories.

This is intended to solve the current split-brain model where a single exercise is spread across:

- `exercises/` for teacher-facing notes
- `notebooks/` for student and solution notebooks
- `tests/` for exercise-specific test files

## Proposed Canonical Layout

### Design Rules

1. `exercises/` becomes the only canonical home for exercise-specific assets.
2. Construct-wide material stays directly under `exercises/<construct>/`.
3. Each exercise lives at `exercises/<construct>/<exercise_key>/`.
4. Exercise type is stored in metadata, not encoded by an extra path segment.
5. Shared test framework code remains in the top-level `tests/` package unless Phase 4 explicitly replaces that with a dedicated support package.
6. Exercise-local tests live inside the exercise folder and may continue to import shared helpers from the top-level `tests/` package unless Phase 4 changes that shared-runtime decision explicitly.
7. During migration, packaging may still flatten notebooks and tests for template repositories if that keeps downstream Classroom workflows stable.
8. During migration, layout state must be explicit per exercise; resolvers must not silently fall back between legacy and migrated paths.
9. The canonical resolver input is `exercise_key`; path-based resolution is not part of the target API.
10. Legacy callers that still pass paths or rely on legacy layout conventions should fail until they are refactored onto the new resolver model.
11. Migration success must be demonstrated by explicit acceptance criteria at each phase rather than inferred from partial compatibility.
12. Prefer deliberate breaking changes over compatibility wrappers, fallback resolution, or dual-interface support during this migration.
13. Exported Classroom repositories remain metadata-free student repositories; they should not ship `exercise.json` or the full `exercises/` authoring tree unless a later explicit decision changes that contract.
14. Export-safe generated runtime artefacts are allowed only if they are deliberate packaging outputs, remain metadata-free from an authoring perspective, and do not recreate the source-repository authoring tree inside Classroom exports.
15. `exercise.json` is the full single source of truth for the small set of exercise-specific metadata that should remain configurable at repository level.
16. If a property is fixed by repository convention, it should not be duplicated in `exercise.json`.
17. Public interface breaking changes should happen only after the replacement execution model is defined and proven for at least one end-to-end migrated exercise.
18. The authoring repository contract and the exported Classroom contract must be treated as separate first-class designs at every phase.

### Target Tree

```text
PythonExerciseGeneratorAndDistributor/
├── docs/
├── scripts/
├── tests/                             # shared framework and non-exercise tests only
├── exercises/
│   ├── sequence/
│   │   ├── OrderOfTeaching.md
│   │   ├── README.md                  # optional construct overview
│   │   ├── ex001_sanity/ (obsolete, reserved for removal before later phases)
│   │   │   ├── exercise.json
│   │   │   ├── README.md
│   │   │   ├── OVERVIEW.md
│   │   │   ├── STUDENT_GUIDE.md       # optional
│   │   │   ├── TEACHER_GUIDE.md       # optional
│   │   │   ├── CHEAT_SHEET.md         # optional
│   │   │   ├── assets/                # optional
│   │   │   ├── notebooks/
│   │   │   │   ├── student.ipynb
│   │   │   │   └── solution.ipynb
│   │   │   └── tests/
│   │   │       ├── test_ex001_sanity.py
│   │   │       └── fixtures.py        # optional
│   │   └── ex006_sequence_modify_casting/
│   │       ├── exercise.json
│   │       ├── README.md
│   │       ├── OVERVIEW.md
│   │       ├── notebooks/
│   │       │   ├── student.ipynb
│   │       │   └── solution.ipynb
│   │       └── tests/
│   │           └── test_ex006_sequence_modify_casting.py
├── README.md
├── AGENTS.md
└── ACTION_PLAN.md
```

### Naming Notes

1. Keep existing exercise directory names such as `ex006_sequence_modify_casting` for the first migration pass to reduce churn.
2. Standardise notebook file names inside each exercise to `student.ipynb` and `solution.ipynb`.
3. Standardise the main test file name to `test_<exercise_key>.py`.
4. Keep construct-level files like `OrderOfTeaching.md` at `exercises/<construct>/`.

## Proposed Metadata Format

### Canonical Metadata File

`exercises/<construct>/<exercise_key>/exercise.json`

### Metadata Principles

1. Use JSON to stay stdlib-friendly for existing Python scripts.
2. Store facts that should no longer be inferred from path shape.
3. Do not duplicate information that is already fixed by convention unless there is a strong reason.
4. Treat this file as the source of truth for exercise identity, title, type, structural expectations, and other exercise-level metadata currently duplicated in framework registries and docs.

### Example

```json
{
  "schema_version": 1,
  "exercise_key": "ex006_sequence_modify_casting",
  "exercise_id": "ex006",
  "slug": "casting",
  "title": "Casting and Type Conversion",
  "construct": "sequence",
  "exercise_type": "modify",
  "parts": 1
}
```

### Canonical Metadata Fields

| Field | Purpose |
| --- | --- |
| `schema_version` | Allows future migrations without guesswork |
| `exercise_key` | Stable identifier used by scripts and tests |
| `exercise_id` | Short display and ordering identifier such as `ex006` |
| `slug` | Human-readable identifier without needing to preserve the full legacy key shape |
| `title` | Exercise title used in docs and generated notebooks |
| `construct` | Curriculum grouping such as `sequence` |
| `exercise_type` | `debug`, `modify`, or `make` without requiring another folder level |
| `parts` | Number of graded exercise parts in the notebook |

### Single Source Of Truth Scope

`exercise.json` should ultimately replace exercise-level metadata that is currently repeated across multiple places, including:

1. Exercise identity and path assumptions
2. Exercise title and display text used by tooling
3. Exercise type and construct grouping
4. The minimal structural metadata required to derive exercise-local conventions such as part count

This does not mean that every downstream exported student repository must receive `exercise.json`. The repository can use metadata as the source of truth while packaging exports a flattened, metadata-free student contract.

### Explicit Non-Metadata Conventions

The following are deliberate repository conventions and should not be stored in `exercise.json`:

1. Student notebook path: always `notebooks/student.ipynb`
2. Solution notebook path: always `notebooks/solution.ipynb`
3. Primary test path: always `tests/test_<exercise_key>.py`
4. Teacher overview path: always `OVERVIEW.md` when present
5. Exercise ordering: derived from `exercise_id`
6. Student self-check cell: always present as part of the notebook structure
7. Exercise tags: derived from `parts` as `exercise1` through `exerciseN`
8. Debug explanation tags: derived from `exercise_type == "debug"` and `parts`
9. Display labels such as checker titles: derived from `exercise_id` and `title`

### Explicitly Out Of Metadata Scope

The following should remain outside `exercise.json`:

1. Difficulty labels
2. Publication or draft status
3. Prerequisites
4. Checker wiring and module-to-check mappings
5. Expected outputs, prompts, inputs, and behavioural assertions
6. Exported Classroom repository paths and packaging destinations

## Path Assumptions To Replace

The current repository has a number of path assumptions wired into tooling, docs, and tests. Each assumption below should be treated as a migration work item.

| Current assumption | Current examples | Migration action |
| --- | --- | --- |
| Exercise notebooks live under `notebooks/` | [tests/notebook_grader.py](tests/notebook_grader.py), [tests/exercise_framework/paths.py](tests/exercise_framework/paths.py), many `tests/test_ex*.py` files | Introduce a central resolver that works from `exercise_key` or exercise directory rather than hard-coded top-level notebook paths |
| Solution notebooks live under `notebooks/solutions/` and are selected with `PYTUTOR_NOTEBOOKS_DIR` | [tests/notebook_grader.py](tests/notebook_grader.py), [scripts/build_autograde_payload.py](scripts/build_autograde_payload.py), [scripts/verify_solutions.sh](scripts/verify_solutions.sh) | Move to a variant-aware resolver that selects `student.ipynb` or `solution.ipynb` without depending on a global folder name, and do not use `PYTUTOR_NOTEBOOKS_DIR` as a layout compatibility fallback |
| Exercise-specific tests live in the top-level `tests/` directory | [pytest.ini](pytest.ini), [scripts/template_repo_cli/core/collector.py](scripts/template_repo_cli/core/collector.py), [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py) | Update test discovery, packaging, and file collection to recognise `exercises/**/tests/` |
| Exercise type is encoded in the `exercises/<construct>/<type>/<slug>/` path | [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py), [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py) | Move exercise type into `exercise.json` and update selectors and validators to read metadata |
| Scaffolding creates a split structure first and relies on manual moving | [scripts/new_exercise.py](scripts/new_exercise.py), [docs/setup.md](docs/setup.md) | Change scaffolding to create the canonical exercise directory directly |
| Template packaging copies notebooks from `notebooks/` and tests from `tests/` | [scripts/template_repo_cli/core/collector.py](scripts/template_repo_cli/core/collector.py), [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py) | Decide whether packaging flattens exported assets or preserves nested structure, then encode that explicitly |
| Notebook self-check cells assume filename or slug-based lookup | [scripts/new_exercise.py](scripts/new_exercise.py), [tests/student_checker/notebook_runtime.py](tests/student_checker/notebook_runtime.py), [tests/student_checker/api.py](tests/student_checker/api.py), [tests/template_repo_cli/test_integration.py](tests/template_repo_cli/test_integration.py) | Define and migrate a canonical self-check contract so generated notebooks, packaged templates, and student checker APIs resolve exercises consistently |
| Expectation and framework modules hard-code notebook paths per exercise | [tests/exercise_expectations](tests/exercise_expectations), [tests/exercise_framework/api.py](tests/exercise_framework/api.py), [tests/student_checker/checks](tests/student_checker/checks) | Replace raw notebook path constants with exercise-key-driven or metadata-driven resolution so the framework does not maintain a second path model |
| Helper utilities wrap notebook-path behaviour outside the main framework modules | [tests/helpers.py](tests/helpers.py), [tests/test_integration_autograding.py](tests/test_integration_autograding.py), [tests/test_build_autograde_payload.py](tests/test_build_autograde_payload.py) | Move helper-level path handling onto the same resolver and execution-model contract rather than leaving hidden notebook-path assumptions in support code |
| CI and exported workflow configuration assume `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` | [.github/workflows/tests.yml](.github/workflows/tests.yml), [.github/workflows/tests-solutions.yml](.github/workflows/tests-solutions.yml), [template_repo_files](template_repo_files) | Update repository and template workflows alongside the resolver changes so CI behaviour matches the new layout model |
| Docs and tests assume the current flattened template export contract | [docs/CLI_README.md](docs/CLI_README.md), [tests/template_repo_cli](tests/template_repo_cli), [tests/exercise_framework/test_autograde_parity.py](tests/exercise_framework/test_autograde_parity.py) | Make the export contract explicit and migrate its tests and docs together with selector, collector, and packager changes |
| Pytest discovery currently assumes exercise-specific tests live under the top-level `tests/` tree | [pyproject.toml](pyproject.toml), [tests](tests), [tests/template_repo_cli](tests/template_repo_cli) | Define the repository test discovery model explicitly before moving exercise-local tests, including whether pytest collects directly from `exercises/**/tests/` and how shared helper imports continue to work |
| Shared grading/runtime helpers currently live in an importable top-level `tests` package | [pyproject.toml](pyproject.toml), [tests/exercise_framework/api.py](tests/exercise_framework/api.py), [tests/student_checker/api.py](tests/student_checker/api.py) | Decide whether the shared runtime remains an importable `tests` package or moves to a dedicated support package before exercise-local tests are relocated |
| Existing exercise identities are not fully clean or unique | [exercises](exercises), [notebooks](notebooks), [tests](tests), [exercises/sequence/OrderOfTeaching.md](exercises/sequence/OrderOfTeaching.md) | Inventory current exercise keys, duplicate directories, construct/type mismatches, and naming drift before relying on metadata or migration manifests |
| Docs and agent instructions describe the split layout as canonical | [README.md](README.md), [docs/project-structure.md](docs/project-structure.md), [AGENTS.md](AGENTS.md), [.github/agents/exercise_generation.md.agent.md](.github/agents/exercise_generation.md.agent.md) | Rewrite docs and agent instructions after the resolver and scaffolder are in place |
| Current agent files will remain live during migration and therefore need transitional guidance | [.github/agents](.github/agents), [AGENTS.md](AGENTS.md), [ACTION_PLAN.md](ACTION_PLAN.md) | Keep current agent files authoritative until replacements are ready, add clear migration warning blocks that point to `ACTION_PLAN.md`, and only archive old agent files after replacement instructions and references are in place |
| Public interfaces are currently notebook-shaped and path-oriented | [docs/CLI_README.md](docs/CLI_README.md), [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py), [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py), [scripts/new_exercise.py](scripts/new_exercise.py) | Make the interface cutover explicit and favour deliberate breaking changes over compatibility aliases once the new resolver model is ready |
| Exercise registry data is duplicated outside path resolution | [tests/student_checker/api.py](tests/student_checker/api.py), [tests/exercise_framework/api.py](tests/exercise_framework/api.py), [tests/exercise_expectations](tests/exercise_expectations) | Add a dedicated metadata consolidation stream so `exercise.json` replaces duplicated exercise registry data rather than only replacing path logic |
| Repository metadata and exported template contracts have different needs | [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py), [docs/CLI_README.md](docs/CLI_README.md), [tests/template_repo_cli/test_packager.py](tests/template_repo_cli/test_packager.py) | Keep repository metadata rich while preserving a metadata-free exported Classroom contract, and make the transformation between those models explicit in packaging |
| Source repository assets and exported Classroom assets currently share assumptions without a clearly documented mapping contract | [scripts/template_repo_cli](scripts/template_repo_cli), [tests/template_repo_cli](tests/template_repo_cli), [docs/CLI_README.md](docs/CLI_README.md) | Define the source-to-export mapping explicitly so metadata-rich authoring exercises can produce the existing metadata-free flattened export safely and predictably |
| Mixed-layout discovery could collect the same exercise-specific surface twice during migration | [tests/test_ex002_sequence_modify_basics.py](tests/test_ex002_sequence_modify_basics.py), [tests/ex002_sequence_modify_basics](tests/ex002_sequence_modify_basics), [pyproject.toml](pyproject.toml) | Make duplicate-collection detection and hard failure an explicit acceptance criterion for the execution-model and pytest-discovery phases |
| Exercise metadata could become bloated again if conventions are reintroduced as configuration | [ACTION_PLAN.md](ACTION_PLAN.md), [scripts/new_exercise.py](scripts/new_exercise.py), [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py), [tests/student_checker/api.py](tests/student_checker/api.py) | Keep the metadata schema intentionally small, derive all convention-based fields, and reject proposals that reintroduce duplicated configuration without a strong need |

## Migration Checklist

### Phase 1: Repository Inventory And Canonical Model

#### Constraints And Acceptance Criteria

- [ ] Do not begin resolver implementation until the repository inventory is complete enough to identify duplicate or ambiguous exercise identities.
- [ ] The phase is only complete once there is a written inventory of current exercise identities, locations, and known anomalies that later phases can refer to.
- [ ] Do not choose a pilot construct for migration until the inventory confirms it is suitable for a safe first cut.
- [ ] The phase is not complete until duplicate exercise ownership is either resolved directly or represented explicitly in the migration manifest with one canonical target per exercise.
- [ ] Identity normalisation rules must be written down explicitly, not inferred informally from current file names.

- [ ] Inventory every current exercise key and record its current teacher docs path, notebook path, solution notebook path, and test path.
- [ ] Record duplicate directories, stale exercise folders, construct mismatches, slug mismatches, and other naming anomalies that could make migration ambiguous.
- [ ] Identify which current modules treat exercise identity as a filename, a slug, a path, or a directory name.
- [ ] Use this inventory to define the canonical exercise identity that later resolvers and migration manifests will rely on.
- [ ] Use this inventory to identify the safest pilot construct rather than assuming `sequence` is automatically the best first migration target.
- [ ] Keep a running list of likely pain points in: [exercises](exercises), [notebooks](notebooks), [tests](tests), [docs](docs), and [.github/agents](.github/agents).
- [ ] Agree that `exercises/<construct>/<exercise_key>/` is the canonical location for all exercise-specific assets.
- [ ] Confirm that exercise type is moving from the folder hierarchy into `exercise.json`.
- [ ] Confirm standard notebook names: `student.ipynb` and `solution.ipynb`.
- [ ] Confirm that top-level `tests/` remains for shared grading infrastructure only.
- [ ] Confirm whether template exports should flatten notebooks and tests during the transition.
- [ ] Record the early identity-normalisation blockers explicitly and decide their target canonical forms before Phase 2 starts.

#### Identity Normalisation Rules

- [ ] Normalise duplicate exercise homes so each exercise has one canonical target directory under `exercises/<construct>/<exercise_key>/`.
- [ ] Normalise mixed key families so construct naming stays consistent. For example, `ex007` is a `sequence` exercise and should remain `ex007_sequence_debug_casting`, not `ex007_data_types_debug_casting`.
- [ ] Remove obsolete root-level exercises that no longer serve a real repository purpose, and normalise any remaining legacy root-level exercise directories such as `exercises/ex006_sequence_modify_casting/` into the agreed construct-based canonical tree during migration planning.
- [ ] Normalise self-check references, expectation-module names, and notebook stems so they all match the canonical `exercise_key`.
- [ ] Treat stray or non-exercise trees such as [exercises/PythonExerciseGeneratorAndDistributor](exercises/PythonExerciseGeneratorAndDistributor) as anomalies to be removed, relocated, or explicitly documented before the canonical inventory is considered trustworthy.

#### Verified Early Blockers

- [ ] `ex001_sanity` is obsolete, reserved for removal, and must be deleted before later phases can proceed; it should not be migrated into the canonical exercise tree.
- [ ] Duplicate `ex006_sequence_modify_casting` exercise homes currently exist at [exercises/ex006_sequence_modify_casting](exercises/ex006_sequence_modify_casting) and [exercises/sequence/modify/ex006_sequence_modify_casting](exercises/sequence/modify/ex006_sequence_modify_casting); the canonical home is [exercises/sequence/modify/ex006_sequence_modify_casting](exercises/sequence/modify/ex006_sequence_modify_casting), and the root-level duplicate should be removed.
- [ ] `ex007` currently mixes `sequence` and `data_types` naming across notebooks, tests, and self-check references; this must be normalised fully to `ex007_sequence_debug_casting`, with all `data_types` references removed.
- [ ] The repository currently contains mixed exercise directory shapes such as `exercises/<exercise_key>/` and `exercises/<construct>/<type>/<exercise_key>/`; these must not be treated as equally canonical.
- [ ] A stray tree exists under [exercises/PythonExerciseGeneratorAndDistributor](exercises/PythonExerciseGeneratorAndDistributor); this must be classified and removed or relocated before structure docs are finalised.

### Phase 2: Metadata And Resolution Layer

#### Constraints And Acceptance Criteria

- [ ] Do not add path-based compatibility inputs to the resolver layer.
- [ ] Legacy code that still calls old path-based entry points should fail hard and clearly until it is refactored.
- [ ] Prefer deliberate breaking changes over compatibility aliases, soft transitions, or fallback argument handling.
- [ ] Keep the metadata schema intentionally minimal and avoid reintroducing convention-based fields as configuration.
- [ ] The phase is only complete once the shared resolver accepts `exercise_key`, rejects legacy path inputs, ignores `PYTUTOR_NOTEBOOKS_DIR` entirely, and has tests that prove missing migrated files and legacy access patterns fail hard.
- [ ] The phase must state explicitly whether canonical behaviour is proved with a live migrated pilot exercise, isolated fixtures, or both.

- [ ] Add an `exercise.json` loader in a central module rather than scattering path logic across scripts.
- [ ] Add a resolver that locates an exercise directory from `exercise_key`.
- [ ] Add a resolver that returns the student or solution notebook path for a given `exercise_key`.
- [ ] Decide where the shared metadata and resolver module lives so `scripts/`, `tests/`, and packaged template code can all import it cleanly.
- [ ] Use an explicit `variant` argument in Python APIs as the canonical student-versus-solution selector.
- [ ] Treat `exercise_key` as the only supported resolver input in the target model.
- [ ] Do not add compatibility APIs that accept notebook paths, test paths, or legacy folder locations as alternative resolver inputs.
- [ ] Add an explicit migration manifest or registry at `exercises/migration_manifest.json` that records whether each exercise still uses the legacy layout or has moved to the canonical layout.
- [ ] Make resolvers fail hard when an exercise is marked as migrated but the canonical files are missing.
- [ ] Make legacy callers fail clearly when they bypass the new resolver contract, rather than silently adapting legacy path inputs.
- [ ] Add unit tests covering both legacy and canonical exercises without allowing silent cross-layout fallback, using isolated fixtures and one live pilot exercise.
- [ ] Identify and list modules that will need to move onto the resolver early, especially: [tests/notebook_grader.py](tests/notebook_grader.py), [tests/exercise_framework](tests/exercise_framework), [tests/exercise_expectations](tests/exercise_expectations), [tests/student_checker](tests/student_checker), [scripts/build_autograde_payload.py](scripts/build_autograde_payload.py), and [scripts/template_repo_cli](scripts/template_repo_cli).
- [ ] Make the minimal target metadata schema explicit in code and docs: `schema_version`, `exercise_key`, `exercise_id`, `slug`, `title`, `construct`, `exercise_type`, and `parts`.

### Phase 3: Metadata Consolidation And Registry Replacement

#### Constraints And Acceptance Criteria

- [ ] Do not leave duplicated exercise registry data in code once `exercise.json` is capable of owning it.
- [ ] Do not treat this as path migration only; exercise-level titles and identity data should move toward metadata ownership where they are currently duplicated.
- [ ] Do not move convention-based fields such as tags, notebook paths, ordering, or mandatory self-check presence into metadata.
- [ ] The phase is only complete once the repository has a clear plan and initial implementation path for replacing hard-coded exercise registry data with metadata-driven loading.

- [ ] Define which currently duplicated exercise properties must move into `exercise.json`, keeping the schema limited to the agreed minimal field set.
- [ ] Identify all hard-coded exercise registries and lists that should eventually derive from metadata, especially in: [tests/student_checker/api.py](tests/student_checker/api.py), [tests/exercise_framework/api.py](tests/exercise_framework/api.py), and [tests/exercise_expectations](tests/exercise_expectations).
- [ ] Decide which metadata remains exercise-local versus which aggregate views should be derived at runtime or build time.
- [ ] Decide how construct teaching order and display names relate to `exercise.json` and derived indexes, while keeping order derived from `exercise_id`.
- [ ] Make it explicit that exported Classroom repositories may remain metadata-free even if the source repository uses metadata as the single source of truth.

### Phase 4: Execution Model And Source-To-Export Contract

#### Constraints And Acceptance Criteria

- [ ] Do not move exercise-local tests or break public interfaces until the repository execution model is explicitly defined.
- [ ] Do not treat source-repo authoring rules and exported Classroom rules as the same contract.
- [ ] Do not rely on accidental pytest discovery or packaging behaviour that happens to keep legacy top-level files working.
- [ ] Do not treat the current top-level `tests` support package as permanently fixed until Phase 4 confirms whether shared runtime code stays there or moves to a dedicated support package.
- [ ] The phase is only complete once the repository test discovery model, shared runtime import model, student-versus-solution selection model, and source-to-export mapping contract are all documented clearly enough to drive later implementation checklists.
- [ ] The phase is not complete until mixed-layout repository discovery has an explicit duplicate-collection strategy and acceptance criteria proving duplicate collection fails hard rather than being collected twice silently.
- [ ] The phase is not complete until the `ex007` naming mismatch is resolved or explicitly treated as a prerequisite blocker for authoritative variant-selection work.

- [ ] Define how repository pytest discovery will work once exercise-specific tests move under `exercises/**/tests/`.
- [ ] Move shared grading/runtime helpers into a dedicated support package before broad exercise-local test relocation begins.
- [ ] Define the long-term student-versus-solution variant-selection mechanism as an explicit `variant` argument in Python APIs plus a matching CLI flag for scripts and workflows.
- [ ] Define the exact source-to-export mapping from canonical authoring files such as `exercises/<construct>/<exercise_key>/notebooks/student.ipynb` and `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py` to the exported flattened Classroom paths under `notebooks/` and `tests/`.
- [ ] Make it explicit that exported Classroom repositories remain metadata-free even though the source repository is metadata-driven.
- [ ] Define whether any generated runtime index or support artefact is allowed in Classroom exports, and if so, require it to remain export-safe and metadata-free from an authoring perspective.
- [ ] Move directly to repository pytest discovery from real `exercises/**/tests/` locations and make duplicate collection fail hard rather than relying on proxy modules or long-lived mixed discovery.
- [ ] Identify every consumer that depends on the execution model, including repository tests, packaging, workflows, docs, scaffold verification, and agent guidance.
- [ ] Keep a pointer list for execution-model pain points in: [pyproject.toml](pyproject.toml), [tests/notebook_grader.py](tests/notebook_grader.py), [tests/exercise_framework](tests/exercise_framework), [tests/student_checker](tests/student_checker), [scripts/template_repo_cli](scripts/template_repo_cli), and [.github/workflows](.github/workflows).

### Phase 5: Scaffolding And Verification

#### Constraints And Acceptance Criteria

- [ ] Do not preserve the old scaffold layout as a fallback mode once the scaffold switches.
- [ ] The phase is only complete once newly scaffolded exercises are created directly in the canonical location, generated files use the canonical naming conventions, and the verifier checks the new structure rather than the legacy one.

- [ ] Update [scripts/new_exercise.py](scripts/new_exercise.py) to scaffold the new directory structure directly.
- [ ] Make construct and exercise type explicit scaffold inputs.
- [ ] Generate `exercise.json` as part of scaffolding.
- [ ] Generate `notebooks/student.ipynb` and `notebooks/solution.ipynb` instead of top-level notebook files.
- [ ] Generate `tests/test_<exercise_key>.py` inside the exercise directory.
- [ ] Make the generated notebook self-check cell mandatory by convention rather than configurable per exercise.
- [ ] Derive exercise tags and debug explanation tags from `parts` and `exercise_type` rather than storing them in metadata.
- [ ] Update [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py) to validate the new structure and metadata.
- [ ] Remove the manual move step from [docs/setup.md](docs/setup.md).
- [ ] Keep a list of scaffold-linked docs and tests to revisit once the generator changes, especially: [tests/test_new_exercise.py](tests/test_new_exercise.py), [docs/exercise-generation-cli.md](docs/exercise-generation-cli.md), [docs/exercise-generation.md](docs/exercise-generation.md), and [docs/setup.md](docs/setup.md).

### Phase 6: Grading And Autograding

#### Constraints And Acceptance Criteria

- [ ] Do not keep silent legacy-path support in grading helpers once a module is moved onto the new resolver contract.
- [ ] Modules migrated in this phase should accept `exercise_key` or metadata-derived resolution only; legacy path callers should fail until refactored.
- [ ] The phase is only complete once grading, self-checking, and autograding all run through the shared resolver model and tests demonstrate that old path-driven call patterns no longer pass accidentally.

- [ ] Update [tests/notebook_grader.py](tests/notebook_grader.py) to resolve notebooks via the new metadata and resolver layer.
- [ ] Update [tests/exercise_framework/paths.py](tests/exercise_framework/paths.py) to match the same behaviour.
- [ ] Keep student-versus-solution selection separate from layout migration, using a variant selector that does not mask missing migrated files.
- [ ] Update exercise expectation modules and framework APIs so they stop treating top-level notebook paths as canonical.
- [ ] Update student checker code paths that currently resolve by notebook filename or hard-coded slug.
- [ ] Update [scripts/build_autograde_payload.py](scripts/build_autograde_payload.py) so production validation no longer assumes only `notebooks` and `notebooks/solutions`.
- [ ] Update [scripts/verify_solutions.sh](scripts/verify_solutions.sh) to use the new resolution mechanism.
- [ ] Update autograding integration tests to reflect the new variant selection model.
- [ ] Keep a pointer list for likely breakage in: [tests/exercise_framework/test_runtime.py](tests/exercise_framework/test_runtime.py), [tests/exercise_framework/test_paths.py](tests/exercise_framework/test_paths.py), [tests/exercise_framework/test_autograde_parity.py](tests/exercise_framework/test_autograde_parity.py), [tests/student_checker/notebook_runtime.py](tests/student_checker/notebook_runtime.py), and [tests/student_checker/api.py](tests/student_checker/api.py).

### Phase 7: Pytest Discovery, Packaging, And Workflow Contract

#### Constraints And Acceptance Criteria

- [ ] Do not let packaging, CI, or pytest discovery rely on accidental continued presence of top-level exercise notebooks or tests.
- [ ] Do not leak repository authoring metadata into exported Classroom repositories unless that contract is explicitly revised later.
- [ ] The phase is only complete once exercise-local tests are discoverable under the chosen execution model, packaging works from canonical exercise directories, workflow behaviour matches the new variant-selection mechanism, and the exported repository remains metadata-free by design.

- [ ] Update the chosen repository pytest discovery configuration so exercise-local tests are collected intentionally rather than incidentally.
- [ ] Update [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py) to select exercises from the new canonical tree.
- [ ] Update [scripts/template_repo_cli/core/collector.py](scripts/template_repo_cli/core/collector.py) to collect files from each exercise directory.
- [ ] Update [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py) to package from the exercise directory structure while exporting the existing flattened Classroom contract.
- [ ] Make the transformation from metadata-rich source repository to metadata-free exported repository explicit in packaging design, tests, and docs.
- [ ] Review how packaged templates will continue to include shared runtime support from the chosen shared grading package location.
- [ ] Add explicit guards and tests to ensure exported templates do not accidentally include `solution.ipynb`, `exercise.json`, or the full authoring-side `exercises/` tree.
- [ ] Update repository workflows and exported template workflows to use the final variant-selection mechanism rather than `PYTUTOR_NOTEBOOKS_DIR`, using CLI flags rather than environment-based path swapping.
- [ ] Update template CLI tests and workflow-related tests to cover the new collection and export rules.
- [ ] Keep a pointer list for packaging and workflow pain points in: [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py), [scripts/template_repo_cli/core/collector.py](scripts/template_repo_cli/core/collector.py), [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py), [tests/template_repo_cli](tests/template_repo_cli), [docs/CLI_README.md](docs/CLI_README.md), and [.github/workflows](.github/workflows).

### Phase 8: Public Interface Cutover

#### Constraints And Acceptance Criteria

- [ ] Prefer deliberate breaking changes over compatibility wrappers for CLI, verifier, and helper interfaces that currently accept notebook paths or notebook-oriented terminology.
- [ ] Do not leave notebook-shaped public interfaces as hidden aliases if the underlying model has changed to `exercise_key`.
- [ ] Do not cut over public interfaces until the execution model and packaging contract are proven for at least one migrated exercise.
- [ ] The phase is only complete once public-facing repository interfaces clearly use the new model, breaking changes are documented, and tests assert the new contract rather than the legacy one.

- [ ] Decide how public tooling should identify exercises after the cutover, especially for the template CLI, verifier, and notebook self-check surfaces.
- [ ] Update public CLI and script interfaces to use the new canonical exercise identity model.
- [ ] Remove or deliberately break legacy notebook-path-driven invocation patterns once replacement interfaces exist.
- [ ] Update user-facing docs to describe the breaking changes and the new invocation model.
- [ ] Keep a pointer list for interface pain points in: [docs/CLI_README.md](docs/CLI_README.md), [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py), [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py), and [scripts/new_exercise.py](scripts/new_exercise.py).

### Phase 9: Exercise Data Migration

#### Constraints And Acceptance Criteria

- [ ] Do not migrate exercises ad hoc without recording what moved and what still remains in the legacy layout.
- [ ] The phase is only complete for a construct once its notebooks, exercise-local tests, local docs links, and migration state all line up with the canonical layout and no duplicate canonical-versus-legacy source of truth remains for that construct.

- [ ] Write a one-off migration script that moves notebooks and exercise-specific tests into each exercise directory.
- [ ] Choose the pilot construct based on the Phase 1 inventory rather than assuming `sequence` is the correct first target.
- [ ] Update links in construct-level teaching order files.
- [ ] Update each exercise `README.md` and `OVERVIEW.md` so internal links point to the new local notebook and test paths.
- [ ] Move exercise-specific tests out of the top-level `tests/` directory once the new discovery path is proven.
- [ ] Leave shared framework modules in the top-level `tests/` package.
- [ ] Keep an eye on exercises that already have duplicate or partially migrated homes so the migration script does not overwrite the wrong copy.

### Phase 10: Docs, Agents, Workflows, And Contributor Guidance

#### Constraints And Acceptance Criteria

- [ ] Do not leave any maintained docs or agent guidance describing the legacy split layout as the canonical authoring model once the corresponding code path has migrated.
- [ ] Do not rename current `.github/agents` files to `.old` until replacement agent instructions exist and all references have been updated.
- [ ] During migration, keep the current agent files authoritative and mark them clearly as transitional where needed.
- [ ] The phase is only complete once core contributor docs, classroom/export docs, workflows, and agent instructions all point at the same canonical structure and resolver contract.
- [ ] The phase is not complete while repository workflows still present an unclear or duplicated solution-mode contract.

- [ ] Update [README.md](README.md) to describe the new canonical structure.
- [ ] Update [docs/project-structure.md](docs/project-structure.md) and [docs/setup.md](docs/setup.md).
- [ ] Update exercise generation and verification guidance in [docs/exercise-generation.md](docs/exercise-generation.md) and [docs/exercise-generation-cli.md](docs/exercise-generation-cli.md).
- [ ] Update [AGENTS.md](AGENTS.md) and the files under [.github/agents](.github/agents) so custom agents follow the new layout.
- [ ] Update contributor-facing commands and examples to use the final explicit `variant` CLI flag rather than `PYTUTOR_NOTEBOOKS_DIR`.
- [ ] Add short migration warning blocks to the current agent files so contributors know the repository is mid-migration and should consult [ACTION_PLAN.md](ACTION_PLAN.md) for the target structure.
- [ ] Decide the cutover sequence for agent docs: update in place versus replace-then-archive.
- [ ] Update all four current agent files explicitly: [.github/agents/exercise_generation.md.agent.md](.github/agents/exercise_generation.md.agent.md), [.github/agents/exercise_verifier.md.agent.md](.github/agents/exercise_verifier.md.agent.md), [.github/agents/implementer.md.agent.md](.github/agents/implementer.md.agent.md), and [.github/agents/tidy_code_review.md.agent.md](.github/agents/tidy_code_review.md.agent.md).
- [ ] Only archive superseded agent files with a suffix such as `.old` after the replacement files are complete, references have been switched, and the new guidance is confirmed to be authoritative.
- [ ] Update repository workflows and any template workflow sources documented in the repo so CI instructions no longer teach or depend on the legacy layout contract.
- [ ] Rationalise the current repository workflow split so repo workflows validate the authoring repository contract, while the exported Classroom workflow validates the metadata-free student export contract.
- [ ] Update docs that describe the testing and autograding contract, especially: [docs/testing-framework.md](docs/testing-framework.md), [docs/exercise-testing.md](docs/exercise-testing.md), [docs/autograding-cli.md](docs/autograding-cli.md), [docs/development.md](docs/development.md), and [docs/github-classroom-autograding-guide.md](docs/github-classroom-autograding-guide.md).
- [ ] Update examples in teacher docs that currently refer to top-level `notebooks/` and `tests/` paths.

### Phase 11: Validation, Cutover, And Cleanup

#### Constraints And Acceptance Criteria

- [ ] Do not remove legacy support until migrated constructs, CI, packaging, and docs have all been proven against the new contract.
- [ ] Do not use “repository CI is green” as the only proof of migration success.
- [ ] The phase is only complete once repository CI, explicit student-mode checks, solution-mode checks, packaged-template smoke tests, full test collection, and docs/agent guidance all pass against the new contract, and the old top-level exercise-specific notebooks and tests are no longer required as sources of truth.
- [ ] Final cleanup must not proceed until duplicate exercise homes and naming mismatches have been resolved deterministically.

- [ ] Run solution-mode tests for the migrated construct and confirm that the new resolver path is stable.
- [ ] Run explicit student-mode validation for the migrated construct and confirm expected failure/pass behaviour still matches the intended workflow.
- [ ] Run the full student-mode validation suite before each cutover stage rather than relying on a smoke subset.
- [ ] Run template packaging smoke tests for at least one migrated exercise.
- [ ] Run repository CI and packaged-template smoke tests against the new contract before removing legacy support.
- [ ] Run an explicit full test-collection pass before final cleanup so collection-time identity mismatches are caught, not just runtime failures.
- [ ] Update repository workflows and exported template workflows to use the final variant-selection mechanism.
- [ ] Define and document the minimum validation matrix required before each cutover stage, including repository student mode, repository solution mode, and packaged-template runtime checks.
- [ ] Remove legacy path support only after every exercise and every doc set has been migrated.
- [ ] Delete or repurpose the top-level `notebooks/` directory once it is no longer needed.
- [ ] Delete or repurpose the top-level exercise-specific test files once all exercises use local `tests/` directories.

## Recommended Implementation Order

1. Complete the identity inventory and choose a safe pilot scope.
2. Build the metadata and resolver layer first.
3. Consolidate duplicated exercise registry data into `exercise.json`.
4. Define the execution model, shared runtime home, variant selector, and source-to-export mapping before moving exercise-local tests.
5. Update scaffolding and verification to write the new structure.
6. Cut over internal grading and autograding code.
7. Update packaging, pytest discovery, and workflow behaviour.
8. Migrate one construct and prove repository mode and packaged export both work end to end.
9. Apply deliberate public interface breaking changes.
10. Update docs, workflows, and agent instructions.
11. Remove legacy path support only after the repository is fully migrated.

## Migration Checklist Authoring Order

Use this section to track which detailed migration checklist documents have been created.

### Wave 1: Can Be Authored First

- [ ] Phase 1 checklist: Repository Inventory And Canonical Model
- [ ] Phase 2 checklist: Metadata And Resolution Layer
- [ ] Phase 3 checklist: Metadata Consolidation And Registry Replacement
- [ ] Phase 4 checklist: Execution Model And Source-To-Export Contract
- [ ] Phase 10 checklist: Docs, Agents, Workflows, And Contributor Guidance
- [ ] Phase 11 checklist: Validation, Cutover, And Cleanup

These can be written first because they define the migration model, inventory, cross-cutting documentation work, and end-state validation expectations.

### Wave 2: Author After Wave 1 Is Stable

- [ ] Phase 5 checklist: Scaffolding And Verification
- [ ] Phase 6 checklist: Grading And Autograding
- [ ] Phase 7 checklist: Pytest Discovery, Packaging, And Workflow Contract

These depend on the earlier checklist set being stable enough to define the resolver contract, execution model, source-to-export mapping, and shared runtime expectations.

### Wave 3: Author Last

- [ ] Phase 8 checklist: Public Interface Cutover
- [ ] Phase 9 checklist: Exercise Data Migration

These should be written last because they depend most heavily on upstream execution-model, packaging, grading, and scaffolding decisions remaining stable.

### Dependency Notes

- Phase 2 depends on Phase 1 inventory being clear enough to avoid ambiguous exercise identities.
- Phase 4 depends on Phase 1 and should stay aligned with Phase 2 because resolver shape and execution model affect each other.
- Phase 5 depends on Phases 2 and 4.
- Phase 6 depends on Phases 2 and 4, and should stay aligned with Phase 5.
- Phase 7 depends heavily on Phase 4 and should stay aligned with Phase 6.
- Phase 8 depends on Phases 4, 6, and 7.
- Phase 9 depends on Phases 2, 4, 5, 6, and 7.

## Immediate Next Decisions

1. Confirm whether exercise type should remain in the exercise key for now or be removed from future slugs. **A:** Keep it in the key to make migration easier and to make searching for exercises by type using a full text search when they become more numerous easier.
2. Confirm whether exported Classroom repositories should keep the nested layout or flatten notebooks and tests during packaging. **A:** The current behaviour is to flatten exported Classroom repositories so that student notebooks are written to `notebooks/exNNN_slug.ipynb` and exercise-specific tests are written to `tests/test_exNNN_slug.py`. That current contract is documented in [docs/CLI_README.md](docs/CLI_README.md) under "What Gets Included in Templates".
3. Confirm whether the current `PYTUTOR_NOTEBOOKS_DIR` environment variable should be retained as a compatibility layer during the transition. **A:** No. It should not be used as a layout compatibility layer during an exercise-by-exercise migration because silent fallback could make a partial migration look successful when it is not. Migration state should be explicit per exercise, and resolution should fail hard if an exercise marked as migrated is missing its canonical files. Student-versus-solution selection should remain a separate concern, handled by a dedicated variant selector that does not hide layout mistakes.
4. Confirm the canonical input to the new resolver model. **A:** Standardise on `exercise_key` only. Do not support legacy path-based resolver inputs in the target model. Legacy callers should fail hard until they are refactored to use the new resolver contract.
5. Confirm whether the migration should prefer compatibility layers or deliberate breakage when interfaces change. **A:** Prefer deliberate breaking changes over compatibility wrappers, aliases, or fallbacks. Legacy interfaces should fail hard once replacement interfaces exist.
6. Confirm whether exported Classroom repositories should include repository-side metadata such as `exercise.json`. **A:** No. Exported Classroom repositories should remain metadata-free student repositories and should not ship the authoring-side metadata model.
7. Confirm how far `exercise.json` should go as a source of truth. **A:** Go the whole way for exercise-specific metadata, but keep the schema intentionally small. The canonical field set is `schema_version`, `exercise_key`, `exercise_id`, `slug`, `title`, `construct`, `exercise_type`, and `parts`. Convention-based fields such as notebook/test paths, tag names, self-check presence, and ordering should be derived rather than stored.
