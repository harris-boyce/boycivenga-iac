# Boycivenga IaC

Infrastructure as Code (IaC) repository for managing multi-site home network lab with Ubiquiti equipment, smart home automations, and homebridge configuration.

[![Terraform](https://img.shields.io/badge/Terraform-1.6+-623CE4?logo=terraform)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🏗️ Architecture Overview

This repository manages infrastructure across multiple sites using a modular Terraform approach:

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                     │
│              (Self-hosted runners + Attestation)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Terraform Configuration                    │
├─────────────────────────────────────────────────────────────┤
│  Environments:                                               │
│  ├── site-primary/    (Primary home/lab)                    │
│  └── site-secondary/  (Secondary location)                  │
│                                                              │
│  Modules:                                                    │
│  ├── ubiquiti/        (Network, VLANs, WiFi, Firewall)     │
│  ├── homebridge/      (HomeKit integration VM)              │
│  └── automation/      (Smart home automations)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Physical Infrastructure                   │
├─────────────────────────────────────────────────────────────┤
│  • Ubiquiti Network Equipment (USG, Switch, AP)             │
│  • Homebridge VM (HomeKit bridge)                           │
│  • Smart Home Devices (IoT, sensors, etc.)                  │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

- **Multi-Site Support**: Manage multiple home/lab locations with separate configurations
- **Ubiquiti Management**: Automated configuration of UniFi networks, VLANs, WiFi, and firewall rules
- **Homebridge Integration**: VM provisioning and configuration for HomeKit bridge
- **Smart Home Automation**: Declarative automation rules, scripts, and scenes
- **CI/CD Pipeline**: GitHub Actions with self-hosted runners for secure deployments
- **Plan Attestation**: Build provenance attestation for Terraform plans
- **DevContainer**: Full development environment for easy onboarding
- **Security Scanning**: Automated tfsec and checkov security checks
- **Pre-commit Hooks**: Automated formatting, validation, and documentation

## 🚀 Quick Start

**New to this repository?** See the [Quick Start Guide](docs/QUICKSTART.md) for step-by-step instructions!

### Prerequisites

- Terraform >= 1.6.0
- Access to UniFi Controller
- (Optional) Docker for DevContainer

### Using DevContainer (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/harris-boyce/boycivenga-iac.git
   cd boycivenga-iac
   ```

2. Open in VS Code with DevContainer:
   - Install the "Dev Containers" extension
   - Open Command Palette (F1) and select "Dev Containers: Reopen in Container"
   - Wait for the container to build and initialize

3. The DevContainer includes all necessary tools:
   - Terraform & Terragrunt
   - tflint, tfsec, checkov
   - pre-commit hooks
   - GitHub CLI

### Manual Setup

1. Install dependencies:
   ```bash
   # Install Terraform
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/

   # Install pre-commit
   pip install pre-commit
   pre-commit install
   ```

2. Configure your environment:
   ```bash
   cd environments/site-primary
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your actual values
   ```

3. Initialize and apply:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## 📁 Repository Structure

```
.
├── .devcontainer/              # DevContainer configuration
│   ├── devcontainer.json
│   ├── Dockerfile
│   └── post-create.sh
├── .github/
│   └── workflows/              # GitHub Actions workflows
│       ├── terraform-plan.yml  # PR plan with attestation
│       ├── terraform-apply.yml # Manual apply workflow
│       └── pr-validation.yml   # Linting and validation
├── environments/               # Environment configurations
│   ├── site-primary/          # Primary site
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── site.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   └── site-secondary/        # Secondary site
│       └── ...
├── terraform/
│   └── modules/               # Reusable Terraform modules
│       ├── ubiquiti/         # UniFi network management
│       ├── homebridge/       # Homebridge VM configuration
│       └── automation/       # Smart home automations
├── docs/                      # Additional documentation
├── .pre-commit-config.yaml   # Pre-commit hooks
├── .tflint.hcl              # TFLint configuration
├── .editorconfig            # Editor configuration
├── README.md                # This file
└── CONTRIBUTING.md          # Contribution guidelines
```

## 🔧 Modules

### Ubiquiti Module

Manages UniFi network equipment:
- Networks and VLANs
- Wireless networks (WLANs)
- Firewall rules
- Port profiles for switches

[View Module Documentation](terraform/modules/ubiquiti/README.md)

### Homebridge Module

Provisions and configures Homebridge VM:
- VM configuration
- Plugin installation
- Configuration management
- Automated backups

[View Module Documentation](terraform/modules/homebridge/README.md)

### Automation Module

Manages smart home automations:
- Automation rules
- Scripts
- Scenes
- Entity groups
- Notification configurations

[View Module Documentation](terraform/modules/automation/README.md)

## 🔐 Security

### Secrets Management

- **Never commit** `terraform.tfvars` files
- Use environment variables for sensitive data:
  ```bash
  export TF_VAR_unifi_password="your-password"
  ```
- Consider using a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)

### Security Scanning

Automated security scans run on every PR:
- **tfsec**: Terraform security scanning
- **checkov**: Additional policy checks
- **tflint**: Terraform linting

### Plan Attestation

All Terraform plans are attested using GitHub's artifact attestation, providing:
- Build provenance
- Verification of plan integrity
- Audit trail for compliance

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

#### Terraform Plan (PR)
- Runs on every pull request
- Detects changed environments
- Generates and attests plans
- Posts plan summary to PR
- Runs security scans

#### Terraform Apply (Manual)
- Triggered manually via workflow dispatch
- Requires environment selection
- Optional manual approval gate
- Attests applied plans
- Retains artifacts for 90 days

#### PR Validation
- Lints all Terraform code
- Validates module configurations
- Checks documentation
- Runs markdown linting

### Self-Hosted Runners

This repository is configured for self-hosted runners for security and network access:

1. **Setup runner**:
   ```bash
   # On your runner host
   ./config.sh --url https://github.com/harris-boyce/boycivenga-iac --token YOUR_TOKEN
   ./run.sh
   ```

2. **Runner requirements**:
   - Network access to UniFi Controller
   - Terraform installed
   - Sufficient resources (2+ CPU, 4GB+ RAM)

### Migration to Terraform Cloud

The architecture supports future migration to Terraform Cloud:

1. Update backend configuration in `main.tf`:
   ```hcl
   terraform {
     backend "remote" {
       organization = "your-org"
       workspaces {
         prefix = "boycivenga-"
       }
     }
   }
   ```

2. Configure Terraform Cloud token:
   ```bash
   terraform login
   ```

3. Migrate state:
   ```bash
   terraform init -migrate-state
   ```

## 📚 Documentation

- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Architecture Documentation](docs/ARCHITECTURE.md) - Detailed architecture
- [Network Design](docs/NETWORK.md) - Network topology and design
- [Runbook](docs/RUNBOOK.md) - Operational procedures

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Development workflow
- Code style guidelines
- Testing requirements
- Pull request process

## 📝 Common Tasks

### Adding a New Site

1. Create new environment directory:
   ```bash
   cp -r environments/site-primary environments/site-new
   ```

2. Update configuration files with site-specific settings

3. Add to workflow options in `.github/workflows/terraform-apply.yml`

### Adding New Modules

1. Create module directory:
   ```bash
   mkdir terraform/modules/my-module
   cd terraform/modules/my-module
   ```

2. Create required files:
   - `main.tf` - Main configuration
   - `variables.tf` - Input variables
   - `outputs.tf` - Output values
   - `versions.tf` - Terraform and provider versions
   - `README.md` - Module documentation

3. Use the module in your environment configuration

### Running Security Scans Locally

```bash
# Run tfsec
tfsec .

# Run checkov
checkov -d .

# Run tflint
tflint --recursive
```

### Formatting Code

```bash
# Format all Terraform files
terraform fmt -recursive

# Or use pre-commit
pre-commit run --all-files
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Terraform plan fails with authentication error
```bash
# Solution: Verify UniFi credentials
curl -k https://your-unifi-controller:8443
```

**Issue**: Module not found
```bash
# Solution: Initialize Terraform
terraform init
```

**Issue**: State lock error
```bash
# Solution: Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

### Getting Help

- Check [documentation](docs/)
- Review [issues](https://github.com/harris-boyce/boycivenga-iac/issues)
- Ask in [discussions](https://github.com/harris-boyce/boycivenga-iac/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Terraform](https://www.terraform.io/)
- [UniFi Terraform Provider](https://github.com/paultyng/terraform-provider-unifi)
- [Homebridge](https://homebridge.io/)
- [GitHub Actions](https://github.com/features/actions)

## 📊 Status

![Terraform Plan](https://github.com/harris-boyce/boycivenga-iac/workflows/Terraform%20Plan/badge.svg)
![PR Validation](https://github.com/harris-boyce/boycivenga-iac/workflows/PR%20Validation/badge.svg)

---

**Note**: This is a home lab/network management repository. Adjust configurations to match your specific equipment and requirements.

