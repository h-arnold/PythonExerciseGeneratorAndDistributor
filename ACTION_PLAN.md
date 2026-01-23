# Autograder Integration Action Plan

## Overview

This action plan implements GitHub Classroom autograding integration by creating a pytest plugin to capture test results, a CLI wrapper to generate Base64-encoded payloads for the `autograding-grading-reporter` action, and updating the template repository workflow. The implementation preserves granular, task-focused feedback while ensuring compatibility with existing notebook test infrastructure.

---

## 1. Inspect Existing Infrastructure ✅

**Status**: COMPLETED

### Findings

- Notebook execution flows through [tests/notebook_grader.py](tests/notebook_grader.py) and [tests/helpers.py](tests/helpers.py)
- `pytest.mark.task(taskno=N)` already labels multi-step exercises (extensive usage in [tests/test_ex004_sequence_debug_syntax.py](tests/test_ex004_sequence_debug_syntax.py))
- Template packaging copies the grader helper via [scripts/template_repo_cli/core/packager.py](scripts/template_repo_cli/core/packager.py)
- Template workflow currently runs [template_repo_files/.github/workflows/tests.yml](template_repo_files/.github/workflows/tests.yml) without additional autograding tooling
- Tests without `@pytest.mark.task` exist (e.g., [tests/test_ex001_sanity.py](tests/test_ex001_sanity.py)) and need sensible defaults

### Impact

- New plugin must coexist with existing helpers and be shipped into templates alongside the grader
- Tests without `@pytest.mark.task` need sensible defaults (task number `None`, human-readable names from docstrings or nodeids)
- Plugin must handle both tagged and untagged tests gracefully

### Implementation Notes

*Notes from infrastructure inspection will be recorded here.*

---

## 2. Design Pytest Autograde Plugin

### Tasks

- [x] **2.1**: Define data structures for autograding results
  - **File**: Create `tests/autograde_plugin.py`
  - **Implementation**: Define `AutogradeTestResult` TypedDict with fields: `nodeid`, `name`, `taskno`, `status`, `score`, `max_score`, `line_no`, `message`, `duration`
  - **Implementation**: Define `AutogradeCollector` class to store test results during pytest run
  - **Implementation**: Define overall payload structure matching reporter requirements: `max_score`, `status`, `tests` array

- [x] **2.2**: Design pytest hook integration points
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Plan `pytest_addoption` for `--autograde-results-path` CLI option
  - **Implementation**: Plan `pytest_configure` to attach collector to config object
  - **Implementation**: Plan `pytest_collection_modifyitems` to extract task metadata from markers
  - **Implementation**: Plan `pytest_runtest_logreport` to capture test outcomes
  - **Implementation**: Plan `pytest_sessionfinish` to write JSON results

- [x] **2.3**: Define test name extraction logic
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Precedence: `@pytest.mark.task(name="...")` > function docstring first line > nodeid test function name
  - **Implementation**: Handle missing/malformed docstrings gracefully
  - **Implementation**: Strip common test prefixes (`test_`, `test_exercise`) for cleaner names

- [x] **2.4**: Document plugin behaviour in module docstring
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Explain pytest hook usage
  - **Implementation**: Document CLI option requirements
  - **Implementation**: Provide example usage: `pytest --autograde-results-path=tmp/results.json`
  - **Implementation**: Document error handling strategies

### Files to Create
- `tests/autograde_plugin.py` (new file, ~250-300 lines)

### Files to Modify
- None (plugin registration via command-line flag, not pyproject.toml)

### Implementation Notes

*Design decisions, API choices, and architectural notes will be recorded here.*

---

## 3. Implement Pytest Autograde Plugin

### Tasks

- [x] **3.1**: Implement CLI option registration
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_addoption(parser)` hook
  - **Implementation**: Register `--autograde-results-path` option (type: `str`, required in workflow, optional for local testing)
  - **Implementation**: Add help text explaining plugin purpose

- [x] **3.2**: Implement configuration hook
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_configure(config)` hook
  - **Implementation**: Create `AutogradeCollector` instance and attach to `config._autograde_state`
  - **Implementation**: Initialize empty `tests` list and `had_errors` flag

- [x] **3.3**: Implement collection hook
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_collection_modifyitems(config, items)` hook
  - **Implementation**: Extract `taskno` from `@pytest.mark.task(taskno=N)` markers
  - **Implementation**: Extract test name from marker `name`, docstring, or nodeid
  - **Implementation**: Store mapping in collector for later result correlation

- [x] **3.4**: Implement reporting hook
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_runtest_logreport(report)` hook
  - **Implementation**: Filter for `when == "call"` phase
  - **Implementation**: Determine status: `pass`/`fail`/`error` from report
  - **Implementation**: Calculate score: 1 for pass, 0 otherwise
  - **Implementation**: Extract failure message from `report.longreprtext` (truncate to 1000 chars)
  - **Implementation**: Extract line number from `report.location` (default to 0 if unavailable)
  - **Implementation**: Record duration from `report.duration`
  - **Implementation**: Create `AutogradeTestResult` and append to collector

- [x] **3.5**: Implement session finish hook
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_sessionfinish(session, exitstatus)` hook
  - **Implementation**: Calculate `max_score = len(tests)`
  - **Implementation**: Calculate `earned_score = sum(test["score"] for test in tests)`
  - **Implementation**: Determine overall status: `pass` if all pass, `fail` if any fail, `error` if any error
  - **Implementation**: Build JSON payload dictionary
  - **Implementation**: Ensure parent directory exists for output file
  - **Implementation**: Write JSON with UTF-8 encoding, `ensure_ascii=False`, `indent=2`

- [x] **3.6**: Add terminal summary output
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Add `pytest_terminal_summary(terminalreporter, exitstatus, config)` hook
  - **Implementation**: Print results file path to terminal
  - **Implementation**: Print summary: X/Y tests passed, score: N/M

- [x] **3.7**: Add error handling
  - **File**: `tests/autograde_plugin.py`
  - **Implementation**: Handle missing/malformed markers gracefully
  - **Implementation**: Handle file write errors (log to stderr, don't fail pytest)
  - **Implementation**: Handle directory creation failures
  - **Implementation**: Write minimal valid JSON on catastrophic failure: `{"max_score": 0, "status": "error", "tests": []}`

### Test Cases

Plugin testing will be implemented in Task 6.1. Required test cases:
- Plugin correctly captures passing tests
- Plugin correctly captures failing tests
- Plugin correctly captures error tests (setup/teardown failures)
- Plugin extracts task numbers from markers
- Plugin handles missing task markers (defaults to `None`)
- Plugin extracts test names from docstrings
- Plugin handles missing docstrings (falls back to nodeid)
- Plugin writes valid JSON to specified path
- Plugin creates parent directories if missing
- Plugin handles file write errors gracefully

### Files to Create
- `tests/autograde_plugin.py` (new file)

### Files to Modify
- None

### Implementation Notes

*Implementation challenges, deviations from design, and technical decisions will be recorded here.*

---

## 4. Build Payload CLI Wrapper

### Tasks

- [x] **4.1**: Create script skeleton and argument parsing
  - **File**: Create `scripts/build_autograde_payload.py`
  - **Implementation**: Add module docstring explaining purpose
  - **Implementation**: Import required modules: `argparse`, `base64`, `json`, `os`, `subprocess`, `sys`, `pathlib`
  - **Implementation**: Define `parse_args()` function with arguments:
    - `--pytest-args` (action='append', default=['-q']) - forward to pytest
    - `--results-json` (default='tmp/autograde/results.json') - plugin output path
    - `--output` (default='tmp/autograde/payload.txt') - Base64 output path
    - `--summary` (optional) - raw JSON summary path for debugging

- [x] **4.2**: Implement environment validation
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `validate_environment()` function
  - **Implementation**: Check `PYTUTOR_NOTEBOOKS_DIR` is unset or equals `notebooks`
  - **Implementation**: Raise `RuntimeError` with clear message if validation fails
  - **Implementation**: Log environment info for debugging

- [x] **4.3**: Implement pytest execution wrapper
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `run_pytest(results_path, pytest_args)` function
  - **Implementation**: Build command: `["pytest"] + pytest_args + [f"--autograde-results-path={results_path}"]`
  - **Implementation**: Execute via `subprocess.run(cmd, check=False, capture_output=True, text=True)`
  - **Implementation**: Return exit code and combined stdout/stderr for logging
  - **Implementation**: Print pytest output to console in real-time (use `stdout=None, stderr=None`)

- [x] **4.4**: Implement JSON loading and validation
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `load_results(results_path)` function
  - **Implementation**: Check file exists, raise descriptive error if missing
  - **Implementation**: Load JSON with UTF-8 encoding
  - **Implementation**: Validate schema: required keys `max_score`, `status`, `tests`
  - **Implementation**: Validate `tests` is list of dicts with required keys
  - **Implementation**: Return parsed dictionary

- [x] **4.5**: Implement payload builder
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `build_payload(results)` function
  - **Implementation**: Preserve all test fields from plugin output
  - **Implementation**: Add extra debug fields: `task`, `nodeid`, `duration`
  - **Implementation**: Return payload dictionary

- [x] **4.6**: Implement Base64 encoding
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `encode_payload(payload)` function
  - **Implementation**: Serialize JSON with `ensure_ascii=False, indent=2`
  - **Implementation**: Encode to UTF-8 bytes, then Base64
  - **Implementation**: Decode Base64 bytes to ASCII string
  - **Implementation**: Return Base64 string

- [x] **4.7**: Implement summary table printer
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `print_summary(results)` function
  - **Implementation**: Print overall score: `X/Y points (Z%)`
  - **Implementation**: Group tests by task number
  - **Implementation**: Print per-task table: task number, passed/total, score
  - **Implementation**: Print list of failing tests with messages (truncated)
  - **Implementation**: Use proper table formatting for readability

- [x] **4.8**: Implement GitHub Actions output writer
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `write_github_outputs(payload_base64, results)` function
  - **Implementation**: Check `GITHUB_OUTPUT` environment variable exists
  - **Implementation**: Append outputs: `encoded_payload`, `overall_status`, `earned_score`, `max_score`
  - **Implementation**: Use format: `key=value\n`
  - **Implementation**: Handle file write errors gracefully (log warning, don't fail)

- [x] **4.9**: Implement main execution flow
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Define `main()` function
  - **Implementation**: Parse arguments
  - **Implementation**: Validate environment
  - **Implementation**: Create output directories
  - **Implementation**: Run pytest
  - **Implementation**: Load and validate results
  - **Implementation**: Build payload
  - **Implementation**: Encode to Base64
  - **Implementation**: Write Base64 to output file
  - **Implementation**: Write optional summary JSON
  - **Implementation**: Print summary table
  - **Implementation**: Write GitHub outputs if in CI
  - **Implementation**: Return pytest exit code

- [x] **4.10**: Add script entry point
  - **File**: `scripts/build_autograde_payload.py`
  - **Implementation**: Add `if __name__ == "__main__": sys.exit(main())`

### Test Cases

CLI testing will be implemented in Task 6.2. Required test cases:
- Script runs pytest successfully
- Script handles pytest failures (exit code propagation)
- Script validates environment correctly
- Script rejects wrong `PYTUTOR_NOTEBOOKS_DIR`
- Script creates output directories
- Script writes Base64 payload to file
- Script writes summary JSON when requested
- Script outputs valid summary table
- Script writes GitHub outputs in CI environment
- Script handles missing results file gracefully
- Script handles malformed JSON gracefully

### Files to Create
- `scripts/build_autograde_payload.py` (new file, ~300-400 lines)

### Files to Modify
- None

### Implementation Notes

*CLI implementation notes, edge cases handled, and execution flow decisions will be recorded here.*

---

## 5. Integrate CLI with Packager

### Tasks

- [x] **5.1**: Add script to packager file list
  - **File**: `scripts/template_repo_cli/core/packager.py`
  - **Implementation**: Locate `copy_template_base_files()` method (around line 85)
  - **Implementation**: Add copy operation for `scripts/build_autograde_payload.py` to workspace `scripts/` directory
  - **Implementation**: Ensure `scripts/` directory exists in workspace before copying

- [x] **5.2**: Add autograde plugin to packager
  - **File**: `scripts/template_repo_cli/core/packager.py`
  - **Implementation**: Add copy operation for `tests/autograde_plugin.py` to workspace `tests/` directory
  - **Implementation**: Ensure copying happens after `tests/` directory creation

- [x] **5.3**: Update packager validation
  - **File**: `scripts/template_repo_cli/core/packager.py`
  - **Implementation**: Locate `validate_package()` method (around line 118)
  - **Implementation**: Add validation check for `scripts/build_autograde_payload.py` existence
  - **Implementation**: Add validation check for `tests/autograde_plugin.py` existence

- [x] **5.4**: Document packager changes
  - **File**: `scripts/template_repo_cli/core/packager.py`
  - **Implementation**: Update module docstring to mention autograding files
  - **Implementation**: Add inline comments explaining autograding file copies

### Test Cases

Packager testing will be updated in Task 6.3. Required test cases:
- Packager copies `build_autograde_payload.py` to workspace
- Packager copies `autograde_plugin.py` to workspace
- Packager validation checks for autograding files
- Packager maintains correct directory structure
- Integration test verifies complete package includes autograding files

### Files to Modify
- `scripts/template_repo_cli/core/packager.py` (add ~15-20 lines)

### Implementation Notes

*Packager integration notes, file copy strategies, and validation logic will be recorded here.*

---

## 6. Add Automated Tests

### Tasks

- [x] **6.1**: Create plugin unit tests
  - **File**: Create `tests/test_autograde_plugin.py`
  - **Tests to implement**:
    - `test_plugin_captures_passing_test` - Verify plugin captures passing test with score 1
    - `test_plugin_captures_failing_test` - Verify plugin captures failing test with score 0
    - `test_plugin_captures_error_test` - Verify plugin captures error (setup/teardown failure) with status 'error'
    - `test_plugin_extracts_task_number` - Verify plugin extracts taskno from `@pytest.mark.task(taskno=N)`
    - `test_plugin_handles_missing_task_marker` - Verify plugin defaults taskno to None for unmarked tests
    - `test_plugin_extracts_name_from_marker` - Verify `@pytest.mark.task(name="...")` takes precedence
    - `test_plugin_extracts_name_from_docstring` - Verify plugin uses first line of docstring as fallback
    - `test_plugin_extracts_name_from_nodeid` - Verify plugin uses nodeid as final fallback
    - `test_plugin_writes_valid_json` - Verify output JSON is valid and has correct structure
    - `test_plugin_creates_output_directory` - Verify plugin creates parent directories if missing
    - `test_plugin_handles_write_errors` - Verify plugin logs errors but doesn't fail pytest
    - `test_plugin_calculates_max_score` - Verify max_score equals number of tests
    - `test_plugin_calculates_overall_status_pass` - Verify status is 'pass' when all pass
    - `test_plugin_calculates_overall_status_fail` - Verify status is 'fail' when any fail
    - `test_plugin_calculates_overall_status_error` - Verify status is 'error' when any error
    - `test_plugin_truncates_long_messages` - Verify failure messages are truncated to 1000 chars
    - `test_plugin_extracts_line_numbers` - Verify line numbers are extracted from report.location
  - **Implementation**: Use `pytester` fixture for pytest plugin testing
  - **Implementation**: Create minimal test files in `pytester` for each scenario
  - **Implementation**: Invoke pytest with plugin via `pytester.runpytest()`
  - **Implementation**: Load and validate resulting JSON files

- [x] **6.2**: Create CLI integration tests
  - **File**: Create `tests/test_build_autograde_payload.py`
  - **Tests to implement**:
    - `test_cli_runs_pytest_successfully` - Verify CLI executes pytest and captures results
    - `test_cli_propagates_pytest_exit_code` - Verify CLI returns pytest exit code
    - `test_cli_validates_environment` - Verify CLI checks PYTUTOR_NOTEBOOKS_DIR
    - `test_cli_rejects_wrong_notebook_dir` - Verify CLI raises error for wrong PYTUTOR_NOTEBOOKS_DIR
    - `test_cli_creates_output_directories` - Verify CLI creates tmp/autograde/
    - `test_cli_writes_base64_payload` - Verify CLI writes Base64-encoded string to file
    - `test_cli_writes_summary_json` - Verify CLI writes raw JSON when --summary specified
    - `test_cli_prints_summary_table` - Verify CLI prints readable summary to stdout
    - `test_cli_writes_github_outputs` - Verify CLI writes to GITHUB_OUTPUT when present
    - `test_cli_handles_missing_results_file` - Verify CLI raises error when results file missing
    - `test_cli_handles_malformed_json` - Verify CLI raises error for malformed JSON
    - `test_cli_forwards_pytest_args` - Verify CLI forwards additional pytest arguments
    - `test_cli_decodes_base64_correctly` - Verify Base64 can be decoded back to original JSON
  - **Implementation**: Use `subprocess.run()` to invoke CLI script
  - **Implementation**: Use temporary directories for output files
  - **Implementation**: Create minimal notebook and test fixtures
  - **Implementation**: Verify file outputs match expectations

- [x] **6.3**: Update packager tests
  - **File**: `tests/template_repo_cli/test_packager.py`
  - **Tests to implement**:
    - `test_packager_copies_autograde_script` - Verify build_autograde_payload.py is copied
    - `test_packager_copies_autograde_plugin` - Verify autograde_plugin.py is copied
    - `test_packager_validates_autograde_files` - Verify validation checks for autograding files
    - `test_packager_creates_scripts_directory` - Verify scripts/ directory is created
  - **Implementation**: Extend existing `TestCopyFiles` class
  - **Implementation**: Add assertions for new file copies in existing tests
  - **Implementation**: Verify directory structure includes `scripts/`

- [x] **6.4**: Create end-to-end integration test
  - **File**: `tests/test_integration_autograding.py` (new file)
  - **Tests to implement**:
    - `test_full_autograding_flow` - Complete flow from pytest to Base64 payload
      - Run plugin to generate results.json
      - Run CLI to generate payload
      - Decode Base64 and verify structure
      - Verify payload matches reporter requirements
    - `test_autograding_with_real_exercise` - Use actual exercise notebook (ex001_sanity)
      - Run against solution notebook
      - Verify all tests pass and score is 100%
      - Run against student notebook (expect failures)
      - Verify partial score reflects actual completion
  - **Implementation**: Use real notebook files from repository
  - **Implementation**: Set `PYTUTOR_NOTEBOOKS_DIR` appropriately
  - **Implementation**: Verify complete workflow in subprocess

### Files to Create
- `tests/test_autograde_plugin.py` (new file, ~400-500 lines)
- `tests/test_build_autograde_payload.py` (new file, ~300-400 lines)
- `tests/test_integration_autograding.py` (new file, ~150-200 lines)

### Files to Modify
- `tests/template_repo_cli/test_packager.py` (add ~40-60 lines)

### Implementation Notes

*Testing notes, discovered edge cases, fixture strategies, and coverage metrics will be recorded here.*

---

## 7. Update Template Workflow

### Tasks

- [x] **7.1**: Create new classroom workflow
  - **File**: Create `template_repo_files/.github/workflows/classroom.yml`
  - **Implementation**: Add workflow name: `"Autograding"`
  - **Implementation**: Add triggers: `push`, `pull_request`, `workflow_dispatch`
  - **Implementation**: Add permissions: `contents: read`
  - **Implementation**: Define job: `autograding` on `ubuntu-latest`

- [x] **7.2**: Add workflow steps
  - **File**: `template_repo_files/.github/workflows/classroom.yml`
  - **Implementation**: Step 1: Checkout code (`actions/checkout@v4`)
  - **Implementation**: Step 2: Install uv (`astral-sh/setup-uv@v5` or manual installation)
  - **Implementation**: Step 3: Cache uv dependencies (use `actions/cache@v4` with `~/.cache/uv` path)
  - **Implementation**: Step 4: Install dependencies (`uv sync`)
  - **Implementation**: Step 5: Run autograder CLI
    - `id: build`
    - `continue-on-error: true` (allows reporter to run even on failure)
    - `env: PYTUTOR_NOTEBOOKS_DIR: notebooks`
    - `run: uv run python scripts/build_autograde_payload.py --output tmp/autograde/payload.txt`
  - **Implementation**: Step 6: Prepare reporter inputs
    - `if: always()` (run even if build fails)
    - Read Base64 from file: `cat tmp/autograde/payload.txt`
    - Export to environment: `echo "PYTEST_RESULTS=$(cat tmp/autograde/payload.txt)" >> $GITHUB_ENV`
  - **Implementation**: Step 7: Run autograding reporter
    - `if: always()`
    - `uses: classroom-resources/autograding-grading-reporter@v1`
    - `env: PYTEST_RESULTS: ${{ env.PYTEST_RESULTS }}`
    - `with: runners: pytest`
  - **Implementation**: Step 8: Fail job if tests failed
    - `if: steps.build.outcome == 'failure'`
    - `run: exit 1`

- [x] **7.3**: Document workflow behaviour
  - **File**: `template_repo_files/.github/workflows/classroom.yml`
  - **Implementation**: Add comments explaining each step
  - **Implementation**: Add comment explaining `continue-on-error` strategy
  - **Implementation**: Add comment explaining reporter payload format

- [x] **7.4**: Handle old workflow
  - **File**: `template_repo_files/.github/workflows/tests.yml`
  - **Decision**: Determine if keeping both workflows or replacing
  - **Implementation** (if keeping both): Rename to `tests-dev.yml` or similar for local testing
  - **Implementation** (if replacing): Document migration in changelog
  - **Implementation**: Update packager to include new workflow

- [x] **7.5**: Update workflow packaging
  - **File**: `scripts/template_repo_cli/core/packager.py`
  - **Implementation**: Verify `.github/workflows/` directory is copied
  - **Implementation**: Verify `classroom.yml` is included in copy
  - **Implementation**: Update validation to check for `classroom.yml`

### Files to Create
- `template_repo_files/.github/workflows/classroom.yml` (new file, ~80-100 lines)

### Files to Modify
- `template_repo_files/.github/workflows/tests.yml` (optional rename/removal)
- `scripts/template_repo_cli/core/packager.py` (update validation if needed)

### Implementation Notes

*Workflow design decisions, GitHub Actions version choices, and CI/CD integration notes will be recorded here.*

---

## 8. Refresh Documentation

### Tasks

- [x] **8.1**: Update GitHub Classroom integration guide
  - **File**: `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md`
  - **Implementation**: Add section "Custom Pytest Integration"
  - **Implementation**: Explain plugin architecture and how it captures results
  - **Implementation**: Document CLI wrapper usage and arguments
  - **Implementation**: Provide example of running locally: `uv run python scripts/build_autograde_payload.py`
  - **Implementation**: Explain Base64 payload format and why it's needed
  - **Implementation**: Document workflow steps and their purpose
  - **Implementation**: Add troubleshooting section:
    - What to do if plugin doesn't capture tests
    - How to debug missing task numbers
    - How to verify payload format
    - Common workflow errors and solutions
  - **Implementation**: Add example payload structure with annotations

- [x] **8.2**: Update exercise testing documentation
  - **File**: `docs/exercise-testing.md`
  - **Implementation**: Add section on autograding integration
  - **Implementation**: Explain 1 test = 1 point scoring model
  - **Implementation**: Document `@pytest.mark.task(taskno=N)` usage
  - **Implementation**: Document `@pytest.mark.task(name="...")` for custom test names
  - **Implementation**: Explain how unmarked tests are handled
  - **Implementation**: Provide guidelines for writing autograder-friendly tests
  - **Implementation**: Add examples of good vs. bad test naming

- [x] **8.3**: Update project structure documentation
  - **File**: `docs/project-structure.md`
  - **Implementation**: Add `tests/autograde_plugin.py` to structure diagram
  - **Implementation**: Add `scripts/build_autograde_payload.py` to structure diagram
  - **Implementation**: Add description of autograding files purpose
  - **Implementation**: Update template workflow section

- [x] **8.4**: Create autograding CLI reference
  - **File**: Create `docs/autograding-cli.md` (new file)
  - **Implementation**: Document CLI arguments with examples
  - **Implementation**: Provide usage patterns:
    - Local testing: `uv run python scripts/build_autograde_payload.py --summary tmp/summary.json`
    - CI usage: `uv run python scripts/build_autograde_payload.py --output tmp/payload.txt`
  - **Implementation**: Document output formats (JSON, Base64, summary table)
  - **Implementation**: Explain environment requirements and validation
  - **Implementation**: Provide troubleshooting guide
  - **Implementation**: Add examples of payload inspection

- [x] **8.5**: Update development guide
  - **File**: `docs/development.md`
  - **Implementation**: Add section on testing autograding locally
  - **Implementation**: Document how to run plugin in development
  - **Implementation**: Explain how to test workflow changes
  - **Implementation**: Add guidelines for maintaining autograding compatibility

- [x] **8.6**: Update README
  - **File**: `README.md`
  - **Implementation**: Add brief mention of GitHub Classroom integration
  - **Implementation**: Link to detailed autograding documentation
  - **Implementation**: Update feature list to include autograding

### Files to Create
- `docs/autograding-cli.md` (new file, ~100-150 lines)

### Files to Modify
- `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md` (add ~150-200 lines)
- `docs/exercise-testing.md` (add ~80-100 lines)
- `docs/project-structure.md` (add ~30-40 lines)
- `docs/development.md` (add ~60-80 lines)
- `README.md` (add ~10-20 lines)

### Implementation Notes

*Documentation notes, content organization decisions, and user feedback incorporation will be recorded here.*

---

## 9. End-to-End Verification

### Tasks

- [ ] **9.1**: Test plugin locally with solutions
  - **Command**: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q --autograde-results-path=tmp/results.json`
  - **Verification**:
    - JSON file is created at `tmp/results.json`
    - All tests pass (status: "pass" for each test)
    - Score equals max_score
    - Task numbers are correctly extracted
    - Test names are human-readable
  - **Documentation**: Record any issues or unexpected behaviour

- [ ] **9.2**: Test plugin locally with student notebooks
  - **Command**: `pytest -q --autograde-results-path=tmp/results.json`
  - **Verification**:
    - JSON file is created
    - Tests fail as expected (student notebooks are incomplete)
    - Failure messages are descriptive
    - Scores reflect partial completion
  - **Documentation**: Record any issues with error messages

- [ ] **9.3**: Test CLI wrapper with solutions
  - **Command**: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions uv run python scripts/build_autograde_payload.py --output tmp/payload.txt --summary tmp/summary.json`
  - **Verification**:
    - Base64 payload is written to `tmp/payload.txt`
    - Summary JSON is written to `tmp/summary.json`
    - Summary table is printed to stdout
    - Base64 can be decoded back to valid JSON
    - Decoded JSON matches summary JSON
    - Exit code is 0 (all tests pass)
  - **Documentation**: Record payload size and structure

- [ ] **9.4**: Test CLI wrapper with student notebooks
  - **Command**: `uv run python scripts/build_autograde_payload.py --output tmp/payload.txt --summary tmp/summary.json`
  - **Verification**:
    - Base64 payload is written
    - Summary shows partial score
    - Summary table lists failing tests
    - Exit code is non-zero (tests fail)
  - **Documentation**: Record failure reporting quality

- [ ] **9.5**: Inspect Base64 payload structure
  - **Implementation**: Decode Base64 payload and pretty-print JSON
  - **Verification**:
    - Payload matches reporter schema exactly
    - All required fields are present: `max_score`, `status`, `tests`
    - Each test has required fields: `name`, `status`, `score`, `message`
    - Optional fields are included: `task`, `nodeid`, `duration`, `line_no`
  - **Documentation**: Save sample payload for reference

- [ ] **9.6**: Test packager integration
  - **Command**: Run template packager CLI to create test repository
  - **Verification**:
    - `scripts/build_autograde_payload.py` is copied to workspace
    - `tests/autograde_plugin.py` is copied to workspace
    - `.github/workflows/classroom.yml` is copied to workspace
    - Validation passes
  - **Documentation**: Record packager output

- [ ] **9.7**: Test workflow in template repository
  - **Implementation**: Create temporary Git repository from packaged template
  - **Implementation**: Initialize Git and push to test repository
  - **Implementation**: Trigger workflow via push or workflow_dispatch
  - **Verification**:
    - Workflow runs without errors
    - Pytest executes and generates payload
    - Reporter step receives payload
    - Workflow fails if tests fail (student notebooks)
    - Workflow passes if tests pass (solution notebooks)
  - **Documentation**: Save workflow run logs

- [ ] **9.8**: Simulate reporter invocation (optional)
  - **Implementation**: Manually construct reporter environment
  - **Implementation**: Set `PYTEST_RESULTS` environment variable with Base64 payload
  - **Implementation**: Call reporter action locally or inspect what it would receive
  - **Verification**:
    - Reporter would parse payload correctly
    - Score would be displayed in Classroom UI
  - **Documentation**: Record expected reporter behaviour

- [ ] **9.9**: Verify complete student workflow
  - **Implementation**: Simulate student accepting assignment
  - **Implementation**: Student modifies notebook
  - **Implementation**: Student commits and pushes
  - **Verification**:
    - Workflow triggers automatically
    - Autograder runs against student code
    - Partial score is reported correctly
    - Feedback is visible to student
  - **Documentation**: Record student-visible output

### Files to Verify
- `tmp/results.json` (plugin output)
- `tmp/payload.txt` (Base64 encoded payload)
- `tmp/summary.json` (raw JSON for debugging)
- Packaged template workspace
- Workflow run logs

### Implementation Notes

*Verification results, edge cases discovered, performance metrics, and integration issues will be recorded here.*

---

## 10. Deployment Preparation

### Tasks

- [ ] **10.1**: Run complete test suite
  - **Command**: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q`
  - **Verification**: All tests pass, including new autograding tests
  - **Documentation**: Record test coverage metrics

- [ ] **10.2**: Run linting and type checking
  - **Command**: `ruff check . --fix`
  - **Verification**: No linting errors in new code
  - **Implementation**: Fix any issues found
  - **Documentation**: Record any style adjustments made

- [ ] **10.3**: Review code quality
  - **Action**: Run Tidy Code Reviewer agent on all changes
  - **Verification**: Agent approves code quality
  - **Implementation**: Address any reviewer feedback
  - **Documentation**: Record review outcomes

- [ ] **10.4**: Update changelog
  - **File**: Create or update `CHANGELOG.md`
  - **Implementation**: Add entry for autograding integration
  - **Implementation**: List new features:
    - Pytest plugin for autograding
    - CLI wrapper for payload generation
    - GitHub Classroom workflow
    - Template packaging integration
  - **Implementation**: List breaking changes (if any)
  - **Implementation**: List migration steps (if needed)

- [ ] **10.5**: Prepare PR checklist
  - **Implementation**: Create PR description template
  - **Implementation**: List all files changed/created
  - **Implementation**: Summarize implementation approach
  - **Implementation**: Include verification results
  - **Implementation**: Add testing notes
  - **Implementation**: Link to relevant issues/specifications

- [ ] **10.6**: Create migration guide (if needed)
  - **File**: `docs/migration-autograding.md` (if workflow changes require user action)
  - **Implementation**: Document steps to update existing assignments
  - **Implementation**: Explain workflow file changes
  - **Implementation**: Provide migration script if needed

- [ ] **10.7**: Verify documentation completeness
  - **Action**: Review all documentation updates
  - **Verification**: All links work correctly
  - **Verification**: Code examples are accurate
  - **Verification**: Screenshots/diagrams are included where helpful
  - **Documentation**: Note any documentation gaps for future work

- [ ] **10.8**: Final integration test
  - **Action**: Run end-to-end test from exercise creation to autograding
  - **Verification**: Complete workflow works without manual intervention
  - **Documentation**: Record any final issues

### Files to Create
- `CHANGELOG.md` (new file or update existing)
- `docs/migration-autograding.md` (if needed)

### Files to Verify
- All test files pass
- All documentation is accurate
- All code is linted and formatted
- All integration points work

### Implementation Notes

*Deployment notes, release checklist, and final verification results will be recorded here.*

---

## Summary of Deliverables

### New Files Created (7-8 files)
1. `tests/autograde_plugin.py` - Pytest plugin for capturing test results
2. `scripts/build_autograde_payload.py` - CLI wrapper for payload generation
3. `template_repo_files/.github/workflows/classroom.yml` - GitHub Classroom workflow
4. `tests/test_autograde_plugin.py` - Plugin unit tests
5. `tests/test_build_autograde_payload.py` - CLI integration tests
6. `tests/test_integration_autograding.py` - End-to-end integration tests
7. `docs/autograding-cli.md` - CLI reference documentation
8. `CHANGELOG.md` (if not exists) - Project changelog

### Files Modified (6-7 files)
1. `scripts/template_repo_cli/core/packager.py` - Add autograding file packaging
2. `tests/template_repo_cli/test_packager.py` - Add packager tests
3. `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md` - Expand integration guide
4. `docs/exercise-testing.md` - Document autograding test patterns
5. `docs/project-structure.md` - Update structure diagram
6. `docs/development.md` - Add development workflow notes
7. `README.md` - Add feature mention

### Total Estimated Lines of Code
- Plugin: ~300 lines
- CLI: ~400 lines
- Workflow: ~100 lines
- Tests: ~1000 lines
- Documentation: ~500 lines
- **Total: ~2300 lines** (code + docs)
