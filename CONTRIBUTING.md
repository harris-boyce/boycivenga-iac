# Contributing to boycivenga-iac

Thank you for your interest in contributing to this Infrastructure as Code (IaC) repository! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Continuous Integration](#continuous-integration)
- [Code Standards](#code-standards)
- [Making Changes](#making-changes)

## Getting Started

This repository manages Terraform infrastructure for home networking, lab environments, and smart home automations. Contributions can include:

- Infrastructure improvements and new resources
- Documentation updates
- Bug fixes
- Tool and automation enhancements

## Development Environment Setup

You have two options for setting up your development environment:

### Option 1: Using Devcontainer (Recommended)

The devcontainer provides a pre-configured environment with all necessary tools installed. This is the fastest way to get started.

**Prerequisites:**
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

**Steps:**
1. Clone this repository
2. Open the repository in VS Code
3. When prompted, click "Reopen in Container" (or run `Dev Containers: Reopen in Container` from the Command Palette)
4. VS Code will build the container with all tools pre-installed
5. Once the container is ready, run `pre-commit install` to set up git hooks

Alternatively, you can use [GitHub Codespaces](https://github.com/features/codespaces) for a cloud-based development environment.

### Option 2: Manual Setup

If you prefer to work outside the devcontainer, use the bootstrap script to install all required tools:

```bash
# Clone the repository
git clone https://github.com/harris-boyce/boycivenga-iac.git
cd boycivenga-iac

# Run the bootstrap script
bash scripts/bootstrap.sh

# Install pre-commit hooks
pre-commit install
```

The bootstrap script will install:
- Terraform (latest version)
- Python 3 (latest version)
- Docker CLI and Docker Compose
- GitHub CLI
- pre-commit

**Supported Operating Systems:**
- Linux (Ubuntu/Debian-based distributions)
- macOS (with Homebrew)

## Pre-commit Hooks

This repository uses pre-commit hooks to ensure code quality and consistency. The hooks are automatically run before each commit.

### Configured Hooks

- **Terraform:**
  - `terraform_fmt` - Formats Terraform files
  - `tflint` - Lints Terraform files for errors and best practices

- **Python:**
  - `black` - Code formatting
  - `isort` - Import sorting
  - `flake8` - Linting and style checking

- **General:**
  - `check-yaml` - Validates YAML syntax
  - `detect-aws-credentials` - Prevents committing AWS credentials
  - `end-of-file-fixer` - Ensures files end with a newline
  - `trailing-whitespace` - Removes trailing whitespace
  - `check-added-large-files` - Prevents large files from being committed
  - `check-merge-conflict` - Checks for merge conflict markers

### Installing Pre-commit Hooks

After setting up your environment (either via devcontainer or bootstrap script):

```bash
pre-commit install
```

### Running Hooks Manually

To run all hooks on all files:

```bash
pre-commit run --all-files
```

To run a specific hook:

```bash
pre-commit run <hook-id> --all-files
```

### Updating Hooks

To update pre-commit hooks to the latest versions:

```bash
pre-commit autoupdate
```

## Continuous Integration

This repository uses GitHub Actions for continuous integration to ensure code quality and consistency across all contributions.

### CI Workflow

The CI workflow (`.github/workflows/ci.yaml`) automatically runs on:
- Every push to any branch
- Every pull request

### What the CI Checks

The CI pipeline validates:

1. **Pre-commit Hooks**: Runs all configured pre-commit hooks including:
   - YAML validation
   - AWS credentials detection
   - File formatting (end-of-file, trailing whitespace)
   - Large file detection
   - Merge conflict detection
   - Terraform formatting and validation
   - Python formatting (black) and linting (flake8, isort)

2. **Terraform Validation**: Validates Terraform configuration syntax and consistency

3. **Python Code Quality**:
   - `black --check`: Ensures Python code follows Black formatting standards
   - `flake8`: Lints Python code for style and potential errors

### Viewing CI Results

- CI status is displayed on pull requests
- Click "Details" next to each check to view logs
- All checks must pass before merging

### Running CI Checks Locally

To run the same checks locally before pushing:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Check Python formatting
black --check .

# Lint Python code
flake8 .

# Validate Terraform (if you have .tf files)
cd terraform
terraform init -backend=false
terraform validate
```

## Code Standards

### Terraform

- Use consistent formatting (`terraform fmt`)
- Follow naming conventions for resources
- Add comments for complex logic
- Use variables for reusable values
- Document modules with README files

### Python

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep line length to 88 characters (Black default)
- Use meaningful variable and function names

### Documentation

- Update README.md when adding new features
- Document any new scripts or tools
- Include examples where helpful
- Keep documentation up-to-date with code changes

## Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, focused commits
   - Test your changes thoroughly
   - Ensure pre-commit hooks pass

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

   Pre-commit hooks will run automatically. If they fail, fix the issues and commit again.

4. **Push your changes:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request:**
   - Provide a clear description of your changes
   - Reference any related issues
   - Wait for review and address feedback

## Questions or Issues?

If you have questions or run into issues:

1. Check existing issues on GitHub
2. Review the documentation in README.md
3. Open a new issue with details about your question or problem

Thank you for contributing!
