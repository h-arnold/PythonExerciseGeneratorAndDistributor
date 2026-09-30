# SPEC — Reusable Classroom 50 Grading Bundle

## Status

- Draft v3, 29 September 2026.
- This specification replaces the "Native Classroom 50 Bundle Autograder
  Integration" draft and the work already implemented against it. The grading
  manifest, fresh-target dependency bootstrap, pytest trust boundary, pinned
  upstream snapshot, and assignment-schema test matrix from that draft are
  withdrawn and their code reverted.
- The plan concerns the generic teacher-side bundle only. It does not change
  exercises, notebooks, tests, or teaching order.

## Purpose

Provide one reusable, assignment-independent pytest grading bundle that a
teacher can hand to Classroom 50, plus a local dry run that confirms a full
pass before the bundle is ever deployed.

The workflow must:

- build a bundle from a selected exercise set;
- grade a student checkout using the bundle's own hidden test copies;
- run unchanged inside Classroom 50, which invokes `autograder.py` with no
  arguments from the student checkout and reads `./result.json`;
- write a `classroom50/result/v1` document Classroom 50 accepts;
- support an explicit local dry run of the solution variant.

The workflow is not intended to:

- modify the upstream `foundation50/classroom50` repository;
- administer classrooms, rosters, assignments, or score collection;
- add a GUI or a `gh teacher` upload command;
- perform a live Classroom 50 pilot;
- change exercise content, notebook tagging, or pedagogical sequencing.

## Current state

The bundle builder and grader already implement the core of this specification
and are unchanged by it:

- `scripts/build_classroom50_bundle.py` takes `--source-root`,
  `--exercise-set`, `--runtime-source`, and `--output`. For each selected
  exercise it copies the hidden test modules and exercise-local support files
  into `<output>/exercises/<construct>/<exercise_key>/tests/`, regenerates
  `exercise_runtime_support/`, and copies `autograder.py` to the bundle root.
  Notebooks, solutions, metadata, and teacher notes are never copied.
- `scripts/autograder.py` requires `--student-root` and `--result`, forces the
  `PYTUTOR_ACTIVE_VARIANT` value, collects the bundle's hidden tests only, and
  writes a result document with one point per passing case.

Three gaps keep the bundle from running as-is in Classroom 50:

1. **Invocation.** Classroom 50 runs the child with no arguments and reads
   `./result.json` from the student checkout. The current grader requires two
   command-line options and lets the caller choose the result path.
2. **Dependencies.** Classroom 50's grading interpreter does not ship this
   runtime's test dependencies. The grader must install what it needs before
   importing pytest, in the same way Classroom 50's own documented pytest
   template does with `pip install`.
3. **Result shape.** The result document uses the superseded `version` and
   per-test `name` field names, which the current `classroom50/result/v1`
   schema does not accept.

## Agreed decisions

1. The bundle is a per-assignment `autograder.py` override, so the assignment
   keeps `autograder: "default"` and carries no declarative `tests` block.
2. The builder stays assignment-agnostic. Classroom and assignment slugs are
   not builder inputs; the teacher places the built directory at
   `<classroom>/autograders/<assignment>/` in the Classroom 50 repository.
3. The grader has two invocation modes: no arguments (Classroom 50 mode) and
   the explicit `--student-root`/`--result` pair (local dry run). The pair is
   required as a pair; supplying one alone is a usage error.
4. Classroom 50 mode reads its identity from the documented environment
   variables and writes `./result.json` in the current working directory.
5. Local mode keeps explicit roots and result paths and emits clearly
   non-uploadable local identity values.
6. The result document uses the canonical `classroom50/result/v1` field names.
7. Classroom 50 mode installs the grading dependencies with `pip` before
   importing pytest, and installs nothing in local mode.
8. Test discovery stays rooted in the built bundle. That is the functional
   boundary between grading tests and the student-visible self-check copies.
9. One point per passing pytest case, with each case named
   `<exercise_key>::<leaf-nodeid>`.
10. A completed run exits zero whether cases pass or fail; a run that cannot
    grade exits non-zero and writes no result.
11. Deployment remains a manual commit into the Classroom 50 repository.

## Invocation and result contract

### Classroom 50 mode

Classroom 50 starts the child from the student checkout, so:

- the current working directory is the student root;
- the bundle root is the grader script's own parent directory, which is where
  Classroom 50 extracts the assignment bundle and where its sibling files
  live;
- the result is `./result.json`;
- the active notebook variant is forced to `student`.

The grader reads `CLASSROOM`, `ASSIGNMENT`, `ASSIGNMENT_TYPE`,
`SUBMISSION_TAG`, `COMMIT_URL`, `RELEASE_URL`, and `OWNER` (falling back to
`USERNAME`). `REVIEW_URL` is optional and falls back to `COMMIT_URL`. It
ignores unrelated runner variables. A missing required value or unsupported
assignment type is a grading failure that writes no result rather than a
vacuous pass.

### Local mode

With `--student-root` and `--result`, the grader grades that checkout and
writes to that path. `--variant solution` forces the solution notebook variant
for a dry run; the default forces `student`.

The local result uses these exact non-uploadable identity values:

- `classroom = "local"`;
- `assignment = "local"`;
- `assignment_type = "individual"`;
- `owner = "local"`;
- `submission = "submit/local"`;
- `commit`, `release`, and `review` are `local://` values.

A local result is a dry-run artefact. It is never evidence of Classroom 50
identity or collected scores.

### Result document

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

`score` and `max-score` are the sums over the case rows. A case whose call
phase passes but whose teardown fails is recorded as failed, because a teardown
failure is a real failure of that case.

Classroom 50's runner re-stamps `owner`, `assignment_type`, `datetime`,
`graded_at`, and `submitted_by` with its own authoritative values before
validating the document, so the grader only needs to fill them in well enough
to validate.

## Dependency handling

Classroom 50 mode installs the grading dependencies with
`sys.executable -m pip install` before importing pytest, following the pattern
in Classroom 50's own documented pytest autograder template. Local mode installs
nothing and uses the developer's environment.

The runtime's test dependencies are pytest and `tabulate`, which
`exercise_runtime_support/exercise_framework/reporting.py` imports directly.
The exact package set is an implementation decision recorded in
`ACTION_PLAN.md`, not a contract this specification pins.

## Builder contract

The builder takes the existing inputs: `--source-root`, `--exercise-set`,
`--runtime-source`, and `--output`, where `--output` is a bundle directory.
It writes:

```text
<output>/
├── autograder.py
├── exercise_runtime_support/
└── exercises/<construct>/<exercise_key>/tests/
```

For each selected exercise it copies the canonical hidden test module and the
exercise-local Python support files that module needs. Notebooks, solutions,
`exercise.json`, teacher notes, caches, and unrelated files are never copied.

The teacher then places this directory at
`<classroom>/autograders/<assignment>/` in the Classroom 50 repository and
commits it. Classroom 50's publish workflow materialises the per-assignment
archive from there; the builder neither creates nor commits an archive.

Classroom 50 caps a fetched bundle at 10 MiB and its grade job at 15 minutes.
These are operational limits to keep in mind when selecting exercises for one
assignment, not checks this builder performs.

## Constraints and invariants

- Preserve the canonical exercise-local layout under
  `exercises/<construct>/<exercise_key>/`.
- Preserve canonical exported notebook and test paths; flattened mirrors remain
  forbidden.
- Preserve one point per passing case and the `<exercise_key>::<leaf-nodeid>`
  naming rule.
- Preserve the student/solution variant contract.
- Preserve bundle-first runtime imports and student-checkout metadata
  resolution.
- Keep both scripts generic: no construct- or exercise-specific grading branch.
- Templates ship starter code only. Grading sources and hidden tests must
  never enter a student checkout or an exported template.
- Repository tests stay deterministic, fast, and offline.

## Non-goals

This work explicitly does not add:

- a grading manifest or any second wire format for the selected tests;
- a fresh-install target with package-origin or version verification;
- hostile-environment, plugin-autoload, or student-tampering defences;
- a vendored, checksum-pinned snapshot of upstream Classroom 50 sources;
- a Classroom 50 assignment-manifest schema test matrix;
- an archive simulation or builder filesystem threat model;
- a repository-wide documentation campaign.

## Evidence

- `scripts/autograder.py` — mandatory `--student-root`/`--result`, module-scope
  `import pytest`, teardown reports discarded, `version`/`name` payload, caller
  selected result path.
- `scripts/build_classroom50_bundle.py` — current inputs, hidden-test copying,
  and bundle output layout.
- `exercise_runtime_support/exercise_framework/reporting.py:9` — `tabulate` is
  imported directly by the runtime package.
- `tests/test_classroom50_bundle_stage4.py` — current builder and grader
  contract tests.
- `docs/developers/classroom50-autograder.md` — current generic grading
  contract and CLI interfaces.
- Classroom 50 wiki, *Advanced Autograding*, and commit
  `43ec1444f87674cd3276e66eadb6439dc0c97668`: no-argument child invocation, the
  student checkout as working directory, `./result.json` as the result, the
  supplied environment variables, the `classroom50/result/v1` field set, and
  the pip-based pytest autograder template.

## Acceptance criteria

1. A no-argument run in a student checkout writes a `classroom50/result/v1`
   document to `./result.json` and exits zero when cases pass and when cases
   fail.
2. Missing required environment or an unsupported assignment type fails
   clearly, writes no result, and exits non-zero.
3. The local dry run still accepts `--student-root`/`--result` as a pair,
   still supports `--variant solution`, and emits the documented local identity
   values.
4. Result rows use `test-name` and `passed`; no `version` or `name` fields
   remain.
5. A teardown failure cannot receive a passing score.
6. Grading collects only the bundle's hidden test copies, and runtime imports
   resolve to the bundle copy while `exercise_metadata` resolves to the student
   checkout.
7. The grader installs its test dependencies in Classroom 50 mode and installs
   nothing in local mode.
8. The builder emits only the documented bundle contents for the selected
   exercises.
9. A build-then-local-dry-run cycle passes for a real exercise set without any
   network access in the repository test suite.
10. Directly affected developer documentation matches this specification.

## Open questions and risks

- Installing dependencies on the grading interpreter costs startup time on
  every submission. Pinning exact versions is a reasonable later refinement if
  unpinned resolution proves unreliable.
- Classroom 50's contract may advance beyond commit `43ec1444`; recheck before
  the first live deployment.
- Committing the bundle into the Classroom 50 repository remains a manual step.
- No live pilot is included, so the local dry run is the only pre-deployment
  check available here.
