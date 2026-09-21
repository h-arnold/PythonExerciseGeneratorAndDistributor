# SPEC — Classroom 50 Autograder (Selection Pilot, Implementation Round)

## Goal and intended outcome

Replace the broken GitHub Classroom reporter chain with one generic Classroom
50 grading source and generic bundle builder, verified locally. A working round
means: the legacy chain is deleted, selection templates ship starter code only,
and the builder is configured with the selection pilot exercise set to produce
a teacher-side grading bundle (the generic `autograder.py` plus hidden test
copies) that grades the student variant correctly and the solution variant to a
full pass in a local dry run. Selection is the first builder input and
end-to-end validation fixture, not a Selection-specific grader.

Decisions already agreed and built into this spec:

- One Classroom 50 assignment per construct; pilot construct is `selection`.
- One point per passing pytest case; exercise size acts as the difficulty proxy.
- Self-check tests stay visible in the template; grading logic is teacher-side
  and tamper-proof (template edits cannot change the graded outcome).
- A single generic `autograder.py` and builder serve every assignment; no
  per-construct or per-exercise grading logic. The selected exercise set is
  builder input, so the same sources can create a later assignment bundle.
- Runtimes and devcontainers move to Python 3.14 to match the Classroom 50
  default grading runtime.
- Legacy removal lands first; no new implementation reuses the reporter chain.

## Current state

- Source exercises use the canonical layout
  `exercises/<construct>/<exercise_key>/` with `notebooks/student.ipynb`,
  `notebooks/solution.ipynb`, `tests/test_<exercise_key>.py` plus support
  modules (`expectations.py`, `student_checker_support.py`), and
  `exercise.json`. Selection holds four exercises:
  `ex001_selection_modify_basics` (33 tests),
  `ex002_selection_debug_if_then_else` (60 tests),
  `ex003_selection_modify_elif_boundaries` (60 tests),
  `ex004_selection_modify_logical_operators` (71 tests); 224 cases in total.
- Selection tests share one shape: import from `exercise_runtime_support`,
  declare `_EXERCISE_KEY`, load `expectations` via
  `load_exercise_test_module`, and drive tagged notebook cells through
  `RuntimeCache` with the `exercise_key` resolver.
- Notebook resolution (`exercise_metadata/resolver.py`) and test-module
  resolution (`exercise_runtime_support/exercise_test_support.py`) both anchor
  on the location of the imported package, not on the working directory.
- Exported templates preserve canonical paths plus `exercise_metadata/` and
  `exercise_runtime_support/`; flattened mirrors are forbidden.
- The template still ships the legacy chain, confirmed broken:
  `template_repo_files/.github/workflows/classroom.yml` invoking
  `scripts/build_autograde_payload.py --variant student` with
  `-p tests.autograde_plugin`, forwarded to
  `classroom-resources/autograding-grading-reporter@v1`.
- `TemplatePackager` hard-requires that chain (`classroom.yml` checks,
  `REQUIRED_SCRIPTS`, `REQUIRED_TEST_FILES`).
- Runtimes pin Python 3.11+ with 3.12 devcontainer images.

## Scope and non-goals

In scope for this round:

- Delete the legacy autograding chain and its docs references.
- Move runtimes and devcontainers to Python 3.14 (grading-runtime alignment).
- Add one generic `autograder.py` source plus a generic bundle builder that
  assembles a teacher-side grading bundle from its selected exercise-set input;
  Selection supplies the first pilot input only.
- Repackage selection templates as starter-code only, with a test proving the
  grading source never ships inside them.
- Local dry-run verification of the bundle against student-variant and
  solution-variant workspaces.

Explicit non-goals (not in this repo, not in this round):

- No functionality for creating or managing Classroom 50 classrooms: no
  classroom scaffolding, roster management, assignment registration,
  `assignments.json` writing, score collection, submission download, token
  handling, or web/CLI classroom automation of any kind. The teacher performs
  all classroom operation manually in the `classroom50` repository and
  organisation; this repo only produces clean templates and the grading
  bundle source.
- No live pilot operation (no test-student accept, submit, Release inspection,
  or Collect runs) as implementation acceptance; those are manual teacher
  follow-ups outside this repo.
- No new exercises, notebook content changes, tagged-cell changes,
  pedagogical changes, `OrderOfTeaching.md` changes, or exercise-type
  metadata changes.
- No sequence rollout, no per-exercise assignments, no declarative-tests
  route, no weighting beyond one point per case.
- No implementation code or tests are written in this plan document.

## Constraints and invariants

- Preserve the canonical exercise-local contract: `exercise.json` holds type;
  no `<type>` path segment; no flattened mirrors; no solution notebooks in
  templates; notebook identity by `exercise_key` string; resolved `Path`
  values stay as `Path`.
- Preserve grading invariants: solution variant passes, student variant fails
  in this repository; each case stays fast, deterministic, and isolated;
  variant selection via `--variant` / `PYTUTOR_ACTIVE_VARIANT`.
- Single generic grader and builder: the same `autograder.py` source grades
  every assignment, and the same builder source creates each assignment bundle
  from a selected exercise-set input. The Selection set is the pilot fixture,
  not a special code path. The grader's discovery root is the bundle's hidden
  test directories only, never the student checkout's `exercises/.../tests/`,
  so visible self-check copies are never double-counted. It discovers bundled
  tests dynamically at grade time; no hardcoded exercise keys, weights, or
  construct names. The builder supplies per-exercise subdirectories; the
  grader supplies the mechanism. New grading code stays 3.11-compatible so the
  source-repo dry run works before any floor raise.
- Bundle isolation mechanism: the bundle ships its own copy of
  `exercise_runtime_support/` placed ahead of the student checkout on
  `sys.path`, while `exercise_metadata/` stays the student-checkout copy.
  `load_exercise_test_module` then resolves `expectations.py` and support
  modules into the bundle's hidden `exercises/<construct>/<exercise_key>/tests/`
  copies, and the metadata resolver still resolves notebooks to the student
  checkout. The bundle copy of `exercise_runtime_support/` is produced from
  source at build time and must be rebuilt whenever the source package
  changes. The graded run forces the student variant
  (`PYTUTOR_ACTIVE_VARIANT=student`); the solution dry run forces the solution
  variant.
- Bundle isolation rule: notebook resolution must point at the student
  checkout (student work), while test-module resolution
  (`expectations.py`, support modules, test logic) must point at the fresh
  bundle copies. Template edits must not change the graded outcome. The
  Classroom 50 template rules still apply downstream: the template never
  ships `.github/workflows/autograde.yaml` or `autograding.json`.
- Scoring rule: one point per passing pytest case; per-test name format
  `<exercise_key>::<pytest-nodeid>`, where `<pytest-nodeid>` is the leaf
  `test_*.py::test_name` portion of the pytest node id (no absolute paths);
  `max-score` is the sum (224 on a selection full pass, computed not hardcoded).
- Bundle contents: `autograder.py`, per-exercise hidden copies
  (`test_*.py`, `expectations.py`, `student_checker_support.py`) under
  `<bundle>/exercises/<construct>/<exercise_key>/tests/`, and runtime
  copies of `exercise_runtime_support/` at `<bundle>/exercise_runtime_support/`
  (bundle-local) with `exercise_metadata/` resolved from the student checkout.
- `result.json` satisfies the `classroom50/result/v1` contract; identity
  fields are stamped authoritatively by the runner downstream. Exit 0 means
  the run completed (pass/fail is in the payload); non-zero is reserved for
  infrastructure error.
- Hidden is tamper-proof, not secret: no solutions or confidential data go
  into the bundle, since the published bundle is fetchable.
- Assignment slug remains an operator input at bundle use time, not a value
  stored in this repository.

## Relevant docs and file evidence

- `AGENTS.md` — canonical layout, variant contract, pytest invocation.
- `docs/developers/project-structure.md` — authoring tree, packaged runtime
  contract, legacy workflow location.
- `docs/developers/execution-model.md` — discovery roots, runtime imports,
  variant selection, source-to-export mapping.
- `docs/developers/testing-framework.md` — solution/student invocation,
  packaging expectations.
- `docs/developers/development.md` — contributor workflow.
- `docs/teachers/exercise-generation.md`, `docs/exercise-agents/exercise-generation-cli.md`,
  `docs/teachers/pedagogy.md` — no pedagogical change in this round; note that
  `exercise-generation.md` still carries the old distribution-platform label
  and is covered by the teacher-docs deferral below.
  (`docs/exercise-agents/exercise-testing.md` is not unchanged: Stage 1 removes
  its `classroom.yml` CI bullet, reconciles the stale `tests.yml` /
  `tests-solutions.yml` CI bullets, replaces the "autograde plugin assigns one
  point per collected test" note with the new model, and rewords the GitHub
  Classroom runner framing.)
- Platform label: GitHub Classroom is no longer the distribution platform
  label; templates are Classroom 50 templates distributed via GitHub template
  repositories. GitHub remains the hosting platform only. Teacher-facing
  distribution docs (`docs/teachers/creating-exercise-sets.md`,
  `docs/teachers/construct-template-repos.md`, `docs/teachers/in-the-classroom.md`,
  `docs/teachers/classroom-practices.md`, `docs/teachers/it-network-requirements.md`,
  `docs/teachers/understanding-the-tools.md`, `docs/teachers/getting-started.md`,
  `docs/teachers/exercise-generation.md`, `docs/README.md` teacher rows) are
  deferred to a separate Classroom 50 docs pass, as is the identical
  flattening falsehood in `.opencode/agents/planner.md`.
- Classroom 50 wiki: `Autograding-Basics` (pipeline, Releases, collection),
  `Autograder-Recipes` (Python recipe), `Advanced-Autograding`
  (`autograder.py` contract, precedence, `result.json`, `runtime` block),
  `Assignment-Templates` (reserved workflow, re-fetch behaviour).
- Files in scope include:
  `template_repo_files/.github/workflows/classroom.yml`,
  `template_repo_files/pytest.ini`, `template_repo_files/pyproject.toml`,
  `template_repo_files/.devcontainer/devcontainer.json`,
  `.devcontainer/devcontainer.json`, `pyproject.toml`,
  `scripts/build_autograde_payload.py`, `tests/autograde_plugin.py`,
  `tests/test_autograde_plugin.py`, `tests/test_build_autograde_payload.py`,
  `tests/test_integration_autograding.py`,
  `exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py`,
  `scripts/template_repo_cli/core/packager/__init__.py`,
  `tests/template_repo_cli/test_packager.py` (autograde helpers and cases),
  `tests/exercise_runtime_support/test_runtime_contract.py` (delete
  `test_workflow_variant_script_contract` entirely),
  `tests/exercise_runtime_support/test_build_autograde_env.py` (delete:
  legacy-only),
  `exercises/selection/ex001_selection_modify_basics/tests/test_ex001_selection_modify_basics.py`,
  `exercise_runtime_support/exercise_test_support.py` (read-only reference for
  the `sys.path` design, not an edit target),
  `exercise_metadata/resolver.py` (read-only reference, not an edit target),
  `docs/developers/github-classroom-autograding-guide.md` (delete: legacy-only),
  `docs/developers/autograding-cli.md` (delete: legacy-only),
  `docs/developers/template_repo_cli.md` (remove tree entries, bullets, and
  the GitHub Classroom Integration sections),
  `docs/developers/execution-model.md`, `README.md` (repo root: remove legacy
  autograder sentence), `docs/README.md` (remove legacy link rows),
  `docs/exercise-agents/exercise-testing.md`,
  `.opencode/agents/testing-specialist.md` (drop `autograding-cli.md` and
  legacy-script references; correct the flattening claim to the
  forbidden-mirrors contract), `AGENTS.md` (reconcile the L3 platform label).

## Exercise work

- Construct and keys: `selection` —
  `ex001_selection_modify_basics`, `ex002_selection_debug_if_then_else`,
  `ex003_selection_modify_elif_boundaries`,
  `ex004_selection_modify_logical_operators`.
- Intended notebook behaviour: unchanged. Students edit tagged cells
  (`exercise1`, …, plus `explanationN` where the type uses them); self-check
  cells keep calling `run_notebook_checks('<exercise_key>')`.
- Tagged cell expectations: unchanged; no retagging.
- Notebook and test locations: canonical source paths stay; packaged
  templates keep `notebooks/student.ipynb` and visible `tests/` self-checks
  at canonical paths with no flattened mirrors.
- Packaging/export implications: templates stop shipping the legacy reporter
  chain; the new grading bundle (script plus hidden test copies) is produced
  by the builder as a directory for the teacher to commit into the
  `classroom50` repository. It is never a second editable copy in the
  student checkout.

## Acceptance criteria

1. Legacy chain is gone: no `classroom.yml`, reporter reference, payload CLI,
   or plugin wiring in packaged templates; packager no longer requires them;
   docs no longer present them as the grading route (including root
   `README.md`, `docs/README.md` link rows, `docs/developers/execution-model.md`
   example, and all cross-references); the two legacy-only docs
   (`github-classroom-autograding-guide.md`, `autograding-cli.md`) are deleted;
   `project-structure.md` loses its tree entries and description bullets for the
   deleted files; `template_repo_cli.md` and `setup.md` lose their GitHub
   Classroom Integration sections; `testing-framework.md` loses its
   `classroom.yml` bullet; `development.md` loses §Autograding Development
   Workflow and its `classroom.yml` CI bullet; source suite still collects
   and runs.
2. Runtimes and devcontainers resolve Python 3.14; `requires-python` floor is
   raised only if the implementer confirms 3.14 dependency compatibility,
   otherwise only images/pins move. Source suite passes on the solution
   variant with student-variant failure behaviour preserved.
3. One generic `autograder.py` source and one generic builder source exist,
   with no per-construct or per-exercise hardcoding. The builder accepts its
   selected exercise set as input; configuring it with the Selection pilot set
   assembles a Selection bundle with the script plus per-exercise hidden test
   copies, support files, and the runtime copies named above. New scripts ship
   with a dedicated pytest surface (nodeid transform, `result.json` shape,
   `sys.path` isolation) and pass a Tidy Code Reviewer gate.
4. Local dry run: the bundle run against a packaged student-variant workspace
   fails as expected and against a solution-variant workspace passes. The
   solution-variant workspace is produced by running the hidden bundle copies
   directly in the source repo with the solution variant forced (canonical
   tests equal bundle copies for the pilot; pilot shortcut that does not
   exercise packaged `sys.path` isolation, acknowledged). `result.json`
   validates against the `classroom50/result/v1` shape with
   `<exercise_key>::<nodeid>` leaf names and one point per case.
5. Tamper check: editing or deleting template-side test copies does not
   change the dry-run graded outcome.
6. Repackaged selection template validates (`repoman validate`, dry-run sync)
   with no reserved workflow, no authoring-only assets, and provably no
   grading source inside the exported `exercises/` tree.

## Open questions and risks

- None blocking implementation. Slug, assignment naming, roster, collection,
  and live verification are manual teacher operations outside this repo.
- Risk: the two resolutions anchoring on package location (notebooks vs test
  modules) is the subtle point of the build; the dry-run tamper check in
  criterion 5 exists to catch it.
- Risk: Pages CDN lag and the 15-minute grade-job limit affect live rollout
  only, not this round's acceptance.
- Existing old-system student repositories need fresh acceptance at rollout;
  communicate separately.
