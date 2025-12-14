FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install additional packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        curl \
        wget \
        git \
        jq \
        vim \
        python3 \
        python3-pip \
        unzip \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install pre-commit
RUN pip3 install --no-cache-dir pre-commit

# Install tfsec for security scanning
RUN curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# Install checkov for additional security scanning
RUN pip3 install --no-cache-dir checkov

# Install terraform-docs for documentation generation
RUN curl -Lo ./terraform-docs.tar.gz https://github.com/terraform-docs/terraform-docs/releases/download/v0.17.0/terraform-docs-v0.17.0-linux-amd64.tar.gz \
    && tar -xzf terraform-docs.tar.gz \
    && chmod +x terraform-docs \
    && mv terraform-docs /usr/local/bin/ \
    && rm terraform-docs.tar.gz

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace
