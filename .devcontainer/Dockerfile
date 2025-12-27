FROM mcr.microsoft.com/devcontainers/python:3-bullseye

# Ensure npm is available before using it
RUN apt-get update && apt-get install -y npm \
    && pip install --no-cache-dir pre-commit \
    && npm install @anthropic-ai/claude-code