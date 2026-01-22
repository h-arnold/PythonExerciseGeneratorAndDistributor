# Comprehensive Analysis of GitHub Classroom Autograder Data Shapes

This document provides a detailed trace and analysis of the `autograding-grading-reporter` codebase, specifically focusing on the required data shapes, capabilities, and limitations for submitting results to GitHub Classroom Autograder.

## 1. Conclusion on Multiple Test Submissions

The analysis confirms that the architecture of the `autograding-grading-reporter` **explicitly supports the submission of results from multiple test runners simultaneously**.

The entry point of the application is designed to process a comma-separated list of test runner identifiers, each corresponding to a separate, Base64-encoded JSON payload containing its own set of test results and scoring information. The final score reported to GitHub Classroom is an aggregation of the scores from all submitted runners.

## 2. Data Flow and Entry Point Analysis

The application's entry point, `src/main.js`, orchestrates the data processing. The data is consumed via GitHub Actions inputs and environment variables.

| Source | Input Name | Data Type | Purpose |
| :--- | :--- | :--- | :--- |
| GitHub Action Input | `runners` | Comma-separated string (e.g., `"unit_tests,integration_tests"`) | A list of unique identifiers for each test runner whose results are to be processed [1]. |
| Environment Variable | `${RUNNER_ID}_RESULTS` | Base64-encoded JSON string | The actual test results payload for a specific runner, where `RUNNER_ID` is the uppercase, trimmed version of the identifier from the `runners` input. |

The `main.js` file performs the following critical steps for each runner:
1.  Reads the `runners` input string.
2.  Splits the string by comma to get individual runner IDs.
3.  Constructs the environment variable name (e.g., `UNIT_TESTS_RESULTS`).
4.  Reads the Base64-encoded JSON from the environment variable.
5.  Decodes the Base64 string and parses the JSON into a structured object.
6.  Passes the aggregated array of `{ runner, results }` objects to `ConsoleResults` (for console output) and `NotifyClassroom` (for GitHub Classroom API notification).

## 3. Required Data Shape for a Single Test Runner

The JSON payload for each test runner, which is Base64-encoded and stored in the environment variable, must conform to the following structure. This structure is inferred from how the data is consumed by `src/notify-classroom.js` and `src/helpers/test-helpers.js`.

| Field | Type | Description | Source of Requirement |
| :--- | :--- | :--- | :--- |
| `max_score` | `Number` | The total maximum points possible for this specific test runner. | Used by `getMaxScoreForTest` and `NotifyClassroom` to calculate the total possible points [2]. |
| `status` | `String` | The overall status of the test run. Valid values include `"pass"`, `"fail"`, or `"error"`. | Used by `main.js` to determine if the GitHub Action should be marked as failed [3]. |
| `tests` | `Array<Object>` | A list of individual test results. | Iterated over by `ConsoleResults` and `NotifyClassroom` to calculate the final score and display individual results [4]. |

### Required Shape for Individual Test Objects (`tests` array)

Each object within the `tests` array must contain the following fields:

| Field | Type | Description | Source of Requirement |
| :--- | :--- | :--- | :--- |
| `name` | `String` | The human-readable name of the test case. | Used for console output [4]. |
| `status` | `String` | The result of the individual test. Valid values include `"pass"`, `"fail"`, or `"error"`. | Used by `getTestScore` to count passing tests and by `ConsoleResults` for colour-coded output [2] [4]. |
| `score` | `Number` | The points awarded for this specific test case. | Used by `NotifyClassroom` to aggregate the total points earned across all test runners [5]. |
| `line_no` | `Number` | Optional. The line number in the code where the test failed. | Used for enhanced console reporting [4]. |
| `message` | `String` | Optional. An error message or failure description. | Used for console output when `status` is `"error"` [4]. |

**Example JSON Payload for a Single Test Runner:**

```json
{
  "max_score": 10,
  "status": "fail",
  "tests": [
    {
      "name": "Test 1: Correctly calculates sum",
      "status": "pass",
      "score": 5
    },
    {
      "name": "Test 2: Handles edge case input",
      "status": "fail",
      "score": 0,
      "line_no": 42,
      "message": "Expected 0 but received 1 for empty array."
    }
  ]
}
```

## 4. Scoring Mechanism and Limitations

The application uses a proportional scoring mechanism based on the number of passing tests within a runner.

### Scoring Calculation

The score for a single test runner is calculated as follows [2]:

$$
\text{Runner Score} = \left( \frac{\text{Number of Tests with } \text{"pass"} \text{ status}}{\text{Total Number of Tests}} \right) \times \text{max\_score}
$$

**Limitation:** The `score` field in the individual test objects (`tests` array) is **not** used for the runner's score calculation. Instead, it is only used by `NotifyClassroom` to calculate the **total score** reported to GitHub Classroom. This suggests a potential inconsistency or a design choice where the individual test scores are used for the final submission, while the runner's score is calculated based on a pass/fail ratio for console display.

The final score reported to GitHub Classroom is the sum of the `score` fields from **all** individual test objects across **all** runners, provided the runner object also contains a `max_score` [5].

### Overall Status Reporting

The overall status of the GitHub Action is determined by the `status` field of the individual runner results [3]:
*   If **any** runner has a `status` of `"fail"`, the action is marked as failed with the message "Some tests failed."
*   If **no** runner has a `status` of `"fail"`, but **any** runner has a `status` of `"error"`, the action is marked as failed with the message "Some tests errored."
*   If all runners have a `status` of `"pass"`, the action succeeds.

## References

[1] classroom-resources. (2023). *action.yml*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/action.yml
[2] classroom-resources. (2023). *test-helpers.js*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/helpers/test-helpers.js
[3] classroom-resources. (2023). *main.js*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/main.js
[4] classroom-resources. (2023). *console-results.js*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/console-results.js
[5] classroom-resources. (2023). *notify-classroom.js*. GitHub. Retrieved from https://github.com/classroom-resources/autograding-grading-reporter/blob/main/src/notify-classroom.js
