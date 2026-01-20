# Use Microsoft's official Python devcontainer image as base
# This image includes Python 3.11, common development tools, and is optimized for VS Code
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /workspace

# Copy requirements files for reference (not used for installation in base image)
# The base image pre-installs common dependencies; student repos install their
# specific project dependencies via devcontainer postCreateCommand

# Install Python dependencies
# Use --no-cache-dir to reduce image size
# Install in a single RUN command to reduce layers
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    pytest>=8.0 \
    ipykernel>=6.0 \
    jupyterlab>=4.0

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
