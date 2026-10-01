# Classroom 50 Autograder — Generic Grading Contract (Selection Pilot)

This document records the generic scoring rules behind the Classroom 50 grading
system and the command interfaces of its two generic sources: the bundle
builder (`scripts/build_classroom50_bundle.py`) and the bundle grader
(`scripts/autograder.py`). The Selection pilot exercise set is the first input
and the end-to-end validation fixture; it is not a special code path.

Authoritative sources for this contract are the developer documentation itself:
the execution and variant contract in [execution-model.md](execution-model.md) and
the deployment workflow below, reviewed against the Classroom 50
`Advanced-Autograding` result contract. The test surface that keeps this document
aligned is in [testing-framework.md](testing-framework.md). No Classroom 50 classroom creation
or management functionality is built here; classroom operation (assignment
registration, the bundle commit, roster, accept, submit, Collect) stays a manual
teacher follow-up.

There is no OrderOfTeaching.md change in this round.

## Selection pilot set

Selection is a builder configuration and validation fixture, not a special
grader. The same generic `autograder.py` source grades every assignment and the
same builder source creates each assignment bundle from a selected exercise-set
input; the Selection set below is the pilot fixture proving the generic
mechanism works. The grader discovers bundled tests dynamically at grade time
with no hardcoded exercise keys, weights, or construct names.

Titles are read-only references recorded from the canonical selection
`exercise.json` sources (not edited):

| Exercise key | Title | Collected cases |
| --- | --- | --- |
| `ex001_selection_modify_basics` | Selection Modify Basics | 33 |
| `ex002_selection_debug_if_then_else` | Selection Debug If Then Else | 60 |
| `ex003_selection_modify_elif_boundaries` | Selection Modify: Elif Chains, Boundaries and Constants | 60 |
| `ex004_selection_modify_logical_operators` | Selection Modify Logical Operators | 71 |

Full-pass total: 224 cases, computed as the sum of the collected per-exercise
counts.

Counts are collected case totals from pytest collection (including parametrize
expansion), verified with `pytest --collect-only`. The full-pass total and
max-score are sum-derived from those collected counts, computed not hardcoded: a
full pass over the Selection pilot sums to the recorded total.

## Two invocation modes

The grader has exactly two invocation modes: Classroom 50 mode, which takes no
arguments, and the local dry run, which takes an explicit option pair. Both
modes grade the same bundle and write the same result schema; they differ only
in where the roots come from and where the identity values come from.

### Classroom 50 mode (no arguments)

Classroom 50 starts the child in the student checkout, so:

- the current working directory is the student root;
- the bundle root is the grader script's own parent directory, which is where
  Classroom 50 extracts the assignment bundle and where the bundle's sibling
  files live;
- the result is `./result.json` in the working directory, that is, inside the
  student checkout and not in the bundle;
- the graded notebook variant is forced to `student`, whatever value the
  environment already carries.

The identity fields of the result are read from the runner environment:

| Result field | Runner variable |
| --- | --- |
| `classroom` | `CLASSROOM` |
| `assignment` | `ASSIGNMENT` |
| `assignment_type` | `ASSIGNMENT_TYPE` |
| `owner` | `OWNER`, falling back to `USERNAME` when `OWNER` is unset |
| `submission` | `SUBMISSION_TAG` |
| `commit` | `COMMIT_URL` |
| `release` | `RELEASE_URL` |
| `review` | `REVIEW_URL`, falling back to `COMMIT_URL` when `REVIEW_URL` is unset |

`CLASSROOM`, `ASSIGNMENT`, `ASSIGNMENT_TYPE`, `SUBMISSION_TAG`, `COMMIT_URL`, and
`RELEASE_URL` are required, an owner identity must come from either `OWNER` or
`USERNAME`, and `ASSIGNMENT_TYPE` must be `individual`, `group`, or `team`.
Unrelated runner variables are ignored.

Classroom 50 mode installs the grading dependencies into the grading interpreter
with `sys.executable -m pip install pytest tabulate`, because that interpreter
does not ship this runtime's test dependencies, and the install always completes
before pytest is imported.

A missing required value, an unsupported assignment type, and a failed
dependency install are all grading failures: the run names the missing or
invalid value on stderr, exits non-zero, and writes no result.

### Local mode (the dry run)

- The two local options are required as a pair. Supplying `--student-root` or
  `--result` on its own is a usage error, so no result is written.
- `--student-root` is the checkout whose notebooks and `exercise_metadata/` are
  graded, and `--result` is the `classroom50/result/v1` JSON destination.
- `--variant solution` forces the solution notebook variant for the dry run
  that confirms a full pass before deployment. The option applies to the local
  dry run only, Classroom 50 mode ignores it, and the local default is the
  student variant, so `--variant` is only ever needed to force `solution`.

A local result carries these exact identity values:

| Result field | Local value |
| --- | --- |
| `classroom` | `local` |
| `assignment` | `local` |
| `assignment_type` | `individual` |
| `owner` | `local` |
| `submission` | `submit/local` |
| `commit` | `local://commit` |
| `release` | `local://release` |
| `review` | `local://review` |

The local dry run installs nothing: it runs in the developer's own environment,
where the grading dependencies are already present, and `pip` is never invoked.
These identity values are deliberately non-uploadable, so a local result is a
dry-run artefact and is never evidence of Classroom 50 identity or collected
scores.

## Scoring rule

There is one point per passing pytest case.

Each passing leaf case contributes one point. Exercise size therefore acts as
the difficulty proxy. There is no weighting beyond one point per case and no
declarative-tests route.

## Per-test naming rule

Per-test result names use the form `<exercise_key>::<leaf-nodeid>`.

The leaf portion is the leaf `test_*.py::test_name` portion of the pytest node
id, with no absolute paths in names.

## Variant rule

The graded run forces the student variant with `PYTUTOR_ACTIVE_VARIANT=student`.

The student variant is the only graded surface. The solution variant is
reserved for the dry run used to confirm a full pass locally.

## Assignment slug

The assignment slug remains an operator input at bundle use time, not stored in
this repository.

## `classroom50/result/v1` result behaviour

The run writes its result document — `./result.json` in Classroom 50 mode, the
`--result` path in local mode — satisfying the `classroom50/result/v1` contract
cited by `Advanced-Autograding`. The envelope carries the identity fields of
the mode, plus:

| Key | Value |
| --- | --- |
| `schema` | The constant `classroom50/result/v1`. |
| `datetime` | The UTC timestamp of the run, as `YYYY-MM-DDTHH:MM:SSZ`. |
| `tests` | One row per collected leaf case, in collection order. |

Each row in `tests` carries the canonical `test-name`, `passed`, `score`, and
`max-score` keys, with `max-score` fixed at `1` for every case because one point
per case is the only weighting. The superseded `version` and `name` keys are
gone: the version travels in `schema`, and a case is named by `test-name`.

- `score` is the sum of the awarded `score` values of the case rows.
- `max-score` is the count of case rows, that is, the total of the collected
  leaf cases.

A case whose call phase passes but whose teardown fails is recorded as failed,
because a teardown failure is a real failure of that case, so it scores
nothing.

Identity fields are stamped authoritatively by the runner downstream, so the
grader only has to fill them in well enough to validate. Exit 0 means the run
completed, with pass or fail carried in the payload; a non-zero exit is reserved
for infrastructure error. Concretely, a completed pytest run (exit 0 or 1)
writes the payload and exits 0; any other pytest exit, or an empty discovery
set, exits non-zero and writes no result. Any pre-existing result output is
removed before the grading attempt, so a stale result file can never survive a
failure and be misread as a grade.

## Generic builder and grader boundaries

- The grader discovery root is the bundle hidden test directories only, never
  the student checkout `exercises/.../tests/` copies, so visible self-check
  copies are never double-counted.
- The builder supplies per-exercise subdirectories; the grader supplies the
  mechanism.
- Bundle contents are the generic `autograder.py`, per-exercise hidden copies
  (`test_*.py`, `expectations.py`, `student_checker_support.py`) under
  `<bundle>/exercises/<construct>/<exercise_key>/tests/`, and runtime copies
  of `exercise_runtime_support/` at `<bundle>/exercise_runtime_support/` with
  `exercise_metadata/` resolved from the student checkout.
- The bundle-local `exercise_runtime_support/` copy is regenerated from source
  at every build and must be rebuilt whenever the source package changes.
- Hidden is tamper-proof, not secret: no solutions or confidential data go
  into the bundle, since the published bundle is fetchable.

## Command interfaces

Both sources are generic: the selected exercise set is builder input, so no
per-construct or per-exercise grading logic is hardcoded. Neither script is
packaged into a student template.

Build the teacher-side bundle from a JSON exercise set:

```bash
uv run python scripts/build_classroom50_bundle.py \
  --source-root . \
  --exercise-set path/to/exercise-set.json \
  --runtime-source exercise_runtime_support \
  --output path/to/grading-bundle
```

The exercise set is a JSON list of `{"construct": ..., "exercise_key": ...}`
records. For each record the builder copies the exercise's hidden `test_*.py`
modules, `expectations.py`, `student_checker_support.py`, and any further
support module referenced through `load_exercise_test_module` (resolved
transitively) into `<bundle>/exercises/<construct>/<exercise_key>/tests/`. It
regenerates `<bundle>/exercise_runtime_support/` from `--runtime-source` and
copies `scripts/autograder.py` to the bundle root. Notebooks, solutions,
`exercise.json`, teacher notes, and unrelated files are never copied. The
bundle-local runtime copy is regenerated on every build, so a source-package
change must be followed by a rebuild.

Grade with the bundle's own copy of the grader. The local dry run passes the
option pair; Classroom 50 passes no arguments at all and starts the child from
the student checkout:

```bash
# Local dry run: confirm a full pass before deployment
uv run python path/to/grading-bundle/autograder.py \
  --student-root path/to/student-checkout \
  --result path/to/result.json \
  --variant solution

# Classroom 50 mode: the runner invokes the bundle copy with no arguments,
# from the student checkout, and reads ./result.json from there
python path/to/grading-bundle/autograder.py
```

> **⚠️ Important:** a manual no-argument run is the Classroom 50 code path, so
> it installs `pytest` and `tabulate` into the interpreter that launches it. Use
> the local dry run form above for any pre-deployment check.

The grader prepends the bundle root to `sys.path` and places the student
checkout directly behind it, so `exercise_runtime_support` resolves to the
bundle copy while `exercise_metadata` resolves to the student checkout. It
verifies those package origins before grading and refuses to run if they do not
match.

## Deployment: build, place, commit

Deployment stays a manual teacher step. The built bundle is a per-assignment
`autograder.py` override: build the bundle, place it at
`<classroom>/autograders/<assignment>/` in the Classroom 50 repository, and
commit it. Classroom 50's publish workflow materialises the per-assignment
archive from that directory, so neither script uploads anything.

1. Build the bundle from the selected exercise set with
   `scripts/build_classroom50_bundle.py`.
2. Place the built directory at `<classroom>/autograders/<assignment>/` in the
   Classroom 50 repository.
3. Commit that directory.

The assignment itself is unchanged: it keeps `autograder: "default"`, uses
autograded grading mode, and carries no declarative `tests` block, because the
placed bundle supplies the autograder. Classroom and assignment slugs are
teacher inputs, not builder inputs.

> **💡 Tip:** the bundle is fetched afresh on every grading run, so a committed
> bundle update needs no student-repository change.

## Out of scope

No classroom scaffolding, roster management, assignment registration,
`assignments.json` writing, score collection, submission download, token
handling, or web/CLI classroom automation is built here. No live pilot
operation, notebook content change, tagged-cell change, pedagogical change,
exercise-type metadata change, or sequence rollout is included.
