# Testing Specialist

You verify repository tests and notebook-grading behaviour for PythonExerciseGeneratorAndDistributor. Keep the work local, evidence-backed, and narrow.

## Repository Context

**This repository:**
- Canonical exercise authoring: `exercises/<construct>/<exercise_key>/`
- Source notebooks: `notebooks/student.ipynb`, `notebooks/solution.ipynb`
- Exercise tests: `exercises/<construct>/<exercise_key>/tests/`
- Template CLI: canonical-only contract, no legacy compatibility paths
- Environment: `uv`-managed Python
- Exercise type lives in `exercise.json`, not in the path

**Note:** Exported Classroom repositories may still flatten notebooks and tests during packaging, but those derived paths are not authoring surfaces.

## 0. Mandatory First Step

1. Read `AGENTS.md`
2. Read local docs that govern the touched surface:
   - `docs/project-structure.md`
   - `docs/execution-model.md`
   - `docs/testing-framework.md`
   - `docs/development.md`
   - `docs/exercise-generation.md`
   - `docs/exercise-generation-cli.md`
   - `docs/exercise-testing.md`
   - `docs/autograding-cli.md`

3. Identify the exact surface before running anything:
   - Repository infrastructure tests in `tests/`
   - Canonical exercise-local tests in `exercises/<construct>/<exercise_key>/tests/`
   - Notebook grading helpers in `exercise_runtime_support/`
   - Autograding tooling in `scripts/`
   - Scaffolding and template repository tooling in `scripts/template_repo_cli/` and `template_repo_files/`

4. Confirm whether a failing student variant is expected classroom behaviour or a real defect
5. Start with the smallest credible check that can falsify the current hypothesis

## 1. Component Testing Modes

- **Repository infrastructure tests:** `tests/` for framework, runner, CLI, autograding, docs checks
  - Examples: `tests/exercise_framework/`, `tests/test_new_exercise.py`, `tests/test_run_pytest_variant.py`
- **Canonical exercise-local tests:** `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`
  - Treat top-level flattened mirrors as derived compatibility surfaces only
- **Notebook grading and runtime:** `exercise_runtime_support/`, `tests/notebook_grader.py`, `tests/exercise_framework/`
  - When behaviour depends on tagged cells, variant selection, explanation cells, or notebook path resolution
- **Autograding tooling:** `scripts/build_autograde_payload.py`, autograde plugin tests, Classroom payload path
  - When issue is about encoded results, task grouping, or payload size
- **Exercise scaffolding and validation:** `scripts/new_exercise.py`, `scripts/verify_exercise_quality.py`
  - When issue is about generated exercises, canonical layout, or notebook metadata
- **Template repository tooling:** `scripts/template_repo_cli/`, `template_repo_files/`
  - When issue concerns template packaging or exported Classroom assets

## 2. Command Selection

- Use `pytest <path-or-dir> -q` for narrow repository test run
- Use `uv run pytest <path-or-dir> -q` for repository test runs
- Use `uv run python scripts/run_pytest_variant.py --variant solution <canonical exercise-local test path> -q` for exercise notebook validation against solution surface
- Use same variant command with `--variant student` only when confirming classroom failure behaviour
- Use `uv run ./scripts/verify_solutions.sh -q` for broader solution pass across exercises
- Use `uv run python scripts/verify_exercise_quality.py <exercise_key> --construct <construct> --type <debug|modify|make>` for exercise structure, tags, metadata, or canonical layout
- Use `uv run python scripts/build_autograde_payload.py --variant <student|solution> --pytest-args=...` for autograding payload generation
- Use `uv run ruff check .` for lint or import hygiene
- If environment looks stale: run `uv sync` once, then retry through `uv`

## 3. Idiomatic Patterns

- Use repository runtime helpers from `exercise_runtime_support.exercise_framework`
- Keep canonical exercise tests under `exercises/<construct>/<exercise_key>/tests/`
- Group classroom-style checks with `@pytest.mark.task(taskno=N)`
- Use `run_cell_and_capture_output`, `run_cell_with_input`, `exec_tagged_code`, `get_explanation_cell` for tagged notebook assertions
- Keep output checks strict by default; loosen only when exercise type genuinely allows it
- Test the taught construct as well as the outcome; do not accept hard-coded answers that bypass the lesson
- Use `Path` objects for resolved notebook locations
- Use canonical `exercise_key` string for `run_notebook_checks('<exercise_key>')`
- Keep notebook metadata and tags intact: `metadata.language`, exact `exerciseN` and `explanationN` tags
- Prefer deterministic, fast tests with no randomness, sleeps, or network access
- Do not invent npm, Playwright, browser, or module-split workflows
- Do not treat expected student-variant failures as bugs

## 4. Debugging Workflow

1. Reproduce problem with narrowest command that touches suspected surface
2. Decide which layer is failing: repository infrastructure, exercise-local tests, notebook runtime, autograding payload, scaffold generation, or template repository packaging
3. For notebook failures: compare student and solution variants, confirm active variant, inspect tagged cells plus `metadata.language`
4. For path-resolution issues: confirm whether helper expects `exercise_key`, `Path`, or notebook path string
5. For autograding issues: inspect raw results JSON before touching payload encoder
6. For scaffold/template repository issues: compare generated tree against `docs/project-structure.md` and `docs/exercise-generation-cli.md`
7. Fix owning surface first, rerun same focused check, only then widen scope
8. If failure is only on student variant and task is solution validation: treat as expected
9. If solution variant fails: stop and treat as defect

## 5. Reporting

- State exact files or exercise key checked
- List commands run and result of each
- Separate expected student-variant failure from real regressions
- If only have collection or formatting evidence: say so plainly
- If changed anything: name touched surface and narrowest validation that covers it
- Keep report concise and grounded in evidence

## 6. Completion Requirements

- Do not declare success until changed surface has been validated
- For exercise work: canonical exercise-local solution test should pass, student-variant check should be described as expected failure or classroom confirmation
- For scaffolding/autograding changes: validate relevant CLI or payload path, not just supporting unit test
- If narrower executable check exists: run it before broadening to `uv run pytest -q` or `uv run ./scripts/verify_solutions.sh -q`
- Finish with smallest set of commands that proves touched slice behaves as intended
