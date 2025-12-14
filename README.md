# boycivenga-iac
Terraform repository for managing all things home networking, lab, smart home automations, etc.

## Development Environment

This repository includes a development container (devcontainer) configuration that provides a consistent, reproducible development environment for all contributors. The devcontainer comes pre-configured with all necessary tools for working with Terraform, Python, and networking workflows.

### Using the Devcontainer

#### Option 1: Visual Studio Code (Local)

1. **Prerequisites:**
   - Install [Visual Studio Code](https://code.visualstudio.com/)
   - Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Open the project in a devcontainer:**
   - Open this repository in VS Code
   - When prompted, click "Reopen in Container" (or run the command `Dev Containers: Reopen in Container` from the Command Palette)
   - VS Code will build the container and open a new window connected to it

3. **Rebuild the container (if needed):**
   - Run the command `Dev Containers: Rebuild Container` from the Command Palette

#### Option 2: GitHub Codespaces (Cloud)

1. **Create a Codespace:**
   - Navigate to the repository on GitHub
   - Click the "Code" button, then select the "Codespaces" tab
   - Click "Create codespace on [branch]"
   - GitHub will create and configure your cloud development environment

2. **Access your Codespace:**
   - Your Codespace will open in a browser-based VS Code instance
   - Alternatively, you can connect to it from VS Code Desktop

### What's Included

The devcontainer provides:

- **Base:** Ubuntu Linux environment
- **Tools:**
  - Terraform (latest version)
  - Python 3 (latest version) with pip
  - Docker CLI and Docker Compose (with Docker-in-Docker support)
  - GitHub CLI
  - pre-commit (automatically installed on container creation)
- **VS Code Extensions:**
  - Python (`ms-python.python`)
  - Terraform (`hashicorp.terraform`)
  - YAML (`redhat.vscode-yaml`)
  - Markdown All in One (`yzhang.markdown-all-in-one`)

### Network Connectivity

The devcontainer is configured to support network connectivity for:
- Local NetBox/UniFi endpoints
- Remote NetBox/UniFi endpoints
- Docker Compose services for testing

### Customization

The devcontainer can be extended with additional tools:

1. **Add development tools:** Edit `.devcontainer/Dockerfile` to install additional packages
2. **Add VS Code extensions:** Edit the `customizations.vscode.extensions` array in `.devcontainer/devcontainer.json`
3. **Add devcontainer features:** Edit the `features` object in `.devcontainer/devcontainer.json` (see [available features](https://containers.dev/features))

Example: Adding UniFi CLI or additional linters:

```dockerfile
# In .devcontainer/Dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      your-additional-tool \
    && rm -rf /var/lib/apt/lists/*
```
