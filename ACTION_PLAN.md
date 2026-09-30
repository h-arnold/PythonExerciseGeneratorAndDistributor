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

All sections complete. Current phase: final documentation sync completed;
handoff to the teacher pending.

| Stage | Red tests added | Red review clean | Green implementation complete | Green review clean | Checks passed | Action plan updated | Commit created | Push completed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | done (34 expected failures) | clean after OWNER/USERNAME test correction | done (44 targeted tests passing) | clean after datetime-flake fix | targeted, real set, Ruff passed; broad gate deferred to Stage 3 | done | edf2cda (code), 55f243b (plan) | pushed |
| 2 | done (22 expected failures) | clean after field, totals and pair-phrase corrections | done (36 doc checks passing) | clean | docs suite, grader suite, link/stale sweeps, Ruff passed | done | c360b48 (docs and tests), 4e314ba (plan) | pushed |
| 3 | existing failing devcontainer JSON test confirmed | clean; no new tests needed | done (one-line JSON fix) | clean | 1355 passed, 1 skipped; solution green, student expected failures; both repoman validates and Ruff green | done | db84c56 (gate fix), 689060b (plan) | pushed |

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
`fix/classroom50Autograder`. Plan commit: `55f243bc7b376b62c451e471c0fe040ad98590c1`
(`Track Stage 1 Classroom 50 delivery`). `git push origin
fix/classroom50Autograder` succeeded, advancing `46e8966..55f243b`.

Stage 2 red review tightened canonical key wording, row-sum coverage, and
single-option error phrasing; re-review was clean (22 expected failures, 14
passing guards). A redundant context query is an optional green tidy-up.
Stage 2 documentation review is clean; the guide, execution model and
development notes now match the two invocation modes and manual deployment.
No product-contract deviation; a lone `--variant solution` without local pair
is accepted but ignored in Classroom 50 mode as the guide states. No exercise
or teaching-order files changed. The devcontainer JSON gate remains for Stage 3.
Stage 2 code/docs commit `c360b48a0eb5f4c975b28b89a6085f0ed9be5b56`
(`Document Classroom 50 bundle invocation and deployment`) on branch
`fix/classroom50Autograder`.
Plan commit `4e314ba2966b9999f4c4026c6b0f95a571d6877f`
(`Track Stage 2 documentation delivery`); `git push origin
fix/classroom50Autograder` succeeded, advancing `5b75815..4e314ba`.

Stage 3 red: the existing runtime Python-version test exposes a pre-existing
invalid JSONC entry (`".classroom50.yaml"` missing `: true`) in the student
devcontainer, committed in `46e8966`. The red review confirmed existing tests
cover the defect; a comma-less one-line repair is needed to clear the planned
repository-wide gate without weakening any test. This is an explicit,
gate-blocking packaging deviation, not a new grader feature.
Stage 3 Tidy Code Reviewer confirmed clean final diff: no withdrawn features,
tracked bundles or grading sources in the template, and no exercise or
teaching-order edits. The single template devcontainer JSONC syntax repair was
the only plan deviation; it cleared the pre-existing gate failure. Manual
deployment remains with the teacher: build the selected bundle, confirm a
full-pass local solution dry run, place it at
`<classroom>/autograders/<assignment>/` in the Classroom 50 repository and
commit there, leaving `autograder: "default"`. The next implementation owner
for any future grader changes is the Implementer agent; live deployment and
the first live upstream contract recheck belong to the teacher, not this plan.
Stage 3 gate-fix commit: `db84c5665c5d4e0d304b8ea82f69e52fa878b12f`
(`Repair student devcontainer JSONC for final validation`) on branch
`fix/classroom50Autograder`.
Plan commit `689060b1137de7865c9b611f7d4a97ab22814752`
(`Track Stage 3 final gate and handoff`); `git push origin
fix/classroom50Autograder` succeeded, advancing `8a85054..689060b`.

Post-section de-sloppification found a redundant doc-test context lookup,
stale "Future CLI" test comments, an unused test-helper parameter, and two
outdated plan statements. The Implementer removed those confirmed items;
Tidy Code Reviewer re-reviewed the cleanup clean. Targeted docs/grader suites
(36/44), full suite (1355 passed, 1 skipped), collection, and Ruff pass.
Larger fixture extraction and cosmetic guide rewording were deferred because
they would expand this minimal cleanup without changing the contract. The
cleanup changed no grading contract.
Cleanup commit: `6ff2778907a6931c793af3a516b633f4a55da613`
(`Remove stale Classroom 50 test and plan scaffolding`), pushed to
`origin/fix/classroom50Autograder` (`69459f1..6ff2778`). Final documentation
sync followed this cleanup.

The final documentation sync was an accuracy pass over the whole diff, not
feature work. It confirmed that the contract guide, execution model,
development notes, and `AGENTS.md` agree with `SPEC.md` and `WORKFLOW_SPEC.md`,
that no withdrawn requirement survives in any directly affected document, and
that every relative documentation link resolves. It corrected three confirmed
drift points: the Classroom 50 test-surface description in
`docs/developers/testing-framework.md`, which no longer matched the expanded
Stage 1 and Stage 2 suites; the Classroom 50 mode owner requirement in
`docs/developers/classroom50-autograder.md`, which the guide omitted beside the
six required runner variables even though losing both `OWNER` and `USERNAME`
fails the run; and that section's result destination, now stated per mode. A
matching docstring correction in `scripts/autograder.py` names the mode in
`_resolve_invocation`'s return. No production, test, exercise, or teaching-order
behaviour changed, and no grading contract moved.

## Addendum — verifier `--all` (new item 1; historical tracker above unchanged)

1. **RED and existing-work review.** Surfaces: existing changes to
   `tests/test_verify_exercise_quality.py` and
   `scripts/verify_exercise_quality.py`. Inspect the worktree without resetting
   it; run `uv run pytest tests/test_verify_exercise_quality.py -q` and record
   the expected failures, notably the current caller/`options` mismatch.
   Review point: confirm the tests describe only the scoped sweep and existing
   single-key contract before editing production code.
2. **GREEN: finish the narrow verifier change.** Surface:
   `scripts/verify_exercise_quality.py`. Reuse the same per-exercise gates for
   single-key and `--all`, report each discovered canonical exercise separately,
   continue after malformed notebooks, aggregate ERROR status, and leave
   single-key semantics intact. Check: rerun the targeted pytest file; verify
   clean, warning-only, malformed, metadata-defective, and single-key cases.
   Review point: Tidy Code Reviewer checks discovery, error boundaries and
   minimality; address findings without unrelated refactors.
3. **Docs sync and final checks.** Surfaces: only directly affected CLI
   guidance in `docs/developers/development.md` and/or
   `docs/exercise-agents/exercise-generation-cli.md`, plus this addendum if
   outcomes differ. Check `uv run ruff check scripts/verify_exercise_quality.py
   tests/test_verify_exercise_quality.py`, `uv run pytest
    tests/test_verify_exercise_quality.py -q`, and an actual `uv run python
    scripts/verify_exercise_quality.py --all` run. The existing baseline is 26
    errors and 103 warnings across 18 exercises, including ex011's missing
    `expectations.py`; do not fix exercise content. Review point: confirm docs
    match CLI, inspect `git status`/`git diff`, and preserve the historical
    plan/tracker and other branch work. No commit or push.

Progress: RED tests and red review clean after missing-metadata and
`--skip-empty-checks` coverage was added. GREEN implementation complete;
54 targeted tests, full pytest and solution variant passed. Initial green
review flagged a single-key malformed-notebook behaviour change; a regression
test was added and recovery was restricted to `--all`. An empty-tree regression
test prevents a vacuous successful sweep. Final green review was clean after
these fixes. De-sloppification removed duplicated test helpers and a repeated
ordering case; docs sync confirmed CLI guidance. Ruff, Pyright,
`ruff format --check`, `git diff --check`, the full pytest suite, and the full
solution-variant suite pass. Runtime Gate I is deliberately skipped for
exercises with pre-existing input classification errors to prevent a hang. No
exercise content was modified.

| Verifier `--all` checklist | Status |
| --- | --- |
| Red tests added | done |
| Red review clean | done |
| Green implementation complete | done |
| Green review clean | done |
| Checks passed | done (real sweep exits 1 on existing exercise findings) |
| Action plan updated | done |
| Commit created | pending (not requested) |
| Push completed | pending (not requested) |

Completion status: code, tests, cleanup, and documentation complete; delivery
remains uncommitted and unpushed. No deviation from the `--all` CLI contract.
Follow-up: address existing catalogue findings separately before using an
all-exercise zero exit as a release gate.
