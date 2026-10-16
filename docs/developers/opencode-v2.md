# OpenCode V2 Repository Guidance

This document records the repository's OpenCode V2 usage contract. The root
[`AGENTS.md`](../../AGENTS.md) contains general project and coding guidance.

## Agent IDs and invocation

The IDs passed to the V2 `subagent` tool are derived from
`.opencode/agents/<id>.md`; they are not the displayed agent names. Callable
subagents in this repository are:

`explore`, `implementer`, `tidy-code-reviewer`, `docs`, `planner-reviewer`,
`planner`, `testing-specialist`, `de-sloppifier`, `exercise-generation`,
`exercise-reviewer`, `exercise-test-creator`, and `exercise-test-reviewer`.

`agent-orchestrator` is configured for primary use, not subagent mode. Select
it as the session's primary agent rather than invoking it through `subagent`.
Agents configured with `mode: subagent` or `mode: all` can be launched through
that tool; for example, `planner` uses `mode: all`.

## Definitions and compatibility

The repository's `.opencode/agents/` and `.opencode/skills/` Markdown
definitions remain supported in V2. V2 discovers skills from
`.opencode/skills/<skill-id>/SKILL.md`; supporting paths referenced by a skill
are relative to the directory containing its `SKILL.md`. Existing skill
frontmatter and Markdown instructions do not require a format rewrite.

Keep repository-wide persistent instructions in root `AGENTS.md`. Use the
native V2 tool names when describing execution: for example, `subagent` for
delegation and `skill` for loading a skill. Do not confuse an agent's display
label with its path-derived ID.

## Native configuration and tool contract

New agent Markdown frontmatter uses V2's ordered `permissions` array, with
`action`, `resource`, and `effect` fields. Quote wildcard resources so YAML
parses them as strings:

```yaml
permissions:
  - action: shell
    resource: "*"
    effect: ask
  - action: subagent
    resource: implementer
    effect: allow
```

Use native tool names in new guidance: V1 `read_file` is `read`, `bash` is
`shell`, `task` is `subagent`, and `apply_patch` is `patch`. Patch availability
depends on the model; when it is not exposed, use the available `edit` and
`write` tools. Existing ordinary `bash` command examples are shell commands,
not tool-name declarations, and do not need rewriting.

V2 has no dedicated todo tool and does not provide LSP diagnostics. Track plans
in Markdown and use the project's lint, type-check, or compiler commands for
diagnostics. Tools available only through `execute` must be called using the
exact names and signatures in its advertised catalog; do not invent fixed
namespaces or tool interfaces.

> **📖 Official references:** [V1-to-V2 migration](https://opencode.ai/v2/docs/migrate-v1), [Tools](https://opencode.ai/v2/docs/tools), [Agents](https://opencode.ai/v2/docs/agents), [Skills](https://opencode.ai/v2/docs/skills), and [Instructions](https://opencode.ai/v2/docs/instructions).

## Configuration and dependency audit

The following is a **2026-10-16 snapshot of this migration's devcontainer**,
not a requirement for other contributors' global settings or local packages.

The repository has no active project OpenCode config, plugin implementation,
MCP server declaration, custom tool, or server API integration to migrate.
The active global `opencode.jsonc` contains only the published schema declaration;
the global `cli.json` uses the V2 CLI schema and documented settings.

Ignored `.opencode/package.json`, lockfile, `node_modules`, and global OpenCode
package directories contain unused `@opencode-ai/plugin` and SDK packages, but
no plugin source or imports consume them. They are harmless ignored artifacts,
not migration inputs or dependencies that need V2 replacements. Do not add a
replacement dependency or remove these local artifacts absent a consumer or an
explicit cleanup request.
