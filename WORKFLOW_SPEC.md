# WORKFLOW_SPEC — Native Classroom 50 Bundle Deployment

## Purpose

This document records the filesystem and runtime workflow for deploying the generic teacher-side bundle as a native Classroom 50 per-assignment autograder. It is deliberately separate from `SPEC.md`: the specification defines the contract; this document defines the operational path and derived surfaces.

## Source-to-bundle layout

The source repository remains canonical:

```text
exercises/<construct>/<exercise_key>/
├── exercise.json
├── notebooks/
│   ├── student.ipynb
│   └── solution.ipynb
└── tests/
    ├── test_<exercise_key>.py
    ├── expectations.py
    └── student_checker_support.py
```

The builder receives a JSON exercise set containing `construct` and `exercise_key` records, the current `exercise_runtime_support/` source, and deployment coordinates.

The build target is a local Classroom 50 repository root:

```text
<classroom50-repository>/
└── <classroom>/
    └── autograders/
        └── <assignment>/
```

The generated assignment directory contains exactly the bundle contents:

```text
autograder.py
classroom50_manifest.py
grading_manifest.json
requirements.txt
pytest.ini
exercise_runtime_support/
exercises/<construct>/<exercise_key>/tests/
```

There is no extra `bundle/` wrapper directory. The builder stages this directory, validates it, and replaces the target only after validation succeeds.

Source-to-target names are fixed: `scripts/autograder.py` → `autograder.py`, `scripts/classroom50_requirements.txt` → `requirements.txt`, `scripts/classroom50_pytest.ini` → `pytest.ini`, and `scripts/classroom50_manifest.py` → `classroom50_manifest.py`. Native bundle-root resolution is `Path(CLASSROOM50_BUNDLE_DIR).resolve()`. Local mode resolves the script parent and is supported only from a built-bundle copy; in-place `scripts/autograder.py` execution is not supported.

## Build workflow

1. Validate `classroom` and `assignment` against the Classroom 50 slug rules and composed repository-name budget.
2. Validate the exercise set and reject duplicate records.
3. Load each selected `exercise.json` and verify its `construct` and `exercise_key` identity.
4. Require exactly `tests/test_<exercise_key>.py` for every selected exercise.
5. Copy that canonical test plus each present documented support module and support modules reachable through `load_exercise_test_module`; absence of an optional support module is allowed, but a referenced missing module fails.
6. Exclude all other `test_*.py` files, including `test_repo_*` files.
7. Regenerate the bundle-local `exercise_runtime_support/` copy.
8. Write the closed `grading_manifest.json` wire format with schema `classroom50/grading-manifest/v1`, sorted unique records, canonical POSIX-relative paths, and exact `test_<exercise_key>.py` filenames.
9. Copy the shared manifest validator, lock-derived native requirements, and trusted pytest configuration into the bundle.
10. Verify that no notebook, solution, metadata, authoring note, cache, or repository-only test is present.
11. Build a staging gzip archive using exactly `<assignment>/` as the archive's top-level directory, matching the Pages publisher layout.
12. Reject an archive larger than the native 10 MiB fetch ceiling.
13. Replace the target directory only after all checks pass.

The builder copies the committed, lock-parity-checked requirements file. Its exact package set is `pytest==9.0.2`, `tabulate==0.9.0`, `iniconfig==2.3.0`, `packaging==26.0`, `pluggy==1.6.0`, `pygments==2.19.2`, and `colorama==0.4.6` with the Windows platform marker. The active marker is evaluated for the native platform; Linux does not require or install `colorama`.

At runtime, the autograder removes all inherited `PIP_*` keys and invokes exactly `sys.executable -m pip --isolated install --disable-pip-version-check --no-input --no-cache-dir --upgrade --target <fresh-bundle-target> -r <bundle>/requirements.txt` with a 120-second timeout. It removes the prior target, installs into a fresh target, verifies versions and module origins, and only then prepends that target to `sys.path`; module-scope pytest imports are forbidden.

The builder performs no GitHub API operation and does not create a Classroom 50 assignment. It does not query organisation existence, protected/unlisted status, or secret-link configuration; those remain upstream deployment concerns.

## Native assignment configuration

The assignment must use:

- `autograder: "default"`;
- Autograded grading mode;
- no declarative `tests` block;
- no `no_autograder`;
- no `empty_repo`;
- a private student repository;
- a valid `template` object with non-empty `owner`, `repo`, and `branch`; the template must provide the canonical student exercise metadata, notebooks, and visible tests that the bundle excludes;
- `init_shim: true` is schema-valid only as a negative/unsupported fixture for this deployment and must be rejected before rollout because it creates no starter exercise surface;
- `template` and `init_shim` are mutually exclusive, and `init_shim` excludes `empty_repo`/`no_autograder`;
- the starter template containing canonical `exercise_metadata/`, student notebooks, and visible tests;
- a Python 3.14 runtime;
- an assignment type of `individual`, `group`, or `team` as supported by Classroom 50.

The `autograder` field does not select the Python file. A value other than `default` selects a separate named workflow YAML and is not used for this bundle.

The native CLI has no command that uploads a per-assignment Python bundle. The teacher commits the generated directory through Git, GitHub's web interface, or an equivalent repository write.

### Assignment manifest validation

The bundle builder does not write `assignments.json`, but native fixtures and deployment documentation must satisfy the pinned `assignments-v1.schema.json`:

- `autograder` is `default`;
- `grading.mode` is `auto` or omitted (omitted means auto);
- `tests` is absent;
- `empty_repo` is false or omitted;
- `no_autograder` is false or omitted;
- a native deployment uses a valid `template` object and no `init_shim`; an `init_shim` entry is retained only as an explicitly unsupported schema fixture;
- `template` and `init_shim` are mutually exclusive, and `init_shim` excludes `empty_repo`/`no_autograder`;
- `individual` omits group-only fields;
- `group` requires `max_group_size` and omits `team_formation`;
- `team` requires both `max_group_size` and `team_formation`.

The builder does not query or rewrite the assignment manifest.

## Local validation workflow

The explicit local mode remains available for fast checks:

```text
uv run python <bundle>/autograder.py \
  --student-root <student-checkout> \
  --result <result-path> \
  [--variant solution]
```

Local mode uses exact deterministic local identity values and is not uploadable. The solution variant is for dry-run validation only; the default graded path forces the student variant.

## Native environment

The upstream runner supplies the following relevant environment to the child:

- `CLASSROOM50_BUNDLE_DIR`;
- `CLASSROOM`;
- `ASSIGNMENT`;
- `ASSIGNMENT_TYPE`;
- `OWNER` and `USERNAME`;
- `SUBMISSION_TAG`;
- `COMMIT_URL`;
- `RELEASE_URL`;
- `REVIEW_URL`;
- `PAGES_BASE_URL`;
- `SECRET`, `MODE`, `ALLOWED_FILES`, and `RELEASE_ASSETS`;
- standard `GITHUB_*` variables.

The autograder requires the bundle path, classroom, assignment, assignment type, owner identity, submission tag, commit URL, and release URL. `REVIEW_URL` is optional and falls back to `COMMIT_URL`. The upstream runner derives `OWNER` and `USERNAME` from the same repository identity and derives `ASSIGNMENT_TYPE` from its mode; they are not independent student inputs. The result-supported assignment types are `individual`, `group`, and `team`.

## Native runtime workflow

1. The teacher commits the generated assignment directory to the Classroom 50 config repository.
2. The repository's publish workflow materialises the assignment bundle and publishes the per-assignment archive.
3. A student accepts the assignment and receives the normal Classroom 50 control files.
4. A later submission triggers the built-in runner.
5. The runner downloads and extracts the per-assignment bundle.
6. The runner invokes `autograder.py` with no arguments, from the student checkout, with the native environment.
7. The autograder creates a fresh verified dependency target, removes inherited `PIP_*`, `PYTEST_*`, and `PYTHON_*` keys plus `GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_PATH`, and `GITHUB_STEP_SUMMARY`, sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, reads `grading_manifest.json`, and calls `pytest.main` with exactly the manifest paths followed by `-c <bundle>/pytest.ini`, `--rootdir <bundle-root>`, `--confcutdir <bundle-root>`, and `-p no:cacheprovider`; it writes `<student-checkout>/result.json`.
8. Classroom 50 validates and authoritatively stamps the result, derives the outer status from the validated result, publishes the submission Release, and later collects scores.

The bundle is fetched on each grading run, so a committed bundle update does not require a student-repository change. Pages/CDN propagation may delay visibility.

## Child and outer runner failure semantics

The autograder child exits 0 for a completed pass or fail and writes a valid result. It exits non-zero and writes no completed result for identity, dependency, configuration, collection, or other infrastructure failures.

The upstream runner handles a child non-zero exit through its own error-finalisation path. It may synthesise a schema-shaped error result, post an error status, avoid publishing a normal scoring Release, and still return an outer exit code of 0 according to the upstream implementation. Validation must cover both layers rather than treating the child and runner exit codes as interchangeable.

## Result contract

The result must use:

- `schema: "classroom50/result/v1"`;
- native classroom, assignment, assignment type, owner, submission, commit, release, and review values;
- `test-name`, `passed`, `score`, and `max-score` for every manifest-listed test row;
- the existing `<exercise_key>::<leaf-nodeid>` naming rule.

The native runner supplies or overwrites `owner`, `assignment_type`, `datetime`, `graded_at`, and `submitted_by` as appropriate. The autograder supplies the other required fields.

## Security and visibility

The bundle is tamper-resistant, not secret. Classroom 50 publishes the bundle through Pages, so it must contain no solutions, private datasets, credentials, or other confidential material. Student changes to visible tests, dependency manifests, or pytest configuration must not affect the result.

## Non-goals

This workflow does not add:

- a Classroom 50 GUI bundle importer;
- a `gh teacher` per-assignment upload command;
- classroom or roster automation;
- a live acceptance/submission/collection pilot;
- a new exercise, notebook, or construct sequencing workflow.
