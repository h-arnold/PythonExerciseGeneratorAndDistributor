# Comprehensive Analysis of GitHub Classroom Autograder Data Shapes

This document provides a detailed trace and analysis of the `autograding-grading-reporter` codebase, specifically focusing on the required data shapes, capabilities, and limitations for submitting results to GitHub Classroom Autograder.

## 1. Conclusion on Multiple Test Submissions

The analysis confirms that the architecture of the `autograding-grading-reporter` **explicitly supports the submission of results from multiple test runners simultaneously**.

The entry point of the application is designed to process a comma-separated list of test runner identifiers, each corresponding to a separate, Base64-encoded JSON payload containing its own set of test results and scoring information. The final score reported to GitHub Classroom is an aggregation of the scores from all submitted runners.

## 2. Data Flow and Entry Point Analysis

The application's entry point, `src/main.js`, orchestrates the data processing. The data is consumed via GitHub Actions inputs and environment variables, then routed to console output and Classroom notifications. The runner list is split on commas, each runner name is trimmed, and the corresponding results are read from an environment variable named `${RUNNER_ID}_RESULTS` after uppercasing the runner identifier [1].

| Source | Input Name | Data Type | Purpose |
| :--- | :--- | :--- | :--- |
| GitHub Action Input | `runners` | Comma-separated string (e.g., `"unit_tests,integration_tests"`) | A list of unique identifiers for each test runner whose results are to be processed [1]. |
| Environment Variable | `${RUNNER_ID}_RESULTS` | Base64-encoded JSON string | The actual test results payload for a specific runner, where `RUNNER_ID` is the uppercase, trimmed version of the identifier from the `runners` input [1]. |

The `main.js` file performs the following critical steps for each runner:

1. Reads the `runners` input string.
2. Splits the string by comma to get individual runner IDs.
3. Constructs the environment variable name (e.g., `UNIT_TESTS_RESULTS`).
4. Reads the Base64-encoded JSON from the environment variable.
5. Decodes the Base64 string and parses the JSON into a structured object.
6. Passes the aggregated array of `{ runner, results }` objects to `ConsoleResults` (for console output) and `NotifyClassroom` (for GitHub Classroom API notification).

If parsing fails, the entry point validates the `runners` input against a strict comma-separated list of alphanumeric identifiers and fails the action with a dedicated error message when the pattern does not match [1]. This means values that include brackets or other punctuation can trigger a validation failure if an error occurs while parsing.

## 3. Required Data Shape for a Single Test Runner

The JSON payload for each test runner, which is Base64-encoded and stored in the environment variable, should conform to the following structure. This structure is inferred from how the data is consumed by `src/notify-classroom.js`, `src/console-results.js`, `src/aggregate-results.js`, and `src/helpers/test-helpers.js`.

| Field | Type | Description | Source of Requirement |
| :--- | :--- | :--- | :--- |
| `max_score` | `Number` | Optional, but required if you want points reported to Classroom. When present and non-zero, it drives console scoring and enables the Classroom notice payload. | Used by `getMaxScoreForTest`, `AggregateResults`, and `NotifyClassroom` [2] [4] [5]. |
| `status` | `String` | Recommended. The overall status of the test run. Values used by the action are `"pass"`, `"fail"`, or `"error"`. If omitted, the runner does not influence the action’s final failed/successful status. | Used by `main.js` to determine if the GitHub Action should be marked as failed [1]. |
| `tests` | `Array<Object>` | Required, must contain at least one test. The console output and scoring logic assumes a non-empty list. | Iterated over by `ConsoleResults`, `AggregateResults`, and `NotifyClassroom` [3] [4] [5]. |
| `version` | `Number` | Optional. A schema version field appears in test fixtures but is not read by the reporter. | Present in repository tests only [6]. |

### Required Shape for Individual Test Objects (`tests` array)

Each object within the `tests` array must contain the following fields:

| Field | Type | Description | Source of Requirement |
| :--- | :--- | :--- | :--- |
| `name` | `String` | The human-readable name of the test case. | Used for console output [3]. |
| `status` | `String` | The result of the individual test. Valid values include `"pass"`, `"fail"`, or `"error"`. | Used by `getTestScore` to count passing tests and by `ConsoleResults` for colour-coded output [2] [3]. |
| `score` | `Number` | Required when `max_score` is set. The points awarded for this specific test case. | Used by `NotifyClassroom` to aggregate the total points earned across all test runners [4]. |
| `line_no` | `Number` | Optional. The line number in the code where the test failed. Use `0` when not applicable to avoid showing `line null` in console output. | Used for enhanced console reporting [3]. |
| `message` | `String` | Optional. An error message or failure description. | Used for console output when `status` is `"error"` [3]. |
| `test_code` | `String` | Optional. A snippet shown under “Test code” in the console output. | Printed by `ConsoleResults` when present [3]. |
| `execution_time` | `String` | Optional. Present in repository tests but not used by the reporter. | Present in repository tests only [6]. |

**Example JSON Payload for a Single Test Runner:**

```json
{
  "max_score": 10,
  "status": "fail",
  "tests": [
    {
      "name": "Test 1: Correctly calculates sum",
      "status": "pass",
      "score": 5,
      "line_no": 0
    },
    {
      "name": "Test 2: Handles edge case input",
      "status": "fail",
      "score": 0,
      "line_no": 42,
      "message": "Expected 0 but received 1 for empty array.",
      "test_code": "assert sum([]) == 0"
    }
  ]
}
```

## 4. Scoring Mechanism and Limitations

The application uses a proportional scoring mechanism based on the number of passing tests within a runner for console output and the summary table, and a separate aggregation of per-test `score` values for Classroom notices.

### Scoring Calculation

The score for a single test runner is calculated as follows [2]:

$$
\text{Runner Score} = \left( \frac{\text{Number of Tests with } \text{"pass"} \text{ status}}{\text{Total Number of Tests}} \right) \times \text{max\_score}
$$

**Limitation:** The `score` field in the individual test objects (`tests` array) is **not** used for the runner's score calculation. Instead, it is only used by `NotifyClassroom` to calculate the **total score** reported to GitHub Classroom. This means console output and summary tables use a pass/fail ratio, while Classroom notices use the explicit `score` values.

The final score reported to GitHub Classroom is the sum of the `score` fields from **all** individual test objects across **all** runners, but only for runners whose payload includes a non-zero `max_score` [4]. If any test is missing a numeric `score` while `max_score` is set, the total points can become invalid (e.g., `NaN`) because the notifier simply adds each `score` without validation.

### Overall Status Reporting

The overall status of the GitHub Action is determined by the `status` field of the individual runner results [1]:

* If **any** runner has a `status` of `"fail"`, the action is marked as failed with the message "Some tests failed."
* If **no** runner has a `status` of `"fail"`, but **any** runner has a `status` of `"error"`, the action is marked as failed with the message "Some tests errored."
* If all runners have a `status` of `"pass"`, the action succeeds.
* If a runner omits `status`, it does not affect the action result.

## References

[1] classroom-resources. (2023). *main.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/main.js>
[2] classroom-resources. (2023). *test-helpers.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/helpers/test-helpers.js>
[3] classroom-resources. (2023). *console-results.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/console-results.js>
[4] classroom-resources. (2023). *notify-classroom.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js>
[5] classroom-resources. (2023). *aggregate-results.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/aggregate-results.js>
[6] classroom-resources. (2023). *aggregate-results.test.js*. GitHub. Retrieved from <https://github.com/classroom-resources/autograding-grading-reporter/blob/main/__tests__/aggregate-results.test.js>
