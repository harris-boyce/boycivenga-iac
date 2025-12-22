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
#   - summary: Human-readable summary

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

# Deny if there are destructive changes without approval
deny contains msg if {
	has_destructive_changes
	not deletion_approved
	msg := sprintf("Destructive changes detected without deletion approval - %d resource(s) to be deleted", [count(resources_to_delete)])
}

# Deny if plan contains no resource changes (empty plan)
deny contains msg if {
	not has_resource_changes
	msg := "Plan contains no resource changes - may indicate configuration error"
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

# Check if deletion is approved
deletion_approved if {
	input.metadata.deletion_approved == true
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
	some resource in resources_to_delete
	not deletion_approved
	violation := {
		"type": "unapproved_deletion",
		"severity": "high",
		"message": sprintf("Resource deletion without approval: %s", [resource.address]),
		"resource": resource.address,
		"resource_type": resource.type,
	}
}

violations contains violation if {
	not has_resource_changes
	violation := {
		"type": "empty_plan",
		"severity": "medium",
		"message": "Plan contains no resource changes",
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
# SUMMARY
# ==============================================================================

# Human-readable summary of policy evaluation
summary := {
	"allowed": allow,
	"total_resources": count(input.plan.resource_changes),
	"to_create": count(resources_to_create),
	"to_update": count(resources_to_update),
	"to_delete": count(resources_to_delete),
	"violations": count(violations),
	"denial_reasons": count(deny),
	"artifact_attested": artifact_attested,
	"deletion_approved": deletion_approved,
}
