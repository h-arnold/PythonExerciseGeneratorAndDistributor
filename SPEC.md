# SPEC — Native Classroom 50 Bundle Autograder Integration

## Status

- Draft v2.1, 25 September 2026.
- This specification supersedes the completed Selection Pilot implementation contract in the previous revision of this file.
- The plan is for the generic teacher-side bundle and its native Classroom 50 integration. It does not change exercises, notebooks, or teaching order.

## Purpose

Make the generic `scripts/autograder.py` and `scripts/build_classroom50_bundle.py` workflow usable as a native Classroom 50 per-assignment custom autograder while preserving the existing local dry-run workflow.

The workflow must:

- build a selected exercise set as a native-compatible hidden bundle;
- grade the student variant in a local checkout;
- grade the solution variant in a local dry run;
- run through Classroom 50's built-in runner without command-line arguments;
- produce a canonical `classroom50/result/v1` document;
- preserve hidden-test isolation and the canonical exercise layout.

The workflow is not intended to:

- modify the upstream `foundation50/classroom50` repository;
- automate Classroom 50 classroom, roster, or assignment administration;
- add a GUI or `gh teacher` bundle-upload command;
- perform a live Classroom 50 pilot;
- change exercise content, notebook tagging, pedagogical sequencing, or `OrderOfTeaching.md`.

## Current state

The existing builder produces the essential native tree, but its deployment and selection contracts are incomplete:

```text
autograder.py
exercise_runtime_support/
exercises/<construct>/<exercise_key>/tests/
```

The current autograder behaves as a local-only CLI:

- `--student-root` and `--result` are mandatory;
- the student root is supplied by the caller;
- the result path is caller-selected;
- the payload uses `version` and test-row `name`;
- identity and submission URL fields are absent;
- pytest is imported without a native dependency bootstrap;
- pytest uses no bundle-owned trust boundary;
- teardown failures are not currently terminal failures.

The current builder also needs a native deployment contract and stronger safety checks. It currently stages an arbitrary output directory, follows copied filesystem links, accepts duplicate/path-unsafe exercise records, includes every `test_*.py` file, and does not measure the compressed Pages bundle.

The current Classroom 50 reference is `foundation50/classroom50` commit `43ec1444f87674cd3276e66eadb6439dc0c97668`. Its built-in runner invokes a per-assignment `autograder.py` with no arguments, from the student checkout, and reads `<student-checkout>/result.json`.

## Agreed decisions

1. The bundle is a native per-assignment Python override, not a named custom workflow shim. The assignment manifest keeps `autograder: "default"`.
2. The builder is assignment-aware for deployment coordinates: it requires `--classroom` and `--assignment`, and `--output` is a local Classroom 50 repository root. It writes the bundle contents to `<output>/<classroom>/autograders/<assignment>/`.
3. The builder remains assignment-agnostic in grading logic. Classroom and assignment are deployment coordinates only; no construct- or exercise-specific branch is permitted.
4. The autograder has two modes:
   - no arguments: native Classroom 50 mode;
   - explicit `--student-root` and `--result`: local dry-run mode.
5. The two local arguments are required as a pair. Supplying only one is an error.
6. Native mode requires `CLASSROOM50_BUNDLE_DIR`, `CLASSROOM`, `ASSIGNMENT`, `SUBMISSION_TAG`, `COMMIT_URL`, `RELEASE_URL`, and `ASSIGNMENT_TYPE`, plus at least one of `OWNER` and `USERNAME`. `REVIEW_URL` is optional and falls back to `COMMIT_URL`.
7. Native `ASSIGNMENT_TYPE` accepts `individual`, `group`, and `team`, matching the current Classroom 50 result schema. Local mode uses `individual` as its diagnostic value.
8. Local mode writes a schema-valid but explicitly non-uploadable result using exact deterministic local identity values.
9. The native payload uses the canonical `classroom50/result/v1` field names. No `version` or old `name` aliases are retained.
10. Native dependencies are bootstrapped with `sys.executable -m pip`, not `uv`, using a lock-derived requirements set with exact pins for the full pytest/tabulate dependency closure.
11. The native target is always a fresh bundle-local install target; the autograder does not reuse packages from the student or global environment. Package origins are verified under that target before import.
12. Pytest runs with a bundle-owned configuration, explicit arguments, a sanitised environment, and controlled plugin loading; student-controlled configuration cannot define the hidden-test grading boundary.
13. The builder writes `grading_manifest.json`. The manifest is the sole list of hidden test files consumed by the autograder, and builder/autograder use one shared validator.
14. Only `test_<exercise_key>.py` and its transitive exercise-local support closure are bundled. Repository-only tests such as `test_repo_*` are excluded.
15. Child-script and outer-runner failure semantics are modelled separately. A child non-zero exit is an infrastructure error from the autograder's perspective; the upstream runner then synthesises its own error result and does not publish a normal score.
16. The native assignment manifest must be accepted by the current Classroom 50 assignment schema: `autograder: "default"`, grading mode `auto` or omitted, no declarative `tests`, `empty_repo` false/omitted, and `no_autograder` false/omitted. Group/team entries carry their schema-required group fields.
17. No live Classroom 50 operation is required for local acceptance. Manual commit/upload into the Classroom 50 config repository remains the deployment step.

## Invocation and environment contract

### Native mode

When no arguments are supplied:

- the current working directory is the student checkout;
- `CLASSROOM50_BUNDLE_DIR` is the bundle root;
- the result is `<student-checkout>/result.json`;
- the active notebook variant is forced to `student`;
- the script exits 0 for a completed pytest pass or failure.

The upstream runner supplies the following native environment. The autograder uses the result-related variables and preserves the standard GitHub variables for any downstream code.

| Variable | Source/use |
| --- | --- |
| `CLASSROOM50_BUNDLE_DIR` | Required extracted per-assignment bundle path |
| `CLASSROOM` | Required classroom slug for result identity |
| `ASSIGNMENT` | Required assignment slug for result identity |
| `ASSIGNMENT_TYPE` | Required mode: `individual`, `group`, or `team`; validated before use and overwritten by the runner |
| `OWNER` | Preferred owner/team repository identity; required if `USERNAME` is absent |
| `USERNAME` | Fallback owner/repository identity; required if `OWNER` is absent |
| `SUBMISSION_TAG` | Required canonical `submit/...` tag |
| `COMMIT_URL` | Required graded commit URL |
| `RELEASE_URL` | Required submission release URL |
| `REVIEW_URL` | Optional review URL; falls back to `COMMIT_URL` |
| `PAGES_BASE_URL` | Inherited upstream Pages origin; not written into the result |
| `SECRET`, `MODE`, `ALLOWED_FILES`, `RELEASE_ASSETS` | Inherited runner configuration; not written into the result |
| `GITHUB_*` | Standard GitHub Actions identity and workflow variables |

The autograder must fail clearly when a required native variable is missing, when `ASSIGNMENT_TYPE` is unsupported, or when both owner variables are absent. In the pinned upstream runner, `OWNER` and `USERNAME` are both set to the same `username_from_repo(GITHUB_REPOSITORY, CLASSROOM, ASSIGNMENT, GITHUB_ACTOR)` value: the expected `<classroom>-<assignment>-` repository prefix is stripped case-insensitively, the remaining repository tail is used (including `group-<n>` group/team tails), and the GitHub actor is the fallback. `ASSIGNMENT_TYPE` is normalised from the runner's `MODE` value. They are not independent student identity sources.

The result identity fields are sourced as follows:

| Result field | Native source |
| --- | --- |
| `schema` | Constant `classroom50/result/v1` |
| `classroom` | `CLASSROOM` |
| `assignment` | `ASSIGNMENT` |
| `assignment_type` | Validated `ASSIGNMENT_TYPE`; overwritten by the runner |
| `owner` | `OWNER`, falling back to `USERNAME`; overwritten by the runner |
| `submission` | `SUBMISSION_TAG` |
| `commit` | `COMMIT_URL` |
| `release` | `RELEASE_URL` |
| `review` | `REVIEW_URL`, falling back to `COMMIT_URL` |
| `datetime` | Current UTC time; overwritten by the runner with the submission instant |
| `score` / `max-score` | Sum of collected test scores and maxima |
| `tests` | Collected leaf outcomes from `grading_manifest.json` |

The native runner additionally supplies or overwrites `owner`, `assignment_type`, `datetime`, `graded_at`, and (when available) `submitted_by`.

### Local mode

When explicit local arguments are supplied:

- `--student-root` identifies the checkout;
- `--result` identifies the output path;
- `--variant solution` remains available for dry runs;
- default local mode forces `student`.

The local result uses these exact schema-valid, non-uploadable values:

- `classroom = "local"`;
- `assignment = "local"`;
- `assignment_type = "individual"`;
- `owner = "local"`;
- `submission = "submit/local"`;
- `commit = "local://commit"`;
- `release = "local://release"`;
- `review = "local://review"`;
- `datetime` is current UTC time.

Local mode must not be used as evidence of Classroom 50 identity or score collection.

## Child and outer runner semantics

The autograder child and the upstream runner have different responsibilities:

- Child exit 0 with a valid result: pytest completed; passing and failing cases are both represented in `result.json`; the child exits 0.
- Child exit non-zero for missing identity, dependency, collection, configuration, or other infrastructure failure: the child writes no completed result and returns non-zero.
- The upstream runner receives that child failure, runs its own `Finalizer.error` path, may synthesise a schema-shaped error result, posts an error status, and does not publish a normal scoring Release. The outer runner process itself may still exit 0 according to the upstream contract.

The local test suite must distinguish these two layers rather than asserting that every infrastructure failure produces a non-zero outer process.

## Native result contract

The result document must satisfy the current Classroom 50 schema:

```json
{
  "schema": "classroom50/result/v1",
  "classroom": "...",
  "assignment": "...",
  "assignment_type": "individual",
  "owner": "...",
  "submission": "submit/...",
  "commit": "...",
  "release": "...",
  "review": "...",
  "datetime": "YYYY-MM-DDTHH:MM:SSZ",
  "score": 1,
  "max-score": 1,
  "tests": [
    {
      "test-name": "exercise_key::test_file.py::test_case",
      "passed": true,
      "score": 1,
      "max-score": 1
    }
  ]
}
```

The per-test name remains `<exercise_key>::<leaf-nodeid>`, where the leaf node id is the `test_*.py::test_name` portion without absolute paths. One passing case contributes one point.

A test whose call phase passes but whose teardown phase fails must be recorded as failed. Teardown failure must not be discarded in favour of an earlier call-phase pass.

## Hidden-test manifest contract

The builder writes `grading_manifest.json` at the bundle root with this exact closed shape:

```json
{
  "schema": "classroom50/grading-manifest/v1",
  "exercises": [
    {
      "construct": "selection",
      "exercise_key": "ex001_selection_modify_basics",
      "test_path": "exercises/selection/ex001_selection_modify_basics/tests/test_ex001_selection_modify_basics.py"
    }
  ]
}
```

`schema` and `exercises` are required; each exercise record has exactly `construct`, `exercise_key`, and `test_path`. Paths are POSIX-style bundle-relative paths, contain no absolute prefix, `.`/`..` components, backslashes, or empty segments, and resolve beneath the bundle root. Records are sorted by `(construct, exercise_key)`, exercise keys are unique, and each `test_path` is unique and exactly matches `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`.

A shared validator owned by `scripts/classroom50_manifest.py` is used by both the builder and the bundle autograder. The builder copies that validator into the bundle root. The autograder must consume the manifest rather than recursively collecting arbitrary `test_*.py` files, and must reject missing, duplicate, malformed, non-canonical, or out-of-bundle entries.

The builder must:

1. require each `exercise_key` to be a non-path string matching `^ex[0-9]{3}_[a-z0-9]+(?:_[a-z0-9]+)*$`, with a construct segment known to the canonical resolver;
2. call the source-root-aware canonical resolver (`exercises_root=<source-root>/exercises`) and require the returned directory to be exactly `<source-root>/exercises/<construct>/<exercise_key>`;
3. load and validate the selected `exercise.json`, including field types and exact `construct`/`exercise_key` identity;
4. require exactly `tests/test_<exercise_key>.py`;
5. copy that file plus each documented support module that is present, followed by the transitive `load_exercise_test_module` closure; absence of an optional documented support module is allowed, but a referenced-but-missing module fails;
6. exclude every other `test_*.py`, including `test_repo_*`;
7. write and validate the manifest only after all selected files and support modules are present.

Support-closure discovery uses Python AST parsing, not regex matching. The supported form is a direct call named `load_exercise_test_module` with two positional arguments whose second argument is a literal safe Python module identifier; the first argument may be the existing exercise-key expression. Comments, strings, and unrelated calls are ignored. A dynamic, keyword-only, malformed, path-like, `test_*`, or `test_repo_*` module reference is rejected rather than silently omitted, and a repository-only test can never enter the transitive closure. The builder must test comments containing fake calls, dynamic references, missing modules, and attempted `test_repo_*` references.

The synthetic test fixture must use the canonical `test_<exercise_key>.py` filename and include an extra `test_repo_*.py` regression file that is present in the source but absent from the bundle, manifest, result count, and score. Negative identity fixtures cover path-like keys, malformed `exNNN` keys, unknown constructs, legacy nested paths, invalid metadata types, and metadata identity mismatches. The optional-support rule must also build `exercises/sequence/ex011_sequence_gaps_consolidation/tests/`, whose directory has `student_checker_support.py` but no `expectations.py`.

The native custom entrypoint must not assume the student repository's environment.

The bundle will include the committed, lock-parity-checked `scripts/classroom50_requirements.txt`. Its exact initial contents are:

```text
pytest==9.0.2
tabulate==0.9.0
iniconfig==2.3.0
packaging==26.0
pluggy==1.6.0
pygments==2.19.2
colorama==0.4.6; sys_platform == "win32"
```

The lock-parity check must confirm every line against `uv.lock` and the active platform marker: `colorama` is required on Windows and must not be required or installed on Linux. The file is the sole requirements source copied into the bundle.

Native mode always creates a fresh bundle-local target; it never reuses packages from the student or global environment. `pytest` must not be imported at module load; the import is deferred until after the fresh target is installed, version-checked, origin-checked, and prepended to `sys.path`. Before importing pytest, native mode must:

1. remove and create the target beneath the bundle's runtime directory;
2. remove every inherited `PIP_*` environment key and run the fixed isolated pip invocation against the bundle requirements file;
3. verify every required package version and module origin under the fresh target;
4. prepend only the verified target to `sys.path` before importing pytest or test modules;
5. sanitise inherited Python and pytest environment variables.

The install command is fixed to the equivalent of `sys.executable -m pip --isolated install --disable-pip-version-check --no-input --no-cache-dir --upgrade --target <fresh-bundle-target> -r <bundle>/requirements.txt`, with a 120-second subprocess timeout. `--isolated` and the `PIP_*` scrub prevent inherited pip configuration or environment from redirecting the install. The target is removed and recreated for a fresh install, never populated from a student-controlled directory, and cleaned up on failure. The command must not invoke `uv` or read the student's dependency manifest.

A failed, timed-out, incomplete, wrong-origin, or version-mismatched bootstrap is an infrastructure failure: no completed result is written and the child exits non-zero. Repository tests must mock package-version discovery, module-origin checks, and pip subprocesses; they must not access the network.

The bundle must include a minimal pytest configuration separate from the repository's broad root `pytest.ini`. The exact `pytest.main` argument vector is the ordered list of manifest-listed test paths followed by:

- `-c <bundle>/pytest.ini`;
- `--rootdir <bundle-root>`;
- `--confcutdir <bundle-root>`;
- `-p no:cacheprovider`.

Before that call, the autograder removes every inherited environment key beginning with `PYTEST_` or `PYTHON_`, removes `GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_PATH`, and `GITHUB_STEP_SUMMARY`, and sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Before dependency bootstrap it also removes every `PIP_*` key; hostile `PIP_TARGET`, index, find-links, and user configuration must not redirect the verified target. The child never reads or writes a status/summary output file. The outer runner derives status from the validated result. Tests must assert that hostile `GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_PATH`, `GITHUB_STEP_SUMMARY`, `PYTEST_*`, `PYTHON*`, and `PIP_*` values cannot affect the result.

The bundle’s runtime package must remain before the student checkout on `sys.path`, while `exercise_metadata` must resolve from the student checkout.

## Builder and deployment contract

The builder accepts the existing source, exercise-set, and runtime-source inputs, plus required deployment coordinates:

- `--classroom`;
- `--assignment`;
- `--output`, interpreted as a local Classroom 50 repository root.

It writes exactly:

```text
<output>/<classroom>/autograders/<assignment>/
```

The builder's source-to-target mapping is fixed: `scripts/autograder.py` → `autograder.py`, `scripts/classroom50_requirements.txt` → `requirements.txt`, `scripts/classroom50_pytest.ini` → `pytest.ini`, and `scripts/classroom50_manifest.py` → `classroom50_manifest.py`; the manifest records generate `grading_manifest.json`. Native bundle-root resolution is `Path(CLASSROOM50_BUNDLE_DIR).resolve()`. Local mode uses the script parent and is supported only from a built-bundle copy, where all target files exist; in-place `scripts/autograder.py` is not a supported local execution form.

The target directory contains:

- `autograder.py`;
- `classroom50_manifest.py`;
- `grading_manifest.json`;
- `requirements.txt`;
- `pytest.ini`;
- `exercise_runtime_support/`;
- canonical hidden test files and their support closure under `exercises/<construct>/<exercise_key>/tests/`.

There is no extra `bundle/` wrapper directory. The builder stages this directory, validates the final archive, and replaces the target only after validation succeeds. It must not destructively delete an arbitrary output directory.

### Slug and classroom rules

- `classroom` and `assignment` each match `^[a-z0-9][a-z0-9-]{1,99}$`.
- The composed classroom/assignment budget is enforced: `len(classroom) + 1 + len(assignment) <= 59`, matching Classroom 50's student-repository name budget.
- The builder does not create or query a classroom, so it does not validate organisation existence, protected status, unlisted-link status, or secret URL configuration. Those remain upstream deployment concerns.
- The upstream new-classroom 40-character cap is documented but not reimplemented as classroom creation; the builder accepts an existing path-safe classroom within the composed budget.

Input validation must reject:

- duplicate construct/exercise records;
- non-path-safe classroom, assignment, construct, or exercise-key values;
- records whose canonical source path or `exercise.json` does not match;
- output roots that overlap the source tree or runtime source;
- symlinks and special files in selected source content;
- a compressed archive above Classroom 50's 10 MiB fetch ceiling.

The archive-size check must reproduce the Pages layout: gzip/tar the target contents with exactly `<assignment>/` as the archive's top-level directory. The optional upstream secret URL changes the published URL, not the archive contents. The builder does not create or commit a tarball; Classroom 50's publish workflow creates the live archive.

The bundle must exclude notebooks, solutions, exercise metadata, teacher notes, authoring files, caches, and repository-only tests.

## Native assignment-manifest requirements

The autograder does not write `assignments.json`, but its native path is valid only when the teacher- or CLI-written assignment entry satisfies the pinned Classroom 50 schema:

- required `slug` and `name` values are present and non-empty;
- `autograder` is the normalised short name `default`;
- `grading.mode` is `auto` or omitted (omitted means auto), never `off` or `manual`;
- `tests` is absent;
- `empty_repo` is false or omitted;
- `no_autograder` is false or omitted;
- `mode` is `individual`, `group`, or `team`;
- `group` includes `max_group_size` in the range 2–100 and omits `team_formation`;
- `team` includes `max_group_size` in the range 2–100 and `team_formation` equal to `teacher` or `student`;
- `individual` omits both group-only fields;
- a native bundle assignment must use a valid `template` object with non-empty `owner`, `repo`, and `branch`, because the student checkout must contain the canonical exercise metadata, notebooks, and visible tests that this bundle deliberately excludes;
- `init_shim: true` is retained as a pinned schema fixture, but is unsupported for this native bundle deployment because it creates no starter exercise surface; the deployment validator must reject it rather than claim it is deployable;
- `template` and `init_shim` are mutually exclusive; `init_shim` also excludes `empty_repo: true` and `no_autograder: true`.

The native contract fixtures must cover all three modes, repository-name/group tails, actor fallback, valid template-backed assignments, an explicitly unsupported `init_shim` fixture, valid conditional fields, and invalid/omitted combinations. The builder does not create or rewrite the assignment manifest.

## Constraints and invariants

- Preserve the canonical exercise-local layout under `exercises/<construct>/<exercise_key>/`.
- Preserve canonical exported notebook and test paths; flattened mirrors remain forbidden.
- Do not change the Selection pilot exercises, metadata, tests, notebook cells, or teaching order.
- Do not introduce legacy compatibility paths or result-field aliases.
- Keep tests deterministic, fast, and independent of network access; the upstream snapshot is inert test data and is excluded from repository collection and linting.
- Student-variant failures remain expected; solution-variant tests must pass.
- Hidden tests are tamper-resistant but public through Pages; no solutions or confidential data may enter the bundle.
- The native grade job's 15-minute limit and 10 MiB compressed bundle limit are operational constraints.
- The builder performs local filesystem staging only; it does not call GitHub or manage Classroom 50 state.
- Generated documentation is reproducible: the generator has an explicit owner/timestamp input, uses temporary output for test-owner smoke checks, and the tracked page is regenerated with the real owner and a fixed timestamp.

## Evidence

- `scripts/autograder.py:40-64` — mandatory local arguments.
- `scripts/autograder.py:83-98` — current teardown-report handling.
- `scripts/autograder.py:166-180` — old result shape.
- `scripts/autograder.py:188-237` — local roots, pytest invocation, and result writing.
- `scripts/build_classroom50_bundle.py:70-163` — current input, copying, and output behaviour.
- `exercise_metadata/resolver.py:41-109` and `exercise_metadata/loader.py` — canonical key/construct/path and metadata identity checks used by the builder.
- `tests/test_classroom50_bundle_stage4.py:74-92,233-267` — synthetic filename and old-payload assertions.
- `pyproject.toml:10-17` and `uv.lock:216-222,338-344,808-814,856-862,935-941,957-970,1286-1292` — direct/runtime dependency versions and the complete lock closure; `pytest` depends on `iniconfig`, `packaging`, `pluggy`, `pygments`, and Windows-only `colorama`, while `tabulate` is required directly by `exercise_runtime_support/exercise_framework/reporting.py`.
- `docs/developers/execution-model.md:69-78` — bundle isolation and variant contract.
- Classroom 50 `runner.py` at commit `43ec1444`, `run_entrypoint`, `finalize_result`, and `Finalizer.error` — child invocation, environment, result location, stamping, and outer error semantics.
- Classroom 50 `schemas/result-v1.schema.json` at commit `43ec1444` — canonical result fields and supported assignment modes.
- Classroom 50 `schemas/assignments-v1.schema.json` at commit `43ec1444` — assignment modes, group/team conditional fields, and grading/autograder flags.
- Classroom 50 `autograde-runner.yaml`, `publish-pages.yaml`, `autograder_cmd.go`, and the pinned runner/autograder tests at commit `43ec1444` — outer status/release gates, archive layout, and absence of a per-assignment upload command.
- The native contract fixture must checksum the full upstream paths for `runner.py`, both workflows, both schemas, `autograder_cmd.go`, `autograder_cmd_test.go`, `autograders_tests/conftest.py`, `autograders_tests/test_runner.py`, `autograders_tests/test_default_autograder.py`, `skeleton_tests/conftest.py`, `skeleton_tests/test_runner_bundle_dir.py`, `skeleton_tests/test_runner_grade_python.py`, `skeleton_tests/test_runner_release_assets.py`, `skeleton_tests/test_assignments_schema.py`, and `skeleton_tests/test_contract_parity.py`; it must not use a network fallback or hand-written substitute.

## Acceptance criteria

1. A native no-argument child run writes a schema-valid result to the student checkout and exits 0 for both passing and failing collected cases.
2. Missing or invalid native identity variables fail clearly, remove stale child results, and return non-zero.
3. A pinned native-runner contract check, backed by a SHA-256 manifest and network-free fixtures for the named upstream source/test files, proves the upstream finalisation/stamping/error boundary, including the distinction between child and outer exit semantics.
4. Explicit local mode remains supported, including solution dry runs, and emits the same canonical result shape with exact documented local identity values.
5. Result rows use `test-name` and `passed`; no old `version` or `name` fields remain.
6. Teardown failures cannot receive a passing score.
7. Hidden tests are selected only through the exact `grading_manifest.json` wire contract; repository-only test files cannot affect collection or score.
8. Hidden tests remain bundle-only, runtime imports remain bundle-first, metadata imports remain student-checkout-backed, and visible-test tampering has no effect.
9. Native dependency bootstrap uses the full lock-derived closure, a fresh verified target, the fixed pip invocation, bounded cleanup, and network-free tests.
10. Student-controlled pytest configuration, inherited `PYTEST_*`/`PYTHON_*`/`PIP_*` and GitHub output-sink state, and plugin autoloading cannot change hidden-test collection or result status.
11. The builder writes the documented native target path, validates exercise identity and canonical test selection, and excludes all authoring/solution assets.
12. Unsafe records, duplicate records, unsafe filesystem entries, overlapping output paths, and oversized compressed bundles fail before target replacement.
13. Template-backed individual, group, and team assignment-manifest fixtures satisfy the pinned conditional schema requirements and native environment contract; `init_shim` is explicitly rejected for this bundle.
14. Local Selection validation remains 224/224 for solutions and 0/224 for students, with completed child exit code 0.
15. Directly affected developer, teacher, generated-page, and agent documentation contains no stale broken-autograder, GitHub Classroom scoring, or canonical-layout claims; explicitly deferred exceptions are recorded.
16. All repository quality gates pass, with expected student-variant failures treated as expected.

## Open questions and risks

- Runtime pip installation adds network and startup cost; a public container is a possible later alternative.
- Pages/CDN propagation may delay live bundle availability.
- The Classroom 50 source contract may advance beyond commit `43ec1444`; recheck before implementation begins and before live rollout.
- Manual commit/upload into the Classroom 50 config repository remains an operational step.
- No live pilot is included, so the local native simulation must model the upstream invocation, finalisation, and archive layout precisely.
