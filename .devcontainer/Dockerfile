FROM mcr.microsoft.com/devcontainers/base:ubuntu
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      docker-compose python3-pip \
    && rm -rf /var/lib/apt/lists/*
