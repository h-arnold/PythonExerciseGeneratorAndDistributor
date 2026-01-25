# GitHub Classroom Autograding Integration Guide: Using the Grading Reporter

This guide details the integration of the `autograding-grading-reporter` action into a GitHub Classroom assignment using a custom GitHub Actions workflow, addressing the necessary configuration and the mechanism by which results are reported.

## 1. Configuration and Discovery: The Role of `classroom.yml`

The core of the integration lies in the **template repository** used for your assignment.

### Is `classroom.yml` Sufficient?

**Yes, placing the custom workflow file at `.github/workflows/classroom.yml` in your template repository is the sufficient and recommended method** for configuring autograding (see [Use autograding](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding)).

When a student accepts the assignment, GitHub Classroom automatically copies the contents of the template repository, including the `.github/workflows/classroom.yml` file, into the student's new assignment repository. GitHub Actions then automatically detects and runs this workflow on specified events, such as a `push` or `workflow_dispatch` (see [View autograding results](https://docs.github.com/en/education/manage-coursework-with-github-classroom/learn-with-github-classroom/view-autograding-results)).

### The Reporting Mechanism

GitHub Classroom does not "watch" for a specific file or output. Instead, the `autograding-grading-reporter` action is responsible for communicating the final score back to the GitHub Classroom interface.

The reporter achieves this by using the GitHub Actions workflow command `core.notice` to create annotations containing the score summary and a JSON payload. GitHub Classroom parses these notices to display the score and pass/fail status to both the student and the instructor (see [notify-classroom.js](https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js)).

## 2. Integrating the Grading Reporter into `classroom.yml`

The custom workflow must consist of two main parts: the **Test Runner Steps** and the **Reporting Step**.

### A. Test Runner Steps

Each test runner step must use an action that produces a Base64-encoded JSON string as output. This output contains the test results in the required data shape identified in the previous analysis (which includes `max_score`, `status`, and the `tests` array). For pytest-based projects, run the CLI wrapper so the autograde plugin is activated and payloads are generated consistently; see the [Autograding CLI guide](docs/autograding-cli.md) for the exact invocation.

The key is to assign a unique `id` to each test step and ensure it outputs the result.

### B. The Reporting Step

The `autograding-grading-reporter` action is the final step. It aggregates the results from all preceding test steps.

| Reporter Input | Value | Description |
| :--- | :--- | :--- |
| `uses` | `classroom-resources/autograding-grading-reporter@v1` | Specifies the action to use. |
| `with.runners` | A comma-separated list of the `id`s from the preceding test steps. | This tells the reporter which results to look for. |
| `env` | Environment variables mapping the test step outputs to the reporter's expected input format. | The format is `UPPERCASE_STEP_ID_RESULTS: ${{ steps.step-id.outputs.result }}` with hyphens replaced by underscores in the env var name. |

### Example `classroom.yml` Workflow

The following example demonstrates a custom workflow that runs two separate test suites (a Python test and a command-line test) and reports the combined results.

```yaml
name: Autograding Tests
on:
  push:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  autograding:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      # --- Test Runner Step 1: Python Test ---
      - name: Run Python Unit Tests
        id: python-tests # Unique ID for this runner
        uses: classroom-resources/autograding-python-grader@v1
        with:
          test-name: Python Unit Tests
          max-score: 50
          # ... other python-grader inputs ...

      # --- Test Runner Step 2: Command Test ---
      - name: Run Command-Line Test
        id: cli-test # Unique ID for this runner
        uses: classroom-resources/autograding-command-grader@v1
        with:
          test-name: Command-Line Test
          max-score: 50
          # ... other command-grader inputs ...

      # --- Reporting Step ---
      - name: Autograding Reporter
        uses: classroom-resources/autograding-grading-reporter@v1
        env:
          # Map the output of the first runner (id: python-tests)
          PYTHON_TESTS_RESULTS: ${{ steps.python-tests.outputs.result }}
          # Map the output of the second runner (id: cli-test)
          CLI_TEST_RESULTS: ${{ steps.cli-test.outputs.result }}
        with:
          # Comma-separated list of the runner IDs
          runners: python-tests,cli-test
```

## 3. Summary of Key Requirements

| Requirement | Detail |
| :--- | :--- |
| **Workflow File** | Must be located at `.github/workflows/classroom.yml` in the template repository. |
| **Permissions** | Standard read permissions are sufficient for the reporter in most workflows; the action relies on workflow notices rather than direct checks updates (see [notify-classroom.js](https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js) and the [autograding-grading-reporter README](https://github.com/classroom-resources/autograding-grading-reporter/blob/main/README.md)). |
| **Test Runner Output** | Each test step must output a Base64-encoded JSON string containing the test results, including `max_score` and the `tests` array. |
| **Reporter Configuration** | The `runners` input must be a comma-separated list of the test step `id`s. |
| **Environment Variables** | Environment variables must be set for each runner in the format `UPPERCASE_STEP_ID_RESULTS` to pass the Base64-encoded JSON output. |

## 4. Custom Pytest Integration

### 4.1 Autograde Plugin Architecture

The repository ships a bespoke pytest plugin (`tests/autograde_plugin.py`) that captures task-scoped grading data while the tests run. The plugin hooks into the standard pytest lifecycle to:

- register the command-line flag `--autograde-results-path`, ensuring every run declares a destination for the aggregated results JSON
- capture marker metadata from `@pytest.mark.task(taskno=..., name=...)` during collection so that task numbers and human-friendly labels are preserved
- record pass, fail, and error outcomes during execution, including durations, extracted failure messages, and the originating nodeid
- emit a normalised JSON document (`max_score`, `status`, and a `tests` list where each entry is worth one point) at session end and print a terminal summary pointing to the results path

Because the plugin is only activated when the CLI flag is supplied, day-to-day development workflows remain unaffected unless you explicitly opt into autograding output.

### 4.2 CLI Wrapper (`scripts/build_autograde_payload.py`)

The CLI wrapper orchestrates the full autograding flow so template workflows (and local developers) do not need to wire the plugin manually. Core behaviour:

1. Validate the execution environment (refusing to run if `PYTUTOR_NOTEBOOKS_DIR` points at the wrong notebook set).
2. Invoke pytest with the autograde plugin enabled, forwarding any `--pytest-args` values.
3. Load the resulting JSON, perform schema checks, and build a final payload that mirrors the reporter requirements.
4. Base64-encode the payload, write it to disk, emit an optional plain JSON summary, and surface GitHub Actions outputs (`encoded_payload`, `overall_status`, `earned_score`, `max_score`).
5. Print a per-task summary table that mirrors what GitHub Classroom will display.

#### Example: Local Dry Run

```bash
uv run python scripts/build_autograde_payload.py --pytest-args=-k test_ex001_sanity
```

You can repeat `--pytest-args` to forward multiple options, for example to switch notebooks (`--pytest-args=--maxfail=1 --pytest-args=tests/test_ex001_sanity.py`). The wrapper appends `--autograde-results-path` automatically; no manual wiring is required.

### 4.3 Base64 Payload Format

`autograding-grading-reporter` expects a Base64-encoded JSON string so that the structured payload can be transmitted safely through GitHub Actions outputs, which are limited to UTF-8 text and must avoid control characters that raw JSON might introduce. The CLI produces payloads shaped as:

```json
{
  "status": "pass" | "fail" | "error",
  "max_score": <int>,
  "score": <int>,
  "tests": [
    {
      "name": "Display name",
      "task": <int | null>,
      "score": 0 or 1,
      "max_score": 1,
      "status": "passed" | "failed" | "error",
      "message": "Truncated failure details",
      "duration": <float>,
      "nodeid": "pytest node identifier"
    }
  ]
}
```

The Base64 text is written to the file specified via `--output` (default `tmp/autograde/payload.txt`) and exported as the `encoded_payload` Actions output for the reporter step.

### 4.4 Troubleshooting

- **Missing tests in the payload**: Confirm each grading test imports the plugin by running the CLI wrapper rather than calling pytest directly. Ensure every test file resides under `tests/` and is collected by pytest (watch for typos in the filename pattern).
- **Task number or label issues**: Verify that every autograded test is marked `@pytest.mark.task(taskno=<int>)`. Add an optional `name="Short title"` to override the display label. Unmarked tests appear with `task` set to `null` and are grouped together in the summary.
- **Payload validation failures**: Inspect the raw results JSON (pass `--summary tmp/autograde/results.json` to the CLI) to confirm required keys exist. The CLI prints schema errors to stderr and exits non-zero if validation fails.
- **Workflow wiring errors**: Ensure the GitHub Actions job calls `uv run python scripts/build_autograde_payload.py` and passes the resulting Base64 string to `autograding-grading-reporter`. Double-check that `PYTUTOR_NOTEBOOKS_DIR` matches `notebooks` when grading student submissions and `notebooks/solutions` for dry runs.

## References

- GitHub Docs. (n.d.). *Use autograding*. [GitHub Classroom documentation](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding)
- GitHub Docs. (n.d.). *View autograding results*. [GitHub Classroom documentation](https://docs.github.com/en/education/manage-coursework-with-github-classroom/learn-with-github-classroom/view-autograding-results)
- classroom-resources. (2023). *notify-classroom.js*. [Repository source](https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js)
- classroom-resources. (n.d.). *autograding-grading-reporter README.md*. [Repository documentation](https://github.com/classroom-resources/autograding-grading-reporter/blob/main/README.md)
