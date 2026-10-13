# Final review findings: disposition ledger

Batches A and B are reviewed clean, committed and pushed. Batch C baseline,
implementation and checks are complete; substantive GREEN review is clean and
independent re-review is pending only to confirm corrected status records. Commit
and push remain pending the established delivery workflow. The user approved
retaining the committed model changes (N15).
Line references describe the original review baseline,
not immutable positions. Each Batch A disposition below records implementation
evidence; delivery details are recorded in `ACTION_PLAN.md`.

## Batch A — analyser and shared task discovery

| ID | Finding / baseline evidence | Resolution criterion |
| --- | --- | --- |
| R1 | `exercise_runtime_support/student_checker/readability.py:141–142` catches `ModuleNotFoundError` although `subprocess.run` cannot raise it for a missing `-m ruff`; `tests/exercise_runtime_support/test_student_checker_readability.py:391–403` fabricates that exception. | Remove impossible catch/test case; simulate real child exit/stderr for missing Ruff, retain `FileNotFoundError` for missing interpreter, and assert explicit tool error. |
| R2 | `readability.py:195–211` reimplements saved notebook reading, source guards and tag selection already in `notebook_runtime.py:72–81,94–95,156–198`. Fallback tag collection currently scans all cell types (`:191–197`), whereas readability selects code only. | Share minimal saved-cell reading/tag/source primitives or a task-code iterator where compatible; retain fallback's established cell-type scope and string-valued tag support (`notebook_runtime.py:181–188`), exact `exerciseN` matches, physical indices and source joining; no new malformed topology checks or loosening of existing fail-fast errors. |
| Y5 | `readability.py:99–100` promises one-based cell display; `:146` shows a zero-based tool-error cell label. | Correct public docstring and error label to observed current output contract (one-based error reference); keep internal zero-based index and table's task-only label. |
| N1 | `readability.py:155–159` has redundant `diagnostic: object = item` and repeats invalid-JSON message. | Simplify validated diagnostic handling and error text without weakening malformed-output rejection; prove via existing invalid-record cases. |
| N2 | `student_checker/checks/__init__.py:8–10` uses a multi-line import for the single name `active_variant_context`; the earlier transcription cited `notebook_runtime.py:8–10`, which holds unrelated imports. | Format as one line if Ruff format accepts it. |
| N3 | `readability.py:40–44` uses a one-field `NotebookAnalysis` wrapper. | Inspect consumers (`notebook_runtime.py:296–320`, tests) before changing; retain if stable public result shape/clear ownership outweighs an extra wrapper, otherwise simplify call sites together; record the reason and preserve ordered immutable cells. |
| N4 | `test_student_checker_readability.py:36–38` defines `_SECOND_LINE`, `_OPERATOR_COLUMN`, `_TWO_CELLS` solely for small literal test assertions. | Inline self-explanatory literal expectations where clearer; retain only if reuse has real semantic value. |
| N5 | `test_student_checker_readability.py:73–75` imports `ast` inside a single test branch. | Move import to module scope; Ruff clean. |
| N6 | `test_student_checker_readability.py:130–146` uses a string tag in a non-nbformat-like fixture and repeats markdown exclusion. | Preserve string-tag compatibility already supported by fallback; isolate it as a legacy accepted-representation test with realistic fixture where feasible; remove duplicated markdown check only when other test retains it. No new tag validation. |

### Batch A disposition evidence

- **R1 — resolved:** removed the impossible `ModuleNotFoundError` catch and its
  fabricated subprocess-exception case. Missing Ruff is exercised as a child
  result with exit code 1 and stderr; missing interpreter remains a
  `FileNotFoundError`. The focused readability suite passes.
- **R2 — resolved:** `student_checker/_notebook_cells.py` owns source type narrowing
  and direct joining of list-valued source. Fallback discovery retains the shared
  anchored regex full-match predicate, equivalent to its former `^exercise\d+$`
  behavior; readability retains its original `startswith("exercise")` plus
  `isdigit()` predicate locally. Keeping those predicates consumer-local avoids
  broadening fallback discovery to Unicode digit tags (for example `exercise²`).
  Their tag-container handling remains consumer-specific: fallback validates
  string/list-of-string tags and returns no tags for other forms, while readability
  retains its previous fail-fast behaviour for a non-string list item. The fallback
  still checks valid cell objects across all types; readability still filters to
  code cells. Both retain string-valued tags. Notebook JSON loading remains
  consumer-local: the fallback reports `NotebookGradingError` for validated
  malformed/missing data while readability preserves direct JSON parsing
  behaviour; one common loader would alter established failures without adding a
  useful shared primitive. Existing source-preservation tests pass.
- **Y5 — resolved:** tool failures label `cell_index + 1`; internal indices remain
  zero-based. `analyze_source` now documents that split explicitly: tool errors use
  one-based physical cell numbers, while normal rows omit cell numbers and identify
  the task. The physical-cell-2 regression passes.
- **N1 — resolved:** removed the redundant object annotation and centralised the
  invalid-diagnostic message; malformed JSON and malformed diagnostic records
  remain rejected by existing tests.
- **N2 — resolved:** the sole `active_variant_context` import is one line.
- **N3 — retained with evidence:** `NotebookAnalysis` is the immutable ordered
  result returned by `analyze_notebook` and consumed by the notebook orchestrator;
  analysis tests exercise its `.cells` result. Keeping the result type makes the
  analyser boundary explicit rather than coupling callers to a bare tuple, with
  no behavioural benefit from removal.
- **N4 — resolved:** `_SECOND_LINE`, `_OPERATOR_COLUMN` and `_TWO_CELLS` are absent;
  the former one-off values are direct, contextual assertions.
- **N5 — resolved:** `ast` is imported at test-module scope.
- **N6 — resolved:** the string-valued tag regression uses a complete notebook
  cell object. Shared tag extraction accepts this established representation;
  fallback public-path coverage confirms tags on markdown and code cells, while
  readability selection independently confirms markdown exclusion.
- **GREEN review follow-up — resolved:** added regression
  `test_invalid_tag_item_preserves_existing_fail_fast_error` confirms readability
  still raises `AttributeError` for `metadata.tags == ["exercise1", 1]`.

- **Batch A GREEN correction — resolved:** review of the fallback public-path
  regression exposed that sharing readability's `str.isdigit()` predicate had
  broadened the fallback's prior regex full-match behavior to superscript digits.
  The regression now asserts `exercise²` is ignored while valid string-valued tags
  on markdown and code cells are discovered. The fallback predicate is again the
  shared anchored regex; readability's historical predicate remains local. Focused
  readability and notebook-runtime tests pass (91 passed). This records only the
  Batch A correction; it does not resolve or close any Batch B/C findings.

Verification after implementation: focused readability and notebook-runtime
tests pass (91 tests). The full `tests/exercise_runtime_support/` suite passes;
scoped Pyright reports zero errors for the shared modules, readability tests and
notebook runtime; scoped formatting, repository-wide Ruff, `uv lock --check`,
collection, explicit solution validation and `git diff --check` pass. The separate
Batch B notebook-runtime test file retains its recorded 23 Pyright diagnostics
(8 original and 15 Batch B-owned). The Batch A public fallback assertion in that
test file does not change those Batch B-owned diagnostics; GREEN did not edit those
diagnostic regions.

## Batch B — integration, presentation and test quality

| ID | Finding / baseline evidence | Resolution criterion |
| --- | --- | --- |
| R3 | `test_student_checker_notebook_runtime.py:103,143,961,991,1025` puts pyright ignores on preceding lines; private calls also appear at `:177,197,229` and other same-line usages. Earlier eight baseline diagnostics plus introduced diagnostics are not a waiver. | Eliminate **all obsolete/private-usage suppressions** in this scope, use public `run_notebook_checks`-level behaviour tests in place of private calls, and attain zero errors from scoped pyright including previous baseline; preserve meaningful retry, parse and error-path coverage. |
| R4 | `test_student_checker_notebook_runtime.py:487` infers `row_lines = []` as unknown in scoped pyright (13 errors reported); new private calls at `:479,481` add two errors; total reported 23 = eight baseline + fifteen introduced. | Type the row collection appropriately or use a typed parsing helper; replace private printer calls with public output paths; capture fresh scoped pyright results rather than treating counts as fixed. |
| Y1 | `notebook_runtime.py:303–311` zips row tuples with original results to recover task identity by `isinstance`. | Carry tag identity alongside functional rows or simplify inline orchestration so identity is computed once; maintain one readability row per physical cell and order across both dispatches. |
| Y2 | `notebook_runtime.py:149,321` duplicates header; `:285–289` has a one-caller printing wrapper. | Share tiny header printing or use one clear print site; inline single-use wrapper if clearer; keep functional rows before tool ERROR and header once. |
| Y3 | `notebook_runtime.py:339–353` and `student_checker/reporting.py:93–110` both build exercise rows, but the latter collapses repeated labels while the notebook checker interleaves readability. | Review actual users; share only compatible row conversion, otherwise document deliberate grouping difference in concise code/API comment; never change functional-only congratulations or interleaving. |
| Y4 | `notebook_runtime.py:215,235,256` repeatedly reads variant while inside `active_variant_context()` at `:135`. | Thread selected `Variant` through fallback execution chain; keep default student for notebook self-check and unchanged environment restoration/solution-default repository runner. |
| Y6 | `test_student_checker_notebook_runtime.py:883` asserts a substring already present in the input key; `:463–464` repeats no-footer assertions; `:455` repeats readability assertion. | Remove tautology and redundant assertions while keeping meaningful construct coverage, both no-footer paths and row evidence. |
| Y7 | Table-row parsing repeated in `test_student_checker_notebook_runtime.py:486–496,870–877,905–912`, `test_packaged_readability.py:122–131`, and no-footer assertion lists. | Introduce minimal test-only helper under `tests/` only if it genuinely reduces repeated logic without obscuring status/column meaning; retain independent source/export assertions; type it for pyright. |
| Y8 | `test_packaged_readability.py:18–20` freezes starter 14/16 pass/fail counts; runtime tests `test_student_checker_notebook_runtime.py:16,858` repeat a 30-check assumption. | Derive expected results from actual exercise checks or fixture data, while independently checking export invocation, statuses and count; do not make comparison tautological or change notebooks. |
| N7 | Neutral `⚪ NOT CHECKED` is inline at `exercise_framework/reporting.py:22` (`format_status`) versus sibling status constants at `:12–15` of the same module; `notebook_runtime.py:329` holds the unrelated syntax-blocked message string. | Reuse existing status rendering owner where it fits; do not create a constant solely for a single occurrence; confirm emitted status unchanged. |
| N8 | `exercise_framework/reporting.py:84–91` (`render_grouped_table_with_errors`) docstring omits the four rendered column headers; `Iterable` annotation at `:85` has no known generator caller; the earlier transcription cited `student_checker/reporting.py:87–91`, the thin `print_exercise_results` wrapper. | Clarify docstring/column semantics; inspect callers before narrowing `Iterable`, preserve it if a deliberate small API that accepts generators; record evidence. |
| N9 | `tests/exercise_framework/test_reporting.py:70–75` casing test re-asserts the column-width wrap (`:74`) and input-row non-mutation (`:75`), duplicating the dedicated wrap tests; the earlier transcription cited `test_student_checker_reporting.py:70–75`, an unrelated success-message test. | Remove only proven duplicate checks, retaining one test per behaviour and public API contract. |

### Batch B dispositions and local evidence

- **R3 — resolved locally:** removed all direct private runtime calls and
  `reportPrivateUsage` ignores from the scoped runtime test module. Public
  `run_notebook_checks()` cases retain static and input-driven execution, retries,
  max-input handling and execution errors. Scoped Pyright now reports zero errors
  across changed source and tests; no suppression was added.
- **R4 — resolved locally:** output parsing no longer uses an untyped accumulator;
  the tests use explicit types and the small `tests/readability_table.py` helper
  for shared footer assertions. Scoped Pyright is zero.
- **Y1 — resolved locally:** each functional row carries its task tag at creation;
  orchestration no longer zips rows to results or reconstructs task identity via
  `isinstance`. Existing output ordering tests remain.
- **Y2 — resolved locally:** normal and tool-error paths use one header printer;
  error path still prints header, completed functional rows, then ERROR/re-raises.
- **Y3 — retained with reviewer approval:** functional-only `student_checker.reporting`
  collapses repeated exercise labels and retains congratulations; notebook
  reporting deliberately interleaves per-task functional and readability rows
  and owns its header/table. A concise comment now records the distinct grouping
  policies. The differing contracts make a shared row converter inappropriate;
  no output behaviour was merged.
- **Y4 — resolved locally:** selected `Variant` from the active context is passed
  explicitly into fallback tag execution, `input()` source extraction, static
  execution and interactive execution/retries. No helper rereads the environment.
  Public-path tests verify student/solution selection and exact `Path` boundaries.
- **Y6 — resolved in tests:** preserved nonempty functional backlog assertions and
  output/order checks while redundant no-footer and already-tautological checks
  were removed in the delivered test slice.
- **Y7 — resolved locally:** `tests/readability_table.py` provides typed grid-row
  parsing and a shared no-footer assertion used by runtime and packaged tests.
  It replaces repeated feedback-column parsing in those surfaces and remains under
  `tests/`, not copied into templates; substantive table/status assertions remain
  at each owning test.
- **Y8 — resolved in delivered tests:** exported functional statuses are obtained
  from `run_exercise_checks()` for the actual source exercise, and the backlog
  collection is asserted nonempty before requiring the expected outcome. No
  notebook or fixed pass/fail counts were changed.
- **N7 — resolved locally:** `NOT_CHECKED_STATUS` is a module-level `Final` adjacent
  to the sibling status constants and is returned by the existing renderer;
  neutral visible text remains unchanged.
- **N8 — resolved locally:** the public renderer docstring names Exercise, Check,
  Status and Error, and explains `None`, feedback casing and generator support.
  `Iterable` is retained as the useful public input contract; a one-shot iterator
  test confirms iterable support.
- **N9 — resolved in delivered tests:** caller-owned mutable rows are still
  snapshotted/asserted unchanged. The duplicated wrap assertion was removed from
  casing coverage; dedicated wrap tests continue to own width behavior.

Validation with pytest's configured `addopts` disabled for visible summaries:
`uv run pytest tests/exercise_runtime_support/ tests/exercise_framework/test_reporting.py tests/template_repo_cli/test_packaged_readability.py tests/test_readability_table.py -q -o addopts=''` reports 186 passed;
`uv run python scripts/run_pytest_variant.py --variant solution -q -o addopts=''`
reports 1,618 passed and 1 skipped; `uv run pytest --collect-only -q -o addopts=''`
reports 1,619 collected. The complete support/framework/template-CLI suite passed;
scoped Pyright reports zero errors on touched production and tests; repository
Ruff, scoped format, `uv lock --check` and `git diff --check` pass. Independent
GREEN review and documentation re-review are clean for every Batch B ID.
Batch B was committed as `6449c65` and pushed successfully; `d0c621c` records
the delivery evidence.

## Batch C — exported fixture and documentation consistency

| ID | Finding / baseline evidence | Resolution criterion |
| --- | --- | --- |
| Y9 | `test_packaged_readability.py:206–214` names a non-existent synthetic repository-only fixture file, while `:245` asserts empty exported tests. | Create a minimal test source classified by the existing `test_repo_*.py` exclusion and verify that exact file is omitted from export while canonical metadata/student paths remain covered. Do not generalise this to canonical exercise-local tests or change production packaging/scoring. |
| Y10 | `docs/developers/execution-model.md:101–115` and `docs/developers/testing-framework.md:141–198` repeat presentation/readability policy. | Keep execution/variant/export mapping in canonical execution-model doc and one focused detailed policy in testing-framework, cross-link instead of maintaining duplicate wording; verify statuses and table-only output accurately documented. |
| Y11 | `docs/developers/testing-framework.md:197–198` bans Markdown-string assertions despite real `test_ruff_guide.py:77–100` checking code-index anchor/link parity. | Limit prohibition to mere file-presence/vocabulary-as-semantic-proof tests; explicitly allow substantive anchor/link parity and real Ruff examples. |
| N10 | `test_packaged_readability.py:26,161` has local collector imports. | Move to module imports if dependency order permits; keep offline test isolation. |
| N11 | `template_repo_files/fixing-readability-issues.md:344` says closing bracket, while example ends in `"` followed by `)`. | Say line ends immediately after the closing parenthesis; ensure guide example still produces expected Ruff diagnostic. |
| N12 | Same guide `:8–9` implies one code cell per task. | Describe task-labelled readability rows without asserting a one-cell-per-task structural invariant; keep line/column explanation. |
| N13 | `template_repo_files/README.md.template:5–9` wraps `reported issues; save` awkwardly and claims an overall pass not printed in the table-only checker. | Reflow and describe per-task results without a fictional printed overall result; maintain root guide link. |
| N14 | `SPEC.md:279–325` and `ACTION_PLAN.md:392,422` retain superseded `RUFF_GUIDE.md` and past footer/summary requirements despite the delivered `fixing-readability-issues.md`. | Mark historical sections explicitly archival, add current authoritative clean-up contract; correct live guidance rather than silently rewriting historical delivery ledger. |
| N15 | `16a2184` changed four committed `.opencode/agents/{docs,implementer,testing-specialist,tidy-code-reviewer}.md` models, conflicting with historical config-exclusion claim; current dirty reviewer model is user-owned. | User explicitly approved retaining the already committed four-file model changes. Treat them as intentional branch scope; do not edit any `.opencode` files, touch the dirty reviewer setting, or rewrite history. Correct historical exclusion claims and report the preserved dirty state accurately. |
| N16 | `AGENTS.md:1,97,116` title/version edits versus `main` might look like drive-by changes, but repository runtime pins target Python 3.14. | Compare with runtime pins/tests and current contributor guidance before deciding; retain accurate 3.14 guidance, avoid reverting to an incorrect 3.11 claim; correct title only if evidence warrants. |
| N17 | `AGENTS.md` lacks concise discoverability for the readability self-check and renamed guide. | Add brief accurate pointers without duplicating the 17-rule policy or changing notebook guidance. |

## Execution evidence and constraints

### Batch C dispositions (implementation/checks complete; independent re-review clean)

- **Y9 — verified complete:** the synthetic fixture contains the real
  `tests/.../test_repo_hidden_fixture.py` source and asserts that exact file is
  omitted in export. This is the explicit repository-only hidden-fixture
  classification already enforced by the existing `test_repo_*.py` exclusion;
  it does not imply arbitrary exercise-local tests are hidden. Canonical
  `test_<exercise_key>.py` tests remain intentionally included in packaged output.
- **Y10 — resolved:** execution-model owns execution, variants and mapping;
  testing-framework owns detailed readability output/policy, linked from the
  execution contract. The links and rendered wording were reviewed.
- **Y11 — resolved:** documentation forbids presence-only and isolated
  vocabulary/prose checks as behaviour proof, while explicitly allowing the
  substantive real-Ruff example and guide anchor/index-parity tests. Those tests
  pass.
- **N10 — verified complete:** `ExerciseFiles` and `FileCollector` imports are
  already at module scope; no test code change was needed for this finding.
- **N11 — resolved:** both guide descriptions correctly place trailing whitespace
  after the closing parenthesis; the real-Ruff guide tests pass.
- **N12 — resolved:** guide task wording refers to task-labelled rows and task
  code without asserting one physical cell per task; line/column scope is retained.
- **N13 — resolved:** README prose is reflowed, keeps its root-relative guide
  link, and no longer claims a printed overall result.
- **N14 — resolved:** current SPEC/ACTION_PLAN sections are authoritative;
  historical feature specification and delivery tracker are explicitly archival.
  Historical counts and stage details are preserved as past evidence, not current
  status or policy.
- **N15 — resolved by user decision:** retain the four already-committed model
  changes. No `.opencode` files were edited; the dirty reviewer model remains
  user-owned and unstaged. Branch is not described as wholly excluding config.
- **N16 — retained with evidence:** Python 3.14 is required by both manifests,
  devcontainer pins and `tests/test_runtime_python_version.py`; no version text was
  reverted. The root title remains the project name.
- **N17 — resolved:** `AGENTS.md` now points to the renamed student guide and
  the detailed testing-framework policy without duplicating the rule list.

- **GREEN review:** source, tests and documentation are substantively clean. The
  only reported issue was stale progress/status bookkeeping; ACTION_PLAN, SPEC and
  this ledger now agree, and the status-only independent re-review is clean.

- **Baseline/fixture note:** Y9 and N10 were already present in the supplied
  working tree and tested by the baseline; no new test, dependency, production
  packaging behavior, scoring behavior, or `.opencode` edit was introduced here.

- Batch A/B/C mapping above covers R1–R4, Y1–Y11 and each N1–N17. Any finding found invalid needs an evidence-backed, individually reviewed disposition here, not deletion from this inventory.
- Do not change notebook/exercise catalogue, teacher-side scoring or deployment; do not add dependencies, compatibility wrappers or suppressions. Preserve exact Ruff selection, source-preserving saved-cell analysis, table-only output, syntax `NOT CHECKED`, functional-only grading and canonical-only export.
- Scoped pyright must be clean on touched implementation and tests, **including** old private-access errors; `uv run ruff check .`, appropriate `uv run ruff format --check <touched Python files>`, targeted pytest, collect-only and full solution runner form the validation ladder. Student exercise failures are expected and must not be silenced.
- Working-tree `.opencode/agents/tidy-code-reviewer.md` is user-owned and must remain untouched/un-staged. The user approved keeping the separate committed model changes (N15); no config/history rewrite, deploy or PR is needed.
