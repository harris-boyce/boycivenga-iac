FROM mcr.microsoft.com/devcontainers/python:3-bullseye

# This image includes Python and Node.js pre-installed for faster builds
# Additional features are added via devcontainer.json for Docker, Terraform, and GitHub CLI

# Install Python and Node packages at build time for better caching
RUN pip install --no-cache-dir pre-commit \
    && npm install -g @anthropic-ai/claude-code
