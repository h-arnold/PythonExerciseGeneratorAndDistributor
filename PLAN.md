# Plan: Fix missing devcontainer in construct template repos

## Branch
`fix/missingDevContainerConfig` (already checked out; working tree clean)

## Root cause
`scripts/sync_construct_template_repos.py` builds each per‑construct repo with its own
`build_construct_workspace()`, which copies **only** exercise files + `additional-resources`
and never the base template assets:
- `.devcontainer/`
- `.github/workflows/classroom.yml`
- `pyproject.toml`, `pytest.ini`, `.gitignore`
- `scripts/build_autograde_payload.py`
- `tests/` (required files + `exercise_framework/`)
- `exercise_metadata/`, `exercise_runtime_support/`

`repoman create`/`update` already produce all of these correctly (confirmed working via
`repoman update --construct selection`). The `template_repo_cli` `create`/`update` path is
**not** affected — `copy_template_base_files()` already calls
`_copy_directory(".devcontainer", …)` at `scripts/template_repo_cli/core/packager/__init__.py:259`.
The existing sync tests never asserted base files, so the gap was invisible.

## Approach
Make the sync script a thin orchestrator that delegates package construction **and** push to
`repoman` via subprocess. This decouples the two tools so changes to either don't affect the
other.

## Changes to `scripts/sync_construct_template_repos.py`

### 1. `gh` auth pre‑check (new helper `_check_gh_auth()`)
- Run `gh auth status` via `subprocess.run(..., capture_output=True, text=True)`.
- On non‑zero exit, print a clear message:
  *"Not authenticated with GitHub. Run `gh auth login` (and `gh auth refresh -s repo` for the
  required scopes) first."* and return `False`.
- Call it in `main()` before the sync loop. Abort with exit code 1 if not authed (still be
  informative under `--dry-run`).

### 2. `repoman` wrapper (new `_sync_via_repoman(construct, *, dry_run, verbose, org=None)`)
- Build the command as a list (avoid shell; use the module form so it works without the
  `repoman` binary installed):
  ```
  [sys.executable, "-m", "scripts.template_repo_cli", "update",
   "--repo-name", f"python-exercises-{construct}",
   "--construct", construct]
  ```
  Append `--dry-run`, `--verbose`, and `--org <org>` when applicable.
- **Critical:** run with `cwd=repo_root` (repoman resolves its root via `Path.cwd()`),
  `capture_output=True, text=True`.
- Print repoman's combined stdout/stderr so the user sees progress.
- If exit code != 0 **and** output contains *"Run the create command first"* (repo missing)
  → run the **same** command with `"create"` instead; on success return success.
- Otherwise bubble up the failure. Scan output for auth keywords (`Not authenticated`,
  `gh auth`, `401`, `403`) and, if present, append a clear auth hint to the recorded error.
- Under `--dry-run`, only attempt `update --dry-run` (no `create` fallback).

### 3. Rewrite `_process_single_construct(...)`
- Replace the `build_construct_workspace(...)` + `sync_construct(...)` calls with a call to
  `_sync_via_repoman(...)`.
- Preserve the existing `errors` list aggregation and the `finally: shutil.rmtree(workspace)`
  cleanup. The temp workspace is no longer needed by the build (repoman manages its own), but
  the minimal temp dir / cleanup can be dropped or kept for safety — confirm during
  implementation; prefer dropping it since repoman manages its own workspace.

### 4. Dead‑code removal (full cleanup)
Remove:
- `build_construct_workspace`
- `_ignore_pycache`
- `_copy_exercise_files`
- `_copy_notebooks`
- `sync_construct`
- `_init_and_push`
- `SyncResult` (TypedDict)

Keep (still used by docs/main):
- `discover_constructs`
- `_get_authenticated_owner` (used by `generate_docs_page` + `main`)
- `_construct_repo_name` (used by `generate_docs_page`)
- `generate_docs_page`, `write_docs_page`
- `parse_args`, `main`

Optional: add a `--org` CLI flag and forward it to the `repoman` calls if construct repos
should live under an organization.

## Test changes — `tests/test_sync_construct_template_repos.py`

### Remove
- `TestBuildConstructWorkspace` (7 tests) — targets removed `build_construct_workspace`.
- `TestSyncConstruct` (8 tests) — asserts direct `gh` calls that no longer happen.

### Add — new suite `TestSyncViaRepoman` (mock `subprocess.run`)
- update succeeds → asserts `repoman … update …` is invoked with correct args; success recorded.
- update fails with "repo does not exist" → asserts `create` is attempted next and success
  recorded.
- update fails for other reasons (e.g. auth) → asserts `create` is **not** attempted; error
  bubbled.
- auth pre‑check failure path is reported/aborts appropriately.
- `--dry-run` invokes only `update --dry-run` (no `create` fallback).
- devcontainer coverage: since `repoman` already produces `.devcontainer` (covered by
  `template_repo_cli` tests), here assert the wrapper invokes `repoman` with
  `--construct {construct}` and `--repo-name python-exercises-{construct}`; optionally assert the
  command list would target the canonical layout.

### Keep
- `TestDiscoverConstructs`
- `TestGenerateDocsPage`
- `TestMainCLI` (adjust only if the auth pre‑check changes `--dry-run` behavior)

## Verification
- `uv run pytest tests/test_sync_construct_template_repos.py tests/template_repo_cli/ -q`
- `ruff check . --fix`
- `uv run python scripts/sync_construct_template_repos.py --dry-run --verbose`
  (writes only the docs page; no repo changes)

## Expected outcome
Per‑construct repos (`python-exercises-<construct>`) now contain the canonical
`exercises/<construct>/<exercise_key>/` layout **plus** `.devcontainer/`, the Classroom
`classroom.yml` workflow, `pyproject.toml`, and the full grading runtime — fixing the missing
devcontainer regression, while keeping `repoman` and the sync script fully decoupled.
