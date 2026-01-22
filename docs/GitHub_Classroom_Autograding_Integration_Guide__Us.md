# GitHub Classroom Autograding Integration Guide: Using the Grading Reporter

This guide details the integration of the `autograding-grading-reporter` action into a GitHub Classroom assignment using a custom GitHub Actions workflow, addressing the necessary configuration and the mechanism by which results are reported.

## 1. Configuration and Discovery: The Role of `classroom.yml`

The core of the integration lies in the **template repository** used for your assignment.

### Is `classroom.yml` Sufficient?

**Yes, placing the custom workflow file at `.github/workflows/classroom.yml` in your template repository is the sufficient and recommended method** for configuring autograding [1].

When a student accepts the assignment, GitHub Classroom automatically copies the contents of the template repository, including the `.github/workflows/classroom.yml` file, into the student's new assignment repository. GitHub Actions then automatically detects and runs this workflow on specified events, such as a `push` or `workflow_dispatch` [2].

### The Reporting Mechanism

GitHub Classroom does not "watch" for a specific file or output. Instead, the `autograding-grading-reporter` action is responsible for communicating the final score back to the GitHub Classroom interface.

The reporter achieves this by using the GitHub Actions workflow command `core.notice` to create annotations containing the score summary and a JSON payload. GitHub Classroom parses these notices to display the score and pass/fail status to both the student and the instructor [3].

## 2. Integrating the Grading Reporter into `classroom.yml`

The custom workflow must consist of two main parts: the **Test Runner Steps** and the **Reporting Step**.

### A. Test Runner Steps

Each test runner step must use an action that produces a Base64-encoded JSON string as output. This output contains the test results in the required data shape identified in the previous analysis (which includes `max_score`, `status`, and the `tests` array).

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
| **Permissions** | Standard read permissions are sufficient for the reporter in most workflows; the action relies on workflow notices rather than direct checks updates [3] [4]. |
| **Test Runner Output** | Each test step must output a Base64-encoded JSON string containing the test results, including `max_score` and the `tests` array. |
| **Reporter Configuration** | The `runners` input must be a comma-separated list of the test step `id`s. |
| **Environment Variables** | Environment variables must be set for each runner in the format `UPPERCASE_STEP_ID_RESULTS` to pass the Base64-encoded JSON output. |

## References

[1] GitHub Docs. (n.d.). *Use autograding*. Retrieved from https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding
[2] GitHub Docs. (n.d.). *View autograding results*. Retrieved from https://docs.github.com/en/education/manage-coursework-with-github-classroom/learn-with-github-classroom/view-autograding-results
[3] classroom-resources. (2023). *notify-classroom.js*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js
[4] classroom-resources. (n.d.). *autograding-grading-reporter README.md*. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/README.md
