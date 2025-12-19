# Main Terraform configuration for UniFi infrastructure management
# This configuration uses site-specific tfvars files generated from NetBox exports

# UniFi Provider Configuration
# The provider is configured via environment variables or stub values
# This allows the configuration to be decoupled from artifact generation
provider "unifi" {
  # Configuration options:
  # - username: UniFi controller username (env: UNIFI_USERNAME)
  # - password: UniFi controller password (env: UNIFI_PASSWORD)
  # - api_url: UniFi controller API URL (env: UNIFI_API)
  # - allow_insecure: Allow insecure TLS connections (default: false)

  # Using environment variables for credentials
  # These can be stubbed for plan-only operations
  username = var.unifi_username
  password = var.unifi_password
  api_url  = var.unifi_api_url

  # Allow insecure connections for lab/development environments
  allow_insecure = var.unifi_allow_insecure
}

# Site Configuration
# Site details are loaded from the tfvars file
locals {
  site_name = var.site_name
  site_slug = var.site_slug
}

# UniFi Network Resources
# These resources are managed per site based on tfvars input

# VLANs from NetBox intent
resource "unifi_network" "vlans" {
  for_each = { for vlan in var.vlans : vlan.vlan_id => vlan }

  name    = each.value.name
  purpose = "corporate"

  subnet       = local.vlan_subnets[each.key]
  vlan_id      = each.value.vlan_id
  dhcp_enabled = true

  # Validation: Fail if no subnet is configured for this VLAN
  lifecycle {
    precondition {
      condition     = contains(keys(local.vlan_subnets), each.key)
      error_message = "No subnet prefix found for VLAN ${each.key}. Each VLAN must have a corresponding network prefix."
    }
  }
}

# Map VLANs to their subnet CIDRs from prefixes
locals {
  vlan_subnets = {
    for prefix in var.prefixes :
    prefix.vlan_id => prefix.cidr
    if prefix.vlan_id != null
  }
}

# Outputs for verification
output "site_name" {
  description = "Name of the site being configured"
  value       = local.site_name
}

output "site_slug" {
  description = "Slug identifier for the site"
  value       = local.site_slug
}

output "configured_vlans" {
  description = "List of VLAN IDs configured for this site"
  value       = [for vlan in var.vlans : vlan.vlan_id]
}

output "configured_networks" {
  description = "List of network CIDRs configured for this site"
  value       = [for prefix in var.prefixes : prefix.cidr]
}
