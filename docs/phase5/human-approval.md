# Human Approval Wiring

## Overview

This document describes the human approval mechanism integrated into the Terraform deployment pipeline. The system automatically determines when human approval is required based on policy evaluation, and enforces that approval through GitHub Environments with protection rules.

**Key Principle**: Safe, non-destructive changes proceed automatically. Destructive changes require explicit human approval before apply.

**Status**: Active and Enforced

**Last Updated**: Phase 5

**Document Version**: 1.0.0

## Table of Contents

- [Approval Decision Model](#approval-decision-model)
- [How It Works](#how-it-works)
- [Approval Requirements](#approval-requirements)
- [GitHub Environment Protection](#github-environment-protection)
- [Approval Workflow](#approval-workflow)
- [Safe vs. Destructive Changes](#safe-vs-destructive-changes)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Explicit Non-Goals](#explicit-non-goals)

---

## Approval Decision Model

The approval decision model determines whether a Terraform plan requires human approval based on the nature of changes:

### Decision Criteria

| Change Type | Approval Required | Reason |
|------------|-------------------|---------|
| **Create resources** | ❌ No | Safe, additive operation |
| **Update resources (non-destructive)** | ❌ No | Safe, modification only |
| **Delete resources** | ✅ Yes | Destructive, requires review |
| **Replace resources (delete + create)** | ✅ Yes | Destructive, requires review |

### Policy-Driven Decision

The approval requirement is determined by OPA policy evaluation in the terraform-plan workflow:

```rego
# From .github/policies/terraform_plan.rego

# Human approval is required if there are destructive changes
approval_required if {
    has_destructive_changes
}

has_destructive_changes if {
    count(resources_to_delete) > 0
}
```

**Key Points**:
- Decision is **deterministic** (same changes → same decision)
- Decision is **automated** (no manual override needed)
- Decision is **enforced** through GitHub Environments
- Decision is **traceable** (logged in plan artifacts)

---

## How It Works

### High-Level Flow

```
┌──────────────────────────────────────────┐
│   1. PR Approval & Terraform Plan         │
│   - PR must be approved by reviewer       │
│   - Plan workflow evaluates policy        │
│   - Determines approval requirement       │
└──────────────┬───────────────────────────┘
               │
               ▼
       ┌───────┴────────┐
       │  Destructive   │
       │   Changes?     │
       └───────┬────────┘
               │
       ┌───────┼────────┐
       │ No    │    Yes │
       ▼       ▼        ▼
┌──────────────┐  ┌──────────────────────┐
│ Auto-Approve │  │ Require Approval     │
│              │  │                      │
│ - Upload     │  │ - Upload artifacts   │
│   artifacts  │  │ - Set approval_      │
│ - Set        │  │   required=true      │
│   approval_  │  │                      │
│   required=  │  └──────────────────────┘
│   false      │
└──────────────┘
       │
       │
       └───────┬────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│   2. Trigger Apply Workflow               │
│   - User dispatches apply workflow        │
│   - Workflow reads approval metadata      │
│   - Selects appropriate environment       │
└──────────────┬───────────────────────────┘
               │
               ▼
       ┌───────┴────────┐
       │  Approval      │
       │  Required?     │
       └───────┬────────┘
               │
       ┌───────┼────────┐
       │ No    │    Yes │
       ▼       ▼        ▼
┌──────────────┐  ┌──────────────────────┐
│ Unprotected  │  │ Protected            │
│ Environment  │  │ Environment          │
│              │  │                      │
│ - Apply      │  │ - Wait for human     │
│   proceeds   │  │   approval           │
│   auto-      │  │ - Reviewer must      │
│   matically  │  │   approve            │
│              │  │ - Then apply         │
│              │  │   proceeds           │
└──────────────┘  └──────────────────────┘
       │                   │
       └───────┬───────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│   3. Terraform Apply Executes             │
│   - All security checks re-verified       │
│   - Infrastructure changes applied        │
│   - Complete audit trail recorded         │
└──────────────────────────────────────────┘
```

---

## Approval Requirements

### When Approval is Required

Human approval is **required** when:

1. **Resource Deletions**: Any `delete` action in the plan
2. **Resource Replacements**: Any `replace` action (delete + create)
3. **Destructive Updates**: Updates that require resource replacement

### When Approval is NOT Required

Human approval is **not required** when:

1. **Creating Resources**: Pure `create` actions
2. **Non-Destructive Updates**: In-place modifications (`update` actions)
3. **No-Op Changes**: No actual changes to infrastructure
4. **Empty Plans**: No resource changes at all

### PR Approval vs. Apply Approval

The system has **two levels** of approval:

| Approval Level | Required For | Purpose | Enforced By |
|---------------|--------------|---------|-------------|
| **PR Approval** | ALL plans | Authorization to run plan | GitHub PR review |
| **Apply Approval** | Destructive changes only | Additional review before apply | GitHub Environment protection |

**Important**: PR approval is ALWAYS required. Apply approval is ADDITIONAL and only for destructive changes.

---

## GitHub Environment Protection

The system uses GitHub Environments to enforce human approval when required.

### Environment Types

| Environment Name | Protection | Used When |
|-----------------|-----------|-----------|
| `production-{site}` | ❌ None | Safe changes (auto-approve) |
| `production-{site}-protected` | ✅ Required reviewers | Destructive changes |

### Environment Configuration

Protected environments should be configured with:

1. **Required Reviewers**: At least 1 reviewer must approve
2. **Deployment Branch Rules**: Only specific branches can deploy (optional)
3. **Wait Timer**: Optional delay before deployment (optional)

### Setting Up Environments

To configure protected environments in GitHub:

1. Go to **Settings** → **Environments**
2. Create environment: `production-{site}-protected` (e.g., `production-pennington-protected`)
3. Enable **Required reviewers**
4. Add authorized reviewers (e.g., repository owners, infrastructure team)
5. Save protection rules

**Note**: Unprotected environments (`production-{site}`) do not require manual configuration.

---

## Approval Workflow

### Step-by-Step Process

#### 1. Create and Approve PR

```bash
# Create PR referencing render artifacts run
gh pr create --title "Deploy infrastructure changes" \
  --body "Render Run: 1234567890"

# Get PR approved by reviewer
# (This approval is ALWAYS required)
```

#### 2. Plan Executes Automatically

After PR approval:

```yaml
# terraform-plan.yaml workflow triggers automatically
# - Downloads attested artifacts
# - Generates Terraform plan
# - Evaluates policy
# - Determines approval requirement
# - Uploads plan artifacts with approval metadata
```

The plan output shows:

- ✅ **Auto-Approve Eligible** (if safe changes)
- ⚠️ **Human Approval Required** (if destructive changes)

#### 3. Review Plan Output

Check the plan summary in the workflow run to see:

- Resource changes (create, update, delete)
- Approval requirement status
- Policy evaluation results

#### 4. Trigger Apply

```bash
# Manually trigger apply workflow
gh workflow run terraform-apply.yaml \
  --field plan_run_id=1234567890 \
  --field site=pennington \
  --field pr_number=42
```

#### 5. Approval Gate (if Required)

If destructive changes are detected:

1. Apply workflow **pauses** at environment protection
2. GitHub sends notification to required reviewers
3. Reviewer **reviews** the plan and change details
4. Reviewer **approves** or **rejects** the deployment
5. If approved, apply proceeds automatically
6. If rejected, workflow fails and no changes are applied

If only safe changes:

1. Apply workflow proceeds **immediately**
2. No human interaction required
3. Complete audit trail still recorded

---

## Safe vs. Destructive Changes

### Safe Changes (Auto-Approve)

Examples of changes that proceed automatically:

```hcl
# Creating new VLAN
+ resource "unifi_network" "new_vlan" {
    name    = "Guest-WiFi"
    purpose = "guest"
    subnet  = "10.0.50.0/24"
  }

# Updating VLAN configuration
~ resource "unifi_network" "management" {
    name    = "Management"
  ~ domain  = "old.local" -> "new.local"
    subnet  = "10.0.1.0/24"
  }

# Adding firewall rule
+ resource "unifi_firewall_rule" "allow_web" {
    name    = "Allow Web Traffic"
    action  = "accept"
    protocol = "tcp"
  }
```

### Destructive Changes (Require Approval)

Examples of changes that require human approval:

```hcl
# Deleting VLAN
- resource "unifi_network" "old_guest" {
    name    = "Old-Guest"
    purpose = "guest"
    subnet  = "192.168.100.0/24"
  }

# Replacing network (delete + create)
-/+ resource "unifi_network" "management" {
  ~ name    = "Management" -> "Mgmt-Network"
    subnet  = "10.0.1.0/24"
    # (subnet change forces replacement)
  }

# Deleting firewall rule
- resource "unifi_firewall_rule" "legacy_rule" {
    name    = "Legacy Rule"
    action  = "drop"
  }
```

---

## Configuration

### Policy Configuration

The approval requirement is configured in `.github/policies/terraform_plan.rego`:

```rego
# Approval requirement rule
default approval_required := false

approval_required if {
    has_destructive_changes
}

has_destructive_changes if {
    count(resources_to_delete) > 0
}
```

**To modify approval criteria**: Edit the `approval_required` rule in the policy file.

### Workflow Configuration

The apply workflow automatically reads approval metadata:

```yaml
# In .github/workflows/terraform-apply.yaml

- name: Check approval requirement
  run: |
    # Read approval metadata from plan artifacts
    APPROVAL_REQUIRED=$(jq -r '.approval_required' approval.json)

    if [ "$APPROVAL_REQUIRED" = "true" ]; then
      echo "environment_name=production-${SITE}-protected"
    else
      echo "environment_name=production-${SITE}"
    fi
```

### Environment Names

Environment names are derived from site names:

- **Safe changes**: `production-{site}`
- **Destructive changes**: `production-{site}-protected`

**To change naming**: Update the `check-approval` step in `terraform-apply.yaml`.

---

## Examples

### Example 1: Auto-Approved Safe Changes

**Scenario**: Adding a new VLAN for IoT devices

**Plan Output**:
```
Plan: 1 to add, 0 to change, 0 to destroy.

✅ AUTO-APPROVE: No destructive changes detected
This plan can be auto-applied without additional approval.
```

**Apply Process**:
1. Trigger apply workflow
2. Workflow uses `production-pennington` (unprotected)
3. Apply proceeds immediately
4. No human interaction required

### Example 2: Approval Required for Deletion

**Scenario**: Removing an old guest network

**Plan Output**:
```
Plan: 0 to add, 0 to change, 1 to destroy.

⚠️ HUMAN APPROVAL REQUIRED: Plan contains destructive changes
This plan will require additional human approval in the apply workflow.

Destructive changes detected:
- unifi_network.old_guest will be destroyed
```

**Apply Process**:
1. Trigger apply workflow
2. Workflow uses `production-pennington-protected` (protected)
3. Workflow **pauses** for reviewer approval
4. Reviewer receives notification
5. Reviewer reviews plan and approves
6. Apply proceeds after approval

### Example 3: Mixed Changes

**Scenario**: Adding new VLAN and removing old one

**Plan Output**:
```
Plan: 1 to add, 0 to change, 1 to destroy.

⚠️ HUMAN APPROVAL REQUIRED: Plan contains destructive changes

Destructive changes detected:
- unifi_network.old_vlan will be destroyed
```

**Apply Process**:
- Requires approval (due to deletion)
- Entire plan (including safe addition) requires approval
- All-or-nothing: approve entire plan or reject it

---

## Troubleshooting

### Plan Passes but Apply Blocks

**Symptom**: Plan succeeds, but apply workflow waits for approval

**Cause**: Plan contains destructive changes

**Solution**: This is expected behavior. Review the plan, then approve the environment protection.

### Apply Proceeds Without Approval

**Symptom**: Apply executes immediately, expected approval gate

**Cause**: Plan contains only safe changes (no deletions)

**Solution**: This is correct behavior. If you want to review all changes, modify the policy to always require approval.

### Approval Metadata Missing

**Symptom**: Apply fails with "approval metadata not found"

**Cause**: Plan workflow didn't complete successfully or artifacts expired

**Solution**: Re-run the plan workflow, ensure it completes successfully, then retry apply.

### Wrong Environment Used

**Symptom**: Apply uses wrong environment (protected vs. unprotected)

**Cause**: Approval metadata file may be corrupted or missing

**Solution**:
1. Check plan artifacts for `tfplan-{site}-approval.json`
2. Verify the `approval_required` value
3. Re-run plan if metadata is incorrect

---

## Explicit Non-Goals

This approval mechanism intentionally does **NOT** support:

### ❌ Manual Override for Approval Decisions

**Why**: Approval decisions are policy-driven and deterministic. Manual overrides would compromise security and bypass the policy engine.

**Alternative**: If you need to override, modify the policy rules or fix the issue causing denial.

### ❌ Emergency Bypass Mechanism

**Why**: Emergency bypasses create security vulnerabilities and audit trail gaps.

**Alternative**:
- For emergencies, ensure you have sufficient reviewers configured
- Use shorter review cycles during incidents
- Document emergency procedures that work within the approval system

### ❌ Different Approval Rules for Different Reviewers

**Why**: Simplicity and consistency. All destructive changes are treated equally.

**Alternative**: Use GitHub's environment protection rules to configure different reviewer groups per environment if needed.

### ❌ Approval Based on Change Magnitude

**Why**: Any deletion is potentially destructive. Counting resources is arbitrary.

**Alternative**: The policy is binary: destructive (approve) or safe (auto). This is clearer and safer.

### ❌ Reviewer Selection Based on Resource Type

**Why**: Adds complexity without clear benefit. Infrastructure changes should be reviewed holistically.

**Alternative**: Configure environment reviewers based on site/environment, not resource type.

### ❌ Drift Detection Approval Override

**Why**: Drift should be corrected through the normal approval process.

**Alternative**: See [docs/phase4/drift.md](../phase4/drift.md) for drift handling procedures.

---

## Related Documentation

- [docs/phase5/approval-decision-model.md](./approval-decision-model.md) - Complete approval decision model
- [docs/phase5/policy-engine.md](./policy-engine.md) - Policy engine details
- [docs/phase5/apply-workflow.md](./apply-workflow.md) - Apply workflow documentation
- [docs/phase4/terraform-plan-approval-workflow.md](../phase4/terraform-plan-approval-workflow.md) - Plan approval process
- [docs/phase4/security.md](../phase4/security.md) - Security boundaries

---

## Summary

The human approval wiring provides:

✅ **Policy-Driven Decisions** - Automated evaluation of plan safety
✅ **Selective Approval** - Human review only when truly needed
✅ **Safe Auto-Apply** - Non-destructive changes proceed automatically
✅ **Clear Communication** - Explicit indication of approval requirements
✅ **Environment-Based Enforcement** - GitHub native protection mechanisms
✅ **Complete Audit Trail** - All decisions and approvals logged
✅ **No Bypasses** - Security boundaries cannot be circumvented

This ensures infrastructure changes are both **safe** (reviewed when needed) and **efficient** (automated when safe).
