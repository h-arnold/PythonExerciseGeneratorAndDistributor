# Autograder Integration Action Plan

## 1. Inspect Existing Infrastructure
- **Tasks**: Review `tests/notebook_grader.py`, helper utilities, and current pytest configuration; confirm existing markers (`@pytest.mark.task`) usage; inventory template repo packaging via `scripts/template_repo_cli`.
- **Success Criteria**: Documented notes on current test execution flow and packaging boundaries; no unanswered questions about marker availability or existing CLI behaviours.

## 2. Design Pytest Autograde Plugin
- **Tasks**: Draft interface for `tests/autograde_plugin.py`; define data schema for `AutogradeTestResult`; outline hook usage and truncation rules.
- **Success Criteria**: Approved plugin design covering CLI option, collection, reporting, and JSON output layout with edge-case handling (errors, missing marks).

## 3. Implement Pytest Autograde Plugin
- **Tasks**: Create `tests/autograde_plugin.py`; implement hooks (`pytest_addoption`, `pytest_configure`, `pytest_collection_modifyitems`, `pytest_runtest_logreport`, `pytest_sessionfinish`); ensure UTF-8 JSON writing and directory creation.
- **Success Criteria**: Plugin loads without errors; running `pytest --autograde-results-path=tmp/results.json` produces JSON conforming to the design in both pass and fail scenarios.

## 4. Build Payload CLI Wrapper
- **Tasks**: Implement `scripts/build_autograde_payload.py` with argument parsing, environment validation, pytest invocation, payload synthesis, Base64 encoding, reporter output, and GitHub Actions outputs.
- **Success Criteria**: Local run (`uv run python scripts/build_autograde_payload.py --pytest-args tests/test_ex001_sanity.py`) generates payload file, summary JSON, GitHub output entries, and returns pytest exit code.

## 5. Integrate CLI with Packager
- **Tasks**: Update `scripts/template_repo_cli/core/packager.py` (and related manifests if required) to include the new script in exported template repositories.
- **Success Criteria**: Packaging command includes `scripts/build_autograde_payload.py` in the generated template; manual inspection confirms presence.

## 6. Add Automated Tests
- **Tasks**: Write unit tests for the plugin using `pytester`; create integration test invoking the CLI with sample notebooks; ensure temporary directories cleanup.
- **Success Criteria**: New tests pass in `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q`; failures clearly indicate regression points.

## 7. Update Template Workflow
- **Tasks**: Modify `template_repo_files/.github/workflows/classroom.yml` to run the new CLI, capture payload, call reporter, and enforce failure gate.
- **Success Criteria**: Workflow YAML passes linting; dry-run (or local action validation) confirms correct step sequencing and environment usage.

## 8. Refresh Documentation
- **Tasks**: Amend `docs/GitHub_Classroom_Autograding_Integration_Guide__Us.md` and, if needed, `docs/exercise-testing.md` to describe the plugin, CLI, workflow, and scoring; mention notebook directory requirements.
- **Success Criteria**: Documentation reviewed for clarity and consistency; references to old process removed or updated.

## 9. End-to-End Verification
- **Tasks**: Run full test suite with plugin enabled; execute CLI end-to-end; simulate workflow outputs; confirm Base64 payload compatibility with `autograding-grading-reporter` locally if possible.
- **Success Criteria**: All tests green, payload accepted by reporter, and manual inspection validates per-test feedback integrity.

## 10. Deployment Prep
- **Tasks**: Summarise changes, note testing performed, and prepare for PR review including checklist updates.
- **Success Criteria**: Ready-to-submit PR description referencing implemented features, tests run, and documentation updates.
