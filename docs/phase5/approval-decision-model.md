# Approval Decision Model

## Overview

This document defines the approval decision engine that enforces policy-driven outcomes in the infrastructure deployment pipeline. The decision model provides deterministic, automated evaluation of Terraform plans and maps those evaluations to GitHub PR checks and reviewer requirements.

**Decision Engine**: Open Policy Agent (OPA) integrated with GitHub Actions

**Status**: Active and Enforced

**Last Updated**: Phase 5

**Document Version**: 1.0.0

## Table of Contents

- [Decision Model Overview](#decision-model-overview)
- [Decision Outcomes](#decision-outcomes)
- [Decision Flow](#decision-flow)
- [Policy-Driven Decisions](#policy-driven-decisions)
- [GitHub PR Integration](#github-pr-integration)
- [Reviewer Requirements](#reviewer-requirements)
- [Approval Enforcement](#approval-enforcement)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Explicit Non-Goals](#explicit-non-goals)

---

## Decision Model Overview

The approval decision model is a deterministic engine that evaluates infrastructure changes and produces one of three outcomes based on policy evaluation:

### Core Principles

1. **Policy-Driven**: All decisions are based on declarative OPA policies
2. **Deterministic**: Same inputs always produce the same decision
3. **Fail-Closed**: Ambiguous or error states default to deny
4. **Traceable**: All decisions are logged with full context
5. **Automated**: No manual intervention in decision evaluation

### Decision Authority

The decision model operates at multiple control points:

| Control Point | Location | Authority Level | Bypass Possible? |
|--------------|----------|-----------------|------------------|
| **Policy Evaluation** | terraform-plan.yaml workflow | MANDATORY | ❌ No |
| **PR Approval Gate** | Pull request review | MANDATORY | ❌ No |
| **Attestation Verification** | All workflows | MANDATORY | ❌ No |
| **Manual Review** | Pull request comments | ADVISORY | ✅ Yes (informational only) |

---

## Decision Outcomes

The decision model produces three possible outcomes for each Terraform plan:

### 1. Auto-Approve (PASS) ✅

**Decision**: The plan is automatically approved for apply operations.

**Conditions**:
- ✅ All policy checks pass
- ✅ No destructive changes (no resource deletions)
- ✅ Artifact attestation verified
- ✅ Valid provenance chain
- ✅ PR approval received (required regardless of decision)

**Result**:
- Plan artifacts uploaded for apply workflow
- GitHub check status: ✅ Success
- Apply workflow can proceed when triggered

**Use Cases**:
- Creating new resources
- Non-destructive updates (configuration changes)
- Adding networks, VLANs, or policies
- Expanding infrastructure

**Example**: Creating a new VLAN and network without deleting any existing resources.

---

### 2. Require Approval (CONDITIONAL PASS) ⚠️

**Decision**: The plan requires explicit human approval with additional context.

**Conditions**:
- ⚠️ Policy checks pass with warnings
- ⚠️ Destructive changes detected (resource deletions)
- ✅ Artifact attestation verified
- ✅ Valid provenance chain
- ✅ PR approval received
- ❌ Deletion approval flag NOT set (requires explicit approval)

**Result**:
- GitHub check status: ⚠️ Neutral or ⚠️ Failure (depends on configuration)
- Plan artifacts NOT uploaded (blocks apply workflow)
- Requires manual workflow re-trigger with `deletion_approved: true`
- Human review mandatory before proceeding

**Use Cases**:
- Deleting resources (VLANs, networks, firewall rules)
- Replacing resources (delete + create)
- High-impact changes requiring oversight
- Changes affecting production networks

**Example**: Removing a VLAN that is no longer needed requires explicit approval flag.

---

### 3. Deny (FAIL) ❌

**Decision**: The plan is rejected and cannot proceed.

**Conditions**:
- ❌ One or more policy checks fail
- ❌ Artifact attestation verification failed
- ❌ Invalid or missing provenance
- ❌ Missing PR approval information
- ❌ Policy violation detected

**Result**:
- GitHub check status: ❌ Failure
- Workflow fails immediately
- Plan artifacts NOT uploaded
- Apply workflow cannot proceed
- Requires fixing the violation before retry

**Use Cases**:
- Unattested artifacts (security boundary violation)
- Missing provenance information
- Invalid or tampered artifacts
- Policy rule violations
- Missing required approvals

**Example**: Attempting to use artifacts from an unverified source or bypassing attestation.

---

## Decision Flow

The decision engine evaluates plans through a multi-stage process:

### Stage 1: PR Approval Gate

```
┌─────────────────────────────────────┐
│   GitHub Pull Request Created       │
│   (references render artifacts)     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Await PR Review & Approval        │
│   (human authorization required)    │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴────────┐
      │  PR Approved?  │
      └───────┬────────┘
              │
        Yes   │   No
      ┌───────┴────────┐
      ▼                ▼
   Proceed      Stop (no trigger)
```

**Key Points**:
- PR approval is ALWAYS required (cannot be bypassed)
- Approval triggers the terraform-plan workflow
- No approval = workflow never runs
- This gate is enforced by GitHub Actions event triggers

---

### Stage 2: Artifact Verification

```
┌─────────────────────────────────────┐
│   Download Artifacts                │
│   (from render workflow)            │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Verify Attestations               │
│   (cryptographic verification)      │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴────────┐
      │  Attestation   │
      │   Verified?    │
      └───────┬────────┘
              │
        Yes   │   No
      ┌───────┴────────┐
      ▼                ▼
   Proceed      DENY ❌
                (fail workflow)
```

**Key Points**:
- Attestation verification is MANDATORY
- Failed verification = immediate workflow failure (fail-closed)
- No bypass mechanism exists
- Enforced by verify-attestation composite action

---

### Stage 3: Terraform Plan Generation

```
┌─────────────────────────────────────┐
│   Terraform Init                    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Terraform Plan                    │
│   (generate binary + JSON)          │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴────────┐
      │  Plan Success? │
      └───────┬────────┘
              │
        Yes   │   No
      ┌───────┴────────┐
      ▼                ▼
   Proceed      DENY ❌
                (fail workflow)
```

**Key Points**:
- Plan generation must succeed
- Both binary and JSON formats created
- JSON format used for policy evaluation
- Plan failure = workflow failure

---

### Stage 4: Policy Evaluation (DECISION POINT)

```
┌─────────────────────────────────────┐
│   Prepare Policy Input              │
│   (plan JSON + metadata)            │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   OPA Policy Evaluation             │
│   (deterministic evaluation)        │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴────────────────────────┐
      │   Decision Outcome?            │
      └───────┬────────────────────────┘
              │
      ┌───────┼────────┐
      │       │        │
      ▼       ▼        ▼
   AUTO-   REQUIRE   DENY
   APPROVE APPROVAL   ❌
     ✅       ⚠️
      │       │        │
      ▼       ▼        │
   Upload  Block      │
   Artifacts Upload   │
      │       │        │
      └───────┴────────┴─ All decisions logged
```

**Decision Logic**:

```
IF attestation_verified == false THEN
    OUTCOME = DENY ❌
    MESSAGE = "Artifact attestation verification failed"

ELSE IF has_destructive_changes AND NOT deletion_approved THEN
    OUTCOME = REQUIRE APPROVAL ⚠️
    MESSAGE = "Destructive changes detected - explicit approval required"

ELSE IF all_policy_checks_pass THEN
    OUTCOME = AUTO-APPROVE ✅
    MESSAGE = "All policy checks passed"

ELSE
    OUTCOME = DENY ❌
    MESSAGE = "Policy violation: <specific violation>"
```

**Key Points**:
- This is the PRIMARY decision point
- Evaluation is deterministic (same inputs → same output)
- All three outcomes are possible
- Decision is logged with full context

---

### Stage 5: Outcome Enforcement

```
         Decision Outcome
                │
        ┌───────┼────────┐
        │       │        │
        ▼       ▼        ▼
   AUTO-    REQUIRE   DENY
   APPROVE  APPROVAL   ❌
     ✅       ⚠️
        │       │        │
        ▼       ▼        ▼
   Upload  Fail      Fail
   Plan    Workflow  Workflow
   Artifacts  (no    (stop)
   (proceed)  upload)
        │       │        │
        ▼       ▼        ▼
   Apply   Re-trigger Investigate
   Workflow with     Violation
   Enabled  deletion_  Fix Issue
           approved=   Retry
           true
```

**Enforcement Actions**:

| Outcome | Workflow Status | Artifacts Uploaded | Apply Allowed | Next Steps |
|---------|----------------|-------------------|---------------|-----------|
| **Auto-Approve ✅** | Success | ✅ Yes | ✅ Yes | Trigger apply workflow |
| **Require Approval ⚠️** | Failure | ❌ No | ❌ No | Re-run with approval flag |
| **Deny ❌** | Failure | ❌ No | ❌ No | Fix violation, retry |

---

## Policy-Driven Decisions

All decisions are driven by OPA policy evaluation. Policies are defined in `.github/policies/terraform_plan.rego`.

### Policy Structure

```rego
package terraform.plan

# Main decision rule
default allow := false

allow if {
    count(deny) == 0
}

# Denial rules (checked in order)
deny contains msg if {
    not artifact_attested
    msg := "Artifact attestation verification failed"
}

deny contains msg if {
    has_destructive_changes
    not deletion_approved
    msg := "Destructive changes require explicit approval"
}

# Helper rules
artifact_attested if {
    input.metadata.provenance.attestation_verified == true
}

has_destructive_changes if {
    count(resources_to_delete) > 0
}

deletion_approved if {
    input.metadata.deletion_approved == true
}
```

### Policy Decision Mapping

| Policy Check | Pass Result | Fail Result | Outcome Influence |
|-------------|-------------|-------------|-------------------|
| **Attestation Verified** | Continue evaluation | DENY ❌ | Blocking (fail-closed) |
| **No Destructive Changes** | AUTO-APPROVE ✅ | Check approval flag | Conditional |
| **Deletion Approved** | AUTO-APPROVE ✅ | REQUIRE APPROVAL ⚠️ | Conditional |
| **Valid Provenance** | Continue evaluation | DENY ❌ | Blocking (fail-closed) |
| **PR Approval Present** | Continue evaluation | DENY ❌ | Blocking (fail-closed) |

### Policy Inputs

Policies receive structured JSON input:

```json
{
  "plan": {
    "resource_changes": [ /* Terraform plan JSON */ ]
  },
  "metadata": {
    "artifact": {
      "path": "site-pennington.tfvars.json",
      "site": "pennington"
    },
    "provenance": {
      "render_run_id": "1234567890",
      "attestation_verified": true,
      "pr_number": "42",
      "approver": "username",
      "approved_at": "2024-01-15T10:30:00Z"
    },
    "deletion_approved": false
  }
}
```

See [Policy Input Contract](policy-input-contract.md) for complete input specification.

---

## GitHub PR Integration

The decision model integrates with GitHub Pull Requests through multiple mechanisms:

### 1. PR Approval Requirement

**Enforcement**: GitHub Actions workflow trigger

**Configuration**: `.github/workflows/terraform-plan.yaml`

```yaml
on:
  pull_request_review:
    types: [submitted]

jobs:
  terraform-plan:
    if: github.event.review.state == 'approved'
```

**Behavior**:
- Workflow ONLY triggers on PR approval events
- Cannot be triggered by branch push or other events
- PR approval is captured and logged for traceability

**GitHub Check**: N/A (this is a pre-workflow gate)

---

### 2. Policy Evaluation Check

**Enforcement**: OPA policy evaluation in workflow

**Check Name**: "Policy Evaluation"

**Statuses**:

| Decision Outcome | GitHub Check Status | Icon | Description |
|-----------------|-------------------|------|-------------|
| **Auto-Approve** | ✅ Success | ✅ | All policy checks passed |
| **Require Approval** | ❌ Failure | ⚠️ | Destructive changes need approval |
| **Deny** | ❌ Failure | ❌ | Policy violation detected |

**Check Output**:
```
🔐 Policy Evaluation

Result: pass / fail
Policy Engine: Open Policy Agent (OPA)

Policies Evaluated:
- Artifact attestation verification
- Resource change boundaries
- Destructive change approval

Decision: AUTO-APPROVE / REQUIRE APPROVAL / DENY
Message: <decision-specific message>
```

---

### 3. Workflow Status Check

**Enforcement**: GitHub Actions workflow completion status

**Check Name**: "Terraform Plan / terraform-plan (site)"

**Statuses**:

| Workflow Result | GitHub Check Status | Meaning |
|----------------|-------------------|---------|
| **Success** | ✅ Success | Plan succeeded and policy passed (Auto-Approve) |
| **Failure** | ❌ Failure | Plan failed OR policy failed (Deny or Require Approval) |
| **Cancelled** | ⚪ Cancelled | Workflow cancelled by user |

**Branch Protection**: Can be configured to require this check before merging.

---

### 4. Artifact Upload Status

**Enforcement**: Conditional artifact upload in workflow

**Check Name**: "Upload Plan Artifacts"

**Behavior**:
- Only runs on AUTO-APPROVE ✅ decision
- Skipped on REQUIRE APPROVAL ⚠️ or DENY ❌
- Uploads plan artifacts to GitHub Actions artifacts

**Significance**: Presence of uploaded artifacts indicates the plan is approved for apply.

---

### PR Check Summary

Pull requests display the following checks:

```
Checks:
├─ ✅ Terraform Plan / terraform-plan (pennington) - Success
│  └─ ✅ Policy Evaluation - Passed (Auto-Approve)
│     └─ ✅ Artifact Upload - Completed
│
├─ ❌ Terraform Plan / terraform-plan (countfleetcourt) - Failure
│  └─ ⚠️ Policy Evaluation - Failed (Require Approval)
│     └─ ⏭️ Artifact Upload - Skipped
│
└─ ✅ Other Checks - Success
```

---

## Reviewer Requirements

### Required Reviewers

**Configuration**: GitHub branch protection rules (configured in repository settings)

**Requirement**: At least 1 approving review required

**Enforcement Level**: MANDATORY (enforced by GitHub)

**Who Can Approve**:
- Repository maintainers (configurable)
- Code owners (if CODEOWNERS file exists)
- Users with write access (configurable)

**Recommended Configuration**:
```
Settings → Branches → Branch protection rules for 'main'
  [x] Require pull request reviews before merging
      Number of required approvals: 1
      [x] Dismiss stale pull request approvals when new commits are pushed
      [ ] Require review from Code Owners (optional)
```

---

### Approval Workflow

```
┌─────────────────────────────────────┐
│  1. Developer creates PR            │
│     - References render run ID      │
│     - Describes changes             │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  2. Reviewer examines PR            │
│     - Reviews plan summary          │
│     - Checks artifact source        │
│     - Validates changes             │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴────────┐
      │  Approve PR?   │
      └───────┬────────┘
              │
        Yes   │   No
      ┌───────┴────────┐
      ▼                ▼
   Approve      Request Changes
   (trigger    (block workflow)
   workflow)
      │
      ▼
┌─────────────────────────────────────┐
│  3. Terraform Plan Workflow Runs    │
│     - Downloads artifacts           │
│     - Generates plan                │
│     - Evaluates policy              │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌───────┴──────────────────┐
      │  Policy Decision         │
      │  (Auto/Approve/Deny)     │
      └──────────────────────────┘
```

---

### Special Case: Destructive Changes

When a plan contains destructive changes (resource deletions), an additional approval step is required:

```
┌─────────────────────────────────────┐
│  PR Approved (initial)              │
│  Workflow runs → REQUIRE APPROVAL   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Reviewer validates deletion        │
│  is intentional and safe            │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Re-trigger workflow with:          │
│  deletion_approved: true            │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Policy re-evaluates:               │
│  → AUTO-APPROVE ✅                  │
└─────────────────────────────────────┘
```

**Configuration**: Manual workflow dispatch with `deletion_approved` input

**Enforcement**: Policy checks `input.metadata.deletion_approved` flag

---

## Approval Enforcement

Approval enforcement happens at multiple layers:

### Layer 1: GitHub PR Approval (Pre-Workflow)

**Enforcement Point**: GitHub Actions workflow trigger

**Mechanism**: Workflow only triggers on `pull_request_review` event with `state == 'approved'`

**Bypass Possible**: ❌ No (enforced by GitHub Actions)

**Fail Behavior**: Workflow never runs (no trigger)

---

### Layer 2: Attestation Verification (Workflow)

**Enforcement Point**: verify-attestation composite action

**Mechanism**: Cryptographic verification of SLSA provenance

**Bypass Possible**: ❌ No (fail-closed implementation)

**Fail Behavior**: Immediate workflow failure → DENY ❌

---

### Layer 3: Policy Evaluation (Workflow)

**Enforcement Point**: OPA policy evaluation step

**Mechanism**: Deterministic policy rule evaluation

**Bypass Possible**: ❌ No (no skip flag or override)

**Fail Behavior**: Workflow continues but artifacts not uploaded → Apply blocked

---

### Layer 4: Artifact Upload (Workflow)

**Enforcement Point**: Conditional workflow step

**Mechanism**: Only runs if policy evaluation passes

**Bypass Possible**: ❌ No (conditional on policy result)

**Fail Behavior**: Artifacts not uploaded → Apply cannot proceed

---

### Layer 5: Apply Workflow (Separate Workflow)

**Enforcement Point**: Apply workflow requires plan artifacts

**Mechanism**: Downloads plan artifacts, re-verifies attestations, re-evaluates policy

**Bypass Possible**: ❌ No (requires valid plan run ID and artifacts)

**Fail Behavior**: Apply workflow fails if artifacts missing or invalid

---

### Enforcement Matrix

| Enforcement Layer | Location | Type | Bypass | On Failure |
|------------------|----------|------|--------|-----------|
| **PR Approval** | GitHub | Event-based | ❌ No | No workflow trigger |
| **Attestation** | Workflow | Cryptographic | ❌ No | DENY ❌ |
| **Policy** | Workflow | Logic-based | ❌ No | Workflow failure |
| **Artifact Upload** | Workflow | Conditional | ❌ No | Apply blocked |
| **Apply Re-Check** | Apply Workflow | All of the above | ❌ No | Apply failure |

**Key Principle**: Multiple layers provide defense-in-depth. Bypassing one layer does not bypass others.

---

## Configuration

### Policy Configuration

**File**: `.github/policies/terraform_plan.rego`

**Editable**: Yes (via PR to main branch)

**Format**: Rego policy language

**Example Customizations**:

```rego
# Add custom denial rule
deny contains msg if {
    count(resources_to_create) > 100
    msg := "Plan creates too many resources (>100) - split into smaller changes"
}

# Add resource type restrictions
deny contains msg if {
    some resource in input.plan.resource_changes
    not is_allowed_resource_type(resource.type)
    msg := sprintf("Resource type not allowed: %s", [resource.type])
}
```

---

### Workflow Configuration

**File**: `.github/workflows/terraform-plan.yaml`

**Key Settings**:

```yaml
# Sites to evaluate (matrix)
strategy:
  matrix:
    site: [pennington, countfleetcourt]

# Trigger configuration (DO NOT CHANGE)
on:
  pull_request_review:
    types: [submitted]
```

**Warning**: Changing trigger configuration may bypass security boundaries.

---

### Branch Protection Configuration

**Location**: GitHub repository settings → Branches → Branch protection rules

**Recommended Settings**:

```
Branch name pattern: main

Protect matching branches:
  [x] Require pull request reviews before merging
      Number of required approvals: 1
      [x] Dismiss stale pull request approvals when new commits are pushed

  [x] Require status checks to pass before merging
      [x] Require branches to be up to date before merging
      Status checks:
          [x] Terraform Plan / terraform-plan (pennington)
          [x] Terraform Plan / terraform-plan (countfleetcourt)

  [x] Include administrators (recommended for consistency)
```

**Effect**: Enforces that all PRs must pass policy evaluation before merge.

---

## Examples

### Example 1: Auto-Approve (Creating Resources)

**Scenario**: Adding a new VLAN and network to a site

**Plan Changes**:
```
+ unifi_network.guest_wifi
+ unifi_vlan.guest_vlan
```

**Policy Evaluation**:
- ✅ Attestation verified
- ✅ No destructive changes
- ✅ Valid provenance
- ✅ PR approval present

**Decision**: AUTO-APPROVE ✅

**Outcome**:
- Workflow succeeds
- Plan artifacts uploaded
- Apply workflow can proceed
- GitHub check: ✅ Success

**Next Steps**: Trigger apply workflow when ready

---

### Example 2: Require Approval (Deleting Resources)

**Scenario**: Removing an unused VLAN

**Plan Changes**:
```
- unifi_network.old_network
- unifi_vlan.old_vlan
```

**Policy Evaluation** (Initial):
- ✅ Attestation verified
- ⚠️ Destructive changes detected
- ❌ Deletion approval flag NOT set
- ✅ Valid provenance
- ✅ PR approval present

**Decision**: REQUIRE APPROVAL ⚠️

**Outcome**:
- Workflow fails
- Artifacts NOT uploaded
- GitHub check: ⚠️ Failure with message "Destructive changes require explicit approval"

**Next Steps**:
1. Reviewer validates deletion is intentional
2. Re-trigger workflow with `deletion_approved: true`
3. Policy re-evaluates → AUTO-APPROVE ✅
4. Artifacts uploaded
5. Apply workflow can proceed

---

### Example 3: Deny (Attestation Failure)

**Scenario**: Attempting to use unattested artifacts

**Policy Evaluation**:
- ❌ Attestation verification FAILED
- (other checks not evaluated - fail fast)

**Decision**: DENY ❌

**Outcome**:
- Workflow fails immediately
- No plan generation
- No artifacts uploaded
- GitHub check: ❌ Failure with message "Artifact attestation verification failed"

**Next Steps**:
1. Investigate attestation failure
2. Verify artifacts are from authorized render workflow
3. Re-run render workflow if needed
4. Update PR with valid render run ID
5. Re-trigger plan workflow

---

### Example 4: Deny (Policy Violation)

**Scenario**: Plan attempts to create disallowed resource type

**Plan Changes**:
```
+ custom_resource.disallowed_type
```

**Policy Evaluation**:
- ✅ Attestation verified
- ❌ Resource type not in allowed list
- ✅ Valid provenance
- ✅ PR approval present

**Decision**: DENY ❌

**Outcome**:
- Plan generated but rejected by policy
- Workflow fails
- Artifacts NOT uploaded
- GitHub check: ❌ Failure with message "Resource type not allowed: custom_resource"

**Next Steps**:
1. Review policy for allowed resource types
2. Either:
   - Update plan to use allowed resource type, OR
   - Update policy to allow the resource type (requires separate PR)
3. Re-trigger plan workflow

---

## Troubleshooting

### Decision Outcomes Not As Expected

**Problem**: Policy evaluation produces unexpected decision outcome

**Diagnosis**:
1. Review workflow logs for policy evaluation step
2. Check policy input document (plan JSON + metadata)
3. Verify policy rules in `.github/policies/terraform_plan.rego`

**Solution**:
```bash
# Test policy locally with actual inputs
./opa eval --bundle .github/policies/ \
  --input policy-input.json \
  --format pretty \
  'data.terraform.plan'

# Get detailed decision information
./opa eval --bundle .github/policies/ \
  --input policy-input.json \
  'data.terraform.plan.deny'
```

---

### Workflow Fails But Should Pass

**Problem**: Workflow fails even though plan looks valid

**Common Causes**:
1. Attestation verification failed
2. Missing PR approval information
3. Invalid provenance metadata
4. Policy rule violation

**Diagnosis**:
1. Check attestation verification step output
2. Verify PR approval was recorded
3. Review policy evaluation step logs
4. Check for violations in policy output

**Solution**: Address the specific failure cause identified in logs.

---

### Cannot Trigger Apply Workflow

**Problem**: Apply workflow cannot find plan artifacts

**Cause**: Plan workflow did not upload artifacts (decision was not AUTO-APPROVE)

**Diagnosis**:
1. Check terraform-plan workflow result
2. Verify policy evaluation passed
3. Confirm artifact upload step ran

**Solution**: If plan requires approval (destructive changes), re-trigger with `deletion_approved: true`.

---

### Reviewer Cannot Approve PR

**Problem**: PR approval does not trigger workflow

**Common Causes**:
1. User lacks approval permissions
2. Branch protection rules not configured correctly
3. Workflow trigger misconfigured

**Diagnosis**:
1. Verify user has write access to repository
2. Check branch protection rules in settings
3. Review workflow trigger configuration

**Solution**: Ensure user has proper permissions and branch protection is configured correctly.

---

## Explicit Non-Goals

The following are explicitly OUT OF SCOPE for this phase:

### ❌ Ad Hoc or Hardcoded Approval Rules

**Not Implemented**: Hardcoded logic for specific resource types, sites, or changes

**Reason**: All approval logic must be policy-driven and configurable. Hardcoded rules violate the policy-as-code principle and are not maintainable.

**Alternative**: Use OPA policies to define all approval rules declaratively.

---

### ❌ Manual Override or Emergency Bypass

**Not Implemented**: Ability to bypass policy evaluation or force approval despite policy failure

**Reason**: Violates fail-closed security model. All changes must pass policy evaluation without exception.

**Alternative**: If emergency changes are needed, update policy to allow the change (requires separate PR and review).

---

### ❌ Complex Multi-Stage Approval Workflows

**Not Implemented**: Multiple approval stages with different reviewer requirements based on change type

**Reason**: Out of scope for Phase 5. Current model uses single approval + policy evaluation.

**Future**: Could be added in later phases if needed by enhancing policy rules and adding workflow complexity.

---

### ❌ Time-Based or Scheduled Approvals

**Not Implemented**: Approvals that expire after a certain time or scheduled approval windows

**Reason**: Adds complexity and is not currently needed. Approvals are permanent until PR is updated.

**Future**: Could be added if needed by adding time-based checks to policies.

---

### ❌ External Approval Systems

**Not Implemented**: Integration with external approval systems (e.g., ServiceNow, Jira)

**Reason**: Out of scope for Phase 5. All approvals use GitHub native mechanisms.

**Future**: Could be added if needed by creating webhook integrations.

---

## References

### Related Documentation

- **Policy Engine**: [policy-engine.md](policy-engine.md) - OPA integration and evaluation
- **Policy Input Contract**: [policy-input-contract.md](policy-input-contract.md) - Policy input formats
- **Apply Workflow**: [apply-workflow.md](apply-workflow.md) - Terraform apply workflow
- **Security Boundaries**: [../phase4/security.md](../phase4/security.md) - Trust model and boundaries
- **Terraform Plan Workflow**: [../phase4/terraform-plan-approval-workflow.md](../phase4/terraform-plan-approval-workflow.md) - Complete workflow guide

### Implementation Files

- **Policy Files**: `.github/policies/terraform_plan.rego`, `.github/policies/common.rego`
- **Workflow**: `.github/workflows/terraform-plan.yaml` - Plan workflow with policy evaluation
- **Apply Workflow**: `.github/workflows/terraform-apply.yaml` - Apply workflow
- **Attestation Action**: `.github/actions/verify-attestation/` - Attestation verification

### External Standards

- **OPA Documentation**: https://www.openpolicyagent.org/docs/latest/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Branch Protection**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- **SLSA Provenance**: https://slsa.dev/provenance/

---

**Document Status**: Complete

**Phase**: 5

**Review Schedule**: Every phase or when decision model changes

**Acceptance Criteria Met**:
- ✅ Policy-driven decision outcomes (auto-approve, require approval, deny) are defined
- ✅ Decisions are surfaced in GitHub PRs as checks
- ✅ Reviewer/approval rules are configurable
- ✅ Documented in `docs/phase5/approval-decision-model.md`
