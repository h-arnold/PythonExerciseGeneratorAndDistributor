# SLOP Review

## Summary
Needs Improvement. The `template_repo_cli` package is functional, but it still carries confirmed dead/test-only helpers and duplicated selection/auth logic that will keep drifting unless it is collapsed.

## Critical
- Location: [scripts/template_repo_cli/utils/config.py](scripts/template_repo_cli/utils/config.py#L1). Evidence: the module defines `TemplateRepoConfig`, `default_config_path()`, `load_config()`, and `save_config()`, but code search finds no runtime callers outside the module itself. Why it matters: this is dead configuration plumbing with no live consumer, so every change here is maintenance cost without any package behavior behind it. Recommended simplification: delete the module and its tests, or reintroduce it only when a real CLI command needs persisted config.

- Location: [scripts/template_repo_cli/utils/filesystem.py](scripts/template_repo_cli/utils/filesystem.py#L57) and [scripts/template_repo_cli/utils/filesystem.py](scripts/template_repo_cli/utils/filesystem.py#L83). Evidence: `resolve_notebook_path()` and `create_directory_structure()` are only referenced from [tests/template_repo_cli/test_filesystem.py](tests/template_repo_cli/test_filesystem.py), not from the CLI or packager runtime. Why it matters: these helpers look like production API, but they are really test fixtures living in the shipped package namespace. Recommended simplification: move them into a test helper module or delete them if no runtime caller is expected.

## Improvement
- Location: [scripts/template_repo_cli/cli.py](scripts/template_repo_cli/cli.py#L62) and [scripts/template_repo_cli/cli.py](scripts/template_repo_cli/cli.py#L833). Evidence: `_select_exercises()` and `_select_exercises_for_validation()` are the same branch structure with the same error text; the only difference is which caller wraps the exception message. Why it matters: the selection contract is duplicated in two places, so any future change to exercise-key, construct, or type handling has to be updated twice. Recommended simplification: keep one selection helper and let the caller add a command-specific prefix when printing failures.

- Location: [scripts/template_repo_cli/cli.py](scripts/template_repo_cli/cli.py#L124), [scripts/template_repo_cli/cli.py](scripts/template_repo_cli/cli.py#L153), [scripts/template_repo_cli/cli.py](scripts/template_repo_cli/cli.py#L269), and [scripts/template_repo_cli/core/github.py](scripts/template_repo_cli/core/github.py#L728). Evidence: the CLI classifies `resource not accessible by integration` / `createRepository` errors in `_github_permission_hint()`, `_is_integration_permission_error()`, and `_should_retry_with_reauth()`, while `GitHubClient` independently keeps the same retry classification in `_should_retry_with_fresh_auth()`. Why it matters: the same GitHub auth failure is interpreted in two layers, so any wording or marker change can desynchronize the retry path and the user-facing hint. Recommended simplification: centralize the auth-error classifier in one place and have both layers consume it.

- Location: [scripts/template_repo_cli/core/github.py](scripts/template_repo_cli/core/github.py#L104), [scripts/template_repo_cli/core/github.py](scripts/template_repo_cli/core/github.py#L277), and [scripts/template_repo_cli/core/github.py](scripts/template_repo_cli/core/github.py#L377). Evidence: `is_command_sequence()`, `check_authentication()`, and `parse_json_output()` are only referenced by tests; no runtime path in `scripts/template_repo_cli` uses them. Why it matters: these helpers expand the GitHub client API surface without helping the CLI flow, which makes the module look more public and stable than it really is. Recommended simplification: move test-only helpers into the test tree or make them private if they are not intended for runtime use.

## Nitpick
- None identified beyond the items above.

## Validation
- `uv run pytest tests/template_repo_cli -q` ran against the current tree and failed in an existing integration test: `tests/template_repo_cli/test_integration.py::TestEndToEndDryRun::test_dry_run_workspace_subset_framework_api_rejects_excluded_notebook_early` expects `Unknown notebook ...`, but the current code reports `Unknown exercise key ...`.
- I did not change any production code for this review; the output above is a findings-only slop audit.
