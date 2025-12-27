FROM mcr.microsoft.com/devcontainers/python:3-bullseye

# Ensure npm is available before using it
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh \
    && bash /tmp/nodesource_setup.sh \
    && rm /tmp/nodesource_setup.sh \
    && apt-get install -y nodejs \
    && pip install --no-cache-dir pre-commit \
    && npm install @anthropic-ai/claude-code
