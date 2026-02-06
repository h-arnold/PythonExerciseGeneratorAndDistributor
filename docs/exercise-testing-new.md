# Exercise Testing Specification

This document specifies the intended behaviour of the exercise testing process. It is a natural language reference for refactoring, so it focuses on observable behaviour, inputs, outputs, and edge cases rather than implementation details.

## Scope

- This specification covers the student-facing checking commands and the automated notebook grading used in tests.
- It applies to notebooks in [notebooks/](notebooks/) and [notebooks/solutions/](notebooks/solutions/).
- It describes the current behaviour for exercises ex001 to ex006, with detailed checks for ex002.

## Inputs

- A notebook slug (for a single notebook check), or no slug (for the default multi-notebook check).
- Jupyter notebooks containing code cells tagged with `exerciseN` tags in cell metadata.
- Optional environment variable `PYTUTOR_NOTEBOOKS_DIR`:
	- When set (typically to `notebooks/solutions`), all notebook paths are resolved against that directory.
	- When unset, the student notebooks under `notebooks/` are used.

## Outputs

- A console-rendered table that summarises pass/fail results.
- For ex002, a grouped table with per-exercise checks and error messages.
- No trailing details list is printed after the table.
- A success message is printed only when every check passes:
	- `Great work! Everything that can be checked here looks good.`

## Table Rendering Rules

- Tables are rendered using the `tabulate` library with `tablefmt="grid"`.
- Status values are emoji + tag:
	- Pass: `🟢 OK`
	- Fail: `🔴 NO`
- The grid uses `+`, `-`, and `|` characters. Column alignment must be visually consistent even with emoji.
- For tables that include an error column:
	- Error text is wrapped to a fixed width of 40 characters.
	- Wrapping keeps words intact unless a single word exceeds the width, in which case long words are split.
	- When errors wrap to multiple lines, only the first line includes the exercise/check/status columns; subsequent lines are blank in those columns.

## High-Level Flow

### 1) Default check (all notebooks)

- The checker runs ex001 to ex006 in a fixed order.
- Each notebook produces a single pass/fail result.
- Output is a 2-column table:
	- `Check` (human-readable notebook name)
	- `Status` (`🟢 OK` or `🔴 NO`)
- If all checks pass, the success message is printed after the table.

### 2) Single-notebook check

- If a notebook slug is provided, only that notebook is checked.
- If the slug is `ex002_sequence_modify_basics`, the detailed ex002 workflow is used (see below).
- If the slug is unknown, an error is raised listing available slugs.

## Notebook Grading Behaviour

- Tagged cells are executed using the grading helpers in [tests/notebook_grader.py](tests/notebook_grader.py).
- If a tagged cell is missing or cannot be executed, the error is surfaced as a failing issue for that check.
- Checks are fail-fast per check item, but all check items are still attempted and reported in the table.
- No check should silently swallow errors; problems are reported as messages in the error column.

## ex002 Detailed Checks

The ex002 checker performs three checks per exercise (1 to 10), resulting in 30 checks in total. Output is a 4-column table:

- `Exercise` (e.g., `Exercise 1`)
- `Check` (one of `Logic`, `Formatting`, `Construct`)
- `Status`
- `Error`

### Logic Check

- Runs the tagged cell for the exercise and compares its output to the expected output.
- Exact output is required, including casing and punctuation.
- Single-line and multi-line outputs are supported based on the expectations for that exercise.
- Failure message format (after prefix removal):
	- `expected '<expected output>'.`

### Formatting Check

- Verifies the number of output lines (print calls) matches expectations.
- Failure message format (after prefix removal):
	- `expected N print calls.`

### Construct Check

- Verifies required constructs are present in the student code.
- For example, checks that `print(...)` is used and that specific operators appear where required (`*`, `/`, `-`).
- Failure message format (after prefix removal):
	- `expected to use '<operator>' in the calculation.`

### Error Column Behaviour for ex002

- Error messages must not repeat the exercise prefix. If an error message starts with `Exercise N:`, that prefix is stripped before display.
- Multiple issues for a single check are joined with `; `.
- When a check passes, the error column is blank for that row.

## ex001, ex003, ex004, ex005, ex006 Summary Behaviour

These notebooks use a summary-level pass/fail rather than per-exercise checks.

### ex001

- Requires a function named `example` to exist.
- The function must return a non-empty string.
- Failures report specific messages for missing function, wrong type, or empty string.

### ex003

- Verifies static outputs for specific exercises by running tagged cells.
- Verifies input/output flow for prompts using pre-defined inputs.
- Any mismatch in expected output or prompt flow is a failure.

### ex004

- Validates that explanations are present and meet a minimum length.
- Rejects placeholder phrases and formatting errors.
- Failing outputs list the specific explanation or formatting issue.

### ex005

- Verifies prompt input flow and expected output formatting for multiple exercises.
- Ensures explanations are present and meet quality checks similar to ex004.

### ex006

- Verifies expected outputs and required type conversion behaviour.
- Checks that the input expectations and outputs match the specification for each exercise.

## Expected Console Output Examples (Illustrative)

### ex002 (grouped table)

```
+-------------+------------+----------+------------------------------------------+
| Exercise    | Check      | Status   | Error                                    |
+=============+============+==========+==========================================+
| Exercise 1  | Logic      | 🔴 NO    | expected 'Hello Python!'.                |
+-------------+------------+----------+------------------------------------------+
|             | Formatting | 🟢 OK    |                                          |
+-------------+------------+----------+------------------------------------------+
|             | Construct  | 🟢 OK    |                                          |
+-------------+------------+----------+------------------------------------------+
```

### All notebooks (summary table)

```
+-------------------------------+--------+
| Check                         | Status |
+===============================+========+
| ex001 Sanity                  | 🟢 OK |
+-------------------------------+--------+
| ex002 Sequence Modify Basics  | 🔴 NO |
+-------------------------------+--------+
```

## Non-Goals

- This document does not prescribe how the tests are implemented internally.
- It does not define exercise content or pedagogy; it only defines observable testing behaviour.

