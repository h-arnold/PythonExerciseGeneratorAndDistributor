# Autograder Runner Integration Specification

## Objectives

- Generate GitHub Classroom-compatible autograder payloads from the existing notebook pytest suites while reflecting the exercise testing principles.
- Preserve granular, task-focused feedback for teachers and students by mirroring the per-test assertions used in the suites.
- Ensure the Classroom workflow executes inside student repositories based on the template files in `template_repo_files`.

## In Scope

- New pytest plugin for structured result capture.
- New command-line wrapper that invokes pytest, synthesises the autograder payload, emits per-test diagnostics, and encodes the payload in Base64.
- Template repository workflow that runs tests against student notebooks, feeds the encoded payload to `autograding-grading-reporter`, and fails the job on test failure.
- Repository documentation updates describing setup and behaviour.

## Out of Scope

- Refactoring existing notebook tests (deferred).
- Changing test semantics beyond the weighting-per-test assumption (each pytest assertion equals one point).
- Integrating alternative runners beyond pytest.

## Existing Inputs

- Notebook execution helpers in `tests/notebook_grader.py` and the helper wrappers in `tests/helpers.py` provide deterministic execution and tagging that feed into pytest outcomes.
- Current CI workflows in `.github/workflows/tests.yml` (main repo) and template workflows demonstrate `uv`-based environment setup and pytest invocation patterns.
- Documentation in `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md` and `docs/Comprehensive_Analysis_of_GitHub_Classroom_Autogra.md` defines the required payload format for `autograding-grading-reporter`.

## Data Model

- One pytest *test function* maps to one autograder test case with weight 1.
- Each case records:
  - Human-readable name (nodeid stripped to test function name plus optional docstring heading).
  - Task number (from `@pytest.mark.task(taskno=N)`), used in summary tables.
  - Status `pass`/`fail`/`error`.
  - Score `1` for pass, `0` otherwise.
  - Max score `1` per test; aggregate max equals number of collected test functions.
  - Failure metadata: message (`longreprtext` truncated to sensible length), best-effort line number, captured stdout/stderr snippet when relevant.
  - Execution time (pytest duration) for optional diagnostics.
- Aggregated payload includes total `max_score`, summed `score`, overall `status`, plus sorted `tests` array to satisfy the reporter contract.

## Component Design

### 1. Pytest Autograde Plugin (`tests/autograde_plugin.py`)

Purpose: capture structured pass/fail information during pytest runs without disturbing existing suites.

Key elements:

- **CLI option**: implement `pytest_addoption(parser)` to register `--autograde-results-path` (string, required). The option is mandatory in autograder runs; the CLI wrapper always supplies it. When omitted, plugin skips writing but still collects (for local debugging).
- **Configuration hook**: in `pytest_configure(config)` attach an `AutogradeCollector` object on `config._autograde_state`. Collector stores mutable state:
  - `tests: list[AutogradeTestResult]`
  - `had_errors: bool`
- **Terminal summary**: optionally announce location of results file for human visibility.
- **Collection**:
  - Use `pytest_collection_modifyitems` to store mapping from `item.nodeid` to task number and test names. Extract `mark.kwargs.get("taskno")`; if absent default to `None`.
  - Derive display name via precedence: `item.get_closest_marker("task").kwargs.get("name")`, else `item.function.__doc__` first line, else nodeid.
- **Reporting hooks**:
  - `pytest_runtest_logreport(report)` handles `when == "call"` results.
  - Determine status: `report.passed` -> `pass`, `report.failed` -> `fail`, `report.when != "call" and report.failed` -> `error` (assign once per node).
  - Score: `1` for pass, `0` for fail/error.
  - Capture failure message: `report.longreprtext` truncated to 1,000 chars.
  - Extract line number: for failures with `report.location` use the numeric component if available; fall back to `0`.
  - Duration: `report.duration`.
  - Append `AutogradeTestResult` dataclass/dictionary with fields `nodeid`, `name`, `taskno`, `status`, `score`, `line_no`, `message`, `duration`.
  - Set `had_errors` when `status == "error"`.
- **Session finish**:
  - `pytest_sessionfinish(session, exitstatus)` builds JSON: `{"max_score": len(tests), "status": overall_status, "tests": [...]}`.
  - `overall_status` logic: `"pass"` when all statuses pass; `"fail"` if any `fail`; else `"error"`.
  - Write JSON to `--autograde-results-path` using UTF-8 and ensure parent directory exists.
  - Propagate `exitstatus` untouched (pytest handles workflow failure separately).

### 2. Payload Builder CLI (`scripts/build_autograde_payload.py`)

Purpose: orchestrate pytest execution with the plugin, convert JSON into reporter payload, emit Base64 string and step outputs.

Behaviour:

- **Invocation**: script is executed via `uv run python scripts/build_autograde_payload.py`. It must be runnable inside student repositories.
- **Arguments** (handled via `argparse`):
  - `--pytest-args` (optional, repeatable) to forward flags (default `-q`).
  - `--results-json` (optional) path override; defaults to temp file under `tmp/autograde/results.json`.
  - `--output` path for the Base64 payload file (default `tmp/autograde/payload.txt`).
  - `--summary` optional path; when provided, raw JSON summary gets written for inspection.
- **Environment expectations**:
  - Verify `PYTUTOR_NOTEBOOKS_DIR` is unset or equals `notebooks` (raise otherwise) to enforce student notebook execution.
  - Honour `UV_PROJECT_ENVIRONMENT` etc. but do not mutate.
- **Execution steps**:

 1. Build `pytest_cmd`: `["pytest", "-q", f"--autograde-results-path={results_json}"] + forwarded args` and run via `subprocess.run` with `check=False` to capture exit code.
 2. Ensure pytest exit code and plugin output exist; if plugin omitted results file, raise fatal error.
 3. Load JSON into `AutogradeRun`. Validate schema; raise descriptive error on mismatch.
 4. Compute totals: `max_score = len(tests)`, `earned_score = sum(test["score"] for test in tests)`, `status` from JSON.
 5. Build reporter payload dictionary with fields:

   ```json
   {
    "max_score": max_score,
    "status": status,
    "tests": [
     {
      "name": name,
      "status": status,
      "score": score,
      "line_no": line_no,
      "message": message,
      "task": taskno,
      "nodeid": nodeid,
      "duration": duration
     }
    ]
   }
   ```

   Extra keys (`task`, `nodeid`, `duration`) assist local debugging and will be ignored by the reporter but preserved for teacher tooling.
 6. Serialise with `json.dumps(..., ensure_ascii=False, indent=2)` for the optional summary file.
 7. Generate Base64 string using `base64.b64encode(json_bytes).decode("ascii")`.
 8. Write Base64 string to `--output` and echo a concise summary table to stdout:

- Table per task number with counts of passed/total and score.
- List of failing tests with messages.

 1. Export GitHub Actions outputs by appending to `os.environ["GITHUB_OUTPUT"]`:

- `encoded_payload=<Base64>`
- `overall_status=<status>`
- `earned_score=<float>`
- `max_score=<int>`

 1. Exit code: propagate pytest exit code (non-zero when tests fail or error). The workflow uses `continue-on-error` to keep subsequent steps running.

### 3. Template Workflow (`template_repo_files/.github/workflows/classroom.yml`)

Purpose: run inside student repositories, invoke the payload builder, feed reporter, fail the job if tests fail.

Structure:

- **Triggers**: `on: [push, pull_request, workflow_dispatch]` (confirm final event list with curriculum team).
- **Job** `autograding`:
  - `runs-on: ubuntu-latest`.
  - Steps:
  1. Checkout repository with `actions/checkout@v4`.
  2. Install environment using `astral-sh/uv@v1` or shell `uv sync` (match project convention).
  3. Run payload builder:

    ```yaml
    - name: Run notebook tests
     id: build
     continue-on-error: true
     env:
      PYTUTOR_NOTEBOOKS_DIR: notebooks
     run: |
      uv run python scripts/build_autograde_payload.py \
       --output tmp/autograde/payload.txt \
       --summary tmp/autograde/results.json
    ```

    Notes: ensure `tmp/autograde` is created in script when needed.
  4. Export Base64 payload into env var for reporter:

    ```yaml
    - name: Prepare reporter inputs
     if: always()
     run: |
      echo "PYTEST_RESULTS=$(cat tmp/autograde/payload.txt)" >> "$GITHUB_ENV"
    ```

  1. Reporter step:

    ```yaml
    - name: Autograding Reporter
     if: always()
     uses: classroom-resources/autograding-grading-reporter@v1
     env:
      PYTEST_RESULTS: ${{ env.PYTEST_RESULTS }}
     with:
      runners: pytest
    ```

  1. Final failure gate:

    ```yaml
    - name: Fail when tests fail
     if: steps.build.outcome == 'failure'
     run: exit 1
    ```

 	- Document that `steps.build.outcome` works because `continue-on-error: true` allows completion while registering failure.

### 4. Documentation Updates

- `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md`:
  - Add section describing the new workflow, plugin, and CLI.
  - Clarify that tests run against student notebooks (no `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`).
  - Include instructions for consuming the summary JSON and interpreting per-task feedback.
- `docs/exercise-testing.md` (optional addendum) to mention that each pytest assertion now maps to an autograder point.

## Error Handling

- Pytest plugin writes JSON even on internal exceptions; in worst-case it emits `{ "max_score": 0, "status": "error", "tests": [] }` and logs detail to stderr.
- CLI wrapper raises descriptive `RuntimeError` on missing results file, malformed JSON, or violation of notebook directory constraints.
- Workflow fails through dedicated final step to satisfy requirement while still letting the reporter publish results to Classroom.

## Testing Strategy (post-implementation)

- Unit tests for plugin (new module under `tests/test_autograde_plugin.py`) using `pytester` to simulate runs and assert JSON structure.
- Integration smoke test invoked via `uv run python scripts/build_autograde_payload.py --pytest-args tests/test_ex001_sanity.py` to confirm Base64 output and failure propagation.
- Manual verification of workflow inside template repository sandbox, ensuring `autograding-grading-reporter` surfaces per-test feedback in Classroom UI.

## Open Questions / Follow-Up Work

- Implement richer failure summaries (e.g., truncated stdout) once notebook tests are refactored.
- Decide whether to expose task weighting overrides when exercises diverge from one-assertion-per-credit structure.
