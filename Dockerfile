# Use Microsoft's official Python devcontainer image as base
# This image includes Python 3.11, common development tools, and is optimized for VS Code
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /workspace

# Copy the dependency manifests so uv can install the same stack
COPY pyproject.toml uv.lock /workspace/

# Install dependencies through uv for reproducible builds
# Use --no-install-project to skip installing the main package (template_repo_cli)
# Students only need the dependencies (pytest, jupyterlab, etc.), not the CLI tools
# Use copy link mode to avoid hardlink errors across filesystems
ENV UV_LINK_MODE=copy
RUN python -m pip install --upgrade pip uv && \
    uv sync --no-install-project

# Set environment variables for better Python behavior in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user (vscode user is already created in base image)
# Set up workspace permissions
RUN chown -R vscode:vscode /workspace

# Switch to non-root user
USER vscode

# Expose Jupyter Lab port
EXPOSE 8888

# Set default command
CMD ["/bin/bash"]
