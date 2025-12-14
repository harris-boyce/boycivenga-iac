# Contributing to Boycivenga IaC

Thank you for your interest in contributing to the Boycivenga IaC project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

This project follows a standard code of conduct. Be respectful, professional, and considerate in all interactions.

## Getting Started

### Prerequisites

- Terraform >= 1.6.0
- Git
- Docker (for DevContainer)
- Access to a UniFi Controller (for testing)

### Setup Development Environment

#### Option 1: DevContainer (Recommended)

1. Install prerequisites:
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. Clone and open:
   ```bash
   git clone https://github.com/harris-boyce/boycivenga-iac.git
   cd boycivenga-iac
   code .
   ```

3. Reopen in container:
   - Press F1
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build

4. The development environment is ready with all tools pre-installed!

#### Option 2: Manual Setup

1. Install Terraform:
   ```bash
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. Install development tools:
   ```bash
   # Install pre-commit
   pip install pre-commit

   # Install tflint
   curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

   # Install tfsec
   curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

   # Install checkov
   pip install checkov

   # Install terraform-docs
   curl -Lo ./terraform-docs.tar.gz https://github.com/terraform-docs/terraform-docs/releases/download/v0.17.0/terraform-docs-v0.17.0-linux-amd64.tar.gz
   tar -xzf terraform-docs.tar.gz
   sudo mv terraform-docs /usr/local/bin/
   ```

3. Setup pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Your Changes

- Follow the code style guidelines
- Add tests if applicable
- Update documentation as needed
- Keep commits atomic and focused

### 3. Test Your Changes

```bash
# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Run linters
tflint --recursive
tfsec .
checkov -d .

# Test in a specific environment
cd environments/site-primary
terraform init
terraform plan
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature"
```

See [Commit Message Guidelines](#commit-message-guidelines) below.

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style Guidelines

### Terraform Style

1. **Formatting**: Use `terraform fmt -recursive` to format all files
2. **Naming Conventions**:
   - Resources: Use descriptive names with underscores (e.g., `unifi_network_management`)
   - Variables: Use lowercase with underscores (e.g., `unifi_api_url`)
   - Outputs: Use descriptive names indicating what they represent

3. **File Organization**:
   ```
   module/
   ├── main.tf          # Main resource definitions
   ├── variables.tf     # Input variables
   ├── outputs.tf       # Output values
   ├── versions.tf      # Terraform and provider versions
   └── README.md        # Module documentation
   ```

4. **Resource Blocks**:
   ```hcl
   resource "provider_resource" "name" {
     # Required arguments first
     name = "example"

     # Optional arguments
     description = "Example resource"

     # Nested blocks last
     lifecycle {
       create_before_destroy = true
     }
   }
   ```

5. **Variables**:
   ```hcl
   variable "example" {
     description = "Clear description of the variable"
     type        = string
     default     = "default-value"  # If applicable

     validation {
       condition     = length(var.example) > 0
       error_message = "Example cannot be empty."
     }
   }
   ```

6. **Comments**:
   - Use `#` for single-line comments
   - Add comments for complex logic
   - Document why, not what (code should be self-documenting)

### Documentation Style

1. **Module READMEs**:
   - Include usage examples
   - Document all inputs and outputs
   - Add requirements section
   - Include notes about limitations or special considerations

2. **Code Comments**:
   - Use clear, concise language
   - Explain complex logic or non-obvious decisions
   - Keep comments up-to-date with code changes

## Testing

### Pre-deployment Testing

1. **Syntax Validation**:
   ```bash
   terraform validate
   ```

2. **Linting**:
   ```bash
   tflint --recursive --config .tflint.hcl
   ```

3. **Security Scanning**:
   ```bash
   tfsec . --minimum-severity MEDIUM
   checkov -d . --framework terraform
   ```

4. **Plan Review**:
   ```bash
   cd environments/site-primary
   terraform init
   terraform plan
   ```

### Testing Checklist

- [ ] Code is formatted (`terraform fmt`)
- [ ] Code validates (`terraform validate`)
- [ ] Linting passes (`tflint`)
- [ ] Security scans pass (`tfsec`, `checkov`)
- [ ] Plan generates successfully
- [ ] Documentation is updated
- [ ] Examples are provided (if applicable)

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Update documentation
3. Rebase on latest main branch
4. Ensure pre-commit hooks pass

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

1. Automated checks run (GitHub Actions)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

### What to Expect

- **Initial Response**: Within 48 hours
- **Review Time**: Varies based on complexity
- **Feedback**: Constructive comments to improve code
- **Merge**: After approval and passing checks

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Examples

```bash
feat(ubiquiti): add support for port forwarding rules

Add port forwarding configuration to the Ubiquiti module.
Includes variables for destination IP and port mapping.

Closes #123
```

```bash
fix(homebridge): correct VM memory allocation

The VM was using incorrect memory units. Changed from bytes to MB.
```

```bash
docs: update README with new module examples

Add examples for the automation module and improve
quick start instructions.
```

### Scope

The scope should indicate which part of the codebase is affected:
- `ubiquiti` - Ubiquiti module
- `homebridge` - Homebridge module
- `automation` - Automation module
- `ci` - CI/CD workflows
- `docs` - Documentation
- `devcontainer` - DevContainer configuration

## Module Development

### Creating a New Module

1. Create module directory:
   ```bash
   mkdir terraform/modules/my-module
   cd terraform/modules/my-module
   ```

2. Create required files:
   ```bash
   touch main.tf variables.tf outputs.tf versions.tf README.md
   ```

3. Follow the standard structure:
   - `versions.tf`: Define Terraform and provider versions
   - `variables.tf`: Define input variables with descriptions
   - `main.tf`: Implement module logic
   - `outputs.tf`: Define outputs with descriptions
   - `README.md`: Document usage and examples

4. Add validation:
   ```hcl
   variable "example" {
     description = "Example variable"
     type        = string

     validation {
       condition     = can(regex("^[a-z-]+$", var.example))
       error_message = "Example must contain only lowercase letters and hyphens."
     }
   }
   ```

5. Document thoroughly:
   - Usage examples
   - Input/output descriptions
   - Requirements
   - Limitations

## Security Considerations

### Sensitive Data

- **Never commit** sensitive data:
  - Passwords
  - API keys
  - Private keys
  - Certificates
  - `terraform.tfvars` files

- Use variables and mark as sensitive:
  ```hcl
  variable "password" {
    description = "Password for authentication"
    type        = string
    sensitive   = true
  }
  ```

### Security Scanning

All PRs are automatically scanned for:
- Hardcoded secrets
- Security vulnerabilities
- Compliance violations

Fix any issues before requesting review.

## Getting Help

### Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [UniFi Provider Documentation](https://registry.terraform.io/providers/paultyng/unifi/latest/docs)
- [Project Issues](https://github.com/harris-boyce/boycivenga-iac/issues)
- [Project Discussions](https://github.com/harris-boyce/boycivenga-iac/discussions)

### Contact

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Tag maintainers for urgent matters

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Boycivenga IaC! 🎉
