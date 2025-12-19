# Variable definitions for site-specific Terraform deployments
# Values are provided via tfvars files generated from NetBox exports

# UniFi Provider Configuration Variables
variable "unifi_username" {
  description = "UniFi controller username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "unifi_password" {
  description = "UniFi controller password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "unifi_api_url" {
  description = "UniFi controller API URL"
  type        = string
  default     = "https://unifi.local:8443"
}

variable "unifi_allow_insecure" {
  description = "Allow insecure TLS connections to UniFi controller"
  type        = bool
  default     = false
}

# Site Information
variable "site_name" {
  description = "Human-readable name of the site"
  type        = string
}

variable "site_slug" {
  description = "Machine-readable slug identifier for the site"
  type        = string
}

variable "site_description" {
  description = "Description of the site"
  type        = string
  default     = ""
}

# VLANs Configuration
variable "vlans" {
  description = "List of VLANs to configure at this site"
  type = list(object({
    vlan_id     = number
    name        = string
    description = string
    status      = string
  }))
  default = []
}

# Network Prefixes Configuration
variable "prefixes" {
  description = "List of network prefixes (IP ranges) for this site"
  type = list(object({
    cidr        = string
    vlan_id     = number
    description = string
    status      = string
  }))
  default = []
}

# Tags (Optional Metadata)
variable "tags" {
  description = "List of tags from NetBox for organizing resources"
  type = list(object({
    name        = string
    slug        = string
    description = string
    color       = string
  }))
  default = []
}
