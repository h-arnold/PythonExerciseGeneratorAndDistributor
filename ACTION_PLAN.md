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
5. Shared test framework code stays in the top-level `tests/` package.
6. Exercise-local tests live inside the exercise folder and may continue to import shared helpers from the top-level `tests/` package.
7. During migration, packaging may still flatten notebooks and tests for template repositories if that keeps downstream Classroom workflows stable.
8. During migration, layout state must be explicit per exercise; resolvers must not silently fall back between legacy and migrated paths.

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
│   │   ├── ex001_sanity/
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
4. Treat this file as the source of truth for exercise type, title, and structural expectations.

### Example

```json
{
  "schema_version": 1,
  "exercise_key": "ex006_sequence_modify_casting",
  "exercise_id": "ex006",
  "slug": "sequence_modify_casting",
  "title": "Casting and Type Conversion",
  "construct": "sequence",
  "exercise_type": "modify",
  "difficulty": "introductory",
  "parts": 1,
  "student_checker_enabled": true,
  "tags": {
    "exercise_cells": ["exercise1"],
    "explanation_cells": []
  },
  "prerequisites": [
    "ex003_sequence_modify_variables"
  ],
  "status": {
    "draft": true,
    "published": false
  }
}
```

### Fields To Standardise Early

| Field | Purpose |
| --- | --- |
| `schema_version` | Allows future migrations without guesswork |
| `exercise_key` | Stable identifier used by scripts and tests |
| `exercise_id` | Short display and ordering identifier such as `ex006` |
| `slug` | Human-readable identifier |
| `title` | Exercise title used in docs and generated notebooks |
| `construct` | Curriculum grouping such as `sequence` |
| `exercise_type` | `debug`, `modify`, or `make` without requiring another folder level |
| `parts` | Number of tagged exercise cells |
| `student_checker_enabled` | Whether to generate or run the notebook self-check cell |
| `tags` | Declares expected tagged cells for validation tooling |
| `prerequisites` | Optional dependency or sequencing information |
| `status` | Draft or publication state |

### Fields Intentionally Omitted

These should be conventions rather than repeated metadata:

1. Student notebook path: always `notebooks/student.ipynb`
2. Solution notebook path: always `notebooks/solution.ipynb`
3. Primary test path: always `tests/test_<exercise_key>.py`
4. Teacher overview path: always `OVERVIEW.md` when present

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
| Docs and agent instructions describe the split layout as canonical | [README.md](README.md), [docs/project-structure.md](docs/project-structure.md), [AGENTS.md](AGENTS.md), [.github/agents/exercise_generation.md.agent.md](.github/agents/exercise_generation.md.agent.md) | Rewrite docs and agent instructions after the resolver and scaffolder are in place |

## Migration Checklist

### Phase 1: Canonical Model

- [ ] Agree that `exercises/<construct>/<exercise_key>/` is the canonical location for all exercise-specific assets.
- [ ] Confirm that exercise type is moving from the folder hierarchy into `exercise.json`.
- [ ] Confirm standard notebook names: `student.ipynb` and `solution.ipynb`.
- [ ] Confirm that top-level `tests/` remains for shared grading infrastructure only.
- [ ] Confirm whether template exports should flatten notebooks and tests during the transition.

### Phase 2: Metadata And Resolution Layer

- [ ] Add an `exercise.json` loader in a central module rather than scattering path logic across scripts.
- [ ] Add a resolver that can locate an exercise directory from `exercise_key`.
- [ ] Add a resolver that can return the student or solution notebook path for a given exercise.
- [ ] Add an explicit migration manifest or registry that records whether each exercise still uses the legacy layout or has moved to the canonical layout.
- [ ] Make resolvers fail hard when an exercise is marked as migrated but the canonical files are missing.
- [ ] Add unit tests covering both legacy and canonical exercises without allowing silent cross-layout fallback.

### Phase 3: Scaffolding And Verification

- [ ] Update [scripts/new_exercise.py](scripts/new_exercise.py) to scaffold the new directory structure directly.
- [ ] Make construct and exercise type explicit scaffold inputs.
- [ ] Generate `exercise.json` as part of scaffolding.
- [ ] Generate `notebooks/student.ipynb` and `notebooks/solution.ipynb` instead of top-level notebook files.
- [ ] Generate `tests/test_<exercise_key>.py` inside the exercise directory.
- [ ] Update [scripts/verify_exercise_quality.py](scripts/verify_exercise_quality.py) to validate the new structure and metadata.
- [ ] Remove the manual move step from [docs/setup.md](docs/setup.md).

### Phase 4: Grading And Autograding

- [ ] Update [tests/notebook_grader.py](tests/notebook_grader.py) to resolve notebooks via the new metadata and resolver layer.
- [ ] Update [tests/exercise_framework/paths.py](tests/exercise_framework/paths.py) to match the same behaviour.
- [ ] Keep student-versus-solution selection separate from layout migration, using a variant selector that does not mask missing migrated files.
- [ ] Update [scripts/build_autograde_payload.py](scripts/build_autograde_payload.py) so production validation no longer assumes only `notebooks` and `notebooks/solutions`.
- [ ] Update [scripts/verify_solutions.sh](scripts/verify_solutions.sh) to use the new resolution mechanism.
- [ ] Update autograding integration tests to reflect the new variant selection model.

### Phase 5: Pytest Discovery And Packaging

- [ ] Update [pytest.ini](pytest.ini) so exercise-local tests are discoverable.
- [ ] Update [scripts/template_repo_cli/core/selector.py](scripts/template_repo_cli/core/selector.py) to select exercises from the new canonical tree.
- [ ] Update [scripts/template_repo_cli/core/collector.py](scripts/template_repo_cli/core/collector.py) to collect files from each exercise directory.
- [ ] Update [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py) to package from the exercise directory structure.
- [ ] Decide whether exported template repos preserve the nested exercise structure or flatten notebooks and tests into the current student-facing layout.
- [ ] Update template CLI tests to cover the new collection and export rules.

### Phase 6: Exercise Data Migration

- [ ] Write a one-off migration script that moves notebooks and exercise-specific tests into each exercise directory.
- [ ] Migrate one construct first, preferably `sequence`, before touching the whole repository.
- [ ] Update links in construct-level teaching order files.
- [ ] Update each exercise `README.md` and `OVERVIEW.md` so internal links point to the new local notebook and test paths.
- [ ] Move exercise-specific tests out of the top-level `tests/` directory once the new discovery path is proven.
- [ ] Leave shared framework modules in the top-level `tests/` package.

### Phase 7: Docs And Agent Instructions

- [ ] Update [README.md](README.md) to describe the new canonical structure.
- [ ] Update [docs/project-structure.md](docs/project-structure.md) and [docs/setup.md](docs/setup.md).
- [ ] Update exercise generation and verification guidance in [docs/exercise-generation.md](docs/exercise-generation.md) and [docs/exercise-generation-cli.md](docs/exercise-generation-cli.md).
- [ ] Update [AGENTS.md](AGENTS.md) and the files under [.github/agents](.github/agents) so custom agents follow the new layout.
- [ ] Update examples in teacher docs that currently refer to top-level `notebooks/` and `tests/` paths.

### Phase 8: Cutover And Cleanup

- [ ] Run solution-mode tests for the migrated construct and confirm that the new resolver path is stable.
- [ ] Run template packaging smoke tests for at least one migrated exercise.
- [ ] Remove legacy path support only after every exercise and every doc set has been migrated.
- [ ] Delete or repurpose the top-level `notebooks/` directory once it is no longer needed.
- [ ] Delete or repurpose the top-level exercise-specific test files once all exercises use local `tests/` directories.

## Recommended Implementation Order

1. Build the metadata and resolver layer first.
2. Update scaffolding and verification to write the new structure.
3. Migrate one construct and prove grading still works.
4. Update packaging and export behaviour.
5. Update docs and agent instructions.
6. Remove legacy path support only after the repository is fully migrated.

## Immediate Next Decisions

1. Confirm whether exercise type should remain in the exercise key for now or be removed from future slugs. **A:** Keep it in the key to make migration easier and to make searching for exercises by type using a full text search when they become more numerous easier.
2. Confirm whether exported Classroom repositories should keep the nested layout or flatten notebooks and tests during packaging. **A:** The current behaviour is to flatten exported Classroom repositories so that student notebooks are written to `notebooks/exNNN_slug.ipynb` and exercise-specific tests are written to `tests/test_exNNN_slug.py`. That current contract is documented in [docs/CLI_README.md](docs/CLI_README.md) under "What Gets Included in Templates".
3. Confirm whether the current `PYTUTOR_NOTEBOOKS_DIR` environment variable should be retained as a compatibility layer during the transition. **A:** No. It should not be used as a layout compatibility layer during an exercise-by-exercise migration because silent fallback could make a partial migration look successful when it is not. Migration state should be explicit per exercise, and resolution should fail hard if an exercise marked as migrated is missing its canonical files. Student-versus-solution selection should remain a separate concern, handled by a dedicated variant selector that does not hide layout mistakes.
