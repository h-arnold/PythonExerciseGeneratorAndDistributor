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
	- If the override path does not exist, the original notebook path is used as a fallback.
	- If the original path is not under `notebooks/`, only the filename is used for the override lookup.

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
- Checks may accumulate multiple issues per item, and all check items are still attempted and reported in the table.
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
	- Single-line output: `expected '<expected output>'.`
	- Multi-line output: `expected 'line1 | line2'.`

### Formatting Check

- Verifies the number of output lines (print calls) matches expectations when a print count is configured.
- Failure message format (after prefix removal):
 	- `expected N print calls.`

### Construct Check

- Verifies required constructs are present in the student code.
- Requires a `print(...)` statement for each exercise.
- For example, checks that `print(...)` is used and that specific operators appear where required (`*`, `/`, `-`).
- Failure message format (after prefix removal):
	- `expected a print statement.`
	- `expected to use '<operator>' in the calculation.`

### Error Column Behaviour for ex002

- Error messages must not repeat the exercise prefix. If an error message starts with `Exercise N:`, that prefix is stripped before display.
- Multiple issues for a single check are joined with `; `.
- When a check passes, the error column is blank for that row.

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

## Refactor Plan (Technical Specification)

This section defines the intended architecture and migration plan for a clean, modular exercise testing framework. It is a design target for refactoring, not a description of the current code.

### Design Goals

- DRY and KISS: shared helpers for common patterns and minimal branching logic.
- Separation of concerns: execution, expectations, assertions, and reporting live in distinct modules.
- Stable, small APIs: a few well-defined entry points used by tests, scripts, and agents.
- Easy extension: adding a new exercise should involve a small, predictable set of steps.

### Proposed File and Folder Layout

```
tests/
 exercise_framework/
  __init__.py
  api.py               # stable public facade used by tests/scripts/notebooks
  runtime.py           # notebook loading, tag extraction, execution
  paths.py             # notebook path resolution, PYTUTOR_NOTEBOOKS_DIR
  expectations.py      # shared expectation helpers and normalisers
  assertions.py        # reusable assertion helpers with consistent messages
  constructs.py        # construct checks (e.g., print usage, operators)
  reporting.py         # student-facing output tables and formatting
  fixtures.py          # pytest fixtures for runtime and output capture
 exercise_expectations/
  exNNN_*.py            # per-exercise expectations (data + small checks)
 test_exNNN_*.py         # per-exercise tests using the shared framework
scripts/
 verify_exercise_quality.py   # thin wrapper around framework
 new_exercise.py              # scaffolding that references framework defaults
docs/
 exercise-testing-new.md       # this document
```

### Module Responsibilities

- `api.py`:
	- Provides the stable orchestration entry points for callers outside the framework internals.
	- Exposes workflows such as `run_all_checks()`, `run_notebook_check(slug)`, and `run_detailed_ex002_check()`.
	- Is the only module that scripts, notebook check cells, and future agents should import directly.

- `runtime.py`:
 	- Load notebooks and extract tagged code cells.
 	- Execute tagged cells in isolated namespaces.
 	- Provide helpers for captured output and simulated input.
 	- Contains no exercise-specific logic.

- `paths.py`:
 	- Resolve notebook paths with `PYTUTOR_NOTEBOOKS_DIR` override.
 	- Provide a single path resolver used everywhere.

- `expectations.py`:
 	- Normalise outputs (single-line vs multi-line, trailing newline handling).
 	- Provide helpers like `expected_output(exercise_no)` for common patterns.
 	- Contain data structures for expected outputs and print counts.

- `assertions.py`:
 	- Provide high-level assertions with consistent failure text.
 	- Examples: `assert_output_matches`, `assert_print_count`, `assert_constructs`.

- `constructs.py`:
	- Shared checks for code constructs (e.g., `print(...)` usage, operators).
	- Uses AST-based checks by default for Python syntax constructs.
	- Takes parameters to avoid per-exercise duplication.
	- Example helper: `check_required_operator(code, "*")`.

- `reporting.py`:
 	- Student-facing tables and formatting.
 	- Encodes rules for error wrapping and status formatting.
 	- Uses a single table renderer (currently `tabulate`).

- `fixtures.py`:
 	- pytest fixtures for commonly repeated setup.
 	- Example: `notebook_ns`, `captured_output`, `exercise_code`.

### Data Flow (Single Exercise)

1. Resolve the notebook path via `paths.py`.
2. Extract tagged code with `runtime.py`.
3. Execute the tagged code with `runtime.py`.
4. Apply expectations from `expectations.py`.
5. Assert outcomes with `assertions.py`.
6. Report results through `reporting.py` when student-facing output is needed.

### Additional Refactor Constraints and Clarifications

- **No backwards-compatibility shim for legacy tests**:
	- The non-ex002 test suites are intentionally out of date and will be migrated later.
	- Do not add compatibility wrappers solely to preserve legacy test imports or helper names.
	- During this refactor stage, prioritise clean architecture for ex002 and framework internals.

- **Canonical expectations location**:
	- Consolidate expectations into package-based modules under `tests/exercise_expectations/`.
	- Remove or deprecate duplicate expectation definitions to ensure there is exactly one source of truth.

- **Path declaration standard**:
	- Use repo-relative notebook paths in expectations data.
	- Resolve paths only through the shared resolver in `paths.py`; avoid ad-hoc `Path(...).resolve()` in expectation modules.

- **Execution reuse model**:
	- Within a single check run, cache execution artefacts per `(notebook_path, tag, input_signature)` where safe.
	- Reuse captured output/code snapshots across logic/formatting checks to reduce duplicated execution.
	- Keep construct checks independent of runtime side effects by sourcing code via extraction helpers.

- **Error normalisation policy**:
	- All student-facing reporting must use one canonical normalisation pipeline.
	- The pipeline must include prefix stripping, issue joining, wrapping rules, and continuation-row formatting.
	- ex002 remains the reference behaviour, and the same policy should be reusable for later exercise migrations.

- **Autograder scoring stability**:
	- Preserve collected test cardinality and task grouping for existing ex002 tests during migration.
	- Add parity checks for collected test count and task distribution so point allocation does not drift silently.

### Shared Helpers (Examples)

- Construct checks should be parameterised and reusable:
	- `check_print_usage(code)`
	- `check_required_operator(code, operator)`
	- `check_required_operator_ast(code, operator)`
	- `check_no_placeholder_phrases(text, phrases)`

- Expectation helpers should be consistent and minimal:
 	- `expected_single_line(exercise_no)`
 	- `expected_multi_line(exercise_no)`
 	- `expected_print_calls(exercise_no)`

### Test Patterns

- Each exercise test file should only:
 	- Declare expectations for that exercise.
 	- Call shared helpers and assertions.
 	- Avoid custom execution logic and ad-hoc parsing.

- Example pattern:
 	- Use `runtime.exec_tagged_code` to get output.
 	- Use `assertions.assert_output_matches` to validate output.
 	- Use `constructs.check_required_operator` to validate code structure.

### Naming Conventions

- Files and modules: snake_case.
- Helpers: `check_*`, `assert_*`, `expected_*` for clarity.
- Fixtures: descriptive noun phrases (`exercise_output`, `exercise_code`).

### Migration Steps

1. Introduce `tests/exercise_framework/` with small, single-purpose modules.
2. Move notebook resolution into `paths.py` and update callers.
3. Move execution helpers into `runtime.py` and update tests.
4. Add `api.py` as the stable public entry point and route framework consumers through it.
5. Extract repeated construct logic into `constructs.py` (AST-first) and use it in tests.
6. Extract repeated expectation logic into `expectations.py` and remove duplicated expectation sources.
7. Centralise table rendering in `reporting.py` with a shared normalisation pipeline.
8. Update ex002 tests to use fixtures and assertions while preserving observable behaviour.
9. Update scripts and agents to call framework entry points exposed by `api.py`.
10. Migrate non-ex002 legacy tests later, after ex002 parity is proven.

### Parity Gates Per Migration Stage

Each migration step should complete only when the relevant parity gate passes.

- **Gate A (paths/runtime)**:
	- `PYTUTOR_NOTEBOOKS_DIR` override and fallback behaviour unchanged.
	- ex002 checks still execute all 30 check rows.

- **Gate B (constructs/expectations)**:
	- Logic, formatting, and construct failure messages remain behaviourally equivalent.
	- Multi-line expected output messaging remains `line1 | line2`.

- **Gate C (reporting)**:
	- Grid formatting, emoji status labels, and 40-character error wrapping unchanged.
	- Continuation rows keep blank exercise/check/status columns.

- **Gate D (autograde)**:
	- Collected test count and task distribution for ex002 unchanged.
	- Payload schema remains compatible in full and `--minimal` modes.

### Benefits for Exercise Generation and Verifier Agents

- Fewer steps: a single entry point handles path resolution, execution, checking, and reporting.
- Less duplication: generators and verifiers can reuse the same helper APIs.
- Lower error rate: shared helpers prevent inconsistent or incomplete checks.
- Easier extension: new exercises require adding only expectations and minimal test wiring.

### GitHub Classroom Autograder Integration

The refactor must preserve behaviour for both the regular pytest workflow and the GitHub Classroom autograder pipeline.

- **Shared core**: the same runtime, expectation, and assertion helpers should be used by standard tests and autograde runs. This avoids divergence between developer checks and classroom grading.
- **Autograde plugin**: the pytest plugin in [tests/autograde_plugin.py](tests/autograde_plugin.py) must continue to collect results using standard pytest outcomes. The refactor should not require special-casing in the tests for autograde mode.
- **Payload builder**: [scripts/build_autograde_payload.py](scripts/build_autograde_payload.py) relies on the autograde JSON schema produced by the plugin. The refactor must preserve:
	- Test result names and statuses (`pass`, `fail`, `error`).
	- Task markers (`@pytest.mark.task`) and display names.
	- Output capture fields (stdout, stderr, log) when present.
- **Environment control**: autograde runs typically set `PYTUTOR_NOTEBOOKS_DIR=notebooks` to grade student notebooks. The path resolver must keep the same override and fallback behaviour so CI matches local checks.
- **Minimal vs full payload**: the `--minimal` mode must remain viable; do not add required fields that are only present in verbose mode.

**Implication for refactor**: avoid moving or renaming autograde plugin hooks or the payload schema without an explicit migration. The new framework should expose a single test harness API that both standard tests and autograde runs can call, so the plugin observes the same results in all modes.

## Behaviour Parity Checklist

Use this list to verify the refactor preserves observable behaviour.

- Path resolution respects `PYTUTOR_NOTEBOOKS_DIR` with fallback rules unchanged.
- Table output uses `tabulate` with `tablefmt="grid"` and aligned emoji status labels.
- Summary tables show only `Check` and `Status` columns for the default run.
- ex002 uses a 4-column grouped table with `Logic`, `Formatting`, `Construct` rows.
- Error wrapping is 40 characters wide with long-word splitting and blanked columns on continuation lines.
- ex002 error messages strip the `Exercise N:` prefix.
- Multi-line expected outputs are joined with ` | ` in error messages.
- Formatting checks run only when a print count is configured.
- Construct checks require `print(...)` and expected operators per exercise.
- Multiple issues for a single check are joined with `; `.
- Success message prints only when all checks pass.

### Autograder Compatibility Checklist

Use this list to verify GitHub Classroom autograding remains stable after refactor.

- Autograde plugin hooks still run without test changes in autograde mode.
- Test results preserve `pass`/`fail`/`error` statuses and task markers.
- Display names remain derived from markers/docstrings/nodeids as before.
- Autograde JSON schema remains compatible with the payload builder.
- `build_autograde_payload.py` produces identical fields in full and minimal modes.
- `PYTUTOR_NOTEBOOKS_DIR=notebooks` continues to grade student notebooks by default.
