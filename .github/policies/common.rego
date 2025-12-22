# Common Policy Helpers
#
# This module contains reusable helper functions and rules that can be used
# across multiple policy files.
#
# Package: terraform.common

package terraform.common

import future.keywords.contains
import future.keywords.if
import future.keywords.in

# ==============================================================================
# RESOURCE TYPE HELPERS
# ==============================================================================

# List of allowed UniFi resource types
allowed_resource_types := {
	"unifi_network",
	"unifi_port_profile",
	"unifi_user",
	"unifi_wlan",
	"unifi_firewall_rule",
	"unifi_firewall_group",
	"unifi_static_route",
	"unifi_site",
}

# Check if a resource type is allowed
is_allowed_resource_type(resource_type) if {
	resource_type in allowed_resource_types
}

# Extract resource type from full resource address
# Example: "unifi_network.management" -> "unifi_network"
resource_type_from_address(address) := parts[0] if {
	parts := split(address, ".")
	count(parts) > 0
}

# ==============================================================================
# CHANGE ACTION HELPERS
# ==============================================================================

# Check if a change is destructive (delete or replace)
is_destructive(change) if {
	"delete" in change.actions
}

# Check if a change is creation only
is_create_only(change) if {
	change.actions == ["create"]
}

# Check if a change is update only (no-op or update)
is_update_only(change) if {
	"update" in change.actions
	not "delete" in change.actions
}

# Check if a change is no-op
is_noop(change) if {
	change.actions == ["no-op"]
}

# ==============================================================================
# STRING HELPERS
# ==============================================================================

# Check if a string starts with a prefix
starts_with(str, prefix) if {
	startswith(str, prefix)
}

# Check if a string contains a substring
string_contains(str, substr) if {
	contains(str, substr)
}

# ==============================================================================
# ARRAY HELPERS
# ==============================================================================

# Check if an array is empty
is_empty(arr) if {
	count(arr) == 0
}

# Check if an array is not empty
is_not_empty(arr) if {
	count(arr) > 0
}

# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

# Check if a value is null or undefined
is_null_or_undefined(value) if {
	value == null
}

is_null_or_undefined(value) if {
	not value
}

# Check if a string is non-empty
is_non_empty_string(str) if {
	is_string(str)
	count(str) > 0
}

# ==============================================================================
# ATTESTATION HELPERS
# ==============================================================================

# Check if attestation data structure is valid
has_attestation_structure(metadata) if {
	metadata.provenance
	metadata.provenance.attestation_verified
}

# Check if provenance includes required fields
has_complete_provenance(metadata) if {
	metadata.provenance.render_run_id
	metadata.provenance.attestation_verified
}
