# Documentation Index

Documentation is organised by audience. Choose the section that matches your role.

---

## 👩‍🏫 For Teachers

| Document | What it covers |
|---|---|
| [`teachers/pedagogy.md`](teachers/pedagogy.md) | The MDM (Modify, Debug, Make) pedagogical framework — why this approach works. |
| [`teachers/exercise-generation.md`](teachers/exercise-generation.md) | Using the Exercise Generation Copilot agent to create new exercises. |
| [`teachers/CLI_README.md`](teachers/CLI_README.md) | Template Repository CLI — bundling exercises into GitHub Classroom template repos. |
| [`teachers/github-classroom-autograding-guide.md`](teachers/github-classroom-autograding-guide.md) | GitHub Classroom autograding integration — workflow setup, Base64 payloads, reporter wiring. |

---

## 🤖 For Exercise Generation Agents

| Document | What it covers |
|---|---|
| [`exercise-agents/exercise-generation-cli.md`](exercise-agents/exercise-generation-cli.md) | CLI scaffold tool (`new_exercise.py`) — syntax, flags, post-creation workflow. |
| [`exercise-agents/exercise-testing.md`](exercise-agents/exercise-testing.md) | Testing conventions — philosophy, scoring, patterns, anti-patterns, API reference. |
| [`exercise-agents/exercise-types/debug.md`](exercise-agents/exercise-types/debug.md) | Debug exercise format — cell structure, error progression, tagging. |
| [`exercise-agents/exercise-types/modify.md`](exercise-agents/exercise-types/modify.md) | Modify exercise format — cell structure, scaffolding, progression. |
| [`exercise-agents/exercise-types/make.md`](exercise-agents/exercise-types/make.md) | Make exercise format — cell structure, tagged-cell grading model. |
| [`exercise-agents/exercise-types/gaps.md`](exercise-agents/exercise-types/gaps.md) | Gap-fill exercise format — gap conventions, scaffolding progression. |

---

## 🛠️ For Developers & Coding Agents

| Document | What it covers |
|---|---|
| [`developers/development.md`](developers/development.md) | Contributor guide — architecture, grading internals, autograding dev workflow. |
| [`developers/execution-model.md`](developers/execution-model.md) | **Canonical contract** — test discovery, runtime imports, variant selection, source-to-export mapping. |
| [`developers/project-structure.md`](developers/project-structure.md) | Directory layout, naming conventions, tagged cell system, parallel notebook sets. |
| [`developers/testing-framework.md`](developers/testing-framework.md) | Infrastructure testing — testing the codebase itself (scaffolding, grader, CLI). |
| [`developers/setup.md`](developers/setup.md) | Environment setup — prerequisites, uv sync, verification. |
| [`developers/docker-devcontainer-setup.md`](developers/docker-devcontainer-setup.md) | Dockerfile, devcontainer configs, GitHub Actions image build. |
| [`developers/autograding-cli.md`](developers/autograding-cli.md) | Technical reference for `build_autograde_payload.py` — CLI args, outputs, CI usage. |

---

## ⚙️ Agent Pipeline Specs

| Document | What it covers |
|---|---|
| [`agents/plan_templates/`](agents/plan_templates/) | Templates for SPEC and ACTION_PLAN documents used by the Planner and Planner Reviewer agents. |
| [`agents/tidy_code_review/`](agents/tidy_code_review/) | Automated and manual code review procedures for the Tidy Code Reviewer agent. |

---

## 🖼️ Media

| Path | Contents |
|---|---|
| [`images/`](images/) | Screenshots and diagrams used across documentation. |
