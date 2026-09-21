# Docker and DevContainer Setup

This repository ships two devcontainer definitions. The maintainer setup (in this repository) and the student template setup both use Microsoft's upstream VS Code Python image directly and install tooling via `uv`. There is no repository Dockerfile, no published GHCR student image, and no GitHub Actions image-build workflow.

## Overview

- Python 3.14 base image (`mcr.microsoft.com/devcontainers/python:3.14`) with Debian Bullseye, used directly by both devcontainer definitions
- Dependencies (pytest, jupyterlab, ruff, ipykernel, template CLI) managed by `uv` using `pyproject.toml` and `uv.lock`
- VS Code devcontainer settings tailored separately for maintainers and students
- No image build or publishing pipeline exists in this repository; the upstream image is referenced by tag

## Components

### 1. Devcontainer Configuration

Two devcontainer configurations target different audiences.

#### Maintainer devcontainer

Location: `/.devcontainer/devcontainer.json`

- Uses the published `mcr.microsoft.com/devcontainers/python:3.14` image directly
- Installs VS Code features for GitHub CLI and Git LFS
- Runs `curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync && . .venv/bin/activate` as a post-create command to prime the virtual environment
- Installs the maintainer extension set (Ruff, Python, Pylance, Jupyter family, Markdown linting, Copilot Chat)
- Launches the Jupyter kernel watchdog via `postStartCommand`

#### Student template devcontainer

Location: `/template_repo_files/.devcontainer/devcontainer.json`

- Uses the same upstream `mcr.microsoft.com/devcontainers/python:3.14` image as the maintainer devcontainer
- Keeps the extension list to Python, Pylance, Jupyter, and the default Python kernel for a focused student experience
- Applies opinionated VS Code settings (formatter, testing config, file exclusions, startup UX)
- Runs a conditional `postCreateCommand` that installs `uv` when absent and runs `uv sync`
- Runs a conditional `postStartCommand` that runs `uv sync` when a `pyproject.toml` is present and starts the watchdog
- Uses the existing `vscode` user and sets `PYTHONUNBUFFERED=1`

### 2. Jupyter Kernel Watchdog

Location: `scripts/jupyter_watchdog.py`

Both devcontainer configurations launch the Jupyter kernel watchdog as a background process via the `postStartCommand`. Its job is to detect and kill unresponsive Jupyter kernels so VS Code can restart them. See the dedicated [Jupyter Kernel Watchdog](jupyter-watchdog.md) doc for full details on behaviour, configuration, logging, and troubleshooting.

## Usage

### Maintainers (this repository)

1. Open the repository in VS Code and choose **Reopen in Container**
2. The devcontainer uses the upstream Python image, installs helper features, and runs `uv sync`
3. The `.venv` created by `uv` activates for subsequent terminals (`. .venv/bin/activate`)
4. Run `uv run` commands (for example, `uv run pytest -q`) to execute tasks inside the managed environment

### Students (Classroom 50 template repositories)

1. Template repositories include `.devcontainer/devcontainer.json` using the upstream Python 3.14 image
2. When Codespaces or VS Code loads the repo, the image is pulled and `uv sync` installs dependencies
3. Only the Python, Pylance, Jupyter, and default Python kernel extensions are installed, keeping the UI minimal
4. Students can start editing tagged notebook cells immediately; no manual setup is required

### Local development outside Codespaces

1. Install Docker (e.g., Docker Desktop) and VS Code with the Dev Containers extension
2. Clone this repository locally and open it in VS Code
3. Select **Dev Containers: Reopen in Container** from the Command Palette (Ctrl+Shift+P)
4. The maintainer devcontainer provisions the environment, including `uv sync`

## Image Updates

Both devcontainer definitions pin the upstream image tag directly, so there is no separate image to rebuild or publish. To move the runtime, update the `image` value in both `.devcontainer/devcontainer.json` and `template_repo_files/.devcontainer/devcontainer.json`, then regenerate template repositories so the student config picks up the change.

## Customisation

### Modifying the runtime image

1. Update the `image` value in both devcontainer definitions
2. Commit and push the change
3. Regenerate template repositories (or re-run the CLI) so new settings propagate; existing student repos need to pull changes manually

### Modifying VS Code settings

- Maintainer tweaks: edit `/.devcontainer/devcontainer.json`
- Student experience tweaks: edit `/template_repo_files/.devcontainer/devcontainer.json`
- Regenerate template repositories (or re-run the CLI) so new settings propagate; existing student repos need to pull changes manually

## Troubleshooting

### Image pull issues

- Confirm the upstream tag (`mcr.microsoft.com/devcontainers/python:3.14`) is pullable
- Ensure the target repository (or Codespace) has access to the container registry
- Use a specific published tag if `latest`-style tags appear stale

### Devcontainer boot problems

- Delete any existing `.venv` folder and let `uv sync` recreate it on the next container start
- Confirm the Dev Containers extension is up to date and Docker is running locally
- For template repositories, ensure `pyproject.toml` exists so the conditional `postStartCommand` installs dependencies

## Architecture Decisions

### Upstream base image

- Avoids maintaining a custom Docker image and its publishing pipeline
- Keeps maintainer and student environments on the same Python runtime
- Runtime changes ship through the devcontainer definitions and template regeneration

### Extension split between maintainers and students

- Maintainers need linting, Markdown tooling, and authoring extensions to create exercises efficiently
- Students get a distraction-free environment with Python essentials only
