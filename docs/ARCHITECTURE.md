# Architecture Documentation

## Overview

The Boycivenga IaC repository is structured to manage multi-site home network infrastructure using Terraform. This document describes the architecture, design decisions, and component interactions.

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Developer/Operator                       │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ├─► DevContainer (Local Development)
                        │   ├─► Terraform
                        │   ├─► Linters & Validators
                        │   └─► Pre-commit Hooks
                        │
                        ├─► Git Push
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                      GitHub Repository                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              GitHub Actions Workflows                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • PR Validation                                       │  │
│  │  • Terraform Plan (with attestation)                   │  │
│  │  • Terraform Apply (manual trigger)                    │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                   Self-Hosted Runner                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  • Network access to infrastructure                    │  │
│  │  • Terraform execution environment                     │  │
│  │  • Security scanning tools                            │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   UniFi      │ │  Homebridge  │ │  Smart Home  │
│  Controller  │ │      VM      │ │   Platform   │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────────────────────────────────────────┐
│          Physical Infrastructure                  │
│  • Network switches                              │
│  • Access points                                 │
│  • IoT devices                                   │
│  • Smart home devices                            │
└──────────────────────────────────────────────────┘
```

## Directory Structure

### Repository Layout

```
boycivenga-iac/
│
├── .devcontainer/           # Development container configuration
│   ├── devcontainer.json   # Container definition
│   ├── Dockerfile          # Container image
│   └── post-create.sh      # Post-creation setup script
│
├── .github/
│   └── workflows/          # CI/CD pipeline definitions
│       ├── terraform-plan.yml     # Plan generation & attestation
│       ├── terraform-apply.yml    # Infrastructure deployment
│       └── pr-validation.yml      # Code quality checks
│
├── environments/           # Environment-specific configurations
│   ├── site-primary/      # Primary site configuration
│   │   ├── main.tf        # Provider and backend config
│   │   ├── variables.tf   # Input variables
│   │   ├── site.tf        # Site-specific resources
│   │   ├── outputs.tf     # Output values
│   │   └── terraform.tfvars.example
│   │
│   └── site-secondary/    # Secondary site configuration
│       └── ...
│
├── terraform/
│   └── modules/           # Reusable Terraform modules
│       ├── ubiquiti/     # UniFi network management
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   ├── versions.tf
│       │   └── README.md
│       │
│       ├── homebridge/   # Homebridge VM management
│       │   └── ...
│       │
│       └── automation/   # Smart home automations
│           └── ...
│
├── docs/                 # Additional documentation
│   ├── ARCHITECTURE.md  # This file
│   ├── NETWORK.md       # Network design
│   └── RUNBOOK.md       # Operational procedures
│
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .tflint.hcl             # TFLint configuration
├── .editorconfig           # Editor settings
├── .gitignore             # Git ignore patterns
├── README.md              # Project overview
└── CONTRIBUTING.md        # Contribution guidelines
```

## Design Patterns

### 1. Module-Based Architecture

**Pattern**: Each logical component (Ubiquiti, Homebridge, Automation) is implemented as a separate, reusable Terraform module.

**Benefits**:
- Modularity and reusability
- Separation of concerns
- Easier testing and maintenance
- Clear interfaces via variables and outputs

**Example**:
```hcl
module "ubiquiti" {
  source = "../../terraform/modules/ubiquiti"

  unifi_api_url  = var.unifi_api_url
  unifi_username = var.unifi_username
  unifi_password = var.unifi_password

  networks = var.networks
  wlans    = var.wlans
}
```

### 2. Environment Separation

**Pattern**: Each site/environment has its own directory with dedicated state and configuration.

**Benefits**:
- Blast radius limitation
- Independent deployment cycles
- Site-specific customization
- Clear ownership and responsibility

**Implementation**:
- `environments/site-primary/` for primary location
- `environments/site-secondary/` for secondary location
- Each with separate state files

### 3. GitOps Workflow

**Pattern**: Infrastructure changes are made via Git commits and pull requests.

**Benefits**:
- Version control for infrastructure
- Peer review process
- Audit trail
- Rollback capability

**Flow**:
1. Developer creates feature branch
2. Makes infrastructure changes
3. Opens pull request
4. Automated validation runs
5. Peer review
6. Merge to main
7. Manual deployment via workflow dispatch

### 4. Immutable Plans with Attestation

**Pattern**: Terraform plans are generated, attested, and stored as artifacts before apply.

**Benefits**:
- Verification of plan integrity
- Compliance and audit requirements
- Supply chain security
- Drift detection

**Implementation**:
```yaml
- name: Terraform Plan
  run: terraform plan -out=tfplan.binary

- name: Attest Terraform Plan
  uses: actions/attest-build-provenance@v1
  with:
    subject-path: tfplan.binary
```

## Component Details

### Ubiquiti Module

**Purpose**: Manage UniFi network infrastructure.

**Resources Managed**:
- Networks and VLANs
- Wireless networks (WLANs)
- Firewall rules
- Port profiles

**Provider**: `paultyng/unifi`

**Key Features**:
- Dynamic network creation based on variable lists
- VLAN-aware port profiles
- Firewall rule ordering and management
- Guest network support

### Homebridge Module

**Purpose**: Provision and configure Homebridge VM for HomeKit integration.

**Resources Managed**:
- Virtual machine configuration
- Homebridge installation and setup
- Plugin management
- Backup configuration

**Provider**: Placeholder (customizable for your hypervisor)

**Key Features**:
- Automated installation script
- Plugin management
- Configuration templating
- Backup scheduling

### Automation Module

**Purpose**: Manage smart home automations declaratively.

**Resources Managed**:
- Automation rules
- Scripts
- Scenes
- Entity groups
- Notifications

**Provider**: Placeholder (for Home Assistant, Node-RED, etc.)

**Key Features**:
- Declarative automation definition
- Multiple platform support
- Integration with various services
- Version-controlled automations

## CI/CD Pipeline

### Workflow: Terraform Plan

**Trigger**: Pull request to main branch

**Steps**:
1. Detect changed environments
2. For each changed environment:
   - Format check
   - Initialize Terraform
   - Validate configuration
   - Generate plan
   - Attest plan
   - Upload artifacts
   - Comment on PR

**Security**:
- Read-only access to repository
- Plan artifacts are attested
- Security scanning with tfsec

### Workflow: Terraform Apply

**Trigger**: Manual workflow dispatch

**Steps**:
1. Select environment
2. Generate fresh plan
3. Attest plan
4. Optional manual approval
5. Apply plan
6. Upload artifacts
7. Generate summary

**Security**:
- Requires write access (protected)
- Manual approval gate (optional)
- Artifacts retained for audit

### Workflow: PR Validation

**Trigger**: Pull request

**Steps**:
1. Format check
2. Lint with tflint
3. Security scan with tfsec
4. Validate modules
5. Check documentation

**Purpose**: Ensure code quality before plan generation

## State Management

### Current: Local Backend

**Configuration**:
```hcl
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
```

**Pros**:
- Simple setup
- No external dependencies
- Full control

**Cons**:
- No collaboration features
- Manual state management
- No remote locking

### Future: Terraform Cloud

**Migration Path**:
1. Update backend configuration
2. Authenticate with Terraform Cloud
3. Run migration: `terraform init -migrate-state`
4. Update CI/CD workflows

**Benefits**:
- Remote state storage
- State locking
- Collaboration features
- Sentinel policy enforcement
- Cost estimation

## Security Architecture

### Secrets Management

**Current Approach**:
- Sensitive variables marked with `sensitive = true`
- Credentials stored in `terraform.tfvars` (not committed)
- GitHub Secrets for CI/CD

**Best Practices**:
- Never commit sensitive data
- Use environment variables
- Consider external secrets manager (Vault, AWS Secrets Manager)

### Network Security

**Self-Hosted Runner**:
- Runs inside trusted network
- Direct access to UniFi Controller
- No exposure of credentials to GitHub

**Firewall Rules**:
- Network segmentation (VLANs)
- IoT isolation from management network
- Guest network isolation

### Compliance

**Attestation**:
- All plans are attested
- Build provenance tracked
- Audit trail maintained

**Scanning**:
- tfsec for security issues
- checkov for policy compliance
- Pre-commit hooks for prevention

## Scalability Considerations

### Adding New Sites

1. Copy environment template
2. Update site-specific variables
3. Adjust network ranges to avoid conflicts
4. Add to workflow dispatch options

### Adding New Modules

1. Create module directory structure
2. Define variables, resources, outputs
3. Document usage and examples
4. Reference from environment configurations

### Multi-Region Support

**Future Consideration**:
- Regional UniFi Controllers
- Site-to-site VPN configuration
- Distributed Homebridge instances
- Regional automation platforms

## Disaster Recovery

### State Backups

**Recommendation**:
- Regular backups of `.tfstate` files
- Version control of configuration
- Documented recovery procedures

### Recovery Process

1. Restore state file from backup
2. Verify infrastructure status
3. Run `terraform plan` to check drift
4. Apply corrections if needed

### Documentation

See [RUNBOOK.md](RUNBOOK.md) for detailed recovery procedures.

## Performance Considerations

### Plan Generation

- Parallel execution where possible
- Targeted plans for changed environments only
- Caching of provider plugins

### Resource Management

- Batch operations where supported
- Use of `depends_on` for ordering
- Minimize API calls with data sources

## Monitoring and Observability

### Current State

- GitHub Actions workflow status
- Plan/apply logs in artifacts
- Manual monitoring of infrastructure

### Future Enhancements

- Terraform Cloud for insights
- Infrastructure monitoring (Prometheus, etc.)
- Alerting on drift detection
- Cost tracking and optimization

## Technology Stack

### Infrastructure as Code

- **Terraform** >= 1.6.0: Infrastructure provisioning
- **HCL**: Configuration language

### Providers

- **paultyng/unifi**: UniFi network management
- **null**: Placeholder for custom providers

### CI/CD

- **GitHub Actions**: Automation platform
- **Self-hosted runners**: Execution environment

### Development Tools

- **pre-commit**: Git hook framework
- **tflint**: Terraform linter
- **tfsec**: Security scanner
- **checkov**: Policy compliance checker
- **terraform-docs**: Documentation generator

### Container

- **DevContainer**: Development environment
- **Docker**: Container runtime

## Design Decisions

### Why Self-Hosted Runners?

**Decision**: Use self-hosted runners instead of GitHub-hosted.

**Reasoning**:
- Network access to internal infrastructure (UniFi Controller)
- Security: credentials don't leave network
- Performance: faster access to resources

**Trade-offs**:
- Maintenance overhead
- Infrastructure cost
- Setup complexity

### Why Local Backend Initially?

**Decision**: Start with local backend, plan migration to Terraform Cloud.

**Reasoning**:
- Simplicity for initial setup
- No additional dependencies
- Easy to migrate later

**Migration Path**: Documented and planned for future.

### Why Module-Based Structure?

**Decision**: Separate modules for each component type.

**Reasoning**:
- Reusability across environments
- Clear separation of concerns
- Easier testing and validation
- Better organization

**Alternative Considered**: Monolithic configuration (rejected due to complexity).

## Future Enhancements

### Planned

- [ ] Terraform Cloud integration
- [ ] Enhanced monitoring and alerting
- [ ] Automated drift detection
- [ ] Cost optimization tooling
- [ ] Multi-region support

### Under Consideration

- [ ] Terratest for module testing
- [ ] OPA/Sentinel policies
- [ ] Custom provider development
- [ ] GitLab CI/CD support

## Conclusion

This architecture provides a solid foundation for managing multi-site home network infrastructure. It's designed to be:

- **Scalable**: Easy to add new sites and components
- **Secure**: Multiple layers of security controls
- **Maintainable**: Clear structure and documentation
- **Reliable**: Automated testing and validation
- **Flexible**: Easy to customize and extend

For questions or suggestions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
