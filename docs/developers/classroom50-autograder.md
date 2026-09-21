# Classroom 50 Autograder — Generic Grading Contract (Selection Pilot)

Stage 3 written contract. This document records the generic scoring rules that
the grader and builder must implement, using the Selection pilot exercise set
as the first input. No code is built here.

Authoritative sources for this contract are `SPEC.md` (scoring rule and
`classroom50/result/v1` behaviour) and `ACTION_PLAN.md` Stage 3 acceptance,
reviewed against the Classroom 50 `Advanced-Autograding` result contract. No
Classroom 50 classroom creation or management functionality is built in this
round; classroom operation stays a manual teacher follow-up.

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

## Out of scope

No classroom scaffolding, roster management, assignment registration,
`assignments.json` writing, score collection, submission download, token
handling, or web/CLI classroom automation is built here. No live pilot
operation, notebook content change, tagged-cell change, pedagogical change,
exercise-type metadata change, or sequence rollout is included.
