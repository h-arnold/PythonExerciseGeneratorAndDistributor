# Docker and DevContainer Setup

This repository ships with a shared Dockerfile and two devcontainer definitions. The maintainer setup (in this repository) uses the upstream VS Code Python image and installs tooling via `uv`. Template repositories for students consume the Docker image that is built from this Dockerfile and published to GitHub Container Registry (GHCR).

## Overview

- Python 3.11 base image (`mcr.microsoft.com/devcontainers/python:3.11`) with Debian Bullseye
- Dependencies (pytest, jupyterlab, ruff, ipykernel, template CLI) managed by `uv` using `pyproject.toml` and `uv.lock`
- GitHub Actions workflow builds a multi-arch image and pushes to GHCR for student use
- VS Code devcontainer settings tailored separately for maintainers and students

## Components

### 1. Dockerfile

Location: `/Dockerfile`

The Dockerfile extends Microsoft's Python devcontainer image and prepares the student environment:

- Copies `pyproject.toml` and `uv.lock` and upgrades `pip` and `uv`
- Runs `uv sync --no-install-project` to install the pinned dependency set without packaging the CLI
- Sets Python-friendly environment variables and ensures the `vscode` user owns the workspace
- Leaves the container running as the non-root `vscode` user and exposes port 8888 for Jupyter Lab

### 2. GitHub Actions Workflow

Location: `/.github/workflows/docker-build.yml`

The workflow automatically builds and publishes the Docker image when:

- Changes land on the `main` branch
- Relevant files (`Dockerfile`, `.dockerignore`, the workflow file) change
- A maintainer triggers the workflow manually via `workflow_dispatch`

Key characteristics:

- Multi-architecture builds (`linux/amd64`, `linux/arm64`) using Docker Buildx
- Metadata-based tagging (branch, PR, semantic version, commit SHA, and `latest`)
- Pushes to `ghcr.io/<repository>/student-environment` after authenticating with the GitHub token
- Reuses GitHub Actions cache layers to speed up repeat builds

### 3. Devcontainer Configuration

Two devcontainer configurations target different audiences.

#### Maintainer devcontainer

Location: `/.devcontainer/devcontainer.json`

- Uses the published `mcr.microsoft.com/devcontainers/python:3.11` image directly
- Installs VS Code features for GitHub CLI, Git LFS, and `uv`
- Runs `uv sync && . .venv/bin/activate` as a post-create command to prime the virtual environment
- Installs the maintainer extension set (Ruff, Python, Pylance, Jupyter family, Markdown linting)

#### Student template devcontainer

Location: `/template_repo_files/.devcontainer/devcontainer.json`

- Points to the pre-built GHCR image `ghcr.io/h-arnold/pythonexercisegeneratoranddistributor/student-environment:latest`
- Keeps the extension list to Python, Pylance, and Jupyter for a focused student experience
- Applies opinionated VS Code settings (formatter, testing config, startup UX)
- Runs a conditional `postCreateCommand` that performs `uv sync` when a `pyproject.toml` is present
- Uses the existing `vscode` user and sets `PYTHONUNBUFFERED=1`

## Usage

### Maintainers (this repository)

1. Open the repository in VS Code and choose **Reopen in Container**
2. The devcontainer uses the upstream Python image, installs helper features, and runs `uv sync`
3. The `.venv` created by `uv` activates for subsequent terminals (`. .venv/bin/activate`)
4. Run `uv run` commands (for example, `uv run pytest -q`) to execute tasks inside the managed environment

### Students (GitHub Classroom template repositories)

1. Template repositories include `.devcontainer/devcontainer.json` pointing at the GHCR image
2. When Codespaces or VS Code loads the repo, the pre-built image is pulled and `uv sync` installs dependencies
3. Only the Python, Pylance, and Jupyter extensions are installed, keeping the UI minimal
4. Students can start editing tagged notebook cells immediately; no manual setup is required

### Local development outside Codespaces

1. Install Docker (e.g., Docker Desktop) and VS Code with the Dev Containers extension
2. Clone this repository locally and open it in VS Code
3. Select **Dev Containers: Reopen in Container** from the Command Palette (Ctrl+Shift+P)
4. The maintainer devcontainer provisions the environment, including `uv sync`

## Image Updates

The GitHub Actions workflow rebuilds and republishes the student image whenever the Dockerfile (or related files) change on `main`. To trigger a rebuild manually:

1. Navigate to **Actions** in GitHub
2. Select **Build and Push Student Environment Docker Image**
3. Click **Run workflow**

Caching tips:

- The workflow already uses the GitHub Actions cache backend for Docker layers
- Inside the container, `uv` caches packages under `/root/.cache/uv`; the cache is automatically preserved between layers when the lockfile is unchanged

## Customisation

### Modifying the image

1. Update `Dockerfile` (and `uv.lock` if dependencies change)
2. Commit and push to `main`
3. The workflow rebuilds and pushes a fresh image to GHCR

### Modifying VS Code settings

- Maintainer tweaks: edit `/.devcontainer/devcontainer.json`
- Student experience tweaks: edit `/template_repo_files/.devcontainer/devcontainer.json`
- Regenerate template repositories (or re-run the CLI) so new settings propagate; existing student repos need to pull changes manually

## Troubleshooting

### Image pull issues

- Confirm the image exists at `ghcr.io/h-arnold/pythonexercisegeneratoranddistributor/student-environment:latest`
- Ensure the target repository (or Codespace) has access to the container registry
- Use a specific tag (for example, a SHA tag) if `latest` appears stale

### Workflow build failures

- Inspect the failing run under **Actions** for Docker build logs
- Verify Dockerfile edits build locally (`docker build .`)
- Check that dependencies specified in `pyproject.toml` are available (public packages only)

### Devcontainer boot problems

- Delete any existing `.venv` folder and let `uv sync` recreate it on the next container start
- Confirm the Dev Containers extension is up to date and Docker is running locally
- For template repositories, ensure `pyproject.toml` exists so the conditional `postCreateCommand` installs dependencies

## Architecture Decisions

### Pre-built student image

- Minimises Codespaces start-up time and bandwidth
- Guarantees consistent, reproducible exercises for all students
- Allows maintainers to ship updates centrally without rebuilding per repository

### Extension split between maintainers and students

- Maintainers need linting, Markdown tooling, and authoring extensions to create exercises efficiently
- Students get a distraction-free environment with Python essentials only

### GitHub Container Registry

- Free for public repositories and integrates with Actions
- Handles authentication automatically through GitHub tokens
- Supports multi-architecture images consumed by Codespaces

## Future improvements

- Automate smoke tests against the published GHCR image after each build
- Document best practices for pre-warming `uv` caches in CI environments
- Offer alternative profiles for advanced courses (e.g., linting-focused images)
