# Quick Start Guide

Get up and running with Boycivenga IaC in minutes!

## Prerequisites

- Git
- Docker Desktop (for DevContainer) OR Terraform CLI
- GitHub account
- Access to UniFi Controller

## Option 1: DevContainer (Recommended)

### 1. Clone and Open

```bash
git clone https://github.com/harris-boyce/boycivenga-iac.git
cd boycivenga-iac
code .
```

### 2. Reopen in Container

- Press `F1` or `Ctrl+Shift+P`
- Select "Dev Containers: Reopen in Container"
- Wait for container to build (first time only)

### 3. You're Ready!

All tools are pre-installed:
- ✅ Terraform 1.6+
- ✅ tflint, tfsec, checkov
- ✅ pre-commit hooks
- ✅ GitHub CLI

## Option 2: Local Setup

### 1. Install Terraform

**macOS**:
```bash
brew install terraform
```

**Linux**:
```bash
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Windows**:
```powershell
choco install terraform
```

### 2. Install Tools

```bash
# Pre-commit
pip install pre-commit

# tflint
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# tfsec
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash
```

### 3. Clone Repository

```bash
git clone https://github.com/harris-boyce/boycivenga-iac.git
cd boycivenga-iac
```

### 4. Setup Pre-commit

```bash
pre-commit install
```

## Configure Your Environment

### 1. Choose Your Site

```bash
cd environments/site-primary
```

### 2. Create Variables File

```bash
cp terraform.tfvars.example terraform.tfvars
```

### 3. Edit Configuration

Edit `terraform.tfvars` with your values:

```hcl
unifi_api_url = "https://your-unifi-controller.local:8443"
unifi_username = "admin"
unifi_password = "your-password"

wifi_password       = "your-wifi-password"
guest_wifi_password = "your-guest-password"
```

⚠️ **Important**: Never commit `terraform.tfvars` to Git!

## Deploy Your Infrastructure

### 1. Initialize Terraform

```bash
terraform init
```

### 2. Review Plan

```bash
terraform plan
```

This shows what Terraform will create/modify.

### 3. Apply Changes

```bash
terraform apply
```

Type `yes` when prompted.

### 4. View Outputs

```bash
terraform output
```

## Common Commands

### Using Make (Recommended)

```bash
# See all available commands
make help

# Format code
make fmt

# Validate configuration
make validate

# Run linters
make lint

# Run security scans
make security

# Plan changes
make plan-primary

# Apply changes
make apply-primary
```

### Using Terraform Directly

```bash
# Format
terraform fmt -recursive

# Validate
terraform validate

# Plan
terraform plan

# Apply
terraform apply

# Show state
terraform show

# List resources
terraform state list
```

## Making Changes

### 1. Create Branch

```bash
git checkout -b feature/my-change
```

### 2. Edit Configuration

Edit files in `environments/site-primary/` or modules in `terraform/modules/`

### 3. Test Locally

```bash
make test
# or
terraform plan
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: description of change"
git push origin feature/my-change
```

### 5. Create Pull Request

1. Go to GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out PR template
5. Submit for review

## GitHub Actions

### PR Workflow (Automatic)

When you open a PR:
1. ✅ Format check
2. ✅ Validation
3. ✅ Security scan
4. ✅ Terraform plan
5. 💬 Plan posted as comment

### Apply Workflow (Manual)

To deploy:
1. Go to Actions tab
2. Select "Terraform Apply"
3. Click "Run workflow"
4. Select environment
5. Confirm deployment

## Troubleshooting

### "terraform: command not found"

**Solution**: Install Terraform (see above)

### "Authentication failed"

**Solution**: Check your UniFi Controller credentials in `terraform.tfvars`

### "State lock error"

**Solution**:
```bash
terraform force-unlock <LOCK_ID>
```

### "Module not found"

**Solution**:
```bash
terraform init
```

## Next Steps

### Customize Network

Edit `environments/site-primary/site.tf`:

```hcl
module "ubiquiti" {
  # ... existing config ...

  networks = [
    # Add your networks
    {
      name         = "MyNetwork"
      purpose      = "corporate"
      vlan_id      = 40
      subnet       = "10.10.40.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.10.40.100"
      dhcp_stop    = "10.10.40.254"
    }
  ]
}
```

### Add Automations

```hcl
module "automation" {
  # ... existing config ...

  automations = [
    {
      name        = "my-automation"
      description = "My custom automation"
      trigger = {
        platform = "time"
        at       = "08:00:00"
      }
      action = {
        service = "light.turn_on"
        target = {
          entity_id = "light.my_light"
        }
      }
      enabled = true
    }
  ]
}
```

### Add Second Site

```bash
# Copy primary site config
cp -r environments/site-primary environments/site-new

# Update configuration
cd environments/site-new
vim site.tf  # Update site-specific settings
vim terraform.tfvars.example
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Add your credentials
```

## Getting Help

- 📖 [Full Documentation](README.md)
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md)
- 🌐 [Network Design](docs/NETWORK.md)
- 📚 [Runbook](docs/RUNBOOK.md)
- 🤝 [Contributing](CONTRIBUTING.md)

### Support Channels

- [Issues](https://github.com/harris-boyce/boycivenga-iac/issues) - Bug reports
- [Discussions](https://github.com/harris-boyce/boycivenga-iac/discussions) - Questions

## Best Practices

### ✅ Do

- Use DevContainer for consistent environment
- Run `terraform plan` before `apply`
- Commit small, focused changes
- Write descriptive commit messages
- Test in site-primary before site-secondary
- Back up state files regularly
- Use pre-commit hooks

### ❌ Don't

- Commit `terraform.tfvars` files
- Commit secrets or passwords
- Apply changes without planning
- Work directly in production
- Skip validation and linting
- Force-unlock without investigation

## Security Tips

1. **Use Strong Passwords**: For WiFi and controller access
2. **Rotate Credentials**: Change passwords regularly
3. **Enable MFA**: On UniFi Controller if available
4. **Review Firewall Rules**: Before applying
5. **Monitor Logs**: Check GitHub Actions logs
6. **Limit Access**: Use GitHub branch protection

## Performance Tips

1. **Use Workspaces**: For multiple environments (future)
2. **Target Specific Resources**: `terraform plan -target=module.ubiquiti`
3. **Parallel Execution**: Terraform handles this automatically
4. **Cache Providers**: `.terraform` directory

## Maintenance

### Weekly

```bash
# Check for security issues
make security

# Update documentation
# Review and test changes
```

### Monthly

```bash
# Update provider versions
terraform init -upgrade

# Test updates
terraform plan
```

### Quarterly

```bash
# Review all configurations
# Audit access controls
# Test disaster recovery
```

## Cheat Sheet

```bash
# Quick commands
make help              # Show all make targets
make test              # Run all tests
make fmt               # Format code
make validate          # Validate configs
make lint              # Run linters
make security          # Security scan

# Terraform essentials
terraform init         # Initialize
terraform plan         # Preview changes
terraform apply        # Apply changes
terraform destroy      # Destroy resources (careful!)
terraform fmt          # Format files
terraform validate     # Validate syntax
terraform show         # Show current state
terraform output       # Show outputs

# Git workflow
git status             # Check status
git add .              # Stage all changes
git commit -m "msg"    # Commit with message
git push               # Push to remote
git pull               # Pull from remote
```

---

**Ready to deploy?** Start with [Option 1: DevContainer](#option-1-devcontainer-recommended) above!

🎉 Happy Infrastructure as Coding!
