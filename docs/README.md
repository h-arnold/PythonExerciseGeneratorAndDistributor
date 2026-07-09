# Documentation Index

Documentation is organised by audience. Choose the section that matches your role.

---

## 👩‍🏫 For Teachers

If you are new to this project, start with one of these two guides:

- **[Getting Started](teachers/getting-started.md)** — use pre-built template repos, no command line needed.
- **[Creating Custom Exercise Sets](teachers/creating-exercise-sets.md)** — bundle your own exercises with the CLI, or create new ones.

| Document | What it covers |
| --- | --- |
| [Getting Started](teachers/getting-started.md) | **Start here if you want to use existing exercises.** Quick path: pick a pre-built template repo → create Classroom assignment → share with students. No command line needed. |
| [In the Classroom](teachers/in-the-classroom.md) | **Companion to Getting Started.** Student workflow: opening notebooks, selecting the Python kernel, running code, using the self-checker, saving and submitting work. |
| [Creating Custom Exercise Sets](teachers/creating-exercise-sets.md) | **Start here if you need to build custom template repos or create new exercises.** Requires Codespaces, GitHub authentication, and the repoman CLI. |
| [Understanding the Tools](teachers/understanding-the-tools.md) | Plain-English explanation of GitHub, Classroom, Codespaces, version control, and Jupyter notebooks — and how they fit together. |
| [Classroom Practices](teachers/classroom-practices.md) | Day-to-day lesson tips: starting Codespaces early, using the self-checker, good git habits, troubleshooting common issues. |
| [Creating and Editing Exercises](teachers/creating-and-editing-exercises.md) | How to create new exercises (with the AI assistant) or tweak existing ones — including branching, verifying, and committing. |
| [IT Network Requirements](teachers/it-network-requirements.md) | For IT teams — what domains to unblock, security isolation model, and why Codespaces is better than local Python installs. |
| [Pedagogy](teachers/pedagogy.md) | The MDM (Modify, Debug, Make) pedagogical framework — why this approach works. |
| [Exercise Generation with Copilot](teachers/exercise-generation.md) | Detailed reference for using the Exercise Generation Copilot agent to create new exercises. |
| [How to Use the Template Repo CLI](teachers/how-to-use-the-template-repo-cli.md) | Creating template repos for GitHub Classroom — step-by-step teacher guide. |
| [Construct Template Repos](teachers/construct-template-repos.md) | Auto-generated index of per-construct template repositories, updated on each push to main. |
| [Template Repo CLI Reference](../developers/template_repo_cli.md) | Full CLI reference for `repoman` — all flags, options, and technical details. |
| [GitHub Classroom Autograding Guide](../developers/github-classroom-autograding-guide.md) | GitHub Classroom autograding integration — workflow setup, Base64 payloads, reporter wiring. |

---

## 🤖 For Exercise Generation Agents

| Document | What it covers |
| --- | --- |
| [Exercise Generation CLI](exercise-agents/exercise-generation-cli.md) | CLI scaffold tool (`new_exercise.py`) — syntax, flags, post-creation workflow. |
| [Exercise Testing](exercise-agents/exercise-testing.md) | Testing conventions — philosophy, scoring, patterns, anti-patterns, API reference. |
| [Debug Exercise Format](exercise-agents/exercise-types/debug.md) | Debug exercise format — cell structure, error progression, tagging. |
| [Modify Exercise Format](exercise-agents/exercise-types/modify.md) | Modify exercise format — cell structure, scaffolding, progression. |
| [Make Exercise Format](exercise-agents/exercise-types/make.md) | Make exercise format — cell structure, tagged-cell grading model. |
| [Gap-fill Exercise Format](exercise-agents/exercise-types/gaps.md) | Gap-fill exercise format — gap conventions, scaffolding progression. |

---

## 🛠️ For Developers & Coding Agents

| Document | What it covers |
| --- | --- |
| [Development Guide](developers/development.md) | Contributor guide — architecture, grading internals, autograding dev workflow. |
| [Execution Model](developers/execution-model.md) | **Canonical contract** — test discovery, runtime imports, variant selection, source-to-export mapping. |
| [Project Structure](developers/project-structure.md) | Directory layout, naming conventions, tagged cell system, parallel notebook sets. |
| [Testing Framework](developers/testing-framework.md) | Infrastructure testing — testing the codebase itself (scaffolding, grader, CLI). |
| [Setup Guide](developers/setup.md) | Environment setup — prerequisites, uv sync, verification. |
| [Template Repo CLI Reference](developers/template_repo_cli.md) | Full CLI reference for `repoman` — all flags, options, and technical details. |
| [GitHub Classroom Autograding Guide](developers/github-classroom-autograding-guide.md) | GitHub Classroom autograding integration — workflow setup, Base64 payloads, reporter wiring. |
| [Docker & Devcontainer Setup](developers/docker-devcontainer-setup.md) | Dockerfile, devcontainer configs, GitHub Actions image build. |
| [Jupyter Kernel Watchdog](developers/jupyter-watchdog.md) | Kernel health monitor for VS Code devcontainers — detects and kills unresponsive Jupyter kernels so VS Code can restart them. |
| [Autograding CLI Reference](developers/autograding-cli.md) | Technical reference for `build_autograde_payload.py` — CLI args, outputs, CI usage. |

---

## ⚙️ Agent Pipeline Specs

| Document | What it covers |
| --- | --- |
| [Plan Templates](agents/plan_templates/) | Templates for SPEC and ACTION_PLAN documents used by the Planner and Planner Reviewer agents. |
| [Tidy Code Review](agents/tidy_code_review/) | Automated and manual code review procedures for the Tidy Code Reviewer agent. |

---

## 🖼️ Media

| Path | Contents |
| --- | --- |
| [Images](images/) | Screenshots and diagrams used across documentation. |
