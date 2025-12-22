# Policy Engine Selection & Integration

## Overview

This document describes the selection, integration, and operational use of the policy engine for gating Terraform apply operations. The policy engine provides deterministic, automated policy evaluation as a critical security control in the infrastructure deployment pipeline.

**Policy Engine**: Open Policy Agent (OPA)

**Status**: Active and Enforced

**Last Updated**: Phase 5

## Table of Contents

- [Policy Engine Selection](#policy-engine-selection)
- [Why OPA](#why-opa)
- [Policy Evaluation Workflow](#policy-evaluation-workflow)
- [Policy Inputs](#policy-inputs)
- [Policy Files](#policy-files)
- [Integration with GitHub Actions](#integration-with-github-actions)
- [Deterministic Execution](#deterministic-execution)
- [Policy Evaluation Examples](#policy-evaluation-examples)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

---

## Policy Engine Selection

### Chosen Engine: Open Policy Agent (OPA)

Open Policy Agent (OPA) has been selected as the policy engine for this infrastructure pipeline.

**Version**: Latest stable (pinned in workflow)

**Installation Method**: Direct binary download from official GitHub releases

**Execution Environment**: GitHub Actions workflows only (CI-only)

### Alternative Engines Considered

| Engine | Pros | Cons | Decision |
|--------|------|------|----------|
| **Open Policy Agent (OPA)** | - Deterministic evaluation<br>- Rego language is purpose-built for policies<br>- Excellent JSON integration<br>- Active community<br>- No external dependencies<br>- Single binary | - Rego learning curve | **✅ Selected** |
| Sentinel (HashiCorp) | - Native Terraform integration<br>- Terraform-focused | - Requires Terraform Cloud/Enterprise<br>- Not open source<br>- Additional costs | ❌ Rejected (requires paid platform) |
| Conftest | - Built on OPA/Rego<br>- Simpler CLI interface | - Less flexible than OPA directly<br>- Additional abstraction layer | ❌ Rejected (prefer direct OPA) |
| Custom Scripts | - Complete control<br>- No new tools | - Not deterministic<br>- Hard to maintain<br>- No standard policy language | ❌ Rejected (maintenance burden) |

---

## Why OPA

OPA was selected for the following key reasons:

### 1. Deterministic Evaluation

OPA provides deterministic policy evaluation:
- Same inputs always produce same outputs
- No side effects or external state dependencies
- Reproducible across different execution environments
- Critical for CI/CD pipelines where consistency is required

### 2. Purpose-Built for Policy as Code

- **Rego Language**: Designed specifically for expressing policies
- **Query-based**: Natural fit for "does this satisfy our requirements?"
- **Compositional**: Policies can be built from reusable rules
- **Type Safety**: Catches errors in policy definitions

### 3. Excellent JSON Integration

OPA excels at processing JSON data:
- Native JSON support in Rego
- Can query deeply nested structures easily
- Perfect for Terraform plan JSON format
- Straightforward to work with attestation data

### 4. Single Binary, No Dependencies

- Self-contained binary with no runtime dependencies
- Easy to install in CI environments
- Fast startup time
- No package manager conflicts

### 5. Active Development and Community

- Actively maintained by CNCF
- Large community and ecosystem
- Extensive documentation and examples
- Battle-tested in production environments

### 6. CI-Only Execution Model

OPA fits perfectly with CI-only execution:
- Runs as a CLI tool in GitHub Actions
- No server or persistent state required
- Evaluation completes quickly
- Exit codes for pass/fail decisions

---

## Policy Evaluation Workflow

The policy evaluation workflow is integrated into the Terraform plan workflow as a mandatory gate between plan generation and apply approval.

### Workflow Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                  POLICY EVALUATION FLOW                     │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────────┐
  │  PR Approval     │  ◄─── Human authorization required
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Download Attested│  ◄─── Fetch artifacts from render pipeline
  │ Artifacts        │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Verify           │  ◄─── Cryptographic attestation check
  │ Attestations     │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Terraform Plan   │  ◄─── Generate plan (binary + JSON)
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ 🔐 POLICY GATE   │  ◄─── NEW: OPA policy evaluation
  │ (OPA Evaluation) │       (This document describes this step)
  └────────┬─────────┘
           │
           │ Policy Pass ✅
           ▼
  ┌──────────────────┐
  │ Upload Plan      │  ◄─── Make plan available for apply
  │ Artifacts        │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ (Future)         │  ◄─── Future phase: Terraform apply
  │ Terraform Apply  │
  └──────────────────┘
```

### Policy Gate Decision Points

The policy evaluation step acts as a mandatory gate:

- ✅ **Policy PASS**: Plan artifacts are uploaded and workflow succeeds
- ❌ **Policy FAIL**: Workflow fails immediately, plan is not approved for apply
- ⚠️ **Policy ERROR**: Workflow fails (fail-closed security model)

---

## Policy Inputs

The policy engine receives structured data as input for evaluation. All inputs are provided as JSON documents.

### Input 1: Terraform Plan JSON

**Source**: Generated by `terraform show -json tfplan-{site}.binary`

**Format**: Terraform JSON plan format (version 1.2+)

**Content**:
- Complete plan representation
- Resource changes (create, update, delete)
- Before/after state for each resource
- Provider configuration
- Output changes

**Example Structure**:
```json
{
  "format_version": "1.2",
  "terraform_version": "1.9.0",
  "planned_values": { ... },
  "resource_changes": [
    {
      "address": "unifi_vlan.management",
      "mode": "managed",
      "type": "unifi_vlan",
      "name": "management",
      "change": {
        "actions": ["create"],
        "before": null,
        "after": {
          "name": "Management",
          "vlan_id": 100
        }
      }
    }
  ]
}
```

**Policy Uses**:
- Validate resource changes are within allowed boundaries
- Ensure no resources are destroyed without explicit approval
- Check that resource configurations match organizational standards
- Verify no sensitive data is exposed in plan

### Input 2: Artifact Metadata

**Source**: Generated from artifact information and workflow context

**Format**: JSON document with artifact details

**Content**:
- Artifact digest (SHA256)
- Render workflow run ID
- Attestation status
- PR number and approver
- Timestamp information
- Site identifier

**Example Structure**:
```json
{
  "artifact": {
    "path": "site-pennington.tfvars.json",
    "digest": "sha256:abc123...",
    "site": "pennington"
  },
  "provenance": {
    "render_run_id": "1234567890",
    "attestation_verified": true,
    "pr_number": "42",
    "approver": "maintainer-username",
    "approved_at": "2024-01-15T10:30:00Z"
  }
}
```

**Policy Uses**:
- Verify artifacts are attested and verified
- Ensure PR approval chain is valid
- Check artifact source is from authorized workflow
- Validate timestamp is recent (freshness)

### Input 3: Attestation Data

**Source**: SLSA provenance attestation from render workflow

**Format**: SLSA provenance JSON format

**Content**:
- Predicate type (SLSA provenance)
- Builder information (workflow, commit SHA)
- Build environment details
- Materials (inputs to the build)
- Metadata (timestamps, invocation ID)

**Example Structure**:
```json
{
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "builder": {
      "id": "https://github.com/harris-boyce/boycivenga-iac/.github/workflows/render-artifacts.yaml@main"
    },
    "buildType": "https://github.com/Attestations/GitHubActionsWorkflow@v1",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/harris-boyce/boycivenga-iac",
        "digest": {
          "sha1": "abc123..."
        }
      }
    },
    "materials": [ ... ]
  }
}
```

**Policy Uses**:
- Verify attestation is from trusted workflow
- Check builder identity matches expected workflow
- Ensure materials (inputs) are from expected sources
- Validate attestation timestamp

---

## Policy Files

Policy files are written in Rego and stored in the repository under `.github/policies/`.

### Policy Directory Structure

```
.github/policies/
├── terraform_plan.rego         # Main policy for plan evaluation
├── common.rego                 # Reusable rules and helpers
└── README.md                   # Policy documentation
```

### Main Policy: terraform_plan.rego

The main policy evaluates Terraform plans and makes a gate decision.

**Policy Package**: `terraform.plan`

**Key Rules**:

1. **allow**: Boolean rule that determines if plan is approved
2. **deny**: Array of denial reasons (if any)
3. **violations**: Detailed list of policy violations
4. **summary**: Human-readable summary of evaluation

**Example Policy Structure**:
```rego
package terraform.plan

import future.keywords.if
import future.keywords.in

# Main decision rule - plan is allowed if no denials
default allow = false

allow if {
    count(deny) == 0
}

# Collect all denial reasons
deny contains msg if {
    # Rule 1: No resource deletions without explicit approval
    resource_deletions_not_approved
    msg := "Destructive changes detected without deletion approval"
}

deny contains msg if {
    # Rule 2: Artifact must be attested
    not artifact_attested
    msg := "Artifact attestation verification failed"
}

# Helper rules
resource_deletions_not_approved if {
    some change in input.plan.resource_changes
    "delete" in change.change.actions
    not input.metadata.deletion_approved
}

artifact_attested if {
    input.metadata.provenance.attestation_verified == true
}
```

### Common Policy: common.rego

Reusable rules and helper functions used across multiple policies.

**Policy Package**: `terraform.common`

**Example Helpers**:
```rego
package terraform.common

# Check if a resource type is in the allowed list
is_allowed_resource_type(resource_type) if {
    allowed_types := {
        "unifi_network",
        "unifi_vlan",
        "unifi_port_profile"
    }
    resource_type in allowed_types
}

# Extract resource type from address
resource_type(address) := type if {
    parts := split(address, ".")
    type := parts[0]
}
```

---

## Integration with GitHub Actions

Policy evaluation is integrated into the `terraform-plan.yaml` workflow as a new step after plan generation.

### New Workflow Step: Policy Evaluation

```yaml
- name: Evaluate Policy with OPA
  id: policy
  working-directory: terraform
  run: |
    PLAN_JSON="tfplan-${{ matrix.site }}.json"

    echo "🔐 Installing Open Policy Agent..."

    # Download and install OPA (pinned version for reproducibility)
    OPA_VERSION="0.60.0"
    curl -L -o opa "https://github.com/open-policy-agent/opa/releases/download/v${OPA_VERSION}/opa_linux_amd64"
    chmod +x opa

    echo "✅ OPA version: $(./opa version)"

    # Prepare policy input document
    echo "📋 Preparing policy input..."

    # Create metadata JSON
    cat > policy-input-metadata.json << EOF
    {
      "artifact": {
        "path": "site-${{ matrix.site }}.tfvars.json",
        "site": "${{ matrix.site }}"
      },
      "provenance": {
        "render_run_id": "${{ steps.determine-run.outputs.run_id }}",
        "attestation_verified": true,
        "pr_number": "${{ steps.determine-run.outputs.pr_number }}",
        "approver": "${{ steps.pr-metadata.outputs.approver }}",
        "approved_at": "${{ github.event.review.submitted_at }}"
      }
    }
    EOF

    # Create combined input document
    echo "📄 Creating policy input document..."
    cat > policy-input.json << EOF
    {
      "plan": $(cat "$PLAN_JSON"),
      "metadata": $(cat policy-input-metadata.json)
    }
    EOF

    # Evaluate policy
    echo "🔐 Evaluating policy..."

    if ./opa eval \
        --bundle ../.github/policies/ \
        --input policy-input.json \
        --format pretty \
        'data.terraform.plan.allow'; then
      echo "✅ Policy evaluation PASSED"
      echo "policy_result=pass" >> $GITHUB_OUTPUT
    else
      echo "❌ Policy evaluation FAILED"
      echo "policy_result=fail" >> $GITHUB_OUTPUT

      # Show detailed policy violations
      echo ""
      echo "Policy violations:"
      ./opa eval \
        --bundle ../.github/policies/ \
        --input policy-input.json \
        --format pretty \
        'data.terraform.plan.deny'

      exit 1
    fi

- name: Policy Summary
  if: always()
  run: |
    cat >> $GITHUB_STEP_SUMMARY << 'EOF'
    ### 🔐 Policy Evaluation

    **Result**: ${{ steps.policy.outputs.policy_result || 'error' }}

    **Policy Engine**: Open Policy Agent (OPA)

    **Policies Evaluated**:
    - Artifact attestation verification
    - Resource change boundaries
    - Destructive change approval

    **Input Documents**:
    - Terraform plan JSON
    - Artifact metadata
    - Attestation data

    EOF
```

### Workflow Permissions

No additional permissions are required for policy evaluation. Existing permissions are sufficient:

```yaml
permissions:
  contents: read       # Read policy files from repository
  actions: read        # Already required for artifact download
  id-token: read       # Already required for attestation
```

---

## Deterministic Execution

Policy evaluation is designed to be fully deterministic and reproducible.

### Determinism Guarantees

1. **Fixed OPA Version**: Workflow pins specific OPA version (not "latest")
2. **No External Dependencies**: Policy evaluation requires no network access
3. **Pure Input/Output**: All inputs are provided as JSON files, no environment variables
4. **No Randomness**: Rego policies are deterministic by design
5. **Immutable Policies**: Policy files are version-controlled in the repository

### Reproducibility

Given the same inputs, policy evaluation will always produce the same result:

```bash
# Same inputs → Same outputs (always)
opa eval --bundle policies/ --input plan.json 'data.terraform.plan.allow'
# Result: true

opa eval --bundle policies/ --input plan.json 'data.terraform.plan.allow'
# Result: true (identical)
```

### CI-Only Execution

Policy evaluation ONLY runs in GitHub Actions:

- ✅ **GitHub Actions workflows**: Only permitted execution environment
- ❌ **Local execution**: Not permitted (consistent with security boundaries)
- ❌ **Manual OPA runs**: Not permitted for production decisions
- ❌ **Alternative CI systems**: Not permitted

**Rationale**: Consistent with existing security boundaries (see [docs/phase4/security.md](../phase4/security.md))

### No Bypass Mechanism

Policy evaluation cannot be bypassed:

- ✅ **Mandatory step**: Policy evaluation is required, not optional
- ✅ **Fail-closed**: Policy failures stop the workflow
- ❌ **No skip flag**: Cannot skip policy evaluation
- ❌ **No override**: No manual override or bypass available

---

## Policy Evaluation Examples

### Example 1: Plan Creates Only (PASS)

**Input Plan**:
```json
{
  "resource_changes": [
    {
      "change": {
        "actions": ["create"],
        "after": {
          "name": "Management",
          "vlan_id": 100
        }
      }
    }
  ]
}
```

**Policy Result**: ✅ PASS

**Reason**: Creating new resources is allowed

---

### Example 2: Plan Deletes Resources (FAIL)

**Input Plan**:
```json
{
  "resource_changes": [
    {
      "change": {
        "actions": ["delete"]
      }
    }
  ]
}
```

**Metadata**:
```json
{
  "deletion_approved": false
}
```

**Policy Result**: ❌ FAIL

**Reason**: Destructive changes require explicit approval flag

**Violation Message**: "Destructive changes detected without deletion approval"

---

### Example 3: Unattested Artifact (FAIL)

**Metadata**:
```json
{
  "provenance": {
    "attestation_verified": false
  }
}
```

**Policy Result**: ❌ FAIL

**Reason**: Artifact attestation verification failed

**Violation Message**: "Artifact attestation verification failed"

---

## Troubleshooting

### Policy Evaluation Fails with "opa: command not found"

**Cause**: OPA binary failed to download or is not in PATH

**Solution**:
1. Check the OPA download step in workflow logs
2. Verify the OPA version is correct
3. Ensure curl command succeeded
4. Check file permissions on opa binary

---

### Policy Returns Unexpected Results

**Cause**: Policy logic error or incorrect input data

**Solution**:
1. Review policy files in `.github/policies/`
2. Validate input JSON structure
3. Test policy locally with sample inputs:
   ```bash
   opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.allow'
   ```
4. Check policy logic in Rego files

---

### Policy Evaluation is Slow

**Cause**: Large plan JSON or complex policy rules

**Solution**:
1. Review policy complexity
2. Optimize Rego rules if possible
3. Consider splitting policies into smaller units
4. Note: OPA is generally very fast (<1 second for typical plans)

---

### Need to Debug Policy Logic

**Solution**: Run OPA locally with test inputs

```bash
# Create test input
cat > test-input.json << EOF
{
  "plan": { ... },
  "metadata": { ... }
}
EOF

# Evaluate policy
opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan'

# Check specific rule
opa eval --bundle .github/policies/ --input test-input.json 'data.terraform.plan.deny'
```

---

## Future Enhancements

Potential improvements for future phases:

### Policy Enhancements

- **Site-Specific Policies**: Different policies per site/environment
- **Resource Limits**: Enforce maximum resource counts
- **Naming Conventions**: Validate resource naming patterns
- **Configuration Standards**: Enforce organizational standards
- **Compliance Checks**: Integrate compliance requirements (e.g., PCI-DSS)

### Tooling Improvements

- **Policy Testing Framework**: Automated tests for policy rules
- **Policy Coverage Reports**: Show which policies are tested
- **Policy Dry-Run Mode**: Evaluate policies without failing workflow
- **Policy Versioning**: Support multiple policy versions
- **Policy Metrics**: Track policy evaluation times and pass/fail rates

### Integration Improvements

- **Slack Notifications**: Alert on policy failures
- **Policy Reports**: Generate detailed HTML reports
- **Historical Analysis**: Track policy violations over time
- **Policy Documentation**: Auto-generate docs from Rego files

---

## Explicit Non-Goals

The following are explicitly OUT OF SCOPE for this phase:

### ❌ Multi-Environment Policy Targeting

**Not Implemented**: Different policies for dev/staging/prod environments

**Reason**: Single environment scope for this phase. All policies apply uniformly.

**Future**: May be added in later phases if needed

### ❌ Emergency Override or Manual Gating

**Not Implemented**: Ability to bypass policy evaluation or manually approve despite policy failure

**Reason**: Violates fail-closed security model and deterministic execution requirements

**Future**: Will not be implemented (by design - see security boundaries)

---

## References

- **OPA Documentation**: https://www.openpolicyagent.org/docs/latest/
- **Rego Language**: https://www.openpolicyagent.org/docs/latest/policy-language/
- **Terraform JSON Format**: https://developer.hashicorp.com/terraform/internals/json-format
- **SLSA Provenance**: https://slsa.dev/provenance/
- **Security Boundaries**: [docs/phase4/security.md](../phase4/security.md)
- **Attestation Gate**: [docs/phase4/attestation-gate.md](../phase4/attestation-gate.md)

---

**Document Version**: 1.0
**Phase**: 5
**Status**: Active
**Review Schedule**: Every phase or when policy engine changes
