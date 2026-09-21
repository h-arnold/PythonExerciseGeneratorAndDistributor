# ACTION_PLAN — Classroom 50 Autograder (Selection Pilot, Implementation Round)

Each stage states objective, surfaces, acceptance, checks, and review point.
Removal comes first. No classroom creation or management functionality is
built in any stage; classroom operation stays a manual teacher follow-up.
No implementation code is written in this plan. Selection is the first
exercise-set input and end-to-end validation fixture for the generic grader and
builder; no Selection-specific grader is built or later generalised.

## Stage 1 — Remove the legacy autograding chain

- Objective: delete the broken GitHub Classroom reporter path so later work
  cannot confuse it with Classroom 50.
- Files/surfaces: `template_repo_files/.github/workflows/classroom.yml`,
  `template_repo_files/pytest.ini` plugin flag, `scripts/build_autograde_payload.py`,
  `tests/autograde_plugin.py`, `tests/test_autograde_plugin.py`,
  `tests/test_build_autograde_payload.py`, `tests/test_integration_autograding.py`,
  `exercises/sequence/ex002_sequence_modify_basics/tests/test_repo_autograde_parity.py`,
  `tests/template_repo_cli/test_packager.py` (remove autograde helpers
  `_assert_autograde_script_copy`, `_assert_autograde_plugin_copy`,
  `test_package_integrity_missing_autograde_script/plugin` cases and related
  parametrize rows),
  `tests/exercise_runtime_support/test_runtime_contract.py`,
  `tests/exercise_runtime_support/test_build_autograde_env.py`,
  packager `REQUIRED_SCRIPTS` / `REQUIRED_TEST_FILES` / `classroom.yml` checks in
  `scripts/template_repo_cli/core/packager/__init__.py`, and docs references in
  `docs/developers/github-classroom-autograding-guide.md` (delete: legacy-only),
  `docs/developers/autograding-cli.md` (delete: legacy-only),
  `docs/developers/setup.md` (remove GitHub Classroom Integration sections),
  `docs/developers/testing-framework.md` (delete the `classroom.yml` CI bullet),
  `docs/developers/development.md` (delete §Autograding Development Workflow
  and the `classroom.yml` CI bullet),
  `docs/developers/project-structure.md` (remove the `build_autograde_payload.py`
  / `autograde_plugin.py` tree entries and GitHub Classroom description
  bullets), `docs/developers/template_repo_cli.md`,
  `docs/developers/execution-model.md` (drop `build_autograde_payload.py` example,
  retain `run_pytest_variant.py`),
  `README.md` (repo root: remove all GitHub Classroom autograder references,
  including lines 13, 47, 69; correct the line 87 flattening claim to the
  forbidden-mirrors contract; reconcile the lines 20/55 distribution framing
  with the Classroom 50 platform label),
  `docs/README.md` (remove legacy link rows),
  `docs/exercise-agents/exercise-testing.md` (remove `classroom.yml` CI bullet,
  reconcile stale `tests.yml` / `tests-solutions.yml` CI bullets, replace the
  autograde-plugin scoring note with the generic-autograder model, reword the
  GitHub Classroom runner framing), `.opencode/agents/testing-specialist.md`
  (drop `autograding-cli.md` and legacy-script references; correct the
  flattening claim to forbidden-mirrors), `AGENTS.md` (reconcile the platform
  label).
- Acceptance: packaged templates contain no `classroom.yml`, reporter, payload
  CLI, or plugin wiring; packager validation passes without them; source suite
  still collects and runs. All cross-references to the two deleted docs are
  removed or updated so no dangling links remain. `project-structure.md`,
  `template_repo_cli.md`, and `setup.md` lose their directory-tree entries,
  description bullets, and GitHub Classroom Integration sections for the
  deleted files.
- Checks: `uv run pytest --collect-only -q`,
  `uv run python scripts/run_pytest_variant.py --variant solution -q`,
  `uv run repoman validate`, template dry-run sync, `ruff check .`. After the
  legacy test deletions, grep for `build_autograde_env` and
  `exercise_runtime_support.helpers` module consumers; if none remain (note
  `test_build_autograde_env.py` is itself removed), delete `build_autograde_env`
  from `exercise_runtime_support/helpers.py`, and if that empties the module
  delete `exercise_runtime_support/helpers.py` in full, plus its
  `tests/helpers.py` re-export.
- Review point: confirm the exact delete/retain list before deletion lands.
  Legacy assertions are deleted with no migration. Delete the entire
  `test_workflow_variant_script_contract` function in
  `tests/exercise_runtime_support/test_runtime_contract.py` (it reads the
  deleted `classroom.yml` and the absent `tests.yml`/`tests-solutions.yml`,
  so no subset can run).

## Stage 2 — Move runtimes and devcontainers to Python 3.14

- Objective: align all environments with the Classroom 50 default grading
  runtime, which the new autograder will run under.
- Files/surfaces: `.devcontainer/devcontainer.json`,
  `template_repo_files/.devcontainer/devcontainer.json`, root `pyproject.toml`,
  `template_repo_files/pyproject.toml`, CI workflow Python pins,
  `docs/developers/setup.md` (3.11 container pin), `docs/developers/docker-devcontainer-setup.md`
  (3.11 base-image pins), pedagogy devcontainer note in `docs/teachers/pedagogy.md`
  if retained.
- Acceptance: fresh `uv sync` resolves 3.14; source suite passes on solution
  variant; student-variant failure behaviour preserved; template dry-run still
  validates. `requires-python` floor is raised to `>=3.14` only if dependency
  compatibility is confirmed, otherwise only images/pins move.
- Checks: `uv run python -V`, solution-variant run, student-variant spot check
  on one selection exercise, `ruff check .`.
- Review point: confirm 3.14 against the Classroom 50 `runtime` default before
  the autograder build starts.

## Stage 3 — Record the generic grading contract using the selection pilot

- Objective: record the generic scoring rules that the grader and builder must
  implement, using Selection's selected exercise set as the first pilot input.
- Files/surfaces: selection `exercise.json` titles (read-only reference;
  recorded into the deliverable, not edited), collected test counts
  (33/60/60/71; 224 total), per-test naming rule, scoring rule, deliverable
  `docs/developers/classroom50-autograder.md`. No `OrderOfTeaching.md` change.
- Acceptance: written contract stating one point per passing pytest case,
  per-test names as `<exercise_key>::<leaf-nodeid>` (`test_*.py::test_name`,
  no absolute paths), full-pass total computed as the sum, graded run forcing
  the student variant with the solution variant reserved for the dry run, and
  slug treated as operator input rather than a stored value, and Selection
  identified as a builder configuration and validation fixture rather than a
  special grader implementation.
- Checks: counts re-verified; contract reviewed against the
  `Advanced-Autograding` result contract.
- Review point: teacher signs off the contract before the build starts.

## Stage 4 — Build the generic autograder and assignment-bundle builder

- Objective: add one assignment-agnostic grading source plus a builder that
  assembles a teacher-side bundle from its selected exercise-set input. Run the
  generic system first with the Selection pilot set; do not build or refine a
  Selection-specific grader.
- Files/surfaces: new generic `autograder.py` source under `scripts/`, new
  generic bundle builder script under `scripts/`, Selection pilot input drawn
  from `exercises/selection/*/tests/` (`test_*.py`, `expectations.py`,
  `student_checker_support.py`), bundle-local copy of
  `exercise_runtime_support/` plus student-checkout `exercise_metadata/`;
  visible canonical tests and notebook self-checks untouched.
- Acceptance: grader and builder sources have no per-construct or
  per-exercise hardcoding; the builder accepts the selected exercise set as
  input, with the Selection pilot set proving that the generic mechanism works;
  discovery root is the bundle's hidden test directories only, never the
  student checkout's `exercises/.../tests/`; builder output holds the script
  plus per-exercise hidden copies with support files and the runtime copies
  named above; bundle root is prepended to `sys.path` so
  `load_exercise_test_module` resolves into the bundle while the metadata
  resolver still resolves notebooks to the student checkout; graded run forces
  `PYTUTOR_ACTIVE_VARIANT=student`; `result.json` satisfies
  `classroom50/result/v1`; no solutions in the bundle; new grading code stays
  3.11-compatible. The bundle-local `exercise_runtime_support/` copy is
  regenerated from source at every build and must be rebuilt whenever the
  source package changes.
- Checks: dedicated pytest surface for the new scripts (nodeid transform,
  `result.json` shape, `sys.path` isolation); local dry run against packaged
  student-variant workspace (must fail as expected) and solution-variant
  workspace produced by running the hidden bundle copies in the source repo
  with the solution variant forced (must pass; acknowledged pilot shortcut
  that does not exercise packaged isolation); schema validation of
  `result.json` with leaf nodeid names; tamper check (template-side test edits
  do not change the graded outcome); `ruff check .`.
- Review point: Tidy Code Reviewer gates the new scripts; Exercise Test
  Reviewer confirms construct enforcement and coverage parity with the
  canonical tests.

## Stage 5 — Repackage the selection template without grading surfaces

- Objective: ship starter-code-only templates with a provable exclusion.
- Files/surfaces: `scripts/template_repo_cli/` packager and `.github`
  handling, `template_repo_files/` base files, generated selection template
  output.
- Acceptance: template keeps canonical `student.ipynb`, `exercise.json`,
  visible `tests/` self-checks, and non-autograde support files; contains no
  `autograde.yaml`, `classroom.yml`, reporter, plugin, payload CLI, solution
  notebooks, or grading source; new packaging test proves no `autograder.py`
  exists anywhere under the exported `exercises/` tree; `repoman validate`
  and dry-run sync pass.
- Checks: `uv run repoman validate`, dry-run sync, packaged-tree inspection
  for forbidden/reserved files, new exclusion test. The bundle is independent
  of the template output, so no bundle re-verification is needed here; the
  template checks alone gate this stage.
- Review point: confirm the empty `.github` outcome (whole tree removed)
  with the teacher before publishing.

## Manual teacher follow-up (out of scope for this round)

Assignment registration, bundle commit into the `classroom50` repository,
Pages publish, roster, accept, submit, Release inspection, Collect, and CSV
export are performed by the teacher with the Classroom 50 CLI/web app. They
are not built, automated, or accepted here.
