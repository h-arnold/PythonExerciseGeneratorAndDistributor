# Current action plan: final review clean-up

The delivery tracker and numbered feature stages below are **historical
evidence**, not the status or requirements of this clean-up. In particular their
old `RUFF_GUIDE.md`, summaries, footer, syntax-FAIL and stage-5 no-commit
instructions are superseded by the current `SPEC.md` section and the delivered
`fixing-readability-issues.md`/table-only behaviour. Batches A and B are reviewed
clean, committed and pushed. Batch C RED and GREEN reviews are clean;
implementation, checks, plan/ledger updates, commit and push are complete.
Final independent de-sloppification identified nine follow-up cleanups, tracked
as Batch D below. Batch D implementation, validation and independent GREEN
re-review are complete and clean; commit and push succeeded. Final cleanup
confirmation is clean with no actionable slop remaining. Documentation sync and
final whole-branch review are clean; final documentation is committed and pushed.
All cleanup and review work is complete.
`REVIEW_FINDINGS.md` is the complete individually trackable finding ledger.

## Shared sequence and gates for each batch

1. Testing Specialist captures existing behaviour and scoped pyright baseline;
   writes/adjusts meaningful public-behaviour regressions where possible. For
   cleanup/documentation that already passes, log an evidence-backed green
   baseline and an explicit **no artificial RED** deviation. Do not create
   malformed-topology tests or a fake missing-module subprocess exception.
2. Tidy Code Reviewer reviews RED tests/baseline and every assigned ledger item;
   repeat test/review until clean. Implementer makes the smallest change, not a
   feature extension. Tidy reviews GREEN; send all significant findings back to
   Implementer and repeat until clean. Testing Specialist verifies results.
3. Checks: targeted pytest for changed surfaces, scoped pyright on touched Python
   source **and tests** (zero errors, including old private-access baseline),
   `uv run ruff check .`, scoped `uv run ruff format --check` and `git diff --check`.
   Escalate to `uv run pytest --collect-only -q` and
   `uv run python scripts/run_pytest_variant.py --variant solution -q`; run offline
   packaged and representative explicit student variants at integration/final
   boundary. Expected student failures must not be repaired. Preserve fixture
   isolation and no template publication.
4. Mark each ledger ID with outcome/evidence; update this plan and verify staged
   diff excludes the user-owned dirty config. N15's decision gate is resolved:
   the user explicitly requested keeping the committed model changes. Retain them
   as intentional branch scope, with no `.opencode/` edits or history rewriting.
   The separate uncommitted reviewer setting remains untouched and unstaged.
   Before commit inspect `git status`, `git diff`, `git log --oneline -10`; stage
   only intended files. Per-batch commit and push follow the developer-orchestrated
   batch workflow and the prior per-stage authorisation recorded in the delivery
   tracker; record actual hash/push result only after success. Never amend/rewrite
   history.

For **each** batch, fill these eight statuses separately after work:

| Batch | Red tests/baseline | Red review | Green implementation | Green review | Checks | Plan/ledger updated | Commit | Push |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Complete (numbering, fail-fast and tag-matching REDs) | Clean | Complete | Clean | Passed | Complete | Created | Complete |
| B | Complete (already-green public baseline; scoped Pyright 23 → 0; no artificial RED) | Clean | Complete | Clean | Passed: focused 186; full solution 1,618 passed/1 skipped; collect-only 1,619; Ruff/format/lock/diff | Updated | Created | Complete |
| C | Complete (already-green packaged baseline; no artificial RED) | Clean | Complete (documentation and dispositions updated) | Clean | Passed: packaged 208; guide/package focused 24; solution 1,618 passed/1 skipped; collect-only 1,619; Ruff/Pyright/format/lock/diff | Complete | Created | Complete |
| D | Complete (green baseline; no artificial RED) | Clean | Complete | Clean | Passed | Complete | Created | Complete |

### Batch A — shared analyser and task discovery (R1, R2, Y5, N1–N6)

**Objective:** consolidate source-preserving cell discovery and accurate tool
errors without expanding notebook validation.
**Surfaces:** `exercise_runtime_support/student_checker/{readability,notebook_runtime}.py`,
`exercise_runtime_support/student_checker/checks/__init__.py` (N2 one-name import),
focused tests under `tests/exercise_runtime_support/`; a tiny shared module only
if justified by call sites. **Acceptance:** minimal shared saved-cell/tag/source
primitives (or task-code iterator only where semantics match); fallback's cell-type
scope and established string-tag support maintained, Ruff subprocess
missing-module failure represented by child result, one-based error reference and
accurate docstring; individually adjudicate wrapper and small nits in ledger.
**Checks:** real Ruff rule/coordinates, stdin/source byte-preservation, string and
list tags, current invalid JSON/tool ERROR regressions; scoped pyright/formatter,
pytest support suite and shared ladder above. **Review point:** Tidy RED and GREEN
gates, particularly no new structural checks or runtime compatibility shims.

Batch A test baseline at that historical checkpoint: `tests/exercise_runtime_support/test_student_checker_readability.py`
had a single expected RED for one-based tool-error cell numbering (it reported
zero-based `cell 1` for physical cell 2); 89 other focused checker tests passed,
including a new public fallback assertion that string tags are discovered across
markdown and code cells. Missing Ruff is represented as a child result with
returncode 1 and stderr, while `FileNotFoundError` remained the missing-interpreter
case. Existing saved-notebook/source-preservation tests were green baselines rather
than manufactured REDs. Scoped readability implementation/test Pyright is clean;
the notebook-runtime target had 23 diagnostics (8 original and 15
Batch B-owned), with no diagnostics introduced by this Batch A test.

Batch A implementation evidence (clean review; delivered): source
validation and list-source joining then lived in `student_checker/_notebook_cells.py`
and were used by both saved-cell analysis and fallback tag discovery. Fallback tag discovery used the shared anchored regex
full-match predicate, preserving the previous `^exercise\d+$` decimal-digit
semantics (Python regex `\d` includes Unicode decimal digits);
readability kept its original `startswith("exercise")`/`isdigit()` predicate and
therefore its fail-fast `AttributeError` for a non-string tag item. The fallback
validated tag container forms before applying shared matching; readability retained its previous
fail-fast handling for malformed list items. The fallback discovered tags on
every valid cell type; readability selected code cells only. Saved notebook
loading remained at each consumer boundary because
the fallback's established `NotebookGradingError` validation and readability's
direct JSON fail-fast errors differ; centralising JSON loading would change those
error contracts without removing meaningful parsing policy. GREEN implementation
tests passed: the readability + notebook-runtime focused suites reported 91 passed.
Repository Ruff, scoped formatting, scoped Pyright (including the changed runtime),
`uv lock --check`, collection and the full explicit solution runner also passed.
The full support directory pytest suite passed. At that historical checkpoint,
Pyright on the separately changed Batch B test file still reported 23 diagnostics
(8 original and 15 Batch B-owned). Its public fallback assertion belongs to Batch A;
GREEN made no changes to the B-owned diagnostic regions.
Disposition evidence for each finding is recorded in `REVIEW_FINDINGS.md`.

Batch A corrective regression evidence: the initial shared `str.isdigit()` matcher
broadened fallback discovery to Unicode digit tags such as `exercise²`, unlike the
original regex full-match, which matches Unicode decimal digits but not superscript
digits. The public fallback test includes that superscript tag beside valid
string-valued markdown/code tags and asserted it was
ignored. Restoring the regex predicate for fallback and keeping readability's
consumer-local legacy predicate yielded 91 focused tests passed. This correction was
Batch A only; B and C were still pending at this historical checkpoint. Batch B
subsequently resolved its Pyright debt, as recorded in its delivery evidence.

Batch D narrows that helper module to the source type guard, which genuinely has
two consumers. Runtime tag matching and readability list-source joining are now
consumer-local; the above describes Batch A's delivered checkpoint, not the current
helper API.
Final green documentation review corrected the regex's Unicode decimal-digit
description and updated `SPEC.md` from the obsolete planning-only status; no
predicate or runtime behavior changed.
Final independent GREEN re-review is clean for all Batch A IDs. The reviewer
confirmed both parser-preservation regressions and all documented adjudications.
Batch A delivered on `feat/AddLinterRulesToSelfChecker`:
`45915b58cecf9e89737902ed23ee54e2c8151314` —
`Simplify readability parsing and preserve discovery contracts`.
`git push` succeeded (`bef9667..45915b5`); the user-owned config was not staged.

### Batch B — orchestrator and public-behaviour tests (R3, R4, Y1–Y8, N7–N9)

**Objective:** remove private-test coupling, pyright errors and row-construction
duplication while keeping current output identical.
**Surfaces:** `exercise_runtime_support/student_checker/{notebook_runtime,reporting}.py`,
`exercise_runtime_support/exercise_framework/reporting.py` (N7 status owner and
N8 public table docstring/`Iterable`),
`tests/exercise_runtime_support/test_student_checker_{notebook_runtime,reporting}.py`,
`tests/exercise_framework/test_reporting.py` (N9 casing duplicates),
test-only row parser under `tests/` if justified, and
`tests/template_repo_cli/test_packaged_readability.py` for count assertions.
**Acceptance:** public-path tests cover fallback/local support, retries, errors,
student/solution variant, table header/status, multi-check cell interleaving and
no footer; no private-usage suppressions anywhere in scoped tests; scoped pyright
clean including baseline eight and new 15 reported errors (re-measure). Distinct
functional-only reporting remains distinct where necessary. **Checks:** support
suite, offline export fixture, real solution/student exemplars, full validation
ladder. **Review point:** Tidy RED and GREEN review confirms no tautological
assertions, weakened evidence or unintended table changes.

Batch B baseline evidence: the scoped baseline
reported 23 Pyright errors in
`tests/exercise_runtime_support/test_student_checker_notebook_runtime.py` (eight
existing and 15 newly introduced diagnostics). All direct runtime-helper calls and
`reportPrivateUsage` ignores were removed from that test file; public
`run_notebook_checks()` regressions retain static-vs-input execution, input-call
detection, retry/backfill and limit/error behaviour, plus malformed notebook loading
and reporting checks. Existing public behavior was green at baseline, so no
artificial failing test was introduced. The tests-only slice now passes 183 tests
across `tests/exercise_runtime_support/`, framework reporting and packaged
readability; scoped Pyright reports zero errors on the four touched Python tests,
and scoped Ruff lint/format plus `git diff --check` pass. The exported functional
row expectations derive from the source exercise's functional results rather than
frozen 14/16 counts. Existing public behaviour was already green, so no artificial
RED was introduced; the scoped Pyright debt was the measurable failing baseline.

Reviewer follow-up corrections (tests only): long feedback now reconstructs exactly
for both ordinary and tooling-error output, stopping at the next non-continuation
table row; exported status checks compare the Status column exactly to `🟢 OK` or
`🔴 NO`; the ex015 solution test derives task-row labels from the saved solution's
tagged code cells and still requires exactly one E501-failing readability row; the
renderer casing test snapshots and checks the caller's mutable row list; and variant
fallback asserts the resolved value is a `Path`. Restored the missing-cell-type
malformed-notebook fixture and removed duplicate no-footer assertions. The focused
suite passes 183 tests, scoped Pyright is at zero, repository Ruff, scoped format
and `git diff --check` pass. No production finding is resolved by this test-only
follow-up.

Additional reviewer correction: the ex015 backlog test now asserts the functional
result collection is non-empty before requiring all checks to pass. The fallback
execution-selection and explicit-solution tests now assert `Path` type and exact
path equality inside the static, interactive, and source-extraction doubles before
recording arguments; no `Path(value)` normalization can mask a string argument.
The full scoped test slice remains 183 passed, scoped Pyright remains zero, and
repository Ruff, scoped formatting and diff checks pass. This strengthens test
evidence before Batch B production implementation.

Batch B implementation evidence: functional task identity is carried beside its
row rather than recovered by zipping rows/results; the active variant is threaded
through fallback counting, source extraction, static execution and interactive
retries. A shared header printer preserves header/table/error ordering. Functional-
only reporting intentionally remains separate because its grouped labels and
success message differ from notebook interleaving. The neutral status is owned with
sibling status constants, the framework table docstring names all four columns,
and its generator-friendly `Iterable` API is retained. A small test-only output
helper shares footer assertions; the mutable caller-row-list assertion remains,
and exported functional statuses derive from actual exercise results.

Validation with pytest's repository `addopts` disabled to expose summaries:
`uv run pytest tests/exercise_runtime_support/ tests/exercise_framework/test_reporting.py tests/template_repo_cli/test_packaged_readability.py tests/test_readability_table.py -q -o addopts=''` reports 186 passed;
`uv run python scripts/run_pytest_variant.py --variant solution -q -o addopts=''`
reports 1,618 passed and 1 skipped; `uv run pytest --collect-only -q -o addopts=''`
reports 1,619 collected. Scoped Pyright is zero; repository Ruff, scoped format,
`uv lock --check` and `git diff --check` pass. At this Batch B validation handoff,
the reviewer requested documentation wording/count corrections. Those were
completed and reviewed before the Batch C handoff; the current Batch B status above
is clean. No commit or push was made at this historical checkpoint.

### Batch C — export fixture and documentation truth (Y9–Y11, N10–N17)

Batch B delivered on `feat/AddLinterRulesToSelfChecker`:
`6449c6508635810064389cc14dafe0b69445df9f` —
`Simplify self-check orchestration and public behavior tests`.
`git push` succeeded (`3b434c5..6449c65`); user-owned config remained unstaged.

**Objective:** prove omission of the repository-only classified hidden fixture
from the packaged synthetic export, and align live guidance and historical claims
with delivered behaviour. Canonical exercise-local `test_<exercise_key>.py` files
remain intentionally visible in exports; this is not a general hidden-test
exclusion contract.
**Surfaces:** `tests/template_repo_cli/test_packaged_readability.py`,
`docs/developers/{execution-model,testing-framework}.md`,
`template_repo_files/{fixing-readability-issues.md,README.md.template}`,
`AGENTS.md`, root `SPEC.md`, `ACTION_PLAN.md`, `REVIEW_FINDINGS.md`.
**Acceptance:** a real repository-only `test_repo_hidden_fixture.py` remains absent
in export, while canonical exercise-local tests are preserved by the packaging
contract; guide example and anchor parity checks remain substantive. README/guide
avoid a fictional overall footer, inaccurate one-cell-per-task claims and incorrect
trailing-whitespace locations. Execution/export/variant behavior has one owner and
the testing guide owns focused readability details. N15 is resolved by the user's
decision to retain the already committed four-file model changes; do not edit any
`.opencode` file and leave the dirty reviewer-model change unstaged. Accurate 3.14
guidance retained. **Checks:**
offline export test and guide real-Ruff examples, doc/link review, full shared
ladder and branch-vs-main diff audit. **Review point:** Tidy RED/GREEN, then
reviewer sign-off on each adjudication, especially config preservation.

Batch C RED/baseline evidence: the packaged readability test was already green
(5 passed), so no artificial RED was introduced. Its synthetic exercise fixture
contains a real, minimal repository-only test source named
`test_repo_hidden_fixture.py`; the packaged test asserts that exact source file is
absent while canonical metadata/student notebook paths and isolated exported
checker invocation remain covered. This does not claim arbitrary exercise tests
are hidden: canonical exercise-local `test_<exercise_key>.py` files are visible in
the student export by design. Collector imports are module-scoped. N10 and Y9 are
verified complete; the baseline test did not modify production packaging or
scoring.

Batch C implementation evidence (substantive GREEN review clean; status-only
re-review was pending at this historical checkpoint): the execution model linked to
the testing framework for self-check presentation detail; the testing framework
owns the detailed readability policy and explicitly permits substantive Ruff
example and anchor/index parity checks while rejecting presence-only/vocabulary
claims. The student guide described rows as task-labelled, corrected trailing
whitespace to occur after the closing parenthesis, and the README no longer claimed
an unprinted overall result. `AGENTS.md` links the renamed guide. N15 retains the
user-approved committed model deltas without touching `.opencode/`; N16 retained
Python 3.14 based on manifest/runtime-pin evidence; N17 added one concise pointer.
N11–N14 were implemented; the real-Ruff example and anchor/index-parity suite
passed. The template CLI suite, full solution variant, collection, Ruff, scoped
Pyright, formatting, lock and diff checks passed. Independent review found the source,
tests and documentation substantively clean; only the stale status record was
actionable and has been corrected. The final independent re-review is limited to
these status updates. Commit and push were pending at this historical checkpoint;
they subsequently succeeded as recorded below. No publication or deployment was
performed.

## Final independent review and handoff

### Final documentation and whole-branch review

Docs added one clarification in `docs/developers/testing-framework.md`: tag
discovery and loading remain consumer-local because the existing fallback and
readability semantics differ; only the source type guard is shared. Independent
Tidy review of that hunk and the complete branch diff is clean. All 42 ledger
items (the original 32 plus F1–F10) have individually verified dispositions.

Final reproduced validation: 1,624 solution tests passed and one skipped;
1,625 tests collected; the wider support/reporting/export/quality slice passed
329 tests. Pyright reports zero errors across all 17 branch-changed Python files;
repository Ruff, scoped formatting, lock and diff checks pass. The exercise-quality
verifier reports 18 exercises with zero errors or warnings. Explicit student
sequence/selection tests retain their expected 30/33 failures.

Final documentation delivered on `feat/AddLinterRulesToSelfChecker`:
`5ade6bdbb04efd67462c29c8ab5b9659aaa93adb` —
`Document preserved notebook discovery contracts and final validation`.
`git push` succeeded (`fcca9a0..5ade6bd`). All sections, cleanup confirmations
and final documentation review are complete; no review findings remain open.
The user-approved committed model changes remain; the separate dirty
reviewer-model setting is untouched and unstaged. Human teacher review before
guide publication and the separately deferred solution-readability correction
pass remain outside this cleanup. No publication, deployment or notebook edits
were performed.

Final independent de-sloppification is clean: F1–F9 were resolved in `37fc764`,
and F10's count-independent plan wording passed both Tidy review and a fresh
de-sloppification confirmation. No source/test changes followed that confirmation.
At that checkpoint the branch was ready for documentation sync, now completed
and reviewed clean as recorded above; the user-owned config remains
untouched and unstaged.

### Batch D — final audit follow-ups (F1–F9)

Objective: resolve all nine final audit findings in `REVIEW_FINDINGS.md`, without
changing runtime behavior or expanding catalogue scope. Keep shared source typing,
but inline single-consumer tag/source helpers. Remove unused test parameters and
redundant assertions; strengthen the footer-helper test with rejection coverage.
Consolidate diagnostic decoding into one validated construction pass, preserving
error classes, message text and ordering. Correct live delivery statements, remove
the deleted-document comment reference, and separate long-message repetition from
the wrapped-line threshold. No new dependencies, suppressions, config changes,
notebook edits or grading changes.

Sequence: Testing Specialist added footer-rejection coverage and recorded the
already-green source/diagnostic baselines; Tidy reviewed RED/baseline; the
Implementer addressed F1–F9. Independent GREEN review and validation were pending
when this sequence was drafted; both are now complete and clean. Delivery succeeded
before a fresh independent cleanup review and final Docs sync.

Batch D baseline and implementation handoff: four focused test files were already
green, so no artificial RED was introduced. The six footer-rejection cases are
meaningful independent coverage. The source guard module now exposes only its
two-consumer `is_source` TypeGuard; regex tag matching and source joining are
consumer-local. Ruff diagnostics are validated and converted to findings in one
ordered pass. The F1–F9 implementation dispositions have independent GREEN
approval; validation is complete as recorded below. The dirty reviewer-model file and
committed model changes remain untouched.

Batch D validation: the focused changed-file suite reports 239 passed; the wider
support/reporting/export/quality slice reports 329 passed. Separate commands report
159 passes for `tests/exercise_runtime_support/` and 137 for
`tests/test_verify_exercise_quality.py` (these scopes are distinct, not additive to
the wider overlapping slice). Scoped Pyright reports zero errors; repository Ruff,
scoped format, `uv lock --check` and `git diff --check` pass. Collection reports
1,625 tests; the full explicit solution run reports 1,624 passed and 1 skipped.
Explicit student sequence and selection runs retain their expected 30 and 33
failures. The initial nested reviewer request hit the subagent depth limit;
the orchestrator's subsequent independent review and re-review are clean.

Batch D delivered on `feat/AddLinterRulesToSelfChecker`:
`37fc76444100702d11aae98a7f4f00db75acc50b` —
`Resolve final readability cleanup audit findings`.
`git push` succeeded (`dd24a5d..37fc764`); user-owned config remained unstaged.

Batch C delivered on `feat/AddLinterRulesToSelfChecker`:
`f73f95746f01c8672fc6e6af2efb3080f5cc2ec0` —
`Align readability documentation and exported fixture coverage`.
`git push` succeeded (`d0c621c..f73f957`); user-owned config remained unstaged.

After all batches are genuinely clean and pushed, call De-Sloppification
**read-only** on the complete resulting diff. If it finds actionable issues,
route focused fixes through Testing Specialist/baseline → Tidy RED → Implementer
→ Tidy GREEN repeat → checks → ledger/plan → authorised commit/push as an
additional batch; do not silently dismiss them. Then Docs reviews changed
contracts/`AGENTS.md` and handoff; any Docs edits get Tidy re-review and checks,
with an explicit delivery record. Validate `git diff main...HEAD`, branch status,
solution suite, scoped pyright, Ruff, collect-only and representative expected
student failures; report any N15 user-decision blocker honestly. Do not deploy,
publish templates, change scoring or author exercises. No separate layout/workflow
spec is necessary: notebook layout and export mapping remain canonical.

## Historical feature delivery tracker (archival; superseded by current contract)

Implement the requirements in `SPEC.md` locally and sequentially. This handoff
contains no runtime implementation or test code. No separate layout/workflow
specification is required: notebook structure and authoring workflow stay unchanged.
Treat exercise structure as a scaffolding/authoring guarantee. This feature adds no
task-count or tag-topology validation, structural FAIL rows or malformed-exercise tests.
The stage counts and validation totals below are contemporaneous snapshots from
their respective delivery points, not current post-clean-up results. Current
requirements and status are only those stated above and in the current section of
`SPEC.md`.

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
