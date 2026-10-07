# Per-task Ruff readability feedback

## Goal and intended outcome

Extend the notebook self-checker with required Ruff PASS/FAIL checks for each
student task cell, supporting the WJEC GCSE Computer Science readability criteria
that Ruff can check mechanically. Provide a student guide explaining every enabled rule through
a non-example and a corrected example. Present readability alongside functional
results: a task and the overall notebook self-check pass only when both pass.
Functional assertions and teacher-side scoring remain independently defined.

This specification covers shared repository tooling, reporting, documentation and
template packaging, not new exercise authoring. It applies to every construct and
canonical exercise key; there is no new exercise key or teaching-order change.

## Current state and evidence

- `exercise_runtime_support/student_checker/notebook_runtime.py:108–121` exposes
  `run_notebook_checks(exercise_key)`, prints results and returns `None`. Its
  exercise-local-support branch returns early; integration only in the fallback
  would miss supported exercises.
- `exercise_runtime_support/student_checker/checks/__init__.py:81–108` defaults
  self-checks to the student variant and honours `PYTUTOR_ACTIVE_VARIANT`. The
  generic fallback currently hard-codes student resolution and execution.
- `exercise_runtime_support/notebook_grader.py:70–116` inserts source separators
  and strips surrounding whitespace. It is not a source-preserving lint reader.
- `pyproject.toml:10–17,52–65` declares Ruff, excludes notebooks and ignores
  `E501`; maintainer lint configuration is unsuitable for student feedback.
- `uv.lock:1210–1211` locks Ruff to 0.14.13. The source and
  `template_repo_files/pyproject.toml` currently specify a minimum, not an exact pin.
- Existing solution notebooks were not authored against this student-readability
  policy and may fail its selected checks. Their readability findings are known
  migration work, not evidence that their functional solutions are incorrect.
  They will be resolved in a separate future notebook-review pass, not this feature.
- `scripts/template_repo_cli/core/packager/__init__.py:182–280` explicitly copies
  base files and shared runtime packages. A new top-level guide must be explicitly
  added to the base-asset copy list; it will not ship automatically.
- `template_repo_files/README.md.template` supplies the generated student README.

Investigation hypothesis: a shared checker extension can cover all exercises
without editing their checker cells. The dispatch and packaging checks above
support that approach, but disconfirm automatic coverage through the fallback
alone and automatic export of a new guide.

## Scope and non-goals

### In scope

- Static readability analysis of saved, tagged task code, per physical cell.
- Four-space indentation, selected whitespace checks, a 100-character line limit,
  and limited Python naming conventions.
- Required task-level readability PASS/FAIL rows alongside functional checks, with
  diagnostics and one combined exercise-level self-check result.
- A single student guide, available in source and exported repositories.
- Exact Ruff version pinning, infrastructure tests and exported-template checks.

### Out of scope

- Abbreviation dictionaries, custom identifier heuristics, meaningful-name scoring,
  comment quality, required comments/docstrings, type annotations and Pyright checks.
- Automatic formatting/fixes, formatter-compliance checking or notebook mutation.
- Grading penalties, changes to hidden tests, quality-gate scoring or Classroom 50
  result payloads; cross-exercise dashboards and new public checker entry points.
- Live editor-buffer analysis, editor extensions and browser-only Pyodide support.
- Guide-file existence tests, missing-guide tests and bespoke runtime guide-file
  checks. Validate the guide's content, examples and links, not its mere existence.
- Exercise-structure validation or tests for malformed exercise topology: missing,
  duplicate or multiple task tags, task-count checks against metadata, and structural
  FAIL rows. Structure belongs to scaffolding and authoring-time review, not the
  student self-checker. Existing parsing/resolution errors remain unchanged.
- New exercises, catalogue-wide notebook clean-ups, legacy compatibility paths or
  changes to `exercise.json`, `README.md`, `OVERVIEW.md` and `OrderOfTeaching.md`
  within individual exercises.

### Teacher-side scope decision and relative effort

Leaving teacher grading unchanged is less work than including readability:

- `scripts/autograder.py:316–321,399–413` discovers bundled hidden pytest modules
  and runs pytest; it does not call `run_notebook_checks()` or run checker cells.
- Invoke readability in the notebook orchestrator only. Leave the functional
  `run_exercise_checks()` API and exercise-local `CHECKS` unchanged. This also
  preserves their use by existing hidden tests and quality Gate I. No teacher-mode
  opt-out, filtering, suppression flag or exclusion table is needed.
- Teacher inclusion would additionally require Ruff in the grader dependency list
  (`scripts/autograder.py:59–61,220–239`), a hidden pytest adapter, and trusted task
  enumeration in the bundle builder (`scripts/build_classroom50_bundle.py:140–162`).
  One point is awarded per pytest leaf (`scripts/autograder.py:343–375`), so added
  readability cases change score totals and need grading regression/doc updates.
- Scored readability would also expose the deferred solution-readability backlog
  to the teacher-side full-pass solution dry run. Do not silently weaken that
  existing contract to avoid a separate migration.

Therefore teacher inclusion is deferred, not actively disabled. Keep the analyser
reusable without duplicating policy so a future teacher-only adapter can use it.
No teacher-side reporting/scoring changes are part of this implementation.

## Readability policy

Use Ruff **0.14.13**, pinned in the source manifest's project dependencies and dev
extra, and in the student-template manifest. Update the uv lock consistently.
Upgrades require revalidating the policy and student examples together.

Use an explicit, centrally owned selection of these **17 rules**, not broad rule
prefixes, `ALL`, or inherited maintainer settings. Preview mode is required for
the selected preview rules. The line limit is **100** and indentation width **4**.
In Ruff 0.14.13, **E111, E117, E225, E226, E227, E228 and E231** require preview
mode; the other selected rules are stable.

| Code | Student-facing purpose |
| --- | --- |
| E101 | Avoid mixing spaces and tabs in indentation. |
| E111 | Indent code by multiples of four spaces. |
| E117 | Avoid over-indentation. |
| E225 | Use spaces around assignment and comparison operators. |
| E226 | Use appropriate spaces around arithmetic operators. |
| E227 | Use spaces around bitwise and shift operators. |
| E228 | Use spaces around the modulo operator. |
| E231 | Use appropriate spaces after punctuation. |
| E501 | Keep lines within the configured length, subject to Ruff's exceptions. |
| E741 | Avoid the ambiguous variable names `l`, `O` and `I`. |
| N802 | Use lowercase function names. |
| N803 | Use lowercase argument names. |
| N806 | Use lowercase variable names inside functions. |
| N816 | Avoid mixedCase variables at module/global scope. |
| W191 | Use spaces rather than tabs for indentation. |
| W291 | Remove trailing whitespace. |
| W293 | Remove whitespace from otherwise blank lines. |

These are Ruff's actual rules, not stricter custom interpretations. In particular:

- Lowercase/mixedCase checks support `snake_case` conventions but cannot infer
  word boundaries or judge whether a name is descriptive. Uppercase constants
  remain permitted where Ruff permits them.
- E111 checks multiples of four, not a complete custom block-depth policy.
- E501 is not an unconditional character count; document its relevant exceptions.
- Function and bitwise examples belong in clearly labelled later-topic sections
  of the guide; early exercises do not gain new construct requirements.
- Do not select file-ending-newline rules for notebook cells.

## Notebook behaviour and execution invariants

1. Preserve `run_notebook_checks('<exercise_key>')` as the notebook-facing API,
   with its existing `None` return. Existing and newly scaffolded notebooks gain
   feedback through the shared runtime, without adding or retagging cells.
2. Resolve one active self-check variant: student when the environment variable
   is absent; honour explicit student/solution selection and reject invalid values.
   Both functional and readability checks must use that variant, including the
   generic fallback. Propagate it through the fallback's existing execution helpers;
   do not change repository orchestration's default solution variant or leave
   additional environment changes behind.
3. Read canonical `exercises/<construct>/<exercise_key>/notebooks/{student,solution}.ipynb`.
   Preserve already resolved paths as `Path` objects. Unknown keys, missing metadata,
   missing notebooks and malformed notebook data retain fail-fast behaviour.
4. Analyse only code cells whose metadata contains an exact `exerciseN` tag.
   Ignore markdown/explanation cells, untagged examples, scratch cells and checker
   cells. Reuse the existing accepted tag representation without broadening it.
   Ten tasks is a convention, not a limit: analyse the discovered task code cells
   whether the exercise has fewer or more than ten tasks. Do not derive an expected
   tag inventory from `parts` or compare notebook structure against it.
   Assume scaffolded task cells have one `exerciseN` tag each; other non-task tags
   may coexist. Do not add validation, structural failure rows or special support
   for malformed tag arrangements.
5. Preserve original source, joining list-valued source with no inserted separators
   and never stripping it. Keep physical cell index and the cell's single task tag.
   Analyse each selected physical cell once, without adding multi-cell-per-task
   presentation or exercise-structure validation requirements.
6. Run one Ruff analysis per selected physical cell, via stdin and an argument-list
   subprocess without a shell. Use the Ruff installed in the notebook kernel's
   managed environment. Isolate configuration, disable fixes/cache, select the
   policy explicitly and collect JSON. A synthetic `.py` filename is a label only:
   create no extracted source files. Ignore `noqa` directives for this policy so
   selected checks cannot be silently suppressed by task-cell comments.
7. Static analysis must not execute code or require a functional pass. Analyse all
   selected cells, including empty and comment-only starters, and do not cache
   findings across checker runs. A clean placeholder does not imply a solved task.
8. Exit 0 means no selected findings; exit 1 is ordinary student diagnostic output.
   Exit 0 without configuration warnings yields readability PASS; selected findings
   yield readability FAIL. Present Ruff syntax diagnostics as a readability FAIL
   caused by invalid syntax, not an infrastructure failure; identify affected cells
   as syntax-blocked for complete readability assessment and continue analysing
   the other cells.
9. A missing Ruff executable/module, exit 2, invalid diagnostic JSON or other tooling
   failure must produce a clear error, not a clean/skipped-success result. Preserve
   available functional output before surfacing the tooling error. Do not add a
   silent fallback, automatic installation or catch-all exception handler.
   Treat warnings that selected rules have no effect (for example because preview
   is disabled) as policy/configuration errors even when Ruff exits 0; they must
   never become a clean readability result.
10. Assume the pinned Ruff is installed in the managed notebook environment
    (local Jupyter or Codespaces/devcontainers). Invoke it from the notebook
    self-check, not at module import or from functional-only grading APIs. No
    availability preflight, optional-dependency guards or Ruff-free environment
    support is required.

No execution-extractor whitespace change is part of this feature.

## Feedback contract

- Keep functional assertions and their pass/fail outcomes unchanged, but show
  **Readability** rows in the same task-grouped result table as functional checks.
  Identify the canonical exercise key and active variant; do not overload existing
  output-formatting checks or label readability as optional advice.
- Each selected physical cell has a readability PASS/FAIL row. Include all findings
  in its error details: rule code, one-based cell-local line/column and Ruff's
  explanation. Identify the task and physical notebook cell number. Preserve
  deterministic notebook/source order. These rows assess the student's code, not
  the validity of the exercise's structure.
- Identify each analysed cell, including clean cells, and report the number of
  cells analysed, passed/failed readability cells and syntax-blocked cells without
  double-counting. Report functional and readability outcomes separately within
  the summary, followed by a combined self-check PASS/FAIL outcome.
  Preserve existing no-exercise-tags handling without adding a structural check.
  Tooling errors are ERROR states, not student FAIL results, and must never produce
  overall success.
- A task passes only when all its functional checks and readability rows pass.
  Overall success is shown only when all functional checks and all readability
  rows pass and there are no tooling errors. Suppress the existing
  functional-only congratulations in this combined presentation; the orchestrator
  owns the single final success decision. Keep the public `None` return and do
  not raise a grading assertion merely because a student check fails.
- Use “No selected readability issues found” in a PASS row and require students
  to correct FAIL rows before the self-check is complete. A mechanical readability
  PASS does not prove meaningful names, useful comments or correct behaviour.
  Explain that this required self-check does not yet change teacher-side marks.
- Include a reminder to save before checking and a reference to the student guide.
  Guide references must resolve in both authoring and packaged layouts, independent
  of notebook depth/current working directory. Plain-text output remains usable;
  no new rich-display dependency is required.
- Anchor guide lookup to the shared runtime package's repository root, not the
  working directory. The presence of `template_repo_files/` identifies the source
  layout; otherwise use the documented exported root mapping. Derive the reference
  from that layout without opening the guide or checking its existence. Readability
  checking must not depend on whether the Markdown guide is available at runtime.
- The solution variant uses exactly the same readability policy, but existing
  solution readability failures are permitted as a documented migration backlog
  for feature acceptance, not as a runtime exception. A non-compliant solution
  must display readability FAIL and overall self-check FAIL, just like student
  code; do not downgrade it to advice, bypass checks or display a false PASS.
  Document this known limitation in developer guidance and the guide's
  teacher/reference-solution note. Do not
  claim existing reference notebooks are readability-clean; their corrections
  belong to the separate future pass.

## Student guide and export mapping

Author one shared guide at **`template_repo_files/RUFF_GUIDE.md`** and package it
as **`RUFF_GUIDE.md`** at each student repository root. This is a documented base
asset mapping, not a notebook/test compatibility mirror. Do not duplicate the
hand-maintained guide per construct or exercise.

The guide must include:

- How to read task, cell, line, column and rule codes; the save/edit/check cycle;
  functional and required readability PASS/FAIL results; the combined self-check
  pass condition; and a code-index table of contents. Students must fix readability
  failures, not treat them as optional suggestions.
- A stable code anchor for each of the 17 enabled rules, with a plain-English
  explanation, a labelled **Non-example**, a labelled **Corrected example** and
  a short explanation of the change. Examples are small, synthetic and do not
  disclose exercise solutions. Rename examples update every affected reference.
- Explicit visual notation for tabs, trailing spaces and blank-line whitespace,
  with an explanation of the actual characters; Markdown rendering must not make
  the non-example indistinguishable from the corrected version.
- Later-topic labels for function/argument/local-variable and bitwise examples;
  simple sequence/selection examples wherever those suffice.
- The naming and line-length limitations above, with no claim that Python casing
  rules alone fulfil all WJEC identifier requirements.
- A separate syntax-error section explaining why complete readability assessment
  can be blocked, plus a short tooling-error section directing students to ask
  their teacher rather than installing packages or suppressing checks.

“Each Ruff error” means each rule enabled by this checker, plus its syntax-error
category; it does not mean Ruff's entire rule catalogue. Do not enforce comment
spacing or documentation rules in this first policy.

Link the guide from the generated student README using a root-relative repository
link. The source checker references `template_repo_files/RUFF_GUIDE.md`; packaged
feedback references `RUFF_GUIDE.md`, with code anchors where links are rendered.
Copy the guide using the existing base-asset mechanism; ordinary copy failures retain
their usual behaviour. Do not add bespoke guide-existence guards or missing-file tests.
Shared runtime modules continue to ship via the existing package copy. Preserve
canonical notebook/test/metadata paths and existing authoring-only exclusions;
ship no new hidden tests, solutions, maintainer test helpers or grading sources.

## Implementation surfaces

- Shared readability analysis under `exercise_runtime_support/student_checker/`
  (a focused `readability.py` module is the expected starting point), integrated
  through `notebook_runtime.py` and the reporting layer as necessary.
- Source `pyproject.toml`, `uv.lock`, and `template_repo_files/pyproject.toml` for pins.
- `template_repo_files/RUFF_GUIDE.md`, `README.md.template`, and explicit base-asset
  requirements/copying in `scripts/template_repo_cli/core/packager/__init__.py`.
- Infrastructure tests under `tests/exercise_runtime_support/` and
  `tests/template_repo_cli/`; all test fixtures/helpers stay under `tests/`.
- Targeted developer contract/testing documentation updates. No notebook layout,
  scaffolder behaviour, exercise-local tests or teaching-order edits are required.

## Acceptance criteria and validation

1. Every selected rule has a positive/negative regression case against the pinned
   real Ruff. The student guide covers exactly the policy rule codes; each
   non-example produces its stated diagnostic and its corrected example removes
   that diagnostic. Tests reconstruct any visibly annotated whitespace accurately.
   In particular, the E101 non-example must parse successfully; tab/space mixing
   that breaks parsing belongs in the syntax-error section. Verify that every
   selected rule is active under the actual pinned subprocess policy.
2. Unit tests verify source preservation for string/list sources, leading/trailing
   whitespace, cell-local coordinates and code-cell-only selection. Use correctly
   scaffolded exercises with fewer and more than ten tasks to confirm all task
   cells are analysed without a hard-coded count. Include non-task tags alongside
   a single task tag, empty/comment-only cells and repeated runs after saved edits.
   Do not add malformed-exercise, task-count-consistency or tag-topology tests.
3. Both checker dispatch branches show readability PASS/FAIL alongside functional
   results in one task-grouped table. Default-student and
   explicit-solution cases analyse/execute the same notebook, preserve environment
   state and retain functional outcomes. Test all four combinations of functional
   PASS/FAIL and readability PASS/FAIL: overall PASS occurs only when both pass.
   Syntax errors yield readability FAIL; tooling errors prevent overall PASS.
   Check that intermediate printers cannot emit premature success. These outcomes
   do not add teacher-side grading assertions or modify functional-only APIs.
4. Tests cover Ruff exits 0/1/2, missing tool, malformed output, student syntax
   errors, remaining cells after a syntax error and tooling failure
   after functional output. Ordinary diagnostics do not raise grading failures.
   Include exit-0 selection-no-effect warnings as configuration failures.
   Assert that tooling ERROR output is explicitly distinguishable from student
   readability FAIL output, and that neither can produce overall PASS.
5. Assert stdin/no-shell/no-fix/isolated invocation, no source/notebook mutation and
   no tool launch on import or functional-only checks. No network/install step is
   needed by the self-checker or tests. Use the normal pinned environment and
   subprocess test doubles for tooling failures; do not create a Ruff-free test
   environment or add availability probes.
6. Test the source/export reference strings printed by the checker without checking
   guide-file existence. Review the Markdown guide, anchors and README links as
   documentation; no Python guide-existence or missing-guide tests are required.
   An offline packaged-template self-check confirms real Ruff feedback, exact
   dependency pin and unchanged canonical exercise mapping. No test-only fixtures
   enter the output.
   Reuse the test runner's existing pinned Ruff environment; do not install a
   separate fixture environment to perform this check.
7. Existing infrastructure/functional solution suites pass. Explicit student
   exercise validation still reports expected unfinished-task failures; do not
   change student answers or silence those failures.
   Existing solution notebooks may fail readability checks: such findings must
   not fail functional solution validation or block this feature's acceptance.
   Their combined notebook self-check must nevertheless show FAIL when readability
   fails. Verify that distinction explicitly; do not assert that every current
   solution notebook's combined self-check passes. Retain and report failures
   honestly; do not suppress rules or edit the solution catalogue to make it clean.
   Resolve that backlog in a future pass.

Run targeted infrastructure and packaging tests first, then the repository's
collection and explicit solution-variant validation:

- `uv run pytest tests/exercise_runtime_support/ tests/template_repo_cli/ -q`
- `uv run pytest --collect-only -q`
- `uv run python scripts/run_pytest_variant.py --variant solution -q`
- `uv run ruff check .`

Use explicit student-variant runs on representative sequence/selection exercise-local
tests to confirm expected failures, rather than treating them as a regression.
Student-guide examples are tested with the student policy, not maintainer exclusions.

## Relevant repository contracts

- `AGENTS.md`
- `docs/developers/project-structure.md`
- `docs/developers/execution-model.md`
- `docs/developers/testing-framework.md`
- `docs/developers/development.md`
- `docs/developers/classroom50-autograder.md`
- `docs/teachers/exercise-generation.md`
- `docs/exercise-agents/exercise-generation-cli.md`
- `docs/teachers/pedagogy.md`

Rule reference: https://docs.astral.sh/ruff/rules/ (verify examples against the pinned
version, not solely the latest web documentation).

## Assumptions, open questions and risks

- Accepted defaults: required readability PASS/FAIL, combined task-grouped reporting,
  100-character lines, four-space indentation, exact selected rules and native-kernel
  execution. Teacher grading is deferred because leaving it unchanged needs no
  exclusion mechanism and is less work than inclusion. No blocking question remains.
- Exercises are not limited to ten tasks. Assume scaffolding and authoring review
  supply the task structure, with one task tag per task cell. The self-checker
  discovers code to assess; it does not validate task counts or tag topology.
- Existing starter code or mandated identifiers may produce readability failures.
  Do not rename required identifiers or rewrite the catalogue in this work; the
  guide directs students to follow their task instructions and ask their teacher
  about conflicts.
  Do not silently waive a failure; catalogue/policy conflicts need teacher review.
- Existing solution notebooks may also produce readability findings. A future
  pass will correct those notebooks with pedagogical and functional revalidation;
  this work documents the backlog but does not make a readability-clean catalogue
  a prerequisite for release.
- Preview rules can change across versions; the exact pin and example tests are
  the release boundary. Pinning the existing locked version avoids an unrelated upgrade.
- Function/bitwise rules are inert unless that syntax appears; guide organisation
  must avoid presenting later constructs as prerequisites for introductory tasks.
- Browser-only environments cannot be promised native subprocess support. Document
  the supported runtime instead of silently substituting a different checker.
- Existing tests asserting no notebook resolution in the local-support branch or
  fixed student selection in fallback need focused updates for the new orchestration;
  this does not authorise weakening functional assertions.
