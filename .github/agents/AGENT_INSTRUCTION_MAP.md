# Agent Instruction Map

This map compares the agent instruction files in this repository (`PythonExerciseGeneratorAndDistributor`) with the agent set in the remote AssessmentBot branch `feat/ReactFrontend`.

Definitions:

- **Generic**: reusable instruction structure that should transfer cleanly to another repository after swapping repository names, file paths, and tooling references.
- **Repository-specific**: instructions tied to a particular repo layout, docs tree, commands, validation stack, or module architecture.

## At a Glance

| Local file | Remote counterpart | Notes |
|---|---|---|
| `de-sloppifier.agent.md` | `de-sloppification.agent.md` | Same role, same review shape, different repo assumptions. |
| `docs.agent.md` | `docs.agent.md` | Same role name, but the remote version is more explicit about frontend policy and Codex parity. |
| `implementer.md.agent.md` | `implementation.agent.md` | Both are implementation agents; the validation stack and module model differ. |
| `tidy_code_review.md.agent.md` | `code-reviewer.agent.md` | Same review intent, but the remote version is broader and module-aware. |
| `exercise_generation.md.agent.md` | none | Excluded from this map per request. |
| `exercise_verifier.md.agent.md` | none | Excluded from this map per request. |
| none | `agent-orchestrator.agent.md` | Remote-only planning/orchestration agent. |
| none | `planner.agent.md` | Remote-only planning agent. |
| none | `planner-reviewer.agent.md` | Remote-only planning review agent. |
| none | `Testing.agent.md` | Remote-only test-specialist agent. |

## Reusable Instruction Skeleton

Across both repositories, the same core lifecycle repeats:

- read relevant context before acting
- establish scope before editing or reviewing
- validate the touched area with the repository’s preferred checks
- report back with concise, evidence-backed output
- avoid speculative scope expansion
- keep changes local to the request

That skeleton is the part that is most portable between agent files. The sections below separate that portable structure from the repository-specific content.

## Local File Map

### `de-sloppifier.agent.md`

Remote counterpart: [`de-sloppification.agent.md`](https://github.com/h-arnold/AssessmentBot/blob/feat/ReactFrontend/.github/agents/de-sloppification.agent.md)

**Generic sections**

- `0. Mandatory First Step`
- `1. What Counts As Slop`
- `2. Slop-Hunting Workflow`
- `3. Evidence Rules`
- `4. Cleanup Rules`
- `5. Validation Expectations`
- `6. Reporting Format`
- `7. Completion`

**Repository-specific sections**

- Local repo identity: `PythonExerciseGeneratorAndDistributor`
- Canonical exercise-local layout under `exercises/<construct>/<exercise_key>/`
- `uv`-managed Python environment and `uv sync`
- Exercise notebooks, tagged-cell grading, and pytest variant commands
- Repo docs under `docs/` that are specific to the exercise generator/distributor workflow

**Sync note**

- The remote file keeps the same workflow but swaps in AssessmentBot-specific policy docs, component agent references, and frontend/runtime caveats.

### `docs.agent.md`

Remote counterpart: [`docs.agent.md`](https://github.com/h-arnold/AssessmentBot/blob/feat/ReactFrontend/.github/agents/docs.agent.md)

**Generic sections**

- `0. Mandatory First Step`
- `1. Primary Responsibilities`
- `2. Documentation Decision Rules`
- `3. AGENTS and Component-Doc Update Rules`
- `4. JSDoc Quality Checklist`
- `5. Validation Workflow`
- `6. Reporting Back to Orchestrator`
- `7. Guardrails`

**Repository-specific sections**

- Local docs scope: project docs under `docs/` and exercise-specific README/OVERVIEW files
- Local agent guidance: `.github/agents` is the source of truth for repo-specific agent behaviour
- Local repo identity: `PythonExerciseGeneratorAndDistributor`
- Absence of remote-style Codex mirror rules and frontend-specific canonical policy references

**Sync note**

- The remote version is more explicit about `docs/developer/`, frontend layout policy, `src/frontend/AGENTS.md`, and `.codex/agents/*.toml` parity.

### `implementer.md.agent.md`

Remote counterpart: [`implementation.agent.md`](https://github.com/h-arnold/AssessmentBot/blob/feat/ReactFrontend/.github/agents/implementation.agent.md)

**Generic sections**

- `1. Input & Context`
- `2. Workflow`
- `3. Project Coding Standards`
- `4. Testing`
- `5. Decision Tree for Blockers`
- `6. Output Format`
- `7. The Golden Rule`

**Repository-specific sections**

- `uv`-managed Python environment and `source .venv/bin/activate`
- Python 3.11+ typing and docstring expectations
- Notebook authoring rules, including the preference not to edit `.ipynb` directly unless explicitly tasked
- `pytest`, `ruff`, and exercise-variant validation commands
- Exercise-local canonical layout and repository-side test locations

**Sync note**

- The remote version is aligned to AssessmentBot’s backend/frontend/builder split and uses `npm`, Playwright, and builder-specific checks instead of the Python exercise workflow.

### `tidy_code_review.md.agent.md`

Remote counterpart: [`code-reviewer.agent.md`](https://github.com/h-arnold/AssessmentBot/blob/feat/ReactFrontend/.github/agents/code-reviewer.agent.md)

**Generic sections**

- `Phase 1: Automated Review`
- `Phase 2: Manual Review`
- `Phase 3: Final Report & Close`
- `Decision tree`
- `Exit criteria`
- `Output to calling agent`

**Repository-specific sections**

- Local review automation files under `docs/agents/tidy_code_review/`
- Local repo conventions for ignoring notebooks and generated directories
- `source .venv/bin/activate` and the repo’s Python-focused validation path
- Local TODO tracking and the repo-specific problem/diagnostic workflow

**Sync note**

- The remote reviewer is broader: it covers backend, frontend, and builder review standards, module-specific lint/test commands, and security/diagnostic tooling.

## Remote-Only Files

### `agent-orchestrator.agent.md`

**Generic sections**

- `1. Start-Up`
- `2. Mandatory Section Loop`
- `3. Section Exit Criteria`
- `4. Action Plan Updates`
- `5. Commit and Push Rules`
- `6. Mandatory De-Sloppification Pass`
- `7. Final Documentation Pass`
- `8. Guardrails`
- `9. Final Output`

**Repository-specific sections**

- `ACTION_PLAN.md` as the orchestration contract
- Delegation to `Planner`, `Testing Specialist`, `Implementation`, `Code Reviewer`, `De-Sloppification`, and `Docs`
- Mandatory commit and push flow between sections
- AssessmentBot-specific planning and documentation workflow

**Local analogue**

- None.

### `planner.agent.md`

**Generic sections**

- Clarification loop
- Writing `SPEC.md`
- Deciding whether a layout spec is required
- Ant Design consultation and layout loop
- Writing and reviewing `ACTION_PLAN.md`
- Handoff format
- Guardrails

**Repository-specific sections**

- AssessmentBot planning templates under `docs/developer/`
- Component AGENTS references in `src/backend/`, `src/frontend/`, and `scripts/builder/`
- Planned-only helper entries recorded in canonical docs
- Frontend layout requirements and repo-specific architecture constraints

**Local analogue**

- None.

### `planner-reviewer.agent.md`

**Generic sections**

- Review priorities
- Review method for `SPEC.md`, layout specs, and `ACTION_PLAN.md`
- Impartiality rules
- Reporting format
- Guardrails

**Repository-specific sections**

- AssessmentBot planning artefacts and templates
- Component AGENTS and relevant code areas for backend/frontend/builder planning
- Frontend layout review expectations tied to Ant Design and the existing shell
- Shared-helper planning and `Not implemented` reconciliation in canonical docs

**Local analogue**

- None.

### `Testing.agent.md`

**Generic sections**

- Component testing modes
- Command selection
- Idiomatic patterns
- Debugging workflow
- Reporting
- Completion requirements

**Repository-specific sections**

- AssessmentBot test documentation paths
- Backend/frontend/builder command sets and coverage thresholds
- `googleScriptRunHarness` and frontend test harness details
- Playwright installation guidance for browser tests
- Backend test file naming and suite split conventions

**Local analogue**

- None.

## Practical Sync Takeaways

- The local repo’s agent files are narrower and mostly revolve around exercise notebooks, `uv`, and Python test tooling.
- The remote repo’s agent files are broader and mirror a multi-module product split with backend, frontend, and builder concerns.
- The best sync candidates are the shared workflow skeletons, not the repository-specific validation commands or path references.
- If these instructions are harmonised later, the first pass should preserve the generic workflow sections and replace only the repo-specific nouns, docs paths, and validation commands.
