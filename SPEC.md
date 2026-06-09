# SPEC: CI Workflow + Docs for Construct Template Repos

## Goal and Intended Outcome

Create a GitHub Actions workflow and supporting Python script that:

1. On PR, **builds and validates** template packages for every programming construct in the source repo, uploading artifacts for inspection.
2. On push to `main`, **publishes** the template packages to corresponding GitHub template repos (one per construct) and **commits** an auto-generated teacher-facing docs page back to the source repo.
3. On `workflow_dispatch`, allows **manual publish** with an optional dry-run flag.

The teacher docs page at `docs/teachers/construct-template-repos.md` will list every construct with a link to its template repo, exercise count, and last-synced timestamp.

## Current State

- Only the `sequence` construct exists under `exercises/sequence/` with 14 exercises.
- A template repo already exists at `h-arnold/python-exercises-sequence`.
- The `repoman` CLI (`scripts/template_repo_cli/`) has mature `create`, `update`, `list`, and `validate` commands.
- Existing CI workflows: `.github/workflows/tests.yml` (push/PR), `.github/workflows/tests-solutions.yml` (manual).
- Teacher docs live in `docs/teachers/` (getting-started, understanding-the-tools, creating-and-editing-exercises, how-to-use-the-template-repo-cli, etc.).
- No CI workflow or script exists to iterate over all constructs automatically.
- No docs page links to construct-specific template repos.

## Scope

### In scope

- **New script**: `scripts/sync_construct_template_repos.py` — discovers all constructs, builds template packages, creates/updates GitHub repos, generates docs page.
- **New CI workflow**: `.github/workflows/sync-template-repos.yml` — drives the script on PR/push/manual triggers.
- **New docs page**: `docs/teachers/construct-template-repos.md` — auto-generated, committed back by CI.

### Non-goals

- Non-construct template repos (type-specific, exercise-key-specific) — remain a manual `repoman` operation.
- Publishing to GitHub Classroom directly — that's a separate step.
- Migration of existing template repos — script handles both create and update paths.
- Modifications to existing `repoman` internals — pure reuse via imports.

## Constraints and Invariants

- Target org configured via `TEMPLATE_REPO_ORG` environment variable (default: `h-arnold`). This makes the repo forkable — anyone can fork and set their own org. Template repo naming: `python-exercises-{construct}`.
- Must use existing `repoman` internals without modifying them.
- Must follow repository conventions: `snake_case`, type hints, TypedDicts, docstrings, Fail Fast, Ruff-compliant.
- Auth in CI: `GH_TOKEN` environment variable set from `secrets.PAT_FOR_TEMPLATE_REPOS` in the workflow. The `gh` CLI and git credential helpers both recognise `GH_TOKEN`, so `GitHubClient.push_to_existing_repository()` works without extra auth steps.
- The default `GITHUB_TOKEN` provided by GitHub Actions is scoped to the current repository only and **cannot** create or push to other repos. A PAT with `repo` scope (`PAT_FOR_TEMPLATE_REPOS` secret) is required for cross-repo operations.
- PR trigger runs full build + docs gen but does **not** push to template repos. Uploads artifact for inspection.
- Docs page auto-committed when publishing (push to main or workflow_dispatch), **not** on PR. The commit-back is handled by the CI workflow (git add/commit/push steps), not by the Python script — the script only writes the file to a configurable path.
- Continue on error: if `sync_construct()` fails for one construct, the script logs the error and continues to the next. Exits non-zero if any construct failed.
- Docs page timestamp uses `datetime.now()` local time. The generated date reflects when the script ran, not the remote repo's last push time.

## Relevant Docs and File Evidence

- `scripts/template_repo_cli/` — full CLI implementation with `core/` (selector, collector, packager, github) and `utils/`
- `exercise_metadata/registry.py` — `build_exercise_registry()` to discover all constructs
- `template_repo_files/` — base template files copied into each template repo
- `.github/workflows/tests.yml` — existing CI pattern (uv, astral-sh/setup-uv)
- `docs/teachers/how-to-use-the-template-repo-cli.md` — existing teacher CLI guide
- `docs/teachers/creating-and-editing-exercises.md` — exercise authoring guide

## Acceptance Criteria

1. **`uv run pytest tests/test_sync_construct_template_repos.py -q`** passes with ~32 tests.
2. **`uv run python scripts/sync_construct_template_repos.py --dry-run --verbose`** successfully builds and validates the sequence construct workspace.
3. **PR opens** → CI runs, builds all constructs, uploads artifact, **no pushes** to template repos.
4. **PR merges to main** → CI publishes to `python-exercises-sequence`, commits updated `docs/teachers/construct-template-repos.md`.
5. **`docs/teachers/construct-template-repos.md`** contains a table with "Sequence" linking to `h-arnold/python-exercises-sequence`, exercise count, and last-synced date.

## Open Questions and Risks

- **Risk**: `PAT_FOR_TEMPLATE_REPOS` secret must be created in the repo settings before the workflow can publish. Until then, only dry-run works.
- **Risk**: The default `GITHUB_TOKEN` cannot push to external repos. If `PAT_FOR_TEMPLATE_REPOS` is not set, CI will fail with auth errors on publish.
- **Decision**: Script continues on per-construct error, reports all, exits non-zero at end.
- **Decision**: Docs page committed by CI workflow (not the Python script). Script writes to `--docs-output-path`; workflow conditionally commits on publish events.
- **Decision**: CI auth via `GH_TOKEN` env var from `secrets.PAT_FOR_TEMPLATE_REPOS`.
- **Decision**: Target org read from `TEMPLATE_REPO_ORG` environment variable (default `h-arnold`), not a CLI flag — makes repo forkable.
- **Decision**: Docs page timestamp uses `datetime.now()` local time at script runtime.
