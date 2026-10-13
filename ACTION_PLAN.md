# Action plan: per-task Ruff readability feedback

Implement the requirements in `SPEC.md` locally and sequentially. This handoff
contains no runtime implementation or test code. No separate layout/workflow
specification is required: notebook structure and authoring workflow stay unchanged.
Treat exercise structure as a scaffolding/authoring guarantee. This feature adds no
task-count or tag-topology validation, structural FAIL rows or malformed-exercise tests.

## Delivery tracker

### Guide filename rename — single-section follow-up

User requested brief direct planning, then normal delegation; no planner cycle.
Rename the canonical source to `template_repo_files/fixing-readability-issues.md`
and export it as root `fixing-readability-issues.md`. Update required base assets,
copy mapping, README link, existing test references and live developer contracts.
Keep guide contents, runtime policy, grading and notebook assets unchanged; no
old-name alias, new dependencies, bespoke guards or Markdown-presence tests.
Historical delivery records retain their original filenames.

Sequence: Testing Specialist updates existing guide content/example tests and
captures expected missing-new-path failures; Tidy reviews RED; Implementer renames
and updates packaging/references; Tidy reviews GREEN. Run support/packaging tests,
Ruff and diff checks, then section commit/push, cleanup review and final Docs sync.
Preserve user-owned dirty config and both student notebooks. No template publication.
RED complete: 18 expected missing-new-path failures and one pass. Review found
only path-expression formatting; Testing Specialist fixed it and re-review is
clean. Scoped Ruff lint/format pass. GREEN complete and reviewed clean: guide
contents are byte-identical; required base source/copy destination, README link,
test references and live developer contracts use the new name. 367 support/CLI
tests pass under both ordinary pytest and the explicit solution runner. Scoped
Ruff lint/format and diff checks pass. No deviations or new follow-ups.
Section committed and pushed successfully: `3d395972005286f0f81a376b593924eac1bde710`
— `Rename packaged readability guide` on `feat/AddLinterRulesToSelfChecker`.
Mandatory cleanup review passed with no required fixes; repeated filename literals
retain the surrounding base-asset pattern. README source reflow is cosmetic only.
Cleanup independently reproduced 367 ordinary/solution passes and repository Ruff.
Branch ready for final documentation review; no cleanup implementation needed.
Final Docs review clean: all live mapping/link contracts already updated in the
section commit; no further documentation edits needed. Guide contents unchanged,
user config/notebooks excluded, and no templates published. Single section complete;
final delivery-note commit/push evidence is recorded in the session tracker.

| Red tests | Red review | Green | Green review | Checks | Plan updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Added | Clean | Complete | Clean | Passed | Complete | Created | Complete |

### Feedback capitalisation follow-up (direct execution)

User-approved scope: capitalise only the first character of rendered feedback,
after removing any exercise prefix and before wrapping. Preserve the remaining
text, including quoted answers, identifiers and rule codes. Leave source results,
functional outcomes, 40-character wrapping and readability eligibility unchanged.
Untouched-starter detection is explicitly deferred at the user's request.
Plan: RED casing/preservation tests, minimal GREEN rendering change and self-review,
checks/cleanup, documentation sync and commit/push. Preserve existing config and
both saved student notebook edits. RED complete: 13 expected casing failures and
61 passes. Red self-review clean: prefix handling, wrapped sentences, empty feedback,
quoted mixed-case text, identifiers and already-capitalised diagnostics are covered.
GREEN complete and self-reviewed clean: one rendering line changed, with no
source/checker edits. 385 support/reporting/CLI tests pass; full solution validation
is 1,614 passed and one skipped. Ruff lint/format, scoped Pyright and diff checks
pass. Actual sequence ex005 feedback starts `Expected`, `Explanation` and `Output`;
`Alice` is preserved and readability remains nine OK rows and one NO row.
Section commit/push succeeded: `3401e4ee189567e814a56d4bc23fe018f1db6901` —
`Capitalise rendered self-check feedback` on `feat/AddLinterRulesToSelfChecker`.
Direct cleanup self-review found no additional work: simple slicing handles empty
messages without guards or a new helper. Ready for documentation sync; public
rendering docstring and testing contract now describe the casing-only transformation.
Final documentation self-review clean; 421 support/reporting/CLI/documentation
tests pass after sync, with Ruff lint/format and diff checks clean. No deviations;
untouched-starter handling remains deferred. Final docs commit/push evidence is
recorded in the session delivery tracker.

| Red tests | Red self-review | Green | Green self-review | Checks | Plan updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Added | Clean | Complete | Clean | Passed | Complete | Created | Complete |

### Narrow-table follow-up (direct execution)

Scope: label readability rows `Readability`, without physical cell numbers, and
remove both notebook checker overrides of the shared 40-character feedback width.
Feedback wraps over as many lines as needed, without truncation. Task grouping,
cell-local diagnostic coordinates, statuses, analysis and grading stay unchanged.
No responsive browser/terminal sizing is added; other columns remain content-sized.
Plan: RED regression updates and self-review; minimal GREEN presentation changes
and checks/self-cleanup; documentation sync, commit and push. Preserve all existing
user-owned config/notebook edits, including sequence ex005 saved output.
RED complete: 17 expected label/width failures, 42 passes. Red self-review clean:
both dispatch paths and exported runtime retain task/status assertions; long
functional feedback is reconstructed exactly across more than four wrapped lines
in normal and tooling-error presentation paths. GREEN complete and self-reviewed
clean: only three presentation lines changed. 376 support/reporting/CLI tests pass;
full solution validation is 1,605 passed and one skipped. Ruff lint/format, scoped
Pyright and diff checks pass. Actual sequence ex005 table width is 83 characters;
both E226 findings wrap across four lines without truncation. Task grouping,
functional failures and neutral syntax status remain unchanged.
Section commit/push succeeded: `a2bdaf1d2dddbbacc3f24f027b09c265a0bbb71b` —
`Narrow self-check tables and simplify readability labels` on
`feat/AddLinterRulesToSelfChecker`. Direct cleanup self-review found no additional
work: reuse the shared width instead of adding constants/configuration or responsive
rendering. Branch state is ready for documentation sync. Guide and developer
contracts now reflect task-only labels and unlimited 40-character feedback wrapping.
Final documentation self-review clean; 412 support/reporting/CLI/documentation
tests and repository Ruff pass after sync. No new follow-ups or scope deviations.
Final documentation commit/push evidence is recorded in the session delivery tracker.

| Red tests | Red self-review | Green | Green self-review | Checks | Plan updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Added | Clean | Complete | Clean | Passed | Complete | Created | Complete |

### Compact-output follow-up (user-approved direct execution)

Short plan: update output regression tests; remove the footer and present
syntax-blocked readability as neutral NOT CHECKED with
`Not checked - make sure your code runs first`; run checks, self-review/cleanup,
sync the guide/developer contracts and deliver. Valid syntax is assessed even
when functional checks fail. Analysis, functional results and grading stay unchanged.
This follow-up supersedes the historical summary/syntax-FAIL presentation below.
The user requested execution without a planner/sub-agent cycle.

RED evidence: 24 expected output/status failures, 33 passes. Self-review corrected
test row selection so table headers are not counted as functional results.
GREEN complete and self-review clean: only rendering/status handling changed;
Ruff analysis and functional execution remain untouched. 57 focused tests and
374 support/reporting/CLI tests pass; full solution validation is 1,603 passed,
one skipped. Ruff lint/format, scoped Pyright and diff checks pass. Lint findings
in test parametrisation/counts were corrected without suppressions.
Section pushed successfully: `09aa3859cf5b4c231a9e0540dfca4d812d7e603d` —
`Simplify self-check output and defer syntax-blocked readability` on
`feat/AddLinterRulesToSelfChecker`. Self-cleanup found no additional work: dead
guide lookup and obsolete summary-only test helpers were already removed.
Final documentation sync self-review is clean: guide and developer contracts
describe neutral syntax-blocked rows and table-only output. Post-sync validation:
410 support/reporting/CLI/documentation tests pass; Ruff lint/format and diff checks
pass. The actual selection ex002 debug self-check has ten NOT CHECKED readability
rows and ten readability passes, with no footer or Ruff syntax cascade; functional
failures remain. Final documentation commit/push evidence is recorded in the session
delivery tracker. No further scope deviations or new follow-ups.
Preserve the two existing user-owned changes.

| Red tests | Red self-review | Green | Green self-review | Checks | Plan updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Added | Clean | Complete | Clean | Passed | Complete | Created | Complete |

The user explicitly authorised per-stage commits and pushes. This supersedes the
original local-only delivery note; template publication and assignment deployment
remain out of scope. The user's reviewer-model configuration change is excluded
from feature commits.

| Stage | Red tests | Red review | Green implementation | Green review | Checks | Plan updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Complete | Clean | Complete | Clean | Passed | Complete | Created | Complete |
| 2 | Complete | Clean | Complete | Clean | Passed | Complete | Created | Complete |
| 3 | Complete | Clean | Complete | Clean | Passed | Complete | Created | Complete |
| 4 | Complete | Clean | Complete | Clean | Passed | Complete | Created | Complete |
| 5 | Complete | Clean | Complete | Clean | Passed | Complete | Created | Complete |

Stage 1 red evidence: expected collection ImportError for the absent analyser;
test lint/format pass; real Ruff 0.14.13 validates all 17 non-example/corrected pairs.
Review corrections resolved valid task co-tag selection, parseable E101, realistic
diagnostic fixtures, complete subprocess/pin assertions, import/static side-effect
checks, exact string/list stdin and byte preservation, and placeholder invocations.
The third red review was clean. No scope deviation.

Stage 1 green evidence: 43 analyser tests and 46 nearby checker tests pass; scoped
Ruff lint/format, Pyright (implementation and tests), and `uv lock --check` pass.
Green review caught malformed diagnostic-record handling and typing errors; typed
boundary guards and six regression cases resolved both, with a clean re-review.
No grading/extractor changes. Stage 1 complete; no deviation. Pushed
`6788089407bf4de843c5b5629960092b6a9a557d` — `Add source-preserving Ruff readability analyser`
to `feat/AddLinterRulesToSelfChecker` successfully. Stage 2 red tests are next.

Stage 2 red evidence: normal and explicit-solution scoped runs report 25 expected
failures and 19 passes; test lint/format pass. Review-driven corrections expanded
both dispatch paths, all four outcome combinations, tooling ERROR sequencing,
variant/path propagation, category-scoped summaries, saved-file reruns, source/export
references and real functional/readability backlog separation. Contradictory fixture
messages/counts, summary row selection and uncreated-path doubles were corrected.
Final red review clean; eight pre-existing private-usage typing diagnostics remain
unchanged. No scope deviation. Green implementation now in progress.

Stage 2 green evidence: 136 runtime-support tests pass under normal pytest and the
explicit solution runner; scoped lint/format pass and implementation Pyright is
clean. Review found duplicate readability rows on multi-check tasks and inherited
variant assumptions in six helper tests; a red-before-fix regression and explicit
test environment isolation resolved both. Real ex002 shows 30 functional checks
and exactly ten readability rows. Backlog ex015 retains ten functional passes and
one E501 readability FAIL/overall FAIL. Final green review clean. No grading changes
or notebook edits. Stage 2 complete; no scope deviation. Pushed
`6afd5ec5a80f997b0b3d73e544d216817a2be776` — `Require per-task readability in notebook self-checks`
to `feat/AddLinterRulesToSelfChecker` successfully. Stage 3 red tests are next.

Stage 3 red evidence: 18 expected ordinary missing-guide read failures and one
fence-whitespace regression pass; lint/format/Pyright pass. Red review clean after
strict lowercase anchor/index parity and source-preserving fence extraction fixes.
Prose semantics deliberately remain manual Docs review, as specified by the plan;
regex vocabulary checks were removed rather than claiming semantic guarantees.
Guide authoring is now in progress; teacher review remains required before any
actual template publication (none is requested).

Stage 3 green evidence: all 19 guide tests pass, including real-Ruff validation of
17 paired examples and anchor/index parity; 155 support tests pass under solution.
Docs and Tidy reviews are clean. Docs' syntax-help finding was fixed with an actual
parse-blocking example, separately verified by Ruff, distinct from parseable E101.
Manual review covers age-appropriate prose, later-topic labels, visible whitespace,
required self-check/teacher-mark separation, limitations and solution backlog.
No content scope deviation. Human teacher review is an outstanding publication
gate, not authorisation to publish. Stage 3 complete. Pushed
`0a2fa81896d3436b11bd27d386e8b9bf9c9b1751` — `Add student Ruff readability guide and example checks`
to `feat/AddLinterRulesToSelfChecker` successfully. Stage 4 offline packaging tests
are next; no templates will be published.

Stage 4 test-phase evidence: three offline exported-runtime tests pass under both
normal and solution runners; lint/format/Pyright pass. They verify exported module
origins, exact Ruff pin and analyser parity, real saved-edit readability FAIL-to-PASS
while functional failures remain, combined PASS and canonical missing-solution errors.
Review corrected summary association, import isolation, error specificity and typing.
Approved TDD deviation: these regression tests are already green because Stage 2
runtime copying already supplies the behaviour; no artificial failing assertion or
forbidden Markdown-presence test was introduced for the remaining base-asset/docs
delta. Review clean; explicit guide copying and README linkage now in progress.

Stage 4 green evidence: 361 support/packaging tests pass under normal and solution
runners; six focused real-export/canonical-exclusion checks pass in both variants.
Scoped lint/format/Pyright pass. Tidy review clean, including manual guide/README
link review and ordinary required-base-asset copy flow; no bespoke guide guards.
No synthetic fixture edits were necessary, because these tests use real assets.
No template publication/deployment performed. Stage 4 complete. Pushed
`607dee9e17aa03733f5d5b6b63da523a785e1afe` — `Package Ruff guide and verify offline student self-checks`
to `feat/AddLinterRulesToSelfChecker` successfully. Stage 5 validation is next.

Stage 5 test/validation evidence: all required commands succeed: 361 support/CLI
tests pass; 1,599 tests collect; full solution validation gives 1,598 passed and one
skipped; repository Ruff passes. Explicit student ex002 sequence and ex001 selection
runs retain 30 and 33 expected unfinished-task failures. Existing real Classroom 50
bundle tests confirm full-pass solution grading and unchanged case names/maxima.
Review gate clean; eight baseline private-usage diagnostics are unchanged.
As this is the final validation/docs-only section, no artificial new RED tests are
added after the earlier feature TDD phases. Targeted contract guidance is next;
the separate final documentation sync remains after mandatory de-sloppification.

Stage 5 green evidence: targeted execution/testing/development contracts updated;
Docs and Tidy reviews clean. Post-doc support/packaging tests remain 361 passed,
36 autograder-documentation tests pass, repository Ruff and diff checks pass.
The explicit student validation example now correctly uses the student runner.
No runtime/grading/catalogue change. Ready for commit/push, then mandatory cleanup
and a separate final documentation sync. Human teacher review and future solution
readability corrections remain follow-ups; no assignment/template deployment.

Stage 5 complete. Pushed `51d8d5d30ae194cc0d73f13183e7699424ccc6a5` —
`Document required readability and functional grading boundary` to
`feat/AddLinterRulesToSelfChecker` successfully. All numbered sections are delivered.
Mandatory de-sloppification is now in progress; final documentation sync is pending.

Cleanup review found no behavioural defect, but confirmed duplicate variant
restoration, a pass-through analyser wrapper, dead test-helper branches and
redundant test-only self-checks, plus student-guide wording exposing test internals.
Minimal behaviour-preserving fixes are in progress; no catalogue or grading-policy
changes are authorised. Large test-module splitting and broader tag-parser
reorganisation are explicitly not required. Cleanup will be re-reviewed and fully
validated before final documentation sync.

Cleanup complete and Tidy GREEN review clean: shared variant restoration retains
student-default self-checks and solution-default repository orchestration;
the analyser wrapper, dead test branches and redundant pre-dispatch/helper tests
were removed. Existing real-output assertions remain. Guide test-internals prose
was removed and task labels reuse the existing compiled pattern. The public
analyser docstring and test formatting were corrected during re-review.
No functional/grading semantics changed. Final snapshot: 363 support/CLI tests
pass; 1,601 tests collect; full solution validation gives 1,600 passed and one
skipped. Lint, scoped format/Pyright and lock checks pass; eight baseline test
private-usage diagnostics remain. Expected student sequence/selection failures
remain 30/33. Ready for cleanup commit/push, then final documentation sync.

Cleanup pushed successfully: `b79044705e3063e44d94c2fcba74f6cb6c1e8dac` —
`Simplify readability helpers and shared variant restoration` on
`feat/AddLinterRulesToSelfChecker`. Branch feature state is ready for final Docs
sync. Local user reviewer configuration and saved notebook outputs are excluded.
Final documentation sync is now in progress.

Final documentation sync complete and Tidy review clean. Public API docstrings now
describe index coordinates, defaults, restoration, return values and actual error
boundaries; final guidance also records tooling ERROR behaviour and human teacher
review before publication. Review corrected the notebook orchestrator's resolution
versus fallback-loading exception descriptions. No runtime behaviour changed.
All final checks remain green: 363 support/CLI passes, 1,601 collected, 1,600
solution passes and one skip, Ruff/lock checks pass; 30/33 expected student failures.
Final docs commit/push completed successfully: `5b874fec6a9e2fd23c0ac291ba00b38790c22397`
— `Sync final readability API and execution documentation` on
`feat/AddLinterRulesToSelfChecker`. No deployment or catalogue correction performed.

### Delivery artefacts

All listed commits were pushed successfully to `feat/AddLinterRulesToSelfChecker`.
Separate progress commits preserve the requested per-stage delivery evidence.

| Stage | Commit | Exact message |
| --- | --- | --- |
| 1 | `6788089407bf4de843c5b5629960092b6a9a557d` | Add source-preserving Ruff readability analyser |
| 1 notes | `8cdee9e603c9d79875f4e0d779295400804b3c3b` | Record Stage 1 readability delivery |
| 2 | `6afd5ec5a80f997b0b3d73e544d216817a2be776` | Require per-task readability in notebook self-checks |
| 2 notes | `f06ada11f9e0bcd78c0c9ee355679d9b19186560` | Record Stage 2 combined self-check delivery |
| 3 | `0a2fa81896d3436b11bd27d386e8b9bf9c9b1751` | Add student Ruff readability guide and example checks |
| 3 notes | `01d2138672f52a9e64ab97becac03de3661b901a` | Record Stage 3 guide review and delivery |
| 4 | `607dee9e17aa03733f5d5b6b63da523a785e1afe` | Package Ruff guide and verify offline student self-checks |
| 4 notes | `80fc1cd32d9b5a066ba40c02437f07093fc0e4d6` | Record Stage 4 offline packaging delivery |
| 5 | `51d8d5d30ae194cc0d73f13183e7699424ccc6a5` | Document required readability and functional grading boundary |
| 5 notes | `1ae0311c5b05fc5c652603f748df081de7114a22` | Record Stage 5 validation and contract delivery |
| Cleanup | `b79044705e3063e44d94c2fcba74f6cb6c1e8dac` | Simplify readability helpers and shared variant restoration |
| Final docs | `5b874fec6a9e2fd23c0ac291ba00b38790c22397` | Sync final readability API and execution documentation |

**Final status:** all five stages, mandatory cleanup and final documentation sync
are complete, reviewed clean, committed and pushed. This final ledger update is
delivery bookkeeping only. Outstanding follow-ups: human teacher guide review
before publication, the documented future solution-readability correction pass,
and eight pre-existing private-usage typing diagnostics in the runtime test file.
Local reviewer configuration and the selection ex002 saved notebook outputs remain
untouched and uncommitted; no templates or assignments were published/deployed.

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
