FROM mcr.microsoft.com/devcontainers/python:3-bullseye

# Ensure npm is available before using it
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://claude.ai/install.sh | bash \
    && pip install --no-cache-dir pre-commit 
