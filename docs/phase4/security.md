# Security & Authority Boundaries

## Overview

This document explicitly defines the security boundaries, authority boundaries, and prohibition boundaries for this infrastructure-as-code repository. Understanding these boundaries is critical for maintaining the integrity and security of the infrastructure pipeline.

**Last Updated**: Phase 4  
**Status**: Active and Enforced

## Table of Contents

- [Authority Boundaries](#authority-boundaries)
- [Execution Boundaries](#execution-boundaries)
- [Security Boundaries](#security-boundaries)
- [Prohibition Boundaries](#prohibition-boundaries)
- [Enforcement Mechanisms](#enforcement-mechanisms)
- [Consequences of Violations](#consequences-of-violations)

---

## Authority Boundaries

### NetBox is the Authoritative Source of Intent

**Statement**: **NetBox is the sole authoritative source of network infrastructure intent. Terraform is NOT an authority for intent.**

#### What This Means

- ✅ **NetBox defines WHAT infrastructure should exist** (VLANs, subnets, devices, configurations)
- ✅ **Terraform implements HOW to deploy** what NetBox defines
- ✅ All infrastructure changes MUST originate from NetBox data
- ❌ Terraform configurations MUST NOT define intent independently
- ❌ Manual Terraform variable files are NOT authoritative
- ❌ Local overrides of NetBox data are NOT permitted

#### Rationale

NetBox serves as the authoritative source because:

1. **Single Source of Truth**: Centralizes network intent in one system
2. **Human Review**: NetBox changes go through review and approval processes
3. **Audit Trail**: NetBox maintains comprehensive change logs
4. **Access Control**: NetBox has RBAC and authentication mechanisms
5. **Data Integrity**: NetBox validates data consistency and relationships

#### Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                      AUTHORITY FLOW                          │
└──────────────────────────────────────────────────────────────┘

  ┌────────────┐
  │  NetBox    │  ◄─── AUTHORITATIVE SOURCE
  │  (Intent)  │       (What should exist)
  └─────┬──────┘
        │
        │ Export via API
        │ (Read-only)
        ▼
  ┌────────────────┐
  │ Render Pipeline│  ◄─── TRANSLATOR
  │ (GitHub Actions│       (Convert intent to configs)
  └─────┬──────────┘
        │
        │ Generate
        │ Attest
        ▼
  ┌───────────────┐
  │  Artifacts    │  ◄─── IMPLEMENTATION DATA
  │  (tfvars)     │       (How to deploy)
  └─────┬─────────┘
        │
        │ Consume
        │ (Attested only)
        ▼
  ┌───────────────┐
  │  Terraform    │  ◄─── DEPLOYMENT TOOL
  │  (Plan/Apply) │       (Execute deployment)
  └───────────────┘
        │
        │ Apply to
        ▼
  ┌───────────────┐
  │ Infrastructure│  ◄─── REALIZED STATE
  │ (UniFi, etc.) │       (Actual systems)
  └───────────────┘
```

#### Examples

**✅ CORRECT: Intent from NetBox**
```yaml
# In NetBox:
# - Define VLAN 100 "Management"
# - Assign subnet 10.0.100.0/24
# - Set VLAN to site "Pennington"

# Render pipeline generates:
# site-pennington.tfvars.json
{
  "vlans": [
    {
      "id": 100,
      "name": "Management",
      "subnet": "10.0.100.0/24"
    }
  ]
}
```

**❌ INCORRECT: Intent in Terraform**
```hcl
# DO NOT DO THIS:
# Defining intent directly in Terraform bypasses NetBox authority

variable "management_vlan" {
  default = {
    id     = 100
    name   = "Management"
    subnet = "10.0.100.0/24"
  }
}
```

### Terraform's Role: Implementation, Not Authority

**Terraform's Responsibility**:
- ✅ Accept attested artifacts from the render pipeline
- ✅ Translate artifacts into infrastructure API calls
- ✅ Validate configurations against provider schemas
- ✅ Execute deployment plans
- ✅ Report deployment status and drift

**Terraform is NOT Responsible For**:
- ❌ Defining what infrastructure should exist
- ❌ Making decisions about network design
- ❌ Overriding NetBox intent
- ❌ Creating configurations independently
- ❌ Being a source of truth for infrastructure state

---

## Execution Boundaries

### Only GitHub Actions May Execute Plan Jobs

**Statement**: **Terraform plan operations MUST ONLY be executed by GitHub Actions workflows. Manual, local, or ad-hoc execution is PROHIBITED.**

#### What This Means

- ✅ **GitHub Actions workflows** are the ONLY permitted execution environment for Terraform plan
- ✅ Workflows run on GitHub-hosted or self-hosted runners managed by GitHub Actions
- ✅ All Terraform operations are audited via GitHub Actions logs
- ❌ **Local workstations** MUST NOT run Terraform plan
- ❌ **Manual CLI execution** is PROHIBITED
- ❌ **CI/CD systems other than GitHub Actions** are PROHIBITED

#### Rationale

Restricting execution to GitHub Actions provides:

1. **Audit Trail**: Complete logs of all Terraform operations
2. **Access Control**: GitHub repository permissions control who can trigger workflows
3. **Attestation Enforcement**: Workflows enforce artifact attestation verification
4. **Consistency**: Standardized execution environment for all operations
5. **Secret Management**: GitHub Secrets provide secure credential storage
6. **Immutability**: Workflow definitions are version controlled and reviewed

#### Permitted Execution Paths

**✅ PERMITTED: GitHub Actions Workflow Dispatch**
```yaml
# User triggers workflow via GitHub UI or API
# Workflow runs in GitHub Actions
# All operations are logged and auditable

on:
  workflow_dispatch:
    inputs:
      render_run_id:
        description: 'Render artifacts workflow run ID'
        required: true

jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - name: Verify attestations
        uses: ./.github/actions/verify-attestation
        # ... workflow continues
```

**✅ PERMITTED: Automatic Workflow Trigger**
```yaml
# Workflow automatically triggered by render completion
# Still runs in GitHub Actions environment

on:
  workflow_run:
    workflows: ["Render Artifacts"]
    types: [completed]
```

#### Prohibited Execution Paths

**❌ PROHIBITED: Local Workstation Execution**
```bash
# DO NOT DO THIS:
# Running Terraform locally bypasses all security controls

$ cd terraform/
$ terraform plan -var-file=../artifacts/tfvars/site-pennington.tfvars.json

# This is PROHIBITED because:
# - No attestation verification
# - No audit trail
# - No access control enforcement
# - Inconsistent execution environment
# - Potential for using unattested artifacts
```

**❌ PROHIBITED: Manual CLI in SSH Session**
```bash
# DO NOT DO THIS:
# SSHing into a server and running Terraform manually

user@server:~$ terraform plan

# This is PROHIBITED for the same reasons as local execution
```

**❌ PROHIBITED: Other CI/CD Systems**
```yaml
# DO NOT DO THIS:
# Using Jenkins, CircleCI, or other CI systems

# jenkins-pipeline.groovy
pipeline {
  stage('Terraform Plan') {
    sh 'terraform plan'
  }
}

# This is PROHIBITED because:
# - Different audit trail system
# - Different access controls
# - May not enforce attestation verification
# - Inconsistent with repository design
```

#### Development and Testing Exception

**Limited Exception for Local Development**:

Local execution is permitted ONLY for:
- ✅ `terraform init` - Initialize providers for development
- ✅ `terraform validate` - Validate syntax during development
- ✅ `terraform fmt` - Format code during development
- ✅ Testing with stub/mock artifacts (never deployed)

Local execution is PROHIBITED for:
- ❌ `terraform plan` with real artifacts
- ❌ `terraform apply` (under any circumstances)
- ❌ Any operation that consumes attested artifacts
- ❌ Any operation that affects real infrastructure

**Development Workflow**:
```bash
# ✅ PERMITTED: Local syntax validation
$ terraform fmt
$ terraform validate

# ✅ PERMITTED: Testing with local mock data
$ terraform plan -var-file=test-fixtures/mock.tfvars.json

# ❌ PROHIBITED: Planning with real attested artifacts
$ terraform plan -var-file=artifacts/tfvars/site-pennington.tfvars.json
```

---

## Security Boundaries

### Artifact Attestation is Mandatory

**Statement**: **All artifacts consumed by Terraform MUST have valid SLSA provenance attestations. Unattested artifacts MUST be rejected.**

#### Trust Boundary Contract

See [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md) for the complete trust boundary contract.

**Key Points**:
- ✅ Only attested artifacts may be consumed
- ✅ Attestation verification is enforced, not optional
- ✅ Verification failures block workflow execution
- ❌ Bypass is NOT permitted in production
- ❌ Manual artifacts are NOT permitted

#### Attestation Gate

The `.github/actions/verify-attestation` composite action enforces attestation verification.

See [docs/phase4/attestation-gate.md](attestation-gate.md) for complete documentation.

**Production Enforcement**:
```yaml
- name: Verify artifact attestations (REQUIRED)
  uses: ./.github/actions/verify-attestation
  with:
    artifact-path: 'artifacts/tfvars/*.json'
    environment: 'prod'
    # Bypass is NOT allowed - verification is mandatory
```

### GitHub Actions Permissions

**Principle**: Workflows run with minimum required permissions.

**Required Permissions for Plan Workflow**:
```yaml
permissions:
  contents: read       # Read repository code
  actions: read        # Download artifacts from other workflows
  id-token: read       # Verify attestations via OIDC
```

**Prohibited Permissions for Plan Workflow**:
```yaml
# MUST NOT include:
# contents: write      # Would allow code modification
# attestations: write  # Would allow creating attestations
# pull-requests: write # Would allow PR manipulation
```

---

## Prohibition Boundaries

### Explicit Prohibitions

This section explicitly documents what is NOT ALLOWED in this repository.

#### 1. Manual Artifact Creation

**PROHIBITED**: Creating Terraform variable files manually.

**Examples**:
- ❌ Writing `.tfvars.json` files by hand
- ❌ Editing generated artifacts
- ❌ Copying artifacts between environments
- ❌ Creating "emergency" configurations outside the pipeline

**Why**: Manual artifacts bypass NetBox authority and lack provenance attestations.

**Correct Approach**: Update intent in NetBox, then run the render pipeline.

#### 2. Local Terraform Plan/Apply

**PROHIBITED**: Running Terraform plan or apply on local workstations.

**Examples**:
- ❌ `terraform plan` on developer laptop
- ❌ `terraform apply` from command line
- ❌ Testing against real infrastructure locally
- ❌ "Quick fixes" via local Terraform execution

**Why**: Local execution bypasses attestation verification, audit trails, and access controls.

**Correct Approach**: Use GitHub Actions workflows to execute Terraform operations.

#### 3. Bypassing Attestation Verification

**PROHIBITED**: Skipping or bypassing attestation verification in production.

**Examples**:
- ❌ Setting `allow-bypass: 'true'` in production workflows
- ❌ Commenting out attestation verification steps
- ❌ Using unverified artifacts
- ❌ Downloading artifacts without verification

**Why**: Attestation verification is the primary security control for artifact integrity.

**Correct Approach**: Always verify attestations before consuming artifacts. Use dev mode with bypass ONLY for development/testing with mock data.

#### 4. Modifying Attested Artifacts

**PROHIBITED**: Editing or modifying artifacts after they have been attested.

**Examples**:
- ❌ Manually editing `.tfvars.json` files after download
- ❌ Patching artifacts to fix issues
- ❌ Merging multiple artifacts
- ❌ Changing artifact content for "one-time" deployments

**Why**: Modifications invalidate attestations and indicate potential tampering.

**Correct Approach**: Fix issues in NetBox or render pipeline, then regenerate artifacts.

#### 5. Alternative CI/CD Systems

**PROHIBITED**: Using CI/CD systems other than GitHub Actions for Terraform operations.

**Examples**:
- ❌ Jenkins pipelines
- ❌ CircleCI workflows
- ❌ GitLab CI
- ❌ Custom automation scripts

**Why**: Alternative systems have different audit trails, access controls, and may not enforce attestation verification.

**Correct Approach**: All Terraform operations MUST use GitHub Actions workflows defined in this repository.

#### 6. Terraform as Intent Source

**PROHIBITED**: Defining infrastructure intent directly in Terraform variables or modules.

**Examples**:
- ❌ Hard-coded VLAN definitions in Terraform
- ❌ Default variable values that define infrastructure
- ❌ Terraform modules that create infrastructure without NetBox input
- ❌ Configuration decisions made in Terraform code

**Why**: NetBox is the authoritative source of intent. Terraform is only an implementation tool.

**Correct Approach**: All infrastructure intent MUST be defined in NetBox.

#### 7. Emergency/Manual Overrides

**PROHIBITED**: Creating "emergency override" paths that bypass established controls.

**Examples**:
- ❌ Secret "admin" workflows with relaxed controls
- ❌ Manual execution scripts for emergencies
- ❌ Backdoor access to production systems
- ❌ "Break glass" procedures that skip verification

**Why**: Security controls exist to prevent errors and attacks. Bypassing them, even in emergencies, creates significant risk.

**Correct Approach**: If the pipeline is broken, fix the pipeline. Do not bypass controls.

---

## Enforcement Mechanisms

### How Boundaries Are Enforced

| Boundary | Enforcement Mechanism | Implementation |
|----------|----------------------|----------------|
| **NetBox Authority** | Documentation + code review | This document + PR review process |
| **GitHub Actions Only** | No local credentials | Secrets stored in GitHub only; no local execution possible with real credentials |
| **Attestation Required** | Automated gate | `.github/actions/verify-attestation` blocks unattested artifacts |
| **No Manual Artifacts** | Attestation enforcement | Manual artifacts have no attestations and are rejected |
| **Workflow Permissions** | GitHub YAML | `permissions:` block in workflows limits access |

### Automated Enforcement

**Attestation Gate** (`.github/actions/verify-attestation`):
- Automatically verifies all artifacts before consumption
- Fails workflow execution if attestation is invalid
- Cannot be bypassed in production environment
- Provides audit trail in GitHub Actions logs

**Workflow Permissions**:
- Workflows explicitly declare required permissions
- GitHub enforces permission boundaries
- Cannot access resources beyond declared permissions

### Manual Enforcement

**Code Review**:
- All workflow changes require PR review
- Reviewers verify adherence to boundaries
- Changes that violate boundaries are rejected

**Documentation**:
- This document serves as reference for all contributors
- Linked from main README.md for visibility
- Reviewed during onboarding

---

## Consequences of Violations

### Security Impact

Violating these boundaries can result in:

1. **Loss of Audit Trail**: Unable to determine who made changes or when
2. **Compromised Integrity**: Artifacts may be tampered with or unauthorized
3. **Unauthorized Changes**: Infrastructure changes without proper approval
4. **Supply Chain Attacks**: Malicious artifacts could be introduced
5. **Compliance Violations**: Failure to meet security requirements

### Detection

Violations may be detected through:

- ✅ Failed attestation verification in workflows
- ✅ GitHub Actions logs showing unauthorized attempts
- ✅ Infrastructure drift detection
- ✅ Manual audit of changes
- ✅ Code review of PRs

### Response

If a boundary violation is detected:

1. **Immediately halt**: Stop the violating operation
2. **Investigate**: Determine what was affected and why
3. **Remediate**: Roll back changes if necessary
4. **Document**: Record incident for future reference
5. **Prevent**: Update controls to prevent recurrence

---

## Summary

### Key Takeaways

1. ✅ **NetBox is authoritative** - Terraform is NOT an authority for intent
2. ✅ **GitHub Actions only** - Manual/local Terraform execution is PROHIBITED
3. ✅ **Attestations required** - All artifacts MUST be attested and verified
4. ❌ **No manual artifacts** - All artifacts MUST come from render pipeline
5. ❌ **No bypass in production** - Security controls are mandatory
6. ❌ **No alternative CI/CD** - GitHub Actions is the only execution environment

### Checklist for Contributors

Before making changes, verify:

- [ ] I understand that NetBox is the authoritative source of intent
- [ ] I am not defining infrastructure intent in Terraform
- [ ] I am using GitHub Actions for all Terraform operations
- [ ] I am not running Terraform plan/apply locally
- [ ] I am using attested artifacts only
- [ ] I am not creating or modifying artifacts manually
- [ ] I am not bypassing attestation verification in production
- [ ] I have reviewed this security document

### Related Documentation

- [docs/phase3/terraform-boundary.md](../phase3/terraform-boundary.md) - Trust boundary contract
- [docs/phase4/attestation-gate.md](attestation-gate.md) - Attestation verification gate
- [docs/phase3/threat-model.md](../phase3/threat-model.md) - Threat model and trust boundaries
- [docs/phase3/attestation.md](../phase3/attestation.md) - Attestation implementation
- [README.md](../../README.md) - Repository overview with security warnings

---

**Document Version**: 1.0  
**Last Updated**: Phase 4  
**Review Schedule**: Every phase or when boundaries change
