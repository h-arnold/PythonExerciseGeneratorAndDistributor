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
- Trivial simplifications flagged by `ruff`
- Rename unused variables, fix obvious no-op expressions
- Adding or fixing type hints flagged up by `pyright`.

### Suggestions Only (never auto-applied)

The automated review will **report** and **suggest** but **never automatically apply**:

- Function extraction or merging duplicated logic across modules
- Control-flow changes or algorithmic refactors
- Test behavior changes
- External dependency updates

For these, the automated review should generate a patch file with explanation and suggest opening a PR for human review.

## Tools & Commands the automated review uses

**IMPORTANT**: This repository uses a uv-managed virtual environment. Run `uv sync` when dependencies change and execute commands via `uv run ...` (or activate the `.venv` created by uv with `source .venv/bin/activate`) before running diagnostics. Skipping this step leads to missing tooling.

- `uv run ruff check` (with `SIM`, `PLR`, `C90x`, `E/F/W`) — primary lint, complexity, and simplification signals
- `uv run --with pyright pyright [paths...]` — typing diagnostics. Run against the affected files (or the repo root when surface area is large) so pyright reports new issues.
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
2. Ensure the uv-managed environment is active. Run `uv sync` if dependencies changed, then either execute commands with `uv run ...` or activate the `.venv` created by uv via `source .venv/bin/activate`. **Do not run tools outside this environment.**
3. Validate `change_summary`. If missing, reconstruct from git diff.
4. Confirm the affected files by inspecting the diff or change list.
5. Run tests:
   - Set `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions` and run `uv run pytest -q` to verify the solution notebooks pass.
   - Only run `uv run pytest -q` without the environment variable when you need to inspect student notebooks; confirm any failures are the expected pre-solution failures, not regressions.
6. Run `uv run ruff check --fix` for lint, complexity, and simplify signals. Apply only safe edits as defined in "Safe Edits".
7. Run `uv run ruff format` to apply formatting fixes.
8. Run Pyright diagnostics:
   - Execute `uv run --with pyright pyright [paths...]`, supplying the changed files or `.` when many files were touched.
   - Capture the typing issues reported and include them in the automated report so the manual reviewer can triage any remaining errors.
9. Check the total line length of files changed. If over 500 lines, suggest splitting into smaller modules when sensible.
10. Decide next action based on the issues found (see Decision tree).

## Decision tree (automated)

1) Run automated checks (ruff, Pyright, KISS/DRY heuristics).
2) If the number of issues found is <= 15: apply/report safe fixes and proceed to request a manual trace (call the manual review) for a full manual review.
3) If > 15 issues found: apply/report what automation can safely fix, then skip the manual trace for now and report that a follow-up manual review is required after the bulk issues are handled.

## When a tool is missing

- Log which tools are unavailable and which analyses were skipped.
- Fall back to grep/semantic search and any outstanding Pyright hints and annotate reduced confidence.

## Output

Return findings to calling agent including:

- Files checked and tools run
- Safe edits applied (with file + short reason)
- Count of remaining issues and categorised list (lint warnings, complexity hotspots, duplication candidates)
- **Issue count decision**: ≤15 (proceed to Phase 2) or >15 (skip Phase 2)

Calling agent combines Phase 1 and Phase 2 outputs into final report (see main agent instructions).
