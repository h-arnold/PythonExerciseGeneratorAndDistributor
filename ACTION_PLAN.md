# Action plan: per-task Ruff readability feedback

Implement the requirements in `SPEC.md` locally and sequentially. This handoff
contains no runtime implementation or test code. No separate layout/workflow
specification is required: notebook structure and authoring workflow stay unchanged.
Treat exercise structure as a scaffolding/authoring guarantee. This feature adds no
task-count or tag-topology validation, structural FAIL rows or malformed-exercise tests.

## Stage 1 — Establish the policy and source-preserving analyser

**Objective:** deliver a small, independently testable static-analysis slice.

**Surfaces:** source/template Ruff dependency pins and `uv.lock`;
`exercise_runtime_support/student_checker/readability.py`;
`tests/exercise_runtime_support/`.

**Acceptance:** one owner for the 17 rule codes; four-space/100-character policy;
Ruff 0.14.13 pin; exact original source and physical cell/task identity preserved;
one non-writing, isolated stdin invocation per selected cell; structured findings
and explicit syntax/tooling failure handling. No launch on import and no edits to
the grading extractor.

**Checks:** fast source-selection/coordinate tests, subprocess contract tests and
positive/negative real-Ruff cases for every selected rule. Confirm empty starters,
non-task tags alongside a single task tag, correctly scaffolded exercises with
fewer/more than ten tasks, syntax errors, exits 0/1/2 and invalid Ruff JSON behaviour.
Discover task cells without a fixed count or comparison with metadata `parts`;
do not add tests for malformed task-tag arrangements or missing task cells.
Verify all 17 selections are active, including preview rules; exit-0 warnings that
rules have no effect are configuration failures, not clean student feedback.

**Review point:** Implementer handoff to Tidy Code Reviewer; resolve findings before
checker integration. Fixtures and test-only helpers remain under `tests/`.

## Stage 2 — Integrate required PASS/FAIL into the task-grouped results

**Objective:** make readability a required PASS/FAIL check alongside each task's
functional results, without altering teacher-side grading.

**Surfaces:** `exercise_runtime_support/student_checker/notebook_runtime.py` and
reporting/model modules only as needed; existing checker infrastructure tests.

**Acceptance:** existing API/return preserved; local-support and fallback paths
both report readability; default student and explicit solution govern analysis and
execution consistently; environment restored. Functional outcomes remain unchanged;
readability adds a distinct PASS/FAIL row in the same task-grouped table. Task and
overall self-check success require both functional and readability checks to pass.
Cell-local locations, physical-cell disambiguation, deterministic summaries,
syntax-blocked status, save reminder and source/export guide references are shown.
Tool failures are explicit after available functional output, not clean results.
The orchestrator owns overall success; suppress intermediate functional-only
congratulations. Keep `run_exercise_checks()` and exercise-local `CHECKS` unchanged:
teacher grading and Gate I do not call the notebook orchestrator, so no exclusion
switch or special filtering is required.

**Checks:** targeted dispatch, reporting and variant tests; representative real
sequence/selection checker calls in student/solution variants; saved-edit reruns;
ordinary import/functional-only calls do not invoke Ruff. Use the normal pinned
environment, with subprocess test doubles for tooling errors; no Ruff-free test
environment or runtime availability guards. Preserve existing unfinished-student
assertions and solution correctness checks.
Test all four functional/readability PASS/FAIL combinations, syntax FAIL and tool
ERROR cases; only the all-pass combination may display overall success. Confirm
tooling ERROR output is explicitly distinguishable from student readability FAIL.
Confirm the grader's functional-only path does not launch Ruff or acquire new
scored cases.
Existing solution readability failures remain FAIL in the combined self-check,
but are allowed as feature-migration backlog; do not require clean reference
notebooks or correct them during this stage. Check guide
reference strings here without guide-file existence checks; review the actual
Markdown links/anchors as documentation in Stages 3–4.

**Review point:** Tidy Code Reviewer checks integration and absence of duplicate
analysis/grading coupling. Do not edit individual notebooks or support definitions.

## Stage 3 — Author and verify the student error guide

**Objective:** provide actionable explanations for every selected rule.

**Surfaces:** `template_repo_files/RUFF_GUIDE.md`; documentation/example regression
tests under `tests/exercise_runtime_support/`.

**Acceptance:** code-index/anchors cover exactly all 17 policy rules; each entry
has an explanation, non-example, corrected example and change rationale. Whitespace
is visibly explained. Rename corrections update uses. Later-topic labels, syntax
help, tool-failure help, save/check instructions and policy limitations are present.
No copied exercise solutions or instruction to suppress diagnostics.
Explain that readability is required for task/overall self-check PASS rather than
optional advice, while teacher-side marks are unchanged in this implementation.
Explicitly state that existing reference solution notebooks may fail the new
readability policy and combined self-check and will be corrected in a future pass.

**Checks:** real-Ruff validation of every paired example; anchor/rule-set parity;
manual Markdown review for invisible whitespace and age-appropriate language.
Invalid-Python cases are checked under the pinned rule behaviour, not assumed to
produce a particular rule. Corrected examples remove the advertised issue.
Use a parseable E101 non-example; parsing-breaking mixed indentation is syntax help.

**Review point:** Docs checks accuracy and readability; teacher reviews the student
guide before final packaging. This is documentation review, not a new-exercise gate.

## Stage 4 — Package the guide and verify the exported experience

**Objective:** ship the same policy and guide in every student template.

**Surfaces:** explicit required base-asset copying in
`scripts/template_repo_cli/core/packager/__init__.py`;
`template_repo_files/README.md.template`; `tests/template_repo_cli/`.

**Acceptance:** one canonical guide source exports to root `RUFF_GUIDE.md`; its
README/checker references use the documented mapping. Copy it using the existing
base-asset mechanism, without bespoke guide-file guards or existence tests.
Exported runtime and exact Ruff pin match source. Canonical metadata, notebook and
test paths remain unchanged; no new hidden grading sources, solutions, flattened
mirrors or maintainer fixtures are shipped.

**Checks:** manual documentation review of guide/README links; offline exported
self-check with real Ruff, student default and retained functional failures. Update
synthetic packaging fixtures directly rather than adding compatibility fallbacks.
Confirm combined functional/readability results and overall PASS/FAIL in the export.
Do not add Python tests for the presence or absence of the Markdown guide.
Reuse the test runner's pinned Ruff environment for the offline exported check;
do not install a new environment inside the fixture.

**Review point:** Tidy Code Reviewer checks canonical-only packaging and source/export
parity; Testing Specialist verifies the packaged self-check rather than only mocks.

## Stage 5 — Document and validate the complete change

**Objective:** confirm the feature and its constraints across supported runtimes.

**Surfaces:** targeted updates to `docs/developers/testing-framework.md`,
`docs/developers/execution-model.md` and `docs/developers/development.md` where their
checker/validation guidance changes; the files changed in previous stages.

**Acceptance:** documentation states selected policy, supported native runtimes,
saved-file behaviour, guide mapping and required-self-check/teacher-grading boundary.
Record why deferred teacher inclusion is lower effort: the grader already uses a
separate functional pytest path, whereas inclusion adds Ruff installation, hidden
test adaptation and score-total validation. Do not add a disable-readability flag.
Quality gates and teacher grading remain functional-only. Assume Ruff is installed
in the managed notebook environment; introduce no availability probes or optional
runtime paths.
No updates to exercise-local tests, teaching order or notebook layout are needed.
Developer guidance explicitly records that existing solution notebooks may fail
readability checks and that corrections are deferred to a future pass. Those
failures must appear as FAIL in combined self-checks, but do not invalidate
functional solutions or block feature acceptance. Functional solution validation
and teacher-side full-pass grading remain unchanged.

**Checks:**

- `uv run pytest tests/exercise_runtime_support/ tests/template_repo_cli/ -q`
- `uv run pytest --collect-only -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- `uv run ruff check .`
- Explicit student-variant runs on representative canonical sequence/selection
  tests retain expected failures; capture them as evidence, not failures to fix.

**Review point:** Docs review, final Tidy Code Reviewer and Testing Specialist reports;
teacher-facing handoff with changed paths, validation evidence and any remaining
limitations. Do not commit, publish templates or deploy assignments without request.
