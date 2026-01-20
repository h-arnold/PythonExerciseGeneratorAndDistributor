# Tidy Code Reviewer — KISS & DRY checks

This document describes the behaviour and configuration of the Tidy Code Reviewer agent with the newly added KISS (simplicity) and DRY (duplication) checks.

## Overview

The agent runs as a post-change reviewer and performs:

- Linting & small safe cleanups (via `ruff` / repo linter)
- KISS checks (complexity, maintainability, length, nesting)
- DRY checks (duplication detection via `jscpd` or semantic search)

The agent is review-first and only applies automated edits when explicitly allowed (see `agent-config.yml` `allow_auto_edit`).

**Inputs**: The calling agent should provide a structured `change_summary` (required) describing files changed, the intent, and whether tests were run. Example snippet:

```json
{"files": [{"path": "src/foo.py", "change_type": "modified", "intent": "fix bug in bar()", "tests_run": true}]}
```

Suggested refactors that may affect runtime behaviour are produced as patches or PR drafts for manual review.

## Configuration

Default config lives at `.github/agents/tidy_agent_config.yml`.
Adjust thresholds, ignore patterns and the `allow_auto_edit` toggle there. Example `agent-config.yml`:

```yaml
allow_auto_edit: false # default - review-only
cyclomatic_complexity: 8
max_function_length: 120
ignore_globs:
  - "**/notebooks/**"
  - "**/templates/**"
```

If you require the agent to perform automated safe edits, set `allow_auto_edit: true` **and** provide per-file consent in `change_summary`.

## Running the checks locally (developer guidance)

- Install required tools: run `uv sync` (radon/ruff are part of the dev dependencies) and install the Node-based `jscpd` binary (`npm install -g jscpd` or use `npx jscpd ...`)
- Run complexity checks: `radon cc -s -n <threshold> <path>`
- Run duplication: `jscpd --min-lines 5 --reporters json <path>`

## Example workflow

1. The agent validates `change_summary` and enters *reconstruction mode* if missing information is detected.
2. MUST: run lint checks (`ruff`) and collect diagnostics. If `allow_auto_edit` is enabled and per-file consent exists, apply only safe edits.
3. MUST: collect basic KISS signals (AST heuristics) and optionally run `radon cc/mi` when available.
4. OPTIONAL: run duplication checks (`jscpd`) and Sonar scans if configured.
5. Produce both a machine-readable JSON (KISS/DRY) and a short human-readable markdown summary (see below).
6. Exit criteria: TODO completed, report delivered, trivial fixes applied (if enabled), and any high-risk changes accompanied by a patch/PR.

### Human report guidance

Keep the human report concise (<300 words) and include: verification list, edits made (with links), KISS/DRY highlights, lint/tests summary, doc updates, and attachments or PR links for patches.

## Tuning

- Lower the `cyclomatic_complexity` value to be more strict, or increase to avoid noise.
- Add repository-specific ignores to `ignore_globs` for generated files or test fixtures.
