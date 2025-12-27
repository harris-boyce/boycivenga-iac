FROM mcr.microsoft.com/devcontainers/python:3-bullseye

# Install dependencies and tools
# hadolint ignore=DL3008,DL3015
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && curl -fsSL https://claude.ai/install.sh | bash \
    && pip install --no-cache-dir \
        pre-commit \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
