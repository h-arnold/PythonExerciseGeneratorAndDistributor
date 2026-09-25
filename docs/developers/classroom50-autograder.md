# Classroom 50 Autograder — Generic Grading Contract (Selection Pilot)

This document records the generic scoring rules behind the Classroom 50 grading
system and the command interfaces of its two generic sources: the bundle
builder (`scripts/build_classroom50_bundle.py`) and the bundle grader
(`scripts/autograder.py`). The Selection pilot exercise set is the first input
and the end-to-end validation fixture; it is not a special code path.

Authoritative sources for this contract are `SPEC.md` (scoring rule and
`classroom50/result/v1` behaviour) and `ACTION_PLAN.md`, reviewed against the
Classroom 50 `Advanced-Autograding` result contract. No Classroom 50 classroom
creation or management functionality is built here; classroom operation
(assignment registration, bundle commit, roster, accept, submit, Collect) stays
a manual teacher follow-up.

There is no OrderOfTeaching.md change in this round.

## Selection pilot set

Selection is a builder configuration and validation fixture, not a special grader.
The same generic `autograder.py` source grades every assignment and the same
builder source creates each assignment bundle from a selected exercise-set
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

Full-pass total: 224 cases, computed as the sum of the collected per-exercise counts.

Counts are collected case totals from pytest collection (including parametrize
expansion), verified with `pytest --collect-only`. The full-pass total and
max-score are sum-derived from those collected counts, computed not hardcoded:
a full pass over the Selection pilot sums to the recorded total.

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

The assignment slug remains an operator input at bundle use time, not stored in this repository.

## `classroom50/result/v1` result behaviour

The bundle run writes `result.json` satisfying the `classroom50/result/v1`
contract cited by `Advanced-Autograding`. As stated in the written contract:

- Identity fields are stamped authoritatively by the runner downstream.
- Exit 0 means the run completed; pass or fail is carried in the payload.
- A non-zero exit is reserved for infrastructure error.

No per-construct or per-exercise grading logic is added to satisfy this shape;
the Selection pilot only fixes the expected full-pass sum above.

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

Grade a student checkout with the bundle's own copy of the grader:

```bash
uv run python path/to/grading-bundle/autograder.py \
  --student-root path/to/student-checkout \
  --result path/to/result.json
```

- `--student-root` is the checkout whose notebooks and `exercise_metadata/` are
  graded.
- `--result` is the `classroom50/result/v1` JSON destination.
- `--variant solution` forces the solution notebook variant for the local dry
  run only; the default graded run forces the student variant with
  `PYTUTOR_ACTIVE_VARIANT=student`.

The grader prepends the bundle root to `sys.path` and places the student
checkout directly behind it, so `exercise_runtime_support` resolves to the
bundle copy while `exercise_metadata` resolves to the student checkout. It
verifies those package origins before grading and refuses to run if they do not
match. A completed pytest run (exit 0 or 1) writes the payload and exits 0 with
pass/fail carried inside it; any other pytest exit, or an empty discovery set,
is an infrastructure error that exits non-zero and writes no result. Any
pre-existing result output is removed before the grading attempt.

## Out of scope

No classroom scaffolding, roster management, assignment registration,
`assignments.json` writing, score collection, submission download, token
handling, or web/CLI classroom automation is built here. No live pilot
operation, notebook content change, tagged-cell change, pedagogical change,
exercise-type metadata change, or sequence rollout is included.
