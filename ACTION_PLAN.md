# ACTION_PLAN — Native Classroom 50 Bundle Autograder Integration

## Read-first context

This plan is derived from the current `SPEC.md` and `WORKFLOW_SPEC.md`. The previous Selection Pilot plan is superseded. The Selection exercises remain a read-only validation fixture.

Before implementing any stage, read:

- `AGENTS.md`
- `SPEC.md`
- `WORKFLOW_SPEC.md`
- `ACTION_PLAN.md`
- `docs/developers/project-structure.md`
- `docs/developers/execution-model.md`
- `docs/developers/testing-framework.md`
- `docs/developers/development.md`
- `docs/developers/classroom50-autograder.md`
- `scripts/autograder.py`
- `scripts/build_classroom50_bundle.py`
- the relevant files under `tests/`

Every delegated handoff must include an explicit `Files read` list. If a mandatory file is missing from a handoff, return the work to the same agent before proceeding.

## Scope

- Adapt `scripts/autograder.py` for native no-argument execution, canonical result output, and teardown-aware outcomes.
- Add lock-derived native dependencies and a pytest trust boundary.
- Extend `scripts/build_classroom50_bundle.py` to produce a validated native per-assignment directory and exact hidden-test manifest.
- Add a pinned native-runner contract check that distinguishes child and outer-runner semantics.
- Update repository infrastructure tests and directly affected documentation.
- Validate local and native-compatible execution without live Classroom 50 access.

## Out of scope

- Changes to `foundation50/classroom50`.
- Classroom 50 classroom, roster, assignment, or score-collection automation.
- A new `gh teacher` per-assignment bundle-upload command.
- Live GitHub Pages, student acceptance, submission, Release, or Collect operations.
- Changes to exercises, notebooks, tagged cells, exercise metadata, `OrderOfTeaching.md`, or pedagogy.
- Legacy compatibility aliases or migration paths.
- A repository-wide rewrite of unrelated GitHub Platform documentation.

## Product and architecture constraints

- Preserve `exercises/<construct>/<exercise_key>/` as the only canonical exercise layout.
- Preserve canonical exported notebook and test paths; flattened mirrors remain forbidden.
- Preserve one point per passing pytest case and `<exercise_key>::<leaf-nodeid>` test names.
- Preserve the student/solution variant contract.
- Preserve bundle-first runtime imports and student-checkout metadata resolution.
- Use Python 3.14 for native execution.
- Use `uv` for repository development and tests; native runtime code uses `sys.executable -m pip`, never `uv`.
- Keep the builder generic: classroom and assignment are deployment coordinates, not grading branches.
- Fail fast on invalid records, unsafe paths, dependency failures, and invalid native identity.
- Distinguish child-autograder exit semantics from upstream runner finalisation semantics.

## TDD and quality gates

Each implementation stage follows red → green → refactor.

1. Add or update failing tests for the stage acceptance criteria.
2. Implement the smallest coherent change.
3. Refactor only with all stage tests green.
4. Run the stage checks and record results.

Repository-wide gates:

- `uv run pytest --collect-only -q`
- `uv run pytest -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- expected student-variant failure check: `! uv run python scripts/run_pytest_variant.py --variant student -q` (the command must fail)
- `uv run ruff check .`
- final scoped Pyright gate (applicable after Stage 7, when every named file exists): `uv run pyright scripts/autograder.py scripts/build_classroom50_bundle.py scripts/classroom50_manifest.py tests/test_classroom50_native_autograder.py tests/test_classroom50_native_runner_contract.py tests/test_classroom50_bundle_stage4.py tests/test_classroom50_autograder_docs.py` (no whole-repository Pyright gate; record the current 62-error baseline and fail on new errors in these files)
- post-Stage-12 scoped Pyright gate for later Python surfaces: `uv run pyright scripts/sync_construct_template_repos.py scripts/template_repo_cli/cli.py tests/test_classroom50_selection_pilot.py tests/test_classroom50_docs_contract.py tests/test_sync_construct_template_repos.py`; record any baseline separately and fail on new errors in these files
- `uv run repoman validate --construct selection`
- `uv run repoman validate --construct sequence`
- `uv run pytest tests/test_sync_construct_template_repos.py tests/test_classroom50_docs_contract.py -q` once those tests exist
- no network-dependent repository tests

## Stage 1 — Define red tests for native result and identity

### Objective

Lock the native result schema, environment-source matrix, local identity policy, and teardown outcome semantics before changing the autograder.

### Files and surfaces

- New `tests/test_classroom50_native_autograder.py`.
- Update `tests/test_classroom50_bundle_stage4.py` for the canonical result shape.
- Read-only Selection exercises remain fixtures.

### Required test cases

1. A no-argument child invocation writes `result.json` in the synthetic student checkout.
2. Native mode consumes `CLASSROOM50_BUNDLE_DIR`, `CLASSROOM`, `ASSIGNMENT`, `ASSIGNMENT_TYPE`, `OWNER`/`USERNAME`, `SUBMISSION_TAG`, `COMMIT_URL`, `RELEASE_URL`, and optional `REVIEW_URL`, with the upstream derivation of owner and assignment type represented in the fixture.
3. Missing required variables, missing owner identity, and unsupported assignment types return non-zero and remove stale child results.
4. Explicit local arguments are accepted as a pair; either argument alone is rejected.
5. Local mode emits the exact documented local identity values.
6. Native and local payloads use `schema`, `test-name`, and `passed`, with no old aliases.
7. A passing call followed by a failing teardown is scored as failed.
8. `individual`, `group`, and `team` assignment-manifest fixtures satisfy required slug/name fields, `max_group_size` bounds, `team_formation` values, `grading.mode`, `empty_repo`, `no_autograder`, and absent `tests`; invalid combinations are rejected.
9. Assignment fixtures include a valid templated native assignment and an explicitly unsupported template-less `init_shim` fixture; the native deployment validator rejects `init_shim`, and schema-negative cases reject `template` with `init_shim`, `init_shim` with `empty_repo`, and `init_shim` with `no_autograder`.
10. Repository-name fixtures cover case-insensitive prefix stripping, individual owners, `group-<n>` tails, and the GitHub actor fallback; `OWNER` and `USERNAME` are identical in native mode.
11. Native `MODE` normalisation fixtures map to the expected `individual`, `group`, or `team` result type.

### Acceptance criteria

- New tests fail against the current implementation for the intended missing behaviour.
- Existing bundle-stage tests that do not exercise the new native contract remain green; only assertions directly superseded by this feature are marked for replacement in this stage.
- No production code is changed in this stage.

### Checks

- Targeted test collection.
- Red test run.
- Existing test inventory and expected-red/expected-green report.

### Review point

Planner and implementation owner confirm the field-source matrix, exact local values, supported modes, and teardown rule.

## Stage 2 — Implement native and local autograder modes

### Objective

Make the autograder executable both as a local dry-run CLI and as a native Classroom 50 per-assignment entrypoint.

### Files and surfaces

- `scripts/autograder.py`
- `tests/test_classroom50_native_autograder.py`

### Required behaviour

- Make `--student-root` and `--result` optional only as a pair.
- Native mode uses the current working directory as the student root, `Path(CLASSROOM50_BUNDLE_DIR).resolve()` as the bundle root, and `result.json` in the current directory.
- Local mode retains explicit roots and result paths but resolves the script parent as its bundle root; tests must copy the script into a built-bundle fixture before invoking it locally.
- Native mode validates the complete required environment and assignment type.
- Local mode uses the exact non-uploadable identity values in `SPEC.md`.
- Stage 2 native tests use a minimal staged bundle fixture with placeholder contract files; real builder-to-autograder integration is deferred to the atomic Stage 3–5 emissions.
- Both modes force `PYTUTOR_ACTIVE_VARIANT=student` unless the caller explicitly selects `solution` for a local dry run.
- Preserve package-origin checks and bundle-only test discovery.
- Preserve completed child pass/fail exit 0 and child infrastructure non-zero semantics.
- Record teardown failures as failed outcomes.

### Acceptance criteria

- The native no-argument fixture passes against the staged bundle.
- Existing local solution and student dry-run behaviour remains correct.
- The real builder integration test is not a knowingly-red Stage 2 gate; it is resumed after the Stage 3–5 target emissions.
- Missing or invalid native environment is an infrastructure failure, not a vacuous pass.
- In-place `scripts/autograder.py` execution is rejected or unsupported; local tests use a built-bundle copy and native tests use `CLASSROOM50_BUNDLE_DIR`.
- No result-field compatibility aliases remain.
- Group/team result identity is preserved when supplied by the native environment.

### Checks

- Targeted native and bundle-stage tests.
- Native synthetic individual, group, and team fixtures.
- Ruff and Pyright on the touched script and tests.

### Review point

Tidy Code Reviewer reviews mode separation, environment validation, result construction, and teardown handling.

## Stage 3 — Add lock-derived native dependency bootstrap and target contract files

### Objective

Make hidden grading independent of the student checkout's Python environment and package versions, and atomically emit the four bundle files that the autograder requires before any later trust/selection stage runs.

### Files and surfaces

- `scripts/autograder.py`
- `scripts/build_classroom50_bundle.py`
- New `scripts/classroom50_requirements.txt`
- New `scripts/classroom50_pytest.ini`
- New `scripts/classroom50_manifest.py`
- `tests/test_classroom50_native_autograder.py`
- `tests/test_classroom50_bundle_stage4.py`

### Required behaviour

- The builder atomically emits `requirements.txt`, `pytest.ini`, `classroom50_manifest.py`, and a schema-valid `grading_manifest.json` for the selected canonical records; the autograder must not be made to depend on files that this stage has not yet emitted.
- The Stage 3 manifest emission is the minimum closed, canonical-path contract needed for the real-builder test; Stage 5 hardens its support-module closure, identity validation, and rejection rules.
- Use committed, lock-parity-checked `scripts/classroom50_requirements.txt` with exactly `pytest==9.0.2`, `tabulate==0.9.0`, `iniconfig==2.3.0`, `packaging==26.0`, `pluggy==1.6.0`, `pygments==2.19.2`, and `colorama==0.4.6; sys_platform == "win32"`.
- The builder emits this source as `<target>/requirements.txt` in the same atomic stage before the autograder can bootstrap; update the real builder-stage test in this stage.
- Test that `colorama` is required on Windows and not required or installed on Linux.
- Check all required installed versions and module origins after installation.
- Remove every inherited environment key beginning with `PIP_` before installation and use `pip --isolated`, so `PIP_TARGET`, index, find-links, and user configuration cannot redirect or replace the target.
- Always create a fresh bundle-local target; do not reuse global or student packages.
- Use the fixed pip invocation `sys.executable -m pip --isolated install --disable-pip-version-check --no-input --no-cache-dir --upgrade --target <fresh-bundle-target> -r <bundle>/requirements.txt`, with a 120-second timeout.
- Remove and recreate the bundle-local target for a fresh install; never populate it from a student-controlled directory.
- Defer the module-scope `import pytest`; import pytest only after the fresh target has been installed, version-checked, origin-checked, and prepended to `sys.path`.
- Prepend the verified target to `sys.path` before importing pytest or test modules.
- Treat missing pip, timeout, failed install, incomplete target, wrong version, wrong origin, or redirected pip environment as infrastructure failures.
- Do not invoke `uv` or read student dependency manifests from native code.

### Acceptance criteria

- The builder emits a complete minimum target contract atomically; no later stage begins with a missing requirements, pytest, manifest, or validator file.
- Native grading does not read the student's dependency manifest.
- Exact-version, missing-version, mismatch, failed-bootstrap, timeout, hostile `PIP_*`, and redirected-origin paths are tested without network access.
- Requirements pins have a lockfile-parity test.
- The existing real-builder `tests/test_classroom50_bundle_stage4.py` remains green after the builder emits the target requirements file; no knowingly-red inter-stage state is permitted.
- A completed pass/fail still writes the canonical result and exits 0.

### Checks

- Targeted dependency and real-builder tests.
- Assert `<target>/requirements.txt` exists and matches the committed source byte-for-byte.
- Ruff and Pyright on files present at this stage.
- Verify no network command is used by repository tests.

### Review point

Tidy Code Reviewer checks deterministic target lifecycle, version verification, timeout handling, and import-path order.

## Stage 4 — Establish the pytest trust boundary

### Objective

Prevent student-controlled pytest configuration, conftest files, or third-party plugin autoloading from changing hidden-test collection.

### Files and surfaces

- `scripts/autograder.py`
- `scripts/build_classroom50_bundle.py`
- `scripts/classroom50_pytest.ini` (already emitted by Stage 3)
- `tests/test_classroom50_native_autograder.py`
- `tests/test_classroom50_bundle_stage4.py`

### Required behaviour

- Consume the Stage 3 `<target>/pytest.ini` and manifest contract; Stage 4 hardens the invocation and isolation boundary without introducing a new missing target file.
- Use the exact `pytest.main` argument order: manifest-listed test paths, `-c <bundle>/pytest.ini`, `--rootdir <bundle-root>`, `--confcutdir <bundle-root>`, and `-p no:cacheprovider`.
- Remove every inherited environment key beginning with `PYTEST_` or `PYTHON_`, plus `GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_PATH`, and `GITHUB_STEP_SUMMARY`, before execution.
- Set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` while retaining the explicit outcome collector.
- Do not let child code write or influence status/summary output; the outer runner derives status from the validated result.
- Keep the bundle runtime before the student checkout and retain student metadata resolution.
- Do not copy or depend on the repository's broad root `pytest.ini`.

### Acceptance criteria

- A hostile student `pytest.ini`, `pyproject.toml`, conftest, plugin environment, `GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_PATH`, or `GITHUB_STEP_SUMMARY` cannot alter hidden-test discovery, scoring, or status.
- The trusted configuration does not import student code.
- The existing real-builder `tests/test_classroom50_bundle_stage4.py` remains green after the target `pytest.ini` emission.
- The hidden-test isolation tests remain deterministic and network-free.

### Checks

- Targeted hostile-configuration tests.
- Existing runtime/metadata isolation tests.
- Ruff and Pyright.

### Review point

Tidy Code Reviewer reviews the trust boundary and confirms that the student checkout remains the source of notebook/metadata state.

## Stage 5 — Harden canonical hidden-test contents and manifest

### Objective

Make the builder and autograder consume one exact, validated list of canonical hidden tests, building on the minimum manifest and validator emitted atomically in Stage 3.

### Files and surfaces

- `scripts/classroom50_manifest.py`
- `scripts/build_classroom50_bundle.py`
- `scripts/autograder.py`
- `exercise_metadata/resolver.py` and `exercise_metadata/loader.py` as canonical identity sources
- `tests/test_classroom50_bundle_stage4.py`
- `tests/test_classroom50_native_autograder.py`

### Required selection algorithm

1. Require each `exercise_key` to be a non-path string matching `^ex[0-9]{3}_[a-z0-9]+(?:_[a-z0-9]+)*$`, with a construct segment known to the canonical resolver.
2. Call the source-root-aware canonical resolver with `exercises_root=<source-root>/exercises` and require the returned directory to be exactly `<source-root>/exercises/<construct>/<exercise_key>`.
3. Load and validate the selected `exercise.json`, including field types and exact `construct`/`exercise_key` identity.
4. Require exactly `tests/test_<exercise_key>.py`.
5. Copy that file plus each documented support module that is present, then the transitive `load_exercise_test_module` closure. An absent optional `expectations.py` or `student_checker_support.py` is not an error; a referenced-but-missing support module remains an error.
6. Discover support references with AST parsing: accept only a direct `load_exercise_test_module(<expression>, "<safe_identifier>")` call; reject dynamic/keyword-only/malformed/path-like/`test_*`/`test_repo_*` references, and reject missing transitive modules.
7. Exclude every other `test_*.py`, including `test_repo_*`.
8. Write the closed `classroom50/grading-manifest/v1` wire format with sorted unique records and canonical POSIX-relative paths.
9. Copy the shared manifest validator into the bundle.
10. Make builder and autograder use the same validator; reject missing, duplicate, malformed, non-canonical, or out-of-bundle entries.

### Acceptance criteria

- The synthetic fixture uses the canonical filename.
- An extra `test_repo_*.py` source file is absent from the bundle, manifest, result count, and score.
- Exercise identity mismatch or missing canonical test fails before target replacement.
- Path-like, malformed, unknown-construct, legacy-path, invalid-type, and metadata-mismatch fixtures fail before target replacement.
- The autograder cannot collect arbitrary bundled test files outside the manifest.
- The shared validator rejects manifest tampering, duplicate paths, non-canonical names, and out-of-bundle paths in both builder and autograder tests.
- AST support discovery ignores comments and rejects dynamic, keyword-only, path-like, `test_*`, `test_repo_*`, and missing transitive references.
- The real-builder `tests/test_classroom50_bundle_stage4.py` remains green after the Stage 3 minimum manifest is hardened.
- The optional-support-module rule builds `exercises/sequence/ex011_sequence_gaps_consolidation/tests/` even though it has no `expectations.py`, while a missing module explicitly referenced by `load_exercise_test_module` still fails.
- No construct- or exercise-specific grading branch is added.

### Checks

- Builder selection tests.
- Autograder manifest-validation tests.
- Bundle tree and result-count inspection.
- Ruff and Pyright.

### Review point

Tidy Code Reviewer reviews exercise identity validation, support closure, and manifest enforcement.

## Stage 6 — Harden builder filesystem and archive safety

### Objective

Produce a safe native target without destructive path handling or oversized archives. The four target contract files are emitted atomically in Stage 3 and hardened in Stages 4–5; this stage validates the complete output without introducing a knowingly-red inter-stage state.

### Files and surfaces

- `scripts/build_classroom50_bundle.py`
- `scripts/classroom50_requirements.txt`
- `scripts/classroom50_pytest.ini`
- `scripts/classroom50_manifest.py`
- `tests/test_classroom50_bundle_stage4.py`
- `tests/test_classroom50_native_autograder.py`

### Required CLI and target contract

The builder requires:

- `--source-root`;
- `--exercise-set`;
- `--runtime-source`;
- `--classroom`;
- `--assignment`;
- `--output`, interpreted as a local Classroom 50 repository root.

It writes exactly:

`<output>/<classroom>/autograders/<assignment>/`

The target contains `autograder.py`, `classroom50_manifest.py`, `grading_manifest.json`, `requirements.txt`, `pytest.ini`, `exercise_runtime_support/`, and canonical hidden tests.

Source-to-target contract:

| Source | Target |
| --- | --- |
| `scripts/autograder.py` | `autograder.py` |
| `scripts/classroom50_requirements.txt` | `requirements.txt` |
| `scripts/classroom50_pytest.ini` | `pytest.ini` |
| `scripts/classroom50_manifest.py` | `classroom50_manifest.py` |
| generated closed manifest records | `grading_manifest.json` |
| selected runtime package | `exercise_runtime_support/` |
| canonical exercise-local test/support files | `exercises/<construct>/<exercise_key>/tests/` |

Native bundle-root resolution is exactly `Path(CLASSROOM50_BUNDLE_DIR).resolve()`. Local mode resolves the script's parent and is supported only from a built-bundle copy, where all target files above exist; in-place `scripts/autograder.py` is not a supported local execution form.

### Required validation

- Classroom and assignment each match `^[a-z0-9][a-z0-9-]{1,99}$`.
- `len(classroom) + 1 + len(assignment) <= 59`.
- Construct and exercise-key values are path-safe and match canonical metadata.
- Duplicate exercise records are rejected.
- Canonical source paths and `exercise.json` files must exist and agree.
- The output root must not overlap the source tree or runtime source.
- Symlinks and special files in selected source content are rejected.
- Build into staging; do not destructively delete an arbitrary existing output tree.
- Copy and validate the lock-derived requirements, trusted pytest configuration, and shared manifest validator into the target.
- Reproduce the Pages archive layout with exactly `<assignment>/` as the top-level directory.
- Reject archives above the native 10 MiB fetch ceiling before replacing the target.
- Deployment-contract tests reject `init_shim: true` for this native bundle because the student checkout would lack the canonical exercise surface; the schema fixture may remain for compatibility evidence.
- Do not query or infer organisation existence, protected/unlisted status, or secret-link configuration.

### Acceptance criteria

- The generated directory can be copied directly into a Classroom 50 config repository.
- The deployment contract accepts only a valid template-backed assignment; `init_shim` is explicitly rejected because it cannot provide the student exercise surface.
- Invalid slugs, over-budget names, duplicate/path-unsafe records, identity mismatches, overlapping outputs, symlinks, special files, and oversized archives fail safely.
- Existing target contents survive a failed build.
- The output path has no wrapper directory ambiguity.

### Checks

- Builder success and failure cases.
- Boundary tests for slug and composed-name limits.
- Pages-style archive inspection and compressed-size threshold.
- Bundle tree inspection.
- Ruff and Pyright.

### Review point

Tidy Code Reviewer reviews path validation, staging/atomic replacement, archive measurement, and native target semantics.

## Stage 7 — Add the pinned native-runner contract check

### Objective

Verify the exact upstream child invocation, result location, finalisation, and error classification without requiring live GitHub operations.

### Files and surfaces

- New `tests/test_classroom50_native_runner_contract.py`.
- Test-only checksum-pinned contract fixtures under `tests/fixtures/classroom50_native_contract/`, including a `SHA256SUMS` manifest.
- `pytest.ini` and `pyproject.toml` are updated in this stage to exclude the inert snapshot directory from collection and linting.
- The pinned upstream files at commit `43ec1444f87674cd3276e66eadb6439dc0c97668`: `cli/gh-teacher/skeleton/dotgithub/scripts/runner.py`, `cli/gh-teacher/skeleton/dotgithub/workflows/autograde-runner.yaml`, `cli/gh-teacher/skeleton/dotgithub/workflows/publish-pages.yaml`, `schemas/result-v1.schema.json`, `schemas/assignments-v1.schema.json`, `cli/gh-teacher/autograder_cmd.go`, `cli/gh-teacher/autograder_cmd_test.go`, `cli/gh-teacher/autograders_tests/conftest.py`, `cli/gh-teacher/autograders_tests/test_runner.py`, `cli/gh-teacher/autograders_tests/test_default_autograder.py`, `cli/gh-teacher/skeleton_tests/conftest.py`, `cli/gh-teacher/skeleton_tests/test_runner_bundle_dir.py`, `cli/gh-teacher/skeleton_tests/test_runner_grade_python.py`, `cli/gh-teacher/skeleton_tests/test_runner_release_assets.py`, `cli/gh-teacher/skeleton_tests/test_assignments_schema.py`, and `cli/gh-teacher/skeleton_tests/test_contract_parity.py`.

### Required checks

- Use a network-free, SHA-256 checksum manifest and local inert snapshot of every named upstream file; prohibit network fallback, execution of snapshot `test_*.py` files, and hand-written substitutes.
- Add the snapshot directory to `norecursedirs` in both `pytest.ini` and the `[tool.pytest.ini_options]` table, and add `tests/fixtures/classroom50_native_contract/**` to Ruff's force-excluded paths; verify the snapshot is never collected or linted as runtime code.
- Invoke the child exactly as upstream `run_entrypoint` does: no arguments, the grading interpreter, the student checkout as cwd, and the native environment.
- Read the result from the student checkout, not the bundle.
- Apply the same finalisation/stamping rules for owner, assignment type, timestamps, and submitter.
- Validate the canonical schema after finalisation.
- Exercise `Finalizer.error` and verify the workflow condition that suppresses a normal scoring Release.
- Verify child exit 0 plus valid result produces a normal completed outcome.
- Verify child non-zero follows the upstream error-finalisation path and pinned outer exit semantics.
- Verify the archive top-level `<assignment>/` layout and the absence of a **per-assignment** upload command; the classroom-default `set-default` command is expected to remain.
- Record the exact upstream source paths, raw-byte SHA-256 hashes, and commit hash in the test/report.

The harness is test-only and must not become runtime or student-template content. It must not access the network.

### Acceptance criteria

- Child and outer runner semantics are no longer conflated.
- Native result location, environment, stamping, schema, and error classification are reproducible locally.
- The complete pinned snapshot, including both `conftest.py` files, passes its SHA-256 manifest and remains inert under repository pytest/Ruff gates.
- No upstream source is modified.

### Checks

- Targeted native-runner contract test.
- Red/green evidence against the old child-only harness.
- Documentation-contract assertion for the pinned source reference.
- Before Stage 7, run scoped Pyright only on files already present; the final scoped command in the quality-gate section is not an executable precondition for Stage 1.

### Review point

Testing Specialist and Tidy Code Reviewer verify that the harness models the pinned upstream behaviour without becoming production coupling.

## Stage 8 — Run local and native-compatible integration validation

### Objective

Prove both invocation paths and preserve the existing exercise, template, and variant invariants.

### Files and surfaces

- `scripts/autograder.py`
- `scripts/build_classroom50_bundle.py`
- `tests/test_classroom50_bundle_stage4.py`
- `tests/test_classroom50_native_autograder.py`
- `tests/test_classroom50_native_runner_contract.py`
- `tests/test_classroom50_autograder_docs.py`
- `tests/test_classroom50_selection_pilot.py`
- Exported template output, read-only for this feature.

### Required checks

1. Selection solution bundle run returns 224/224.
2. Selection student bundle run returns 0/224 with child exit code 0.
3. Native no-argument child simulation writes a canonical result in the student checkout.
4. Pinned runner finalisation produces the expected stamped result and outer status semantics.
5. Student-visible test tampering does not change the hidden result.
6. Runtime imports still resolve from the bundle and metadata from the student checkout.
7. Student pytest configuration cannot influence collection.
8. Builder output contains no solution, notebook, metadata, authoring, or repository-only test assets.
9. Packaged templates remain starter-only and pass validation.

### Acceptance criteria

- Local and native-compatible paths produce the same score semantics and test names.
- Expected student failure remains expected and is not silenced.
- No live GitHub or Classroom 50 operation is required.

### Checks

- Targeted bundle/native tests.
- Run the re-scoped generic docs contract and the separate Selection pilot test; generic contract assertions must not require Selection counts.
- Full collection and solution suite.
- Expected student-variant spot check.
- `uv run repoman validate --construct selection`
- `uv run repoman validate --construct sequence`
- `uv run pytest tests/test_sync_construct_template_repos.py -q` once that test exists
- Ruff and Pyright.

### Review point

Testing Specialist confirms variant, isolation, tamper, manifest, and packaging invariants.

## Stage 9 — Synchronise developer and contract documentation

### Objective

Make developer documentation describe the native contract and remove stale local-only wording.

### Files and surfaces

- `docs/developers/classroom50-autograder.md`
- `docs/developers/execution-model.md`
- `docs/developers/testing-framework.md`
- `docs/developers/development.md`
- `docs/developers/project-structure.md`
- `docs/developers/template_repo_cli.md`
- `docs/developers/setup.md`
- `AGENTS.md`
- `pyproject.toml`
- `tests/test_classroom50_autograder_docs.py`
- New `tests/test_classroom50_selection_pilot.py`
- New `tests/test_classroom50_docs_contract.py`
- `SPEC.md`
- `WORKFLOW_SPEC.md`
- `ACTION_PLAN.md`

### Required corrections

- Document native no-argument invocation, native environment, result schema, child/outer error semantics, manifest selection, lock-derived dependencies, trusted pytest configuration, and Python 3.14.
- Document the builder's classroom/assignment target and archive contract.
- Document `autograder: "default"`, manual bundle commit, Pages publication, and the absence of a native upload command.
- Remove the old `version`/`name` result shape and arbitrary-output builder description.
- Re-scope the existing documentation assertions: retain only generic scoring/leaf-name/variant/selection-fixture checks in `tests/test_classroom50_autograder_docs.py`; move `SELECTION_DIR`, `EXPECTED_KEYS`, `EXPECTED_COUNTS`, `EXPECTED_TITLES`, `EXPECTED_TOTAL = 224`, `_COLLECT_LINE_RE`, `_canonical_test_file`, `_exercise_titles`, `_collected_counts`, `_documented_count`, the `json`/`re`/`subprocess`/`sys` imports used by those helpers, `test_full_total_computed_and_pilot_counts`, and `test_pilot_titles_match_exercise_json` to a separate Selection-only `tests/test_classroom50_selection_pilot.py`; assert that the generic test has no `SELECTION_DIR` dependency; replace `test_slug_is_operator_input_not_stored` with a native-coordinate test that checks the builder's classroom/assignment path and absence of a result `slug` field.
- Remove stale canonical-layout compatibility wording from the directly affected setup/developer guidance.
- Update the root package description in `pyproject.toml` from “GitHub Classroom friendly” to the native Classroom 50 contract.
- Record the two legacy notebook identifiers in `docs/teachers/pedagogy.md:122,140` as a narrow deferred exception because pedagogy/exercise content is out of scope.
- Keep the Selection pilot as a validation fixture, not the feature's permanent title or special grader.

### Acceptance criteria

- Developer documents agree with the three root planning artefacts.
- No developer document directs users to the old reporter or local-only result contract.
- The generic contract test has no Selection-specific count/title requirement, while the separate Selection pilot test retains the 224/224 and 0/224 regression evidence.

### Checks

- Documentation-contract tests.
- Search for stale result fields, old bundle commands, and broken-autograder claims.
- Link/reference validation.

### Review point

Docs agent and reviewer confirm terminology and British English.

## Documentation inventory and exception record

Every stale surface found during the review is assigned one of these dispositions:

| Surface | Disposition | Reason/contract |
| --- | --- | --- |
| `docs/developers/classroom50-autograder.md` | Update | Native result, manifest, dependency, and child/outer contract |
| `docs/developers/execution-model.md` | Update | Bundle and canonical discovery contract |
| `docs/developers/testing-framework.md` | Update | Native test surface and commands |
| `docs/developers/development.md` | Update | Contributor workflow |
| `docs/developers/project-structure.md` | Update | New bundle/manifest helper surfaces |
| `docs/developers/template_repo_cli.md` | Update | Teacher bundle placement |
| `docs/developers/setup.md` | Update | Remove ambiguous flattened compatibility guidance |
| `AGENTS.md` | Update | Repository-wide canonical/native guidance |
| `pyproject.toml` | Update | Remove stale “GitHub Classroom friendly” package description |
| `scripts/sync_construct_template_repos.py` | Update | Generated-page source |
| `scripts/template_repo_cli/cli.py` | Update | Generated-page source/wording |
| `tests/test_sync_construct_template_repos.py` | Update | Deterministic generator coverage |
| `docs/teachers/construct-template-repos.md` | Regenerate | Derived from the corrected generator |
| `docs/teachers/exercise-generation.md` | Update | Remove GitHub Classroom grading link |
| `docs/teachers/how-to-use-the-template-repo-cli.md` | Update | Replace assignment/autograding setup |
| `docs/teachers/understanding-the-tools.md` | Update | Classroom 50 terminology and scoring |
| `docs/teachers/getting-started.md` | Update | Classroom 50 assignment workflow |
| `docs/teachers/in-the-classroom.md` | Update | Remove broken-autograder/dashboard claims |
| `docs/teachers/creating-exercise-sets.md` | Update | Replace GitHub Classroom pytest setup |
| `docs/teachers/classroom-practices.md` | Update | Submission/results wording |
| `docs/teachers/it-network-requirements.md` | Update | Assignment-management service wording |
| `docs/exercise-agents/exercise-testing.md` | Update | Task markers versus score aggregation |
| `README.md`, `docs/README.md` | Update | Native deployment status and links |
| `.opencode/agents/exercise-test-creator.md` | Update | Remove task-number partial-credit scoring |
| `.opencode/agents/exercise-test-reviewer.md` | Update | Remove GitHub Classroom partial-credit wording |
| `docs/exercise-agents/exercise-generation-cli.md` | Audited, unchanged | No direct native grading/deployment claim |
| `.opencode/agents/agent-orchestrator.md` | Audited, unchanged | No direct native grading/deployment claim |
| `.opencode/agents/docs.md` | Audited, unchanged | No direct native grading/deployment claim |
| `.opencode/agents/testing-specialist.md` | Update | Canonical/native grading contract |
| `.opencode/agents/planner.md` | Update | Flattened-mirror correction |
| `.opencode/agents/exercise-generation.md` | Audit/update | Canonical authoring and generated-surface wording |
| `.opencode/agents/implementer.md` | Audit/update | Derived-surface guidance |
| `.opencode/agents/tidy-code-reviewer.md` | Audit/update | Derived-surface guidance |
| `.opencode/agents/de-sloppifier.md` | Audit/update | Derived-surface guidance |
| `.opencode/agents/exercise-reviewer.md` | Audit/update | Canonical layout guidance |
| `docs/teachers/creating-and-editing-exercises.md` | Audited, unchanged | Contains no direct grading/deployment contract |
| `docs/teachers/pedagogy.md:122,140` | Explicit deferred exception | Legacy `ex004_debug_syntax.ipynb` and `ex005_debug_logic.ipynb` identifiers are outside this grading/pedagogy workstream; do not silently claim the file is clean |
| `exercises/sequence/ex002_sequence_modify_basics/OVERVIEW.md` | Explicit deferred exception | Exercise content is out of scope; this is the only exercise `OVERVIEW.md` found with targeted GitHub Classroom wording |
| All remaining exercise `OVERVIEW.md` files | Audited, unchanged | Repository sweep covered all 16 exercise overview files; no targeted wording was found and no exercise content is changed |
| Unrelated generated platform pages | Audited, unchanged | No native grading contract |

The implementation report must list every deferred exception and the search/test that confirmed it.

## Stage 10 — Synchronise generated template documentation

### Objective

Correct the generated template-repository page and its generator without hand-editing derived output.

### Files and surfaces

- `scripts/sync_construct_template_repos.py`
- `scripts/template_repo_cli/cli.py`
- `tests/test_sync_construct_template_repos.py`
- `docs/teachers/construct-template-repos.md` (generated output)

### Required corrections

- Update the generator wording from GitHub Classroom distribution to Classroom 50 distribution.
- Make the generation timestamp deterministic through an injected/fixed `--generated-at` value; do not call `datetime.now()` implicitly during tests.
- Make owner resolution explicit or mocked so `--dry-run` does not call `gh api user` when `--github-owner` is absent.
- Use `test-owner` only with a temporary `--docs-output-path`; use the real repository owner `h-arnold` for the tracked page.
- Regenerate `docs/teachers/construct-template-repos.md` from the corrected source with `--generated-at 2000-01-01T00:00:00Z`.
- Add or update generator tests for the generated wording, canonical template links, fixed timestamp, and mocked/explicit owner.

### Acceptance criteria

- The generated page and its source agree.
- The generated page contains no stale GitHub Classroom assignment wording.
- Generated output is treated as derived, not as an authoring source.
- Regeneration is deterministic and network-free in the validation command.
- After regeneration, the tracked page is byte-for-byte equal to a fresh fixed-input temporary generation; no unstaged `git diff --exit-code` is used as a pre-commit proof.

### Checks

- Run the focused generator tests.
- Run a network-free temporary-output smoke test twice with identical fixed inputs: `uv run python scripts/sync_construct_template_repos.py --dry-run --verbose --github-owner test-owner --generated-at 2000-01-01T00:00:00Z --docs-output-path /tmp/classroom50-construct-template-repos-a.md` and the same command with `-b.md`.
- Compare the two temporary files with `cmp -s /tmp/classroom50-construct-template-repos-a.md /tmp/classroom50-construct-template-repos-b.md`.
- Regenerate the tracked page with `uv run python scripts/sync_construct_template_repos.py --dry-run --verbose --github-owner h-arnold --generated-at 2000-01-01T00:00:00Z`.
- Generate the comparison copy with `uv run python scripts/sync_construct_template_repos.py --dry-run --verbose --github-owner h-arnold --generated-at 2000-01-01T00:00:00Z --docs-output-path /tmp/classroom50-construct-template-repos-tracked.md`, then compare it using `cmp -s docs/teachers/construct-template-repos.md /tmp/classroom50-construct-template-repos-tracked.md`.
- Inspect `git diff -- docs/teachers/construct-template-repos.md` to confirm that the only tracked change is the intended generated update; do not use unstaged `git diff --exit-code` as a pre-commit assertion.
- `uv run repoman validate --construct selection` and `uv run repoman validate --construct sequence`.

### Review point

Docs agent and reviewer confirm the generator is the source of truth and the generated page was not independently patched.

## Stage 11 — Synchronise teacher-facing workflow documentation

### Objective

Replace stale GitHub Classroom grading instructions and broken-autograder claims with the Classroom 50 bundle workflow.

### Files and surfaces

- `docs/teachers/exercise-generation.md`
- `docs/teachers/how-to-use-the-template-repo-cli.md`
- `docs/teachers/understanding-the-tools.md`
- `docs/teachers/getting-started.md`
- `docs/teachers/in-the-classroom.md`
- `docs/teachers/creating-exercise-sets.md`
- `docs/teachers/classroom-practices.md`
- `docs/teachers/it-network-requirements.md`
- `README.md`
- `docs/README.md`

### Required corrections

- Replace the GitHub Classroom pytest setup in the teacher assignment walkthrough with the Classroom 50 bundle workflow.
- Remove the broken-autograder note and old Classroom dashboard wording.
- Remove task-number partial-credit/plugin scoring language; task markers remain test metadata only.
- Replace stale GitHub Classroom platform labels in the directly affected teacher guides.
- Correct `docs/teachers/it-network-requirements.md` where it identifies the assignment-management service.
- Do not edit exercise notebooks, metadata, or teaching-order files.

### Acceptance criteria

- Directly affected teacher documents describe the native bundle, Pages, Release, and collection flow.
- No directly affected teacher document tells users to use the old reporter, task-number scoring, broken autograder, or GitHub Classroom pytest setup.
- Documentation-contract tests and link checks pass.

### Checks

- Search for `GitHub Classroom`, `GitHub Classroom friendly`, `taskno` partial-credit wording, broken-autograder claims, old dashboard wording, and the two legacy notebook identifiers.
- Documentation-contract tests.
- `tests/test_classroom50_docs_contract.py` searches the teacher surfaces and records explicit deferred exceptions.
- Link/reference validation.

### Review point

Docs agent and reviewer confirm native/legacy instructions are not mixed.

## Stage 12 — Synchronise agent and canonical-layout guidance

### Objective

Align repository agents with the canonical-only layout and the one-point-per-case scoring model.

### Files and surfaces

- `.opencode/agents/exercise-test-creator.md`
- `.opencode/agents/exercise-test-reviewer.md`
- `.opencode/agents/testing-specialist.md`
- `.opencode/agents/planner.md`
- `.opencode/agents/exercise-generation.md`
- `.opencode/agents/implementer.md`
- `.opencode/agents/tidy-code-reviewer.md`
- `.opencode/agents/de-sloppifier.md`
- `.opencode/agents/exercise-reviewer.md`
- `docs/exercise-agents/exercise-testing.md`
- `docs/exercise-agents/exercise-generation-cli.md`
- `.opencode/agents/agent-orchestrator.md`
- `.opencode/agents/docs.md`

### Required corrections

- Remove GitHub Classroom task-number partial-credit guidance; task markers are test metadata, not Classroom 50 score aggregation.
- Correct flattened/compatibility wording that conflicts with the canonical-only contract.
- Preserve the rule that exercise content and metadata are not changed by this tooling work.
- Record exercise-specific `OVERVIEW.md` wording as an explicit deferred exception because exercise changes are out of scope.

### Acceptance criteria

- Agent guidance does not author flattened surfaces or describe task-number scoring as native Classroom 50 scoring.
- Canonical exercise-local authoring and derived packaging surfaces are clearly distinguished.
- The deferred exercise `OVERVIEW.md` exception is recorded in the implementation report.

### Checks

- Search agent files for `taskno` partial-credit and flattened-authoring language.
- `tests/test_classroom50_docs_contract.py` covers the agent surfaces and exception record.
- Agent documentation review.
- Confirm all 16 exercise `OVERVIEW.md` files were swept; only the explicitly recorded ex002 exception may retain targeted wording.

### Review point

Docs agent and reviewer confirm agent guidance is consistent with `AGENTS.md` and `SPEC.md`.

## Stage 13 — Final review and handoff

### Objective

Remove unnecessary complexity and verify the complete contract before implementation handoff.

### Files and surfaces

- Final diff across all touched files.
- `SPEC.md`, `WORKFLOW_SPEC.md`, and `ACTION_PLAN.md`.

### Acceptance criteria

- No legacy compatibility path remains.
- No generated bundle, dependency target, or Classroom 50 config repository is committed.
- No forbidden grading surface enters the student template.
- No exercise or teaching-order file changed, except any explicitly recorded deferred documentation exception.
- All required tests and quality gates pass.

### Checks

- Inspect `git status` and `git diff`.
- Run targeted and full validation.
- Confirm student failures are expected and solution failures are absent.
- Confirm no secrets, solutions, or confidential data appear in fixtures or docs.
- Confirm all generated pages were regenerated from source.
- Confirm deferred documentation surfaces were audited.

### Review point

Tidy Code Reviewer and De-Sloppification pass. Record deviations, unresolved manual deployment work, and the next implementation agent.

## Suggested implementation order

1. Stage 1 — red native result/identity tests.
2. Stage 2 — autograder modes and teardown-aware result construction.
3. Stage 3 — lock-derived dependency bootstrap and atomic target contract-file emission.
4. Stage 4 — pytest trust boundary.
5. Stage 5 — canonical hidden-test manifest and selection hardening.
6. Stage 6 — builder filesystem/archive safety.
7. Stage 7 — pinned native-runner contract check.
8. Stage 8 — integration and regression.
9. Stage 9 — developer/contract documentation.
10. Stage 10 — generated template documentation.
11. Stage 11 — teacher-facing documentation.
12. Stage 12 — agent and canonical-layout guidance.
13. Stage 13 — final review and handoff.

## Implementation handoff

The next implementation owner is the Implementer agent. Its first prompt must require it to read `SPEC.md`, `WORKFLOW_SPEC.md`, this plan, the mandatory repository contracts, and the pinned Classroom 50 source reference; then implement Stage 1 before production changes. Every delegated handoff must report explicit files read and verification results.
