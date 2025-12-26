# Terraform Plan Policy
#
# This policy evaluates Terraform plans to enforce organizational standards
# and security requirements before infrastructure changes are applied.
#
# Package: terraform.plan
# Inputs:
#   - input.plan: Terraform plan JSON (from `terraform show -json`)
#   - input.metadata: Artifact and provenance metadata
#
# Outputs:
#   - allow: Boolean indicating if plan is approved
#   - deny: Array of denial reasons
#   - violations: Detailed violation information
#   - summary: Human-readable summary (legacy)
#   - approval_required: Boolean indicating if human approval is required before apply
#   - decision: Structured decision output (agent-consumable) with complete context
#   - explanation: Human-readable explanation of the decision

package terraform.plan

import future.keywords.contains
import future.keywords.if
import future.keywords.in

# ==============================================================================
# MAIN DECISION RULE
# ==============================================================================

# Default deny - plan must explicitly pass all checks
default allow := false

# Allow if there are no denial reasons
allow if {
	count(deny) == 0
}

# ==============================================================================
# DENIAL RULES
# ==============================================================================

# Deny if artifact attestation is not verified
deny contains msg if {
	not artifact_attested
	msg := "Artifact attestation verification failed - artifact must be attested"
}

# Deny if provenance information is missing
deny contains msg if {
	not has_valid_provenance
	msg := "Missing or invalid provenance information"
}

# Deny if PR approval information is missing
deny contains msg if {
	not has_pr_approval
	msg := "PR approval information is missing"
}

# ==============================================================================
# APPROVAL REQUIREMENT RULES
# ==============================================================================

# Human approval is required if there are destructive changes
# This does NOT deny the plan, but indicates additional approval is needed
default approval_required := false

approval_required if {
	has_destructive_changes
}

# ==============================================================================
# HELPER RULES - ATTESTATION
# ==============================================================================

# Check if artifact is attested
artifact_attested if {
	input.metadata.provenance.attestation_verified == true
}

# ==============================================================================
# HELPER RULES - PROVENANCE
# ==============================================================================

# Check if provenance information is valid
has_valid_provenance if {
	input.metadata.provenance.render_run_id
	count(input.metadata.provenance.render_run_id) > 0
}

# ==============================================================================
# HELPER RULES - APPROVAL
# ==============================================================================

# Check if PR approval is present
has_pr_approval if {
	input.metadata.provenance.pr_number
	input.metadata.provenance.approver
}

# ==============================================================================
# HELPER RULES - RESOURCE CHANGES
# ==============================================================================

# Check if plan has any resource changes
has_resource_changes if {
	count(input.plan.resource_changes) > 0
}

# Check if plan has destructive changes (delete or replace)
has_destructive_changes if {
	count(resources_to_delete) > 0
}

# Get list of resources to be deleted
resources_to_delete contains resource if {
	some resource in input.plan.resource_changes
	"delete" in resource.change.actions
}

# Get list of resources to be created
resources_to_create contains resource if {
	some resource in input.plan.resource_changes
	"create" in resource.change.actions
	not "delete" in resource.change.actions
}

# Get list of resources to be updated
resources_to_update contains resource if {
	some resource in input.plan.resource_changes
	"update" in resource.change.actions
}

# ==============================================================================
# VIOLATION DETAILS
# ==============================================================================

# Detailed violation information for reporting
violations contains violation if {
	not artifact_attested
	violation := {
		"type": "attestation_missing",
		"severity": "high",
		"message": "Artifact attestation verification failed",
		"resource": input.metadata.artifact.path,
	}
}

violations contains violation if {
	not has_valid_provenance
	violation := {
		"type": "missing_provenance",
		"severity": "high",
		"message": "Missing or invalid provenance information",
	}
}

violations contains violation if {
	not has_pr_approval
	violation := {
		"type": "missing_approval",
		"severity": "high",
		"message": "PR approval information is missing",
	}
}

# ==============================================================================
# STRUCTURED DECISION OUTPUT (AGENT-CONSUMABLE)
# ==============================================================================

# Structured decision output that provides complete context for agents/LLMs
# to explain the decision to humans. This includes outcome, reasoning, policies
# evaluated, and actionable next steps.
decision := result if {
	result := {
		"outcome": _decision_outcome,
		"allowed": allow,
		"approval_required": approval_required,
		"reason": _decision_reason,
		"timestamp": time.now_ns(),
		"policies_evaluated": _policies_evaluated,
		"policy_results": _policy_results,
		"resource_summary": {
			"total": count(input.plan.resource_changes),
			"to_create": count(resources_to_create),
			"to_update": count(resources_to_update),
			"to_delete": count(resources_to_delete),
		},
		"context": {
			"artifact": input.metadata.artifact,
			"provenance": input.metadata.provenance,
			"has_destructive_changes": _has_destructive,
			"artifact_attested": _is_attested,
		},
		"violations": violations,
		"next_steps": _next_steps,
	}
}

# Determine the high-level decision outcome
_decision_outcome := "auto_approve" if {
	allow
	not approval_required
} else := "require_approval" if {
	allow
	approval_required
} else := "deny"

# Generate human-readable reason for the decision
_decision_reason := reason if {
	allow
	not approval_required
	reason := "All policy checks passed. No destructive changes detected. Plan is approved for apply."
} else := reason if {
	allow
	approval_required
	reason := sprintf("Destructive changes detected (%d resources to delete). Human approval required before apply.", [count(resources_to_delete)])
} else := reason if {
	not allow
	count(deny) > 0
	reason := sprintf("Policy evaluation failed: %s", [concat("; ", deny)])
}

# List of policies that were evaluated
_policies_evaluated := [
	{"name": "attestation_verification", "description": "Verify artifact attestation is present and valid"},
	{"name": "provenance_validation", "description": "Verify provenance information is complete"},
	{"name": "pr_approval_check", "description": "Verify PR approval information is present"},
	{"name": "destructive_change_gate", "description": "Flag destructive changes for additional approval"},
]

# Detailed results for each policy
_policy_results := result if {
	result := [
		{
			"policy": "attestation_verification",
			"passed": _is_attested,
			"required": true,
			"message": _attestation_message,
		},
		{
			"policy": "provenance_validation",
			"passed": has_valid_provenance,
			"required": true,
			"message": _provenance_message,
		},
		{
			"policy": "pr_approval_check",
			"passed": has_pr_approval,
			"required": true,
			"message": _pr_approval_message,
		},
		{
			"policy": "destructive_change_gate",
			"passed": _no_destructive_changes,
			"required": false,
			"message": _destructive_change_message,
		},
	]
}

# Helper for destructive changes check
_no_destructive_changes := true if {
	not has_destructive_changes
} else := false

# Policy-specific messages
_attestation_message := "Artifact attestation verified successfully" if {
	_is_attested
} else := "Artifact attestation verification failed or missing"

_provenance_message := "Provenance information is complete and valid" if {
	has_valid_provenance
} else := "Provenance information is missing or invalid"

_pr_approval_message := "PR approval information is present" if {
	has_pr_approval
} else := "PR approval information is missing"

_destructive_change_message := sprintf("%d destructive changes detected", [count(resources_to_delete)]) if {
	has_destructive_changes
} else := "No destructive changes detected"

# Next steps based on decision outcome
_next_steps := steps if {
	_decision_outcome == "auto_approve"
	steps := [
		"Plan artifacts will be uploaded for apply workflow",
		"Trigger terraform-apply workflow when ready to deploy",
		"Provide plan_run_id, site, and pr_number to apply workflow",
	]
} else := steps if {
	_decision_outcome == "require_approval"
	steps := [
		"Review destructive changes to ensure they are intentional",
		"Verify resources to be deleted are no longer needed",
		"Re-trigger workflow with deletion_approved: true if approved",
		"Plan artifacts will be uploaded after explicit approval",
	]
} else := steps if {
	_decision_outcome == "deny"
	steps := [
		"Review policy violations listed above",
		"Address each violation (e.g., fix attestation, add PR approval)",
		"Re-run the workflow after fixing issues",
		"Do not attempt to bypass security checks",
	]
}

# ==============================================================================
# HUMAN-READABLE EXPLANATION
# ==============================================================================

# Generate a complete human-readable explanation of the decision
explanation := text if {
	text := sprintf("%s\n\n%s\n\n%s\n\n%s", [
		_explanation_header,
		_explanation_policies,
		_explanation_resources,
		_explanation_next_steps,
	])
}

_explanation_header := header if {
	_decision_outcome == "auto_approve"
	header := "✅ DECISION: AUTO-APPROVE\n\nThis Terraform plan has been automatically approved for apply operations. All policy checks passed and no destructive changes were detected."
} else := header if {
	_decision_outcome == "require_approval"
	header := "⚠️ DECISION: REQUIRE APPROVAL\n\nThis Terraform plan requires explicit human approval before apply operations. Destructive changes were detected that need review."
} else := header if {
	_decision_outcome == "deny"
	header := "❌ DECISION: DENY\n\nThis Terraform plan has been denied and cannot proceed to apply operations. One or more policy violations were detected."
}

_explanation_policies := text if {
	text := sprintf("POLICY EVALUATION RESULTS:\n%s", [concat("\n", [
		sprintf("  • %s: %s - %s", [
			result.policy,
			_pass_fail_label(result.passed),
			result.message,
		]) |
		result := _policy_results[_]
	])])
}

_pass_fail_label(passed) := "✅ PASSED" if {
	passed
} else := "❌ FAILED"

_explanation_resources := text if {
	text := sprintf("RESOURCE CHANGES:\n  • Total: %d\n  • To Create: %d\n  • To Update: %d\n  • To Delete: %d%s", [
		count(input.plan.resource_changes),
		count(resources_to_create),
		count(resources_to_update),
		count(resources_to_delete),
		_resource_details,
	])
}

_resource_details := details if {
	count(resources_to_delete) > 0
	details := sprintf("\n\nRESOURCES TO DELETE:\n%s", [concat("\n", [
		sprintf("  • %s (type: %s)", [resource.address, resource.type]) |
		resource := resources_to_delete[_]
	])])
} else := ""

_explanation_next_steps := text if {
	text := sprintf("NEXT STEPS:\n%s", [concat("\n", [
		sprintf("  %d. %s", [i + 1, step]) |
		step := _next_steps[i]
	])])
}

# ==============================================================================
# SUMMARY (LEGACY - Kept for backwards compatibility)
# ==============================================================================

# Human-readable summary of policy evaluation
summary := result if {
	result := {
		"allowed": allow,
		"approval_required": approval_required,
		"total_resources": count(input.plan.resource_changes),
		"to_create": count(resources_to_create),
		"to_update": count(resources_to_update),
		"to_delete": count(resources_to_delete),
		"violations": count(violations),
		"denial_reasons": count(deny),
		"artifact_attested": _is_attested,
		"has_destructive_changes": _has_destructive,
	}
}

# Helper to safely get attestation status
_is_attested := true if {
	artifact_attested
} else := false

# Helper to safely get destructive changes status
_has_destructive := true if {
	has_destructive_changes
} else := false
