# Docker and DevContainer Setup

This repository includes a pre-built Docker image and devcontainer configuration for student exercises.

## Overview

The student environment provides a minimal, pre-configured setup with:

- Python 3.11
- Jupyter Lab for running notebooks
- pytest for automated testing
- VS Code extensions: Python, Pylance, and Jupyter (only)

All unnecessary features are disabled to provide students with a focused learning environment.

## Components

### 1. Dockerfile

Location: `/Dockerfile`

The Dockerfile creates a minimal student environment based on Microsoft's official Python devcontainer image. It:

- Uses Python 3.11 on Debian Bullseye
- Installs only required packages (pytest, ipykernel, jupyterlab)
- Optimizes build time with layer caching
- Runs as non-root user for security

**Best practices implemented:**

- Minimal layer count
- No unnecessary packages
- Non-root user execution
- Optimized .dockerignore file

### 2. GitHub Actions Workflow

Location: `/.github/workflows/docker-build.yml`

Automatically builds and pushes the Docker image to GitHub Container Registry (GHCR) when:

- Changes are pushed to the main branch
- Dockerfile or related files are modified
- Manually triggered via workflow_dispatch

The workflow:

- Builds for both AMD64 and ARM64 platforms
- Uses GitHub Actions cache for faster builds
- Tags images with branch name, SHA, and 'latest'
- Pushes to `ghcr.io/h-arnold/pythonexercisegeneratoranddistributor/student-environment`

### 3. DevContainer Configuration

Location: `/template_repo_files/.devcontainer/devcontainer.json`

Configures the student environment for GitHub Codespaces and VS Code Remote - Containers:

- Uses the pre-built image from GHCR
- Installs only essential VS Code extensions
- Disables welcome screens and tips
- Configures Python and Jupyter settings
- Hides build artifacts and cache files

**Minimal UI features:**

- No startup editor
- No welcome walkthroughs
- No tips
- Only essential extensions

## Usage

### For Students (GitHub Classroom)

When a student opens their assignment repository in GitHub Codespaces or VS Code with the Remote - Containers extension:

1. The devcontainer automatically pulls the pre-built image
2. VS Code installs only the three required extensions
3. Dependencies are installed via `uv sync`
4. Students can immediately start working on exercises

**No manual setup required!**

### For Template Repository Creation

The CLI automatically includes the devcontainer configuration when creating template repositories:

```bash
template_repo_cli create --construct sequence --repo-name my-exercises
```

The generated repository will include:

- `.devcontainer/devcontainer.json` pointing to the pre-built image
- All necessary VS Code settings
- Jupyter and pytest configuration

### For Local Development

To use the devcontainer locally:

1. Install Docker Desktop
2. Install VS Code with the "Dev Containers" extension
3. Open the repository in VS Code
4. Click "Reopen in Container" when prompted

Or use the Command Palette (Ctrl+Shift+P):

```
Dev Containers: Reopen in Container
```

## Image Updates

The Docker image is automatically rebuilt when changes are pushed to main. To force a rebuild:

1. Go to Actions tab in GitHub
2. Select "Build and Push Student Environment Docker Image"
3. Click "Run workflow"

The new image will be available within a few minutes.

## Customization

### Modifying the Image

To add packages or change configuration:

1. Edit `Dockerfile`
2. Commit and push to main
3. GitHub Actions will automatically rebuild and push the new image

### Modifying VS Code Settings

To change student VS Code settings:

1. Edit `template_repo_files/.devcontainer/devcontainer.json`
2. Commit changes
3. New template repositories will use the updated configuration

**Note:** Existing student repositories won't automatically update. Students would need to pull the latest devcontainer config.

## Troubleshooting

### Image Pull Failures

If students experience image pull failures:

1. Check that the repository is public or students have access
2. Verify the image exists at `ghcr.io/h-arnold/pythonexercisegeneratoranddistributor/student-environment:latest`
3. Try using a specific tag instead of `latest`

### Build Failures

If the GitHub Actions workflow fails:

1. Check the Actions tab for error logs
2. Verify Dockerfile syntax
3. Ensure all required files exist
4. Check that dependencies are available on PyPI

### Students Can't Install Extensions

Extensions are pre-configured in devcontainer.json. If students try to install additional extensions:

- They can install them in their codespace
- Extensions won't persist if devcontainer is rebuilt
- Consider if the extension should be added to devcontainer.json

## Architecture Decisions

### Why Pre-built Images?

Pre-built images provide:

- Faster startup time for students (no build required)
- Consistent environment across all students
- Reduced Codespaces usage time
- Centralized updates

### Why Minimal Extensions?

Only Python, Pylance, and Jupyter are included to:

- Reduce cognitive load for students
- Minimize distractions
- Focus on learning Python
- Faster extension installation

### Why GHCR?

GitHub Container Registry provides:

- Free hosting for public repositories
- Seamless integration with GitHub Actions
- No separate authentication required
- Built-in permission management

## Future Improvements

Potential enhancements:

- Add support for Pyodide (browser-based Python)
- Create exercise-specific images
- Add pre-installed linting tools
- Support for different Python versions
