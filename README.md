# boycivenga-iac
Infrastructure-as-Code repository for managing home networking, lab, and smart home automations via UniFi API.

> **Note**: This repository originally used Terraform but has migrated to direct UniFi API integration due to Terraform provider compatibility issues. All security boundaries (attestation, policy, approval) remain intact.

## ⚠️ Security & Authority Boundaries

**IMPORTANT: Read this before contributing or using this repository.**

This repository has explicit security and authority boundaries that MUST be respected:

### 🎯 Authority Boundary

**NetBox is the SOLE authoritative source of infrastructure intent. Apply scripts are NOT an authority.**

- ✅ All infrastructure definitions MUST originate from NetBox
- ❌ DO NOT define infrastructure intent directly in apply scripts or configuration files
- ❌ DO NOT create manual variable files outside the render pipeline

### 🔒 Execution Boundary

**Only GitHub Actions may execute infrastructure apply operations. Manual execution is PROHIBITED.**

- ✅ All apply operations MUST run in GitHub Actions workflows
- ❌ DO NOT run apply scripts (`apply_via_unifi.py`) locally outside testing
- ❌ DO NOT use alternative CI/CD systems
- ℹ️  Local execution of plan scripts (`plan_unifi.py`) is permitted for drift detection

### 🛡️ Security Boundary

**All artifacts MUST be attested with SLSA provenance. Unattested artifacts are rejected.**

- ✅ Only attested artifacts from the render pipeline may be consumed
- ❌ DO NOT create, edit, or modify artifacts manually
- ❌ DO NOT bypass attestation verification in production

**📖 Complete Documentation**: See [docs/phase4/security.md](docs/phase4/security.md) for comprehensive security and authority boundaries.

### Contributor Checklist

Before contributing, verify you understand:

- [ ] NetBox is authoritative for intent; apply scripts implement the desired state
- [ ] GitHub Actions is the only permitted execution environment
- [ ] Attestation verification is mandatory and cannot be bypassed in production
- [ ] Manual artifacts and local apply script execution are prohibited (plan scripts permitted)
- [ ] All boundaries are documented in [docs/phase4/security.md](docs/phase4/security.md)

## Repository Layout

This repository is organized into the following top-level directories:

- **`netbox-client/`** – Tools and scripts for interacting with the NetBox API and managing network intent data
- **`terraform/`** – Legacy Terraform modules (deprecated, see UniFi API scripts)
- **`scripts/`** – Apply and plan scripts for UniFi API integration, plus bootstrap utilities
- **`artifacts/`** – Rendered outputs and generated files (used for local development, not version controlled)
- **`docs/`** – Project documentation, architecture decisions, and operational guides
- **`.github/workflows/`** – CI/CD workflows including the automated render pipeline

## Automated Render Pipeline

This repository includes an automated [render pipeline](docs/render-pipeline.md) that:
- Exports data from the NetBox API
- Generates tfvars configuration files with network definitions
- Publishes artifacts for review and manual deployment
- **Attests all artifacts** with SLSA provenance for supply chain security

**Important:** The render pipeline is read-only and does not apply infrastructure changes. Apply operations use the UniFi API directly via Python scripts. See [docs/render-pipeline.md](docs/render-pipeline.md) for details.

## PR Approval-Gated Apply Workflow

**NEW: Infrastructure plans now require PR approval before execution.**

The plan workflow (`terraform-plan.yaml`) enforces an approval gate:

### How It Works

1. **Create a PR** that references a specific render artifacts workflow run
   - Include the render run ID in the PR description: `Render Run: <run_id>`
   - Or include a link to the workflow run: `https://github.com/.../actions/runs/<run_id>`

2. **Get PR Approval** from a repository maintainer
   - The PR approval serves as explicit authorization to run infrastructure plan

3. **Automatic Plan Execution** after approval
   - Workflow automatically triggers on PR approval event
   - Extracts render run ID from PR description
   - Downloads and verifies attested artifacts from the specified run
   - Executes plan via UniFi API for all sites
   - Records full traceability: PR number, approver, artifact source

### Key Security Properties

- ✅ **Cannot be triggered by branch push** - Only PR approval events trigger the workflow
- ✅ **Explicit artifact references** - PR must specify which render run to use
- ✅ **Full traceability** - PR number, approver, and artifact source are recorded
- ✅ **Impossible to run on non-approved artifacts** - No automatic execution after render completion
- ❌ **No bypass** - Branch pushes and workflow completion events do not trigger plans

### Manual Dispatch (Testing Only)

For testing purposes, the workflow can be manually triggered via GitHub Actions UI:
- Requires explicit `render_run_id` input
- Optionally accepts `pr_number` for traceability
- Should only be used for development/testing scenarios

### Complete Workflow Guide

See [docs/phase4/terraform-plan-approval-workflow.md](docs/phase4/terraform-plan-approval-workflow.md) for:
- Step-by-step approval workflow
- PR template and examples
- Troubleshooting guide
- Security guarantees

Also see:
- [docs/phase4/security.md](docs/phase4/security.md) for complete security documentation
- [docs/architecture/state-management.md](docs/architecture/state-management.md) for state management architecture

## Artifact Attestation & Trust Boundary

All artifacts generated by the render pipeline are cryptographically attested using SLSA provenance. This provides:
- **Provenance verification**: Proof that artifacts originate from trusted CI/CD workflows
- **Integrity protection**: Assurance that artifacts have not been tampered with
- **Supply chain security**: Protection against unauthorized modifications

**Trust Boundary Contract**: **Apply scripts must only consume attested artifacts**. This requirement ensures that all infrastructure deployments are traceable to verified sources.

**Attestation Verification Gate**: A reusable composite action (`.github/actions/verify-attestation`) enforces this contract by verifying attestations before artifacts can be consumed. The gate fails closed in production and provides explicit bypass capability for development/testing.

See documentation:
- [docs/phase4/attestation-gate.md](docs/phase4/attestation-gate.md) - Attestation verification gate
- [docs/phase3/attestation.md](docs/phase3/attestation.md) - Attestation implementation
- [docs/architecture/state-management.md](docs/architecture/state-management.md) - State management architecture

## Quick Start

### For Contributors

If you're contributing to this repository, please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions and development guidelines.

**Quick setup:**
1. Use the devcontainer (recommended) - all tools are pre-installed, or
2. Run `bash scripts/bootstrap.sh` for manual setup
3. Run `pre-commit install` to enable code quality checks

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
  - Python 3 (latest version) with pip
  - Docker CLI and Docker Compose (with Docker-in-Docker support)
  - GitHub CLI
  - pre-commit (automatically installed on container creation)
  - Terraform (legacy, for reference only)
- **VS Code Extensions:**
  - Python (`ms-python.python`)
  - YAML (`redhat.vscode-yaml`)
  - Markdown All in One (`yzhang.markdown-all-in-one`)
  - Terraform (`hashicorp.terraform`) - for reference only

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
