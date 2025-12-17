# Contributing to boycivenga-iac

Thank you for your interest in contributing to this Infrastructure as Code (IaC) repository! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Required Tools and Extensions](#required-tools-and-extensions)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Code Standards](#code-standards)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Message Format](#commit-message-format)
- [Pull Request Workflow](#pull-request-workflow)
- [GitHub Copilot Usage](#github-copilot-usage)
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

## Required Tools and Extensions

### Core Tools

All contributors should have the following tools installed in their environment:

- **Terraform** (latest version) - Infrastructure as Code tool
- **Python 3** (latest version) - For automation scripts
- **Docker** and **Docker Compose** - Container management
- **Git** - Version control
- **pre-commit** - Git hook framework for code quality
- **GitHub CLI** (`gh`) - GitHub command-line tool (optional but recommended)

### VS Code Extensions

For the best development experience in Visual Studio Code, install these extensions:

- **ms-python.python** - Python language support
- **hashicorp.terraform** - Terraform language support and validation
- **redhat.vscode-yaml** - YAML language support
- **yzhang.markdown-all-in-one** - Markdown editing and preview
- **github.codespaces** - GitHub Codespaces support

These extensions are automatically installed when using the devcontainer or GitHub Codespaces.

### Python Packages

The following Python packages are used for code quality and should be installed in your environment:

- **black** - Code formatter
- **isort** - Import statement organizer
- **flake8** - Style guide enforcement
- **pre-commit** - Pre-commit hook management

These are automatically configured via the pre-commit hooks and don't need manual installation if using pre-commit.

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

## Branch Naming Conventions

Use descriptive branch names that follow these patterns:

- **`feature/`** - New features or enhancements
  - Example: `feature/add-netbox-export`
  - Example: `feature/terraform-aws-module`

- **`fix/`** - Bug fixes
  - Example: `fix/bootstrap-osx-detection`
  - Example: `fix/terraform-state-lock`

- **`chore/`** - Maintenance tasks, dependency updates, documentation
  - Example: `chore/update-dependencies`
  - Example: `chore/docs-module-usage`

- **`refactor/`** - Code refactoring without changing functionality
  - Example: `refactor/netbox-client-structure`

- **`docs/`** - Documentation-only changes
  - Example: `docs/contributing-guidelines`

**Branch Naming Tips:**
- Use lowercase and hyphens (kebab-case)
- Keep names concise but descriptive
- Avoid special characters except hyphens and slashes

## Commit Message Format

This repository follows [Conventional Commits](https://www.conventionalcommits.org/) specification for clear and structured commit messages.

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes only
- **chore**: Maintenance tasks, dependency updates
- **refactor**: Code changes that neither fix bugs nor add features
- **test**: Adding or updating tests
- **ci**: Changes to CI/CD configuration
- **perf**: Performance improvements
- **style**: Code style changes (formatting, missing semicolons, etc.)

### Scope

The scope should indicate the area of the codebase affected:
- `netbox` - NetBox client scripts and tools
- `terraform` - Terraform configurations
- `bootstrap` - Bootstrap and setup scripts
- `docs` - Documentation
- `ci` - CI/CD workflows
- `deps` - Dependencies

### Examples

```bash
# Feature addition
feat(netbox): add script for prefix export

# Bug fix
fix(bootstrap): fix OS X detection bug in install script

# Documentation update
chore(docs): update module usage instructions

# Dependency update
chore(deps): upgrade terraform to v1.7.0

# Refactoring
refactor(terraform): restructure module directory layout
```

### Best Practices

- Use the imperative mood in the subject line ("add" not "added")
- Don't capitalize the first letter of the subject
- No period at the end of the subject line
- Limit the subject line to 50 characters
- Wrap the body at 72 characters
- Use the body to explain *what* and *why* vs. *how*

## Pull Request Workflow

### Creating a Pull Request

1. **Ensure your branch is up to date:**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Push your branch:**
   ```bash
   git push origin your-branch
   ```

3. **Open a Pull Request on GitHub:**
   - Provide a clear, descriptive title following commit conventions
   - Fill out the PR description with:
     - Summary of changes
     - Related issue numbers (e.g., "Fixes #123")
     - Testing performed
     - Screenshots (if UI changes)
     - Any breaking changes or migration notes

### PR Requirements

- ✅ All pre-commit hooks must pass
- ✅ Code follows established style guidelines
- ✅ Documentation is updated (if applicable)
- ✅ Commit messages follow Conventional Commits format
- ✅ Branch name follows naming conventions
- ✅ No merge conflicts with the base branch

### Review Process

1. **Automated Checks:**
   - Pre-commit hooks validate code style and quality
   - CI/CD pipelines run (if configured)
   - All checks must pass before review

2. **Code Review:**
   - At least one approval from a maintainer is required
   - Reviewers will check:
     - Code quality and correctness
     - Adherence to project standards
     - Security considerations
     - Documentation completeness

3. **Addressing Feedback:**
   - Make requested changes in new commits
   - Push changes to the same branch
   - Respond to comments with explanations or confirmations
   - Mark conversations as resolved once addressed

4. **Merging:**
   - Maintainers will merge approved PRs
   - Squash merging is preferred for clean history
   - Delete your branch after merging

### Branch Protection

The `main` branch is protected with the following rules:

- Direct pushes are not allowed
- Pull requests require at least one approval
- Status checks must pass before merging
- Branches must be up to date before merging

## GitHub Copilot Usage

This repository is designed to work seamlessly with GitHub Copilot and GitHub Copilot Workspace. Here's how Copilot is expected to be used:

### What Copilot Handles Well

- **Code Generation:** Generating boilerplate Terraform modules, Python scripts, and configuration files
- **Documentation:** Writing and updating README files, inline comments, and docstrings
- **Test Creation:** Suggesting test cases and test code
- **Refactoring:** Suggesting improvements and modernizing code patterns
- **Debugging:** Helping identify and fix issues in existing code

### Copilot Best Practices

1. **Review AI-Generated Code:**
   - Always review code suggestions carefully
   - Ensure generated code follows project conventions
   - Verify security implications of suggested changes

2. **Use Context Effectively:**
   - Keep relevant files open to provide Copilot with context
   - Reference existing patterns in the codebase
   - Use descriptive comments to guide Copilot's suggestions

3. **Pre-commit Validation:**
   - All Copilot-generated code must pass pre-commit hooks
   - Run `pre-commit run --all-files` before committing
   - Fix any style or linting issues

4. **Security Considerations:**
   - Never commit API keys, passwords, or sensitive data
   - Review Copilot suggestions for security vulnerabilities
   - The `detect-aws-credentials` hook will catch some issues, but manual review is essential

5. **Copilot Workspace Integration:**
   - Copilot Workspace can help plan and implement larger features
   - Use it to break down complex tasks into smaller changes
   - Review the generated plan before executing

### When to Override Copilot

- When suggestions don't match existing project patterns
- When generated code has security implications
- When simpler, more maintainable solutions exist
- When Copilot suggests outdated or deprecated approaches

Remember: Copilot is a tool to enhance productivity, not a replacement for thoughtful engineering. Always apply critical thinking and code review practices.

## Making Changes

1. **Create a branch following the naming convention:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   # or
   git checkout -b chore/your-maintenance-task
   ```

2. **Make your changes:**
   - Write clear, focused commits
   - Follow the code standards for the language you're working in
   - Test your changes thoroughly
   - Ensure pre-commit hooks pass

3. **Commit your changes using Conventional Commits format:**
   ```bash
   git add .
   git commit -m "feat(scope): add new feature"
   ```

   Pre-commit hooks will run automatically. If they fail, fix the issues and commit again.

4. **Push your changes:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request:**
   - Follow the pull request workflow outlined above
   - Provide a clear description of your changes
   - Reference any related issues
   - Wait for review and address feedback

## Questions or Issues?

If you have questions or run into issues:

1. Check existing issues on GitHub
2. Review the documentation in README.md
3. Open a new issue with details about your question or problem

Thank you for contributing!
