# Autograding CLI

This guide explains how to use `scripts/build_autograde_payload.py` to generate GitHub Classroom compatible payloads from the local pytest suite.

## Purpose

The CLI wraps pytest so every run produces:

- a structured JSON results file emitted by `tests/autograde_plugin.py`
- a Base64-encoded payload consumable by `autograding-grading-reporter`
- optional human-readable summaries and GitHub Actions outputs

Using the wrapper keeps local and CI executions aligned with the Classroom workflow.

## Arguments

`build_autograde_payload.py` accepts the following parameters:

- `--pytest-args`: forward one or more pytest arguments. Repeat the flag for multiple options (e.g. `--pytest-args=-k --pytest-args=test_ex001_sanity`). Defaults to `-q` when omitted.
- `--results-json`: path for the raw plugin output. Default `tmp/autograde/results.json`.
- `--output`: path for the Base64 payload text file. Default `tmp/autograde/payload.txt`.
- `--summary`: optional path for a plain JSON dump of the payload before encoding. Useful for debugging (no file is written unless you supply this flag).
- `--minimal`: strip verbose fields (stdout/stderr/log/extra/nodeid/duration) from the payload to reduce size. Essential for GitHub Classroom workflows to avoid environment variable size limits. Error messages are truncated to 200 characters.

All paths are created on demand. The script exits non-zero if pytest fails or if the payload cannot be produced.

## Usage Examples

### Local iteration against the solutions set

```bash
PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions \
uv run python scripts/build_autograde_payload.py \
  --pytest-args=tests/test_ex001_sanity.py
```

### Focused subset using keyword expression

```bash
uv run python scripts/build_autograde_payload.py --pytest-args=-k --pytest-args=exercise1
```

### GitHub Actions step (classroom workflow excerpt)

```yaml
- name: Build autograde payload
  run: |
    uv run python scripts/build_autograde_payload.py \
      --pytest-args="-p tests.autograde_plugin" \
      --output=tmp/autograde/payload.txt \
      --summary=tmp/autograde/payload.json \
      --minimal
```

The `--minimal` flag is required in GitHub Actions to ensure the Base64 payload fits within environment variable size limits (typically 32KB). This strips verbose output fields while preserving test names, statuses, scores, and truncated error messages that students need to see.

## Outputs

- **Results JSON** (`--results-json`): direct dump from the pytest plugin showing every test, score, and failure message. Inspect this when debugging collection issues. Always contains full verbose output regardless of `--minimal` flag.
- **Payload file** (`--output`): Base64 text containing the structure required by Classroom. Feed this to `autograding-grading-reporter`. Use `--minimal` in CI to reduce size.
- **Summary JSON** (`--summary`): optional, mirrors the decoded payload for quick inspection without manual Base64 decoding. Contains full payload when `--minimal` is not used, or minimal payload when flag is set.
- **GitHub outputs**: when `GITHUB_OUTPUT` is set, the CLI appends the encoded payload plus overall score metrics so downstream workflow steps can pass them to the reporter.

## Interpreting the Printed Summary

After pytest completes the CLI prints a task-level table. Keep in mind:

- Scores are expressed as `earned/available` per task number; unmarked tests appear under `Ungrouped`.
- The percentage reflects total earned points versus `max_score` in the payload.
- Failures list the truncated assertion messages the student will see; review them to ensure they are concise and actionable.

If the summary omits expected tests, rerun with `--summary` and confirm that pytest collected the file you anticipated. Missing task numbers usually indicate a forgotten `@pytest.mark.task(taskno=...)` decorator.
