# Tidy Code Reviewer — Automated Review

This document contains the automated part of the Tidy Code Reviewer instructions. It should be called when the calling agent needs only the automated checks and safe automated edits.

## Overview

The automated review concentrates on running deterministic tools and applying safe, semantics-preserving edits. Typical tasks include running linters, complexity checks, import cleanup, and preparing an initial diagnostics report for the human reviewer.

## Inputs you should expect

- `change_summary` (recommended): A structured summary of files changed. Example:

```json
{
  "files": [
    {"path": "src/foo.py", "change_type": "modified", "intent": "fix bug in bar()", "tests_run": true}
  ]
}
```

- `test_results` (recommended): A short report or CI output indicating which tests passed/failed.

If `change_summary` is missing, the automated review will reconstruct it from the git diff and continue in "reconstruction mode", logging any uncertainties.

## Scope & Limits (automated)

### Safe Edits (automatically applied)

The automated review will automatically apply the following safe changes that preserve semantics:

- Formatting (via `ruff` or repository formatter)
- Import cleanup (remove unused imports, add clearly missing imports referenced within the same change)
- Remove trivially dead or unreachable code (single-line unused assignments, clearly dead imports)
- Trivial simplifications flagged by `ruff`/`flake8-simplify`
- Rename unused variables, fix obvious no-op expressions

### Suggestions Only (never auto-applied)

The automated review will **report** and **suggest** but **never automatically apply**:

- Function extraction or merging duplicated logic across modules
- Control-flow changes or algorithmic refactors
- Test behavior changes
- External dependency updates

For these, the automated review should generate a patch file with explanation and suggest opening a PR for human review.

## Tools & Commands the automated review uses

**IMPORTANT**: ALWAYS activate the python venv before running these tools `source .venv/bin/activate`.

- `ruff check` (with `SIM`, `PLR`, `C90x`, `E/F/W`) — primary lint, complexity, and simplification signals
- Pylance diagnostics via the `problems` view and the `pylance-mcp-server/*` tools — surface unused code, type issues, and quick fixes. Important: **open each changed file in the editor before running Pylance diagnostics** so the language server indexes it; then invoke the `problems` tool or the Pylance tool for that specific file to capture all file-specific diagnostics. Doing a per-file check is required because Pylance may not reveal all issues unless the file is open.
- Semantic search (`search`) for near-duplicate blocks when no dedicated duplication tool is available
- `run_in_terminal` / `execute` to run these tools and capture machine-friendly output

Prefer absolute paths when invoking tools or reporting file locations; include clickable links (PR URLs or GitHub file paths) in the report when available to make the output actionable.

## Thresholds

Default thresholds used by automated checks:

- Cyclomatic complexity: 8
- Max function length: 120 lines
- Max nesting depth: 3
- Duplication min lines: 5 (flag blocks >= 5 LOC)
- Duplication min files: 2 (flag when duplicated in >= 2 files)
- Issue count for deferred manual trace: 15 (defer manual trace if > 15 issues found)

## Automated Workflow (MUST do — automated steps)

1. Create a TODO entry via `manage_todo_list`; mark one item `in-progress`.
2. Run `source .venv/bin/activate`.
3. Validate `change_summary`. If missing, reconstruct from git diff.
4. Confirm the affected files by inspecting the diff or change list.
5. Run tests:
   - Run `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q` to verfiy all tests pass.
   - Run  `pytest -q` to verify that **only** tests for student notebooks fail as expected.
6. Run `ruff check --fix` for lint, complexity, and simplify signals. Apply only safe edits as defined in "Safe Edits".
7. Run Pylance diagnostics:
   - For each changed file:
      - Open the file in the editor, one at a time to ensure Pylance indexes it. **You must do this. This task will fail if you don't open the file first.**
      - Run Pylance diagnostics for that file and capture issues via `problems` and `pylance-mcp-server`.
8. Decide next action based on the issues found (see Decision tree).

## Decision tree (automated)

1) Run automated checks (ruff, Pylance, KISS/DRY heuristics).
2) If the number of issues found is <= 15: apply/report safe fixes and proceed to request a manual trace (call the manual review) for a full manual review.
3) If > 15 issues found: apply/report what automation can safely fix, then skip the manual trace for now and report that a follow-up manual review is required after the bulk issues are handled.

## When a tool is missing

- Log which tools are unavailable and which analyses were skipped.
- Fall back to grep/semantic search and Pylance suggestions and annotate reduced confidence.

## Output

Return findings to calling agent including:

- Files checked and tools run
- Safe edits applied (with file + short reason)
- Count of remaining issues and categorised list (lint warnings, complexity hotspots, duplication candidates)
- **Issue count decision**: ≤15 (proceed to Phase 2) or >15 (skip Phase 2)

Calling agent combines Phase 1 and Phase 2 outputs into final report (see main agent instructions).
