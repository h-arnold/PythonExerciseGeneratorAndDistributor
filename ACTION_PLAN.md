# ACTION_PLAN — Reusable Classroom 50 Grading Bundle

This plan implements `SPEC.md`: one reusable, assignment-independent pytest
grading bundle that Classroom 50 can run, plus a local dry run.

The earlier thirteen-stage plan and its progress tracker are withdrawn. The
grading manifest, fresh-target dependency bootstrap, pytest trust boundary,
pinned upstream snapshot, and assignment-schema test matrix are out of scope,
and the code committed against them has been reverted to the state before that
implementation began.

## Read-first context

- `AGENTS.md`
- `SPEC.md`
- `WORKFLOW_SPEC.md`
- `docs/developers/execution-model.md`
- `docs/developers/classroom50-autograder.md`
- `scripts/autograder.py`
- `scripts/build_classroom50_bundle.py`
- `tests/test_classroom50_bundle_stage4.py`

Every delegated handoff must list the files it read.

## Scope

- Add a no-argument Classroom 50 invocation mode to the grader.
- Emit the canonical `classroom50/result/v1` field names.
- Install the grading dependencies in Classroom 50 mode only.
- Update the affected tests and documentation.

## Out of scope

- Anything under `foundation50/classroom50`.
- Classroom, roster, assignment, or score-collection automation.
- A `gh teacher` bundle-upload command or any GUI.
- Live GitHub Pages, submission, Release, or Collect operations.
- Exercise content, notebooks, tagged cells, metadata, or teaching order.
- The withdrawn manifest, bootstrap, trust-boundary, upstream-snapshot, and
  assignment-schema work.

## Product constraints

- Preserve `exercises/<construct>/<exercise_key>/` as the only canonical
  exercise layout, and the canonical exported notebook and test paths.
- Preserve one point per passing case and `<exercise_key>::<leaf-nodeid>` names.
- Preserve the student/solution variant contract.
- Preserve bundle-first runtime imports and student-checkout metadata
  resolution.
- Keep the builder and grader generic: no construct- or exercise-specific
  branch.
- Templates ship starter code only.
- Fail clearly, and write no result, when a run cannot grade.
- Keep repository tests deterministic, fast, and offline.

## TDD and quality gates

Each stage follows red → green → refactor.

1. Add failing tests for the stage acceptance criteria.
2. Implement the smallest coherent change.
3. Refactor only with the stage tests green.
4. Run the stage checks and record the result.

Repository-wide gates:

- `uv run pytest tests/test_classroom50_bundle_stage4.py -q`
- `uv run pytest --collect-only -q`
- `uv run pytest -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- expected student-variant check: `! uv run python scripts/run_pytest_variant.py --variant student -q` (the command must fail)
- `uv run repoman validate --construct selection`
- `uv run repoman validate --construct sequence`
- `uv run ruff check .`

No repository test may reach the network.

## Stage 1 — Add the Classroom 50 invocation mode and result shape

### Objective

Let the grader run with no arguments from a student checkout and write the
result document Classroom 50 reads.

### Files and surfaces

- `scripts/autograder.py`
- `tests/test_classroom50_bundle_stage4.py`

### Required behaviour

- Make `--student-root` and `--result` optional, but required as a pair;
  supplying one alone is a usage error.
- With no arguments: the current working directory is the student root, the
  script's parent is the bundle root, and the result is `result.json` in the
  current directory.
- With no arguments, read the identity from the documented environment and
  fail clearly when a required variable is missing or the assignment type is
  unsupported.
- Support `individual`, `group`, and `team` assignment types.
- Keep the local identity values and the local dry run unchanged.
- Force the `student` variant in Classroom 50 mode; keep `--variant solution`
  for the local dry run only.
- Emit `schema`, `test-name`, and `passed`; remove the `version` and `name`
  aliases.
- Record a teardown failure as a failed case.
- Retain the existing pre-grading result invalidation so a failed run cannot
  leave a stale grade behind.
- Install `pytest` and `tabulate` with `sys.executable -m pip` in Classroom 50
  mode only, before importing pytest. Do not install anything in local mode.
  A failed install exits non-zero and writes no result.

### Acceptance criteria

- A no-argument run against a staged bundle writes `result.json` in the
  student checkout with the canonical fields and exits zero.
- The same fixture with missing environment exits non-zero and writes no
  result.
- The existing local dry-run tests still pass, including the solution variant.
- The grader imports pytest only after any Classroom 50 mode install.
- A build-then-local-solution-dry-run with a real exercise set passes; the
  student run completes with expected failures and exit zero. Both variants
  retain the same case names and maxima.
- The built bundle contains only the selected tests and their support files;
  runtime imports remain bundle-first and metadata resolves from the checkout.

### Checks

- Targeted tests for both modes.
- Offline test of the install boundary: the local dry runs must never install,
  and the Classroom 50 mode install must be replaceable by a test double.
- One real exercise-set build and local dry run, with no live Classroom 50
  operations or network access.
- Ruff.

### Review point

Tidy Code Reviewer reviews mode separation, result construction, and the
install boundary. Testing Specialist confirms the build-and-grade check.

## Stage 2 — Update the directly affected documentation

### Objective

Make the developer documentation describe the two invocation modes, the result
contract, and the teacher workflow, with no stale wording.

### Files and surfaces

- `docs/developers/classroom50-autograder.md` (update).
- `AGENTS.md`, `docs/developers/execution-model.md`,
  `docs/developers/development.md`, `docs/developers/project-structure.md`
  (check for incorrect wording; edit only if necessary).

### Required corrections

- Document the no-argument Classroom 50 invocation, its environment, and
  `./result.json`.
- Document the local dry run and the local identity values.
- Document the result schema and the one-point-per-case rule.
- Document the build → place at `<classroom>/autograders/<assignment>/` →
  commit workflow, and that the assignment keeps `autograder: "default"`.
- Do not add descriptions of the withdrawn manifest, bootstrap, or trust
  boundary.

### Acceptance criteria

- The updated guide agrees with `SPEC.md` and `WORKFLOW_SPEC.md`.
- No directly affected guide describes a withdrawn requirement or the
  superseded result shape.

### Checks

- Search for stale result fields and withdrawn feature names.
- Link and reference validation.

### Review point

Docs agent and reviewer confirm terminology and British English.

## Stage 3 — Final review and handoff

### Objective

Remove unnecessary complexity and confirm the contract before handoff.

### Files and surfaces

- The final diff across all touched files.
- `SPEC.md`, `WORKFLOW_SPEC.md`, and `ACTION_PLAN.md`.

### Acceptance criteria

- No withdrawn requirement survives in code or documentation.
- No generated bundle, install target, or Classroom 50 configuration is
  committed.
- No grading surface enters a student template.
- No exercise or teaching-order file changed.
- All quality gates pass.

### Checks

- Inspect `git status` and `git diff`.
- Run the full validation set.
- Confirm student failures are expected and solution failures are absent.

### Review point

Tidy Code Reviewer and De-Sloppification pass. Record the remaining manual
deployment step and the next implementation owner.

## Implementation order

1. Stage 1 — Classroom 50 invocation mode, result shape, dependency install.
2. Stage 2 — directly affected documentation.
3. Stage 3 — final review and handoff.

## Delivery tracker

Current section: Stage 1. Current phase: checks and commit/push in progress.

| Stage | Red tests added | Red review clean | Green implementation complete | Green review clean | Checks passed | Action plan updated | Commit created | Push completed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | done (34 expected failures) | clean after OWNER/USERNAME test correction | done (44 targeted tests passing) | clean after datetime-flake fix | targeted, real set, Ruff passed; broad gate deferred to Stage 3 | done | edf2cda (code), plan commit pending | pending |
| 2 | pending | pending | pending | pending | pending | pending | pending | pending |
| 3 | pending | pending | pending | pending | pending | pending | pending | pending |

Implementation notes and commit/push evidence will be recorded at each section exit.

Stage 1 red review found a contradictory OWNER-missing case despite USERNAME being
available; the test now requires both to be missing, and the re-review is clean.
The first broad solution check exposes a pre-existing devcontainer JSON parse
failure in `tests/test_runtime_python_version.py` (committed invalid JSON in
`template_repo_files/.devcontainer/devcontainer.json`); triage is deferred to
the Stage 3 repository-wide gate. Green review found a time-dependent equality
assertion in the tampering test once results acquired a datetime; comparing
grade-bearing fields removed the flake and re-review was clean. The real
`ex002_sequence_modify_basics` build and local solution/student dry runs pass
with matching 34 case names/maxima; student scores 4/34 as expected.
Stage 1 implementation complete without deviation to the product contract;
the unrelated pre-existing devcontainer parse error remains a Stage 3 gate
follow-up. Code commit: `edf2cda0c74782b49d3802b63c92c49922af14af`
(`Add Classroom 50 invocation mode and canonical grading result`), branch
`fix/classroom50Autograder`.

## Implementation handoff

The next implementation owner is the Implementer agent. Its first prompt must
require it to read `SPEC.md`, this plan, the read-first context above, and the
withdrawn-scope list, then implement Stage 1 test-first.
