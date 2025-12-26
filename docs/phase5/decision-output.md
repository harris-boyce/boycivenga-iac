# Agent-Consumable Decision Outputs

## Overview

This document describes the structured decision outputs emitted by the policy evaluation engine for Terraform plan operations. These outputs are designed to be both human-readable and machine-parseable, enabling agents and LLMs to understand and explain infrastructure deployment decisions to humans.

**Purpose**: Provide complete context for why approval was required or skipped, which policies fired, and what actions are needed next.

**Status**: Active and Implemented

**Last Updated**: Phase 5

**Document Version**: 1.0.0

## Table of Contents

- [Design Principles](#design-principles)
- [Decision Output Structure](#decision-output-structure)
- [Decision Outcomes](#decision-outcomes)
- [Output Fields](#output-fields)
- [Example Decision Outputs](#example-decision-outputs)
- [Consuming Decision Outputs](#consuming-decision-outputs)
- [Agent Interpretation Guide](#agent-interpretation-guide)
- [Integration Points](#integration-points)
- [Troubleshooting](#troubleshooting)

---

## Design Principles

The decision output format follows these core principles:

### 1. Agent-Consumable Structure

**Principle**: Outputs must be structured JSON that agents/LLMs can easily parse and understand.

**Implementation**:
- Consistent JSON schema across all decision outcomes
- Clear field naming with semantic meaning
- Hierarchical structure for easy navigation
- No ambiguous or overloaded fields

### 2. Human Explainability

**Principle**: Agents must be able to generate clear, accurate explanations for humans.

**Implementation**:
- Human-readable `explanation` field with formatted text
- Contextual information about what changed and why
- Clear next steps for each decision outcome
- Policy-specific messages explaining pass/fail status

### 3. Complete Context

**Principle**: All information needed to understand the decision must be included.

**Implementation**:
- Resource change summary (create/update/delete counts)
- Individual policy evaluation results
- Artifact and provenance metadata
- Timestamp for decision traceability
- Explicit reasons for the outcome

### 4. Consistency

**Principle**: Format must be identical for all decision outcomes.

**Implementation**:
- Same top-level fields regardless of outcome
- Consistent field types and structures
- No optional fields that change based on outcome
- Guaranteed presence of all fields

### 5. Actionability

**Principle**: Outputs must guide users on what to do next.

**Implementation**:
- Explicit `next_steps` array with ordered actions
- Outcome-specific guidance
- Links to relevant resources (when appropriate)
- Clear indication of blocking vs. non-blocking issues

---

## Decision Output Structure

The decision output is emitted as the `data.terraform.plan.decision` OPA rule and contains the following top-level structure:

```json
{
  "outcome": "auto_approve | require_approval | deny",
  "allowed": true | false,
  "approval_required": true | false,
  "reason": "Human-readable reason for the decision",
  "timestamp": 1234567890123456789,
  "policies_evaluated": [...],
  "policy_results": [...],
  "resource_summary": {...},
  "context": {...},
  "violations": [...],
  "next_steps": [...]
}
```

### Schema Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `outcome` | string | ✅ Yes | High-level decision outcome: `auto_approve`, `require_approval`, or `deny` |
| `allowed` | boolean | ✅ Yes | Whether the plan is allowed to proceed (may still require approval) |
| `approval_required` | boolean | ✅ Yes | Whether additional human approval is required |
| `reason` | string | ✅ Yes | Human-readable explanation of why this decision was made |
| `timestamp` | integer | ✅ Yes | Timestamp of decision in nanoseconds since Unix epoch |
| `policies_evaluated` | array | ✅ Yes | List of all policies that were evaluated |
| `policy_results` | array | ✅ Yes | Detailed results for each policy evaluation |
| `resource_summary` | object | ✅ Yes | Summary of resource changes in the plan |
| `context` | object | ✅ Yes | Additional context (artifact, provenance, etc.) |
| `violations` | array | ✅ Yes | List of policy violations (empty if none) |
| `next_steps` | array | ✅ Yes | Ordered list of actions to take next |

---

## Decision Outcomes

The `outcome` field maps to three possible values:

### 1. `auto_approve`

**Meaning**: The plan is automatically approved and ready for apply operations.

**Conditions**:
- All required policies passed
- No destructive changes detected
- Artifact attestation verified
- PR approval present

**Next Action**: Upload plan artifacts and proceed to apply workflow.

---

### 2. `require_approval`

**Meaning**: The plan requires explicit human approval before apply operations.

**Conditions**:
- All required policies passed
- Destructive changes detected (resources to delete)
- Artifact attestation verified
- PR approval present

**Next Action**: Review destructive changes and re-trigger with explicit approval flag.

---

### 3. `deny`

**Meaning**: The plan is denied and cannot proceed to apply operations.

**Conditions**:
- One or more required policies failed
- Common causes: missing attestation, invalid provenance, missing PR approval

**Next Action**: Fix policy violations and re-run the workflow.

---

## Output Fields

### policies_evaluated

**Type**: Array of objects

**Description**: List of all policies that were evaluated during the decision process.

**Schema**:
```json
{
  "name": "policy_name",
  "description": "Human-readable description of what this policy checks"
}
```

**Example**:
```json
[
  {
    "name": "attestation_verification",
    "description": "Verify artifact attestation is present and valid"
  },
  {
    "name": "provenance_validation",
    "description": "Verify provenance information is complete"
  },
  {
    "name": "pr_approval_check",
    "description": "Verify PR approval information is present"
  },
  {
    "name": "destructive_change_gate",
    "description": "Flag destructive changes for additional approval"
  }
]
```

---

### policy_results

**Type**: Array of objects

**Description**: Detailed evaluation results for each policy.

**Schema**:
```json
{
  "policy": "policy_name",
  "passed": true | false,
  "required": true | false,
  "message": "Policy-specific result message"
}
```

**Fields**:
- `policy`: Matches the `name` from `policies_evaluated`
- `passed`: Whether this specific policy check passed
- `required`: Whether this policy is required for approval (blocking)
- `message`: Human-readable message explaining the result

**Example**:
```json
[
  {
    "policy": "attestation_verification",
    "passed": true,
    "required": true,
    "message": "Artifact attestation verified successfully"
  },
  {
    "policy": "destructive_change_gate",
    "passed": false,
    "required": false,
    "message": "2 destructive changes detected"
  }
]
```

**Interpretation**:
- `required: true` + `passed: false` → Blocks approval (outcome = `deny`)
- `required: false` + `passed: false` → Requires additional approval (outcome = `require_approval`)
- All `required: true` policies must pass for plan to be allowed

---

### resource_summary

**Type**: Object

**Description**: Summary of resource changes in the Terraform plan.

**Schema**:
```json
{
  "total": 10,
  "to_create": 5,
  "to_update": 3,
  "to_delete": 2
}
```

**Fields**:
- `total`: Total number of resource changes in the plan
- `to_create`: Number of resources to be created
- `to_update`: Number of resources to be updated in-place
- `to_delete`: Number of resources to be deleted

**Note**: Resources that are replaced (delete + create) are counted in both `to_create` and `to_delete`.

---

### context

**Type**: Object

**Description**: Additional context about the plan evaluation.

**Schema**:
```json
{
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
  "has_destructive_changes": false,
  "artifact_attested": true
}
```

**Fields**:
- `artifact`: Information about the artifact being evaluated
- `provenance`: Provenance chain information (render run, PR, approver)
- `has_destructive_changes`: Quick check for destructive changes
- `artifact_attested`: Quick check for attestation status

---

### violations

**Type**: Array of objects

**Description**: Detailed information about policy violations (empty if none).

**Schema**:
```json
{
  "type": "violation_type",
  "severity": "high | medium | low",
  "message": "Detailed violation message",
  "resource": "affected_resource (if applicable)"
}
```

**Example**:
```json
[
  {
    "type": "attestation_missing",
    "severity": "high",
    "message": "Artifact attestation verification failed",
    "resource": "site-test.tfvars.json"
  }
]
```

---

### next_steps

**Type**: Array of strings

**Description**: Ordered list of actions to take based on the decision outcome.

**Outcome-Specific Examples**:

**Auto-Approve**:
```json
[
  "Plan artifacts will be uploaded for apply workflow",
  "Trigger terraform-apply workflow when ready to deploy",
  "Provide plan_run_id, site, and pr_number to apply workflow"
]
```

**Require Approval**:
```json
[
  "Review destructive changes to ensure they are intentional",
  "Verify resources to be deleted are no longer needed",
  "Re-trigger workflow with deletion_approved: true if approved",
  "Plan artifacts will be uploaded after explicit approval"
]
```

**Deny**:
```json
[
  "Review policy violations listed above",
  "Address each violation (e.g., fix attestation, add PR approval)",
  "Re-run the workflow after fixing issues",
  "Do not attempt to bypass security checks"
]
```

---

## Example Decision Outputs

### Example 1: Auto-Approve (Creating Resources)

**Scenario**: Adding two new resources with no destructive changes.

**Complete Decision Output**:
```json
{
  "outcome": "auto_approve",
  "allowed": true,
  "approval_required": false,
  "reason": "All policy checks passed. No destructive changes detected. Plan is approved for apply.",
  "timestamp": 1766785998043686233,
  "policies_evaluated": [
    {
      "name": "attestation_verification",
      "description": "Verify artifact attestation is present and valid"
    },
    {
      "name": "provenance_validation",
      "description": "Verify provenance information is complete"
    },
    {
      "name": "pr_approval_check",
      "description": "Verify PR approval information is present"
    },
    {
      "name": "destructive_change_gate",
      "description": "Flag destructive changes for additional approval"
    }
  ],
  "policy_results": [
    {
      "policy": "attestation_verification",
      "passed": true,
      "required": true,
      "message": "Artifact attestation verified successfully"
    },
    {
      "policy": "provenance_validation",
      "passed": true,
      "required": true,
      "message": "Provenance information is complete and valid"
    },
    {
      "policy": "pr_approval_check",
      "passed": true,
      "required": true,
      "message": "PR approval information is present"
    },
    {
      "policy": "destructive_change_gate",
      "passed": true,
      "required": false,
      "message": "No destructive changes detected"
    }
  ],
  "resource_summary": {
    "total": 2,
    "to_create": 2,
    "to_update": 0,
    "to_delete": 0
  },
  "context": {
    "artifact": {
      "path": "site-pennington.tfvars.json",
      "site": "pennington"
    },
    "provenance": {
      "render_run_id": "1234567890",
      "attestation_verified": true,
      "pr_number": "42",
      "approver": "testuser",
      "approved_at": "2024-01-15T10:30:00Z"
    },
    "has_destructive_changes": false,
    "artifact_attested": true
  },
  "violations": [],
  "next_steps": [
    "Plan artifacts will be uploaded for apply workflow",
    "Trigger terraform-apply workflow when ready to deploy",
    "Provide plan_run_id, site, and pr_number to apply workflow"
  ]
}
```

**Human Explanation**:
```
✅ DECISION: AUTO-APPROVE

This Terraform plan has been automatically approved for apply operations. 
All policy checks passed and no destructive changes were detected.

POLICY EVALUATION RESULTS:
  • attestation_verification: ✅ PASSED - Artifact attestation verified successfully
  • provenance_validation: ✅ PASSED - Provenance information is complete and valid
  • pr_approval_check: ✅ PASSED - PR approval information is present
  • destructive_change_gate: ✅ PASSED - No destructive changes detected

RESOURCE CHANGES:
  • Total: 2
  • To Create: 2
  • To Update: 0
  • To Delete: 0

NEXT STEPS:
  1. Plan artifacts will be uploaded for apply workflow
  2. Trigger terraform-apply workflow when ready to deploy
  3. Provide plan_run_id, site, and pr_number to apply workflow
```

---

### Example 2: Require Approval (Deleting Resources)

**Scenario**: Removing two resources that are no longer needed.

**Complete Decision Output**:
```json
{
  "outcome": "require_approval",
  "allowed": true,
  "approval_required": true,
  "reason": "Destructive changes detected (2 resources to delete). Human approval required before apply.",
  "timestamp": 1766786100123456789,
  "policies_evaluated": [
    {
      "name": "attestation_verification",
      "description": "Verify artifact attestation is present and valid"
    },
    {
      "name": "provenance_validation",
      "description": "Verify provenance information is complete"
    },
    {
      "name": "pr_approval_check",
      "description": "Verify PR approval information is present"
    },
    {
      "name": "destructive_change_gate",
      "description": "Flag destructive changes for additional approval"
    }
  ],
  "policy_results": [
    {
      "policy": "attestation_verification",
      "passed": true,
      "required": true,
      "message": "Artifact attestation verified successfully"
    },
    {
      "policy": "provenance_validation",
      "passed": true,
      "required": true,
      "message": "Provenance information is complete and valid"
    },
    {
      "policy": "pr_approval_check",
      "passed": true,
      "required": true,
      "message": "PR approval information is present"
    },
    {
      "policy": "destructive_change_gate",
      "passed": false,
      "required": false,
      "message": "2 destructive changes detected"
    }
  ],
  "resource_summary": {
    "total": 2,
    "to_create": 0,
    "to_update": 0,
    "to_delete": 2
  },
  "context": {
    "artifact": {
      "path": "site-countfleetcourt.tfvars.json",
      "site": "countfleetcourt"
    },
    "provenance": {
      "render_run_id": "9876543210",
      "attestation_verified": true,
      "pr_number": "50",
      "approver": "maintainer",
      "approved_at": "2024-01-16T14:00:00Z"
    },
    "has_destructive_changes": true,
    "artifact_attested": true
  },
  "violations": [],
  "next_steps": [
    "Review destructive changes to ensure they are intentional",
    "Verify resources to be deleted are no longer needed",
    "Re-trigger workflow with deletion_approved: true if approved",
    "Plan artifacts will be uploaded after explicit approval"
  ]
}
```

**Human Explanation**:
```
⚠️ DECISION: REQUIRE APPROVAL

This Terraform plan requires explicit human approval before apply operations. 
Destructive changes were detected that need review.

POLICY EVALUATION RESULTS:
  • attestation_verification: ✅ PASSED - Artifact attestation verified successfully
  • provenance_validation: ✅ PASSED - Provenance information is complete and valid
  • pr_approval_check: ✅ PASSED - PR approval information is present
  • destructive_change_gate: ❌ FAILED - 2 destructive changes detected

RESOURCE CHANGES:
  • Total: 2
  • To Create: 0
  • To Update: 0
  • To Delete: 2

RESOURCES TO DELETE:
  • unifi_network.old_network (type: unifi_network)
  • unifi_vlan.old_vlan (type: unifi_vlan)

NEXT STEPS:
  1. Review destructive changes to ensure they are intentional
  2. Verify resources to be deleted are no longer needed
  3. Re-trigger workflow with deletion_approved: true if approved
  4. Plan artifacts will be uploaded after explicit approval
```

---

### Example 3: Deny (Attestation Failure)

**Scenario**: Attempting to use an artifact without valid attestation.

**Complete Decision Output**:
```json
{
  "outcome": "deny",
  "allowed": false,
  "approval_required": false,
  "reason": "Policy evaluation failed: Artifact attestation verification failed - artifact must be attested; PR approval information is missing",
  "timestamp": 1766786200987654321,
  "policies_evaluated": [
    {
      "name": "attestation_verification",
      "description": "Verify artifact attestation is present and valid"
    },
    {
      "name": "provenance_validation",
      "description": "Verify provenance information is complete"
    },
    {
      "name": "pr_approval_check",
      "description": "Verify PR approval information is present"
    },
    {
      "name": "destructive_change_gate",
      "description": "Flag destructive changes for additional approval"
    }
  ],
  "policy_results": [
    {
      "policy": "attestation_verification",
      "passed": false,
      "required": true,
      "message": "Artifact attestation verification failed or missing"
    },
    {
      "policy": "provenance_validation",
      "passed": true,
      "required": true,
      "message": "Provenance information is complete and valid"
    },
    {
      "policy": "pr_approval_check",
      "passed": false,
      "required": true,
      "message": "PR approval information is missing"
    },
    {
      "policy": "destructive_change_gate",
      "passed": true,
      "required": false,
      "message": "No destructive changes detected"
    }
  ],
  "resource_summary": {
    "total": 1,
    "to_create": 1,
    "to_update": 0,
    "to_delete": 0
  },
  "context": {
    "artifact": {
      "path": "site-test.tfvars.json",
      "site": "test"
    },
    "provenance": {
      "render_run_id": "123",
      "attestation_verified": false,
      "pr_number": "",
      "approver": ""
    },
    "has_destructive_changes": false,
    "artifact_attested": false
  },
  "violations": [
    {
      "type": "attestation_missing",
      "severity": "high",
      "message": "Artifact attestation verification failed",
      "resource": "site-test.tfvars.json"
    },
    {
      "type": "missing_approval",
      "severity": "high",
      "message": "PR approval information is missing"
    }
  ],
  "next_steps": [
    "Review policy violations listed above",
    "Address each violation (e.g., fix attestation, add PR approval)",
    "Re-run the workflow after fixing issues",
    "Do not attempt to bypass security checks"
  ]
}
```

**Human Explanation**:
```
❌ DECISION: DENY

This Terraform plan has been denied and cannot proceed to apply operations. 
One or more policy violations were detected.

POLICY EVALUATION RESULTS:
  • attestation_verification: ❌ FAILED - Artifact attestation verification failed or missing
  • provenance_validation: ✅ PASSED - Provenance information is complete and valid
  • pr_approval_check: ❌ FAILED - PR approval information is missing
  • destructive_change_gate: ✅ PASSED - No destructive changes detected

RESOURCE CHANGES:
  • Total: 1
  • To Create: 1
  • To Update: 0
  • To Delete: 0

NEXT STEPS:
  1. Review policy violations listed above
  2. Address each violation (e.g., fix attestation, add PR approval)
  3. Re-run the workflow after fixing issues
  4. Do not attempt to bypass security checks
```

---

## Consuming Decision Outputs

### In GitHub Actions Workflows

The decision output is captured in the terraform-plan workflow:

```yaml
- name: Evaluate Policy with OPA
  id: policy
  run: |
    # ... OPA evaluation ...
    
    # Extract structured decision output
    /tmp/opa eval \
      --bundle .github/policies/ \
      --input policy-input.json \
      --format json \
      'data.terraform.plan.decision' > decision-output.json
    
    # Extract human explanation
    /tmp/opa eval \
      --bundle .github/policies/ \
      --input policy-input.json \
      --format raw \
      'data.terraform.plan.explanation' > decision-explanation.txt
    
    # Parse outcome for workflow control
    OUTCOME=$(jq -r '.result.outcome' decision-output.json)
    echo "outcome=${OUTCOME}" >> $GITHUB_OUTPUT
```

### Upload as Artifact

Decision outputs can be uploaded as workflow artifacts for downstream consumption:

```yaml
- name: Upload Decision Output
  uses: actions/upload-artifact@v4
  with:
    name: decision-output-${{ matrix.site }}
    path: |
      decision-output.json
      decision-explanation.txt
    retention-days: 90
```

### In Apply Workflow

The apply workflow can download and include decision context:

```yaml
- name: Download Decision Output
  uses: actions/download-artifact@v4
  with:
    name: decision-output-${{ inputs.site }}
    run-id: ${{ inputs.plan_run_id }}

- name: Include Decision Context
  run: |
    echo "## Original Decision Context" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo '```json' >> $GITHUB_STEP_SUMMARY
    cat decision-output.json >> $GITHUB_STEP_SUMMARY
    echo '```' >> $GITHUB_STEP_SUMMARY
```

---

## Agent Interpretation Guide

### For Agents and LLMs

When consuming these decision outputs, agents should:

1. **Parse the JSON structure** to extract decision details
2. **Use the `explanation` field** as a starting point for human communication
3. **Check `outcome` field** to determine high-level decision
4. **Review `policy_results`** to identify which policies passed/failed
5. **Present `next_steps`** to guide the user on what to do
6. **Highlight violations** (if any) with severity levels

### Example Agent Response Template

```
Based on the policy evaluation, I can explain the decision:

The Terraform plan was [AUTO-APPROVED / REQUIRES APPROVAL / DENIED].

Here's what happened:
- [Summary from `reason` field]

Policy Checks:
[For each policy in `policy_results`]
- [policy name]: [✅ PASSED / ❌ FAILED] - [message]

Resource Changes:
- [X] resources will be created
- [Y] resources will be updated  
- [Z] resources will be deleted

[If outcome is not auto_approve:]
What you need to do:
[Present each item from `next_steps`]

[If violations exist:]
⚠️ Issues Detected:
[For each violation]
- [message] (severity: [severity])
```

### Handling Different Outcomes

**Auto-Approve**:
- Congratulate the user
- Emphasize that all checks passed
- Guide them to trigger apply workflow
- Provide specific parameters needed

**Require Approval**:
- Explain what destructive changes were detected
- List resources to be deleted
- Ask user to review and confirm intentionality
- Explain how to provide explicit approval

**Deny**:
- Be clear that the plan cannot proceed
- Highlight each violation
- Provide specific remediation steps
- Do NOT suggest bypassing security checks

---

## Integration Points

### With Terraform Plan Workflow

**File**: `.github/workflows/terraform-plan.yaml`

**Integration**:
- Policy evaluation step extracts both `decision` and `explanation` outputs
- Workflow uses `outcome` to control artifact upload
- Step summary includes human explanation
- Decision output uploaded as artifact

### With Terraform Apply Workflow

**File**: `.github/workflows/terraform-apply.yaml`

**Integration**:
- Apply workflow downloads decision output from plan run
- Re-validates decision context
- Includes decision in apply metadata
- References original decision in apply summary

### With Policy Files

**File**: `.github/policies/terraform_plan.rego`

**Outputs**:
- `data.terraform.plan.decision` - Structured decision output
- `data.terraform.plan.explanation` - Human-readable explanation
- `data.terraform.plan.summary` - Legacy summary (for backwards compatibility)
- `data.terraform.plan.allow` - Boolean decision
- `data.terraform.plan.deny` - Array of denial reasons

---

## Troubleshooting

### Decision Output Not Generated

**Symptom**: OPA evaluation succeeds but decision output is missing.

**Possible Causes**:
- OPA version mismatch
- Policy file syntax error
- Input document malformed

**Resolution**:
```bash
# Test policy locally
/tmp/opa eval --bundle .github/policies/ \
  --input test-input.json \
  --format pretty \
  'data.terraform.plan.decision'

# Check for policy errors
/tmp/opa check .github/policies/
```

### Inconsistent Decision Outcomes

**Symptom**: Same plan produces different outcomes on different runs.

**Possible Causes**:
- Non-deterministic policy logic (NOT EXPECTED - report as bug)
- Different input metadata between runs
- Timestamp-based logic (should not affect decision)

**Resolution**:
- Compare input documents between runs
- Verify metadata consistency
- Report any true non-determinism as a policy bug

### Agent Cannot Parse Output

**Symptom**: Agent fails to consume decision output JSON.

**Possible Causes**:
- Malformed JSON in workflow
- Missing fields in output
- Schema version mismatch

**Resolution**:
- Validate JSON with `jq` or JSON validator
- Verify all required fields present
- Check OPA policy outputs complete structure

---

## Explicit Non-Goals

The following are explicitly OUT OF SCOPE for decision outputs:

### ❌ Unstructured Log-Based Communication

**Not Implemented**: Agents parsing raw workflow logs to understand decisions.

**Reason**: Logs are not guaranteed to be structured or stable. Decision outputs must be explicit and structured.

### ❌ External Decision Storage

**Not Implemented**: Storing decision outputs in external systems (databases, APIs).

**Reason**: Decision outputs are captured as workflow artifacts. External storage is out of scope for this phase.

### ❌ Real-Time Decision Streaming

**Not Implemented**: Streaming decision updates as policy evaluation progresses.

**Reason**: Policy evaluation is fast and atomic. Streaming is unnecessary complexity.

### ❌ Multi-Version Schema Support

**Not Implemented**: Supporting multiple decision output schema versions simultaneously.

**Reason**: Single schema version simplifies consumption. Schema evolution will be handled through versioned documentation.

---

## References

### Related Documentation

- [Approval Decision Model](approval-decision-model.md) - Decision engine and outcomes
- [Policy Engine](policy-engine.md) - OPA integration and evaluation
- [Policy Input Contract](policy-input-contract.md) - Input format specification
- [Apply Workflow](apply-workflow.md) - Terraform apply workflow
- [Terraform Plan Workflow](../phase4/terraform-plan-approval-workflow.md) - Plan approval process

### Implementation Files

- **Policy File**: `.github/policies/terraform_plan.rego` - Decision output generation
- **Plan Workflow**: `.github/workflows/terraform-plan.yaml` - Decision output capture
- **Apply Workflow**: `.github/workflows/terraform-apply.yaml` - Decision context inclusion

### External Standards

- **OPA Documentation**: https://www.openpolicyagent.org/docs/latest/
- **JSON Schema**: https://json-schema.org/
- **ISO 8601 Timestamps**: https://en.wikipedia.org/wiki/ISO_8601

---

**Document Status**: Complete

**Phase**: 5

**Review Schedule**: Every phase or when decision output format changes

**Acceptance Criteria Met**:
- ✅ Decision outputs are structured and documented
- ✅ Output format consistent/generateable for all apply events
- ✅ Example explanations provided in `docs/phase5/decision-output.md`
- ✅ Agent and human explainability ensured together
