variable "unifi_api_url" {
  description = "URL of the UniFi Controller API"
  type        = string
}

variable "unifi_username" {
  description = "Username for UniFi Controller authentication"
  type        = string
  sensitive   = true
}

variable "unifi_password" {
  description = "Password for UniFi Controller authentication"
  type        = string
  sensitive   = true
}

variable "site_name" {
  description = "Name of the UniFi site to manage"
  type        = string
  default     = "default"
}

variable "networks" {
  description = "List of networks to create"
  type = list(object({
    name         = string
    purpose      = string
    vlan_id      = number
    subnet       = string
    dhcp_enabled = optional(bool, true)
    dhcp_start   = optional(string)
    dhcp_stop    = optional(string)
    domain_name  = optional(string)
  }))
  default = []
}

variable "wlans" {
  description = "List of wireless networks to create"
  type = list(object({
    name          = string
    security      = string
    passphrase    = optional(string)
    network_id    = optional(string)
    user_group_id = optional(string)
    hide_ssid     = optional(bool, false)
    is_guest      = optional(bool, false)
    wlan_band     = optional(string, "both")
  }))
  default = []
}

variable "firewall_rules" {
  description = "List of firewall rules to create"
  type = list(object({
    name             = string
    ruleset          = optional(string, "LAN_IN")
    action           = string
    protocol         = string
    src_network_id   = optional(string)
    src_network_type = optional(string)
    dst_network_id   = optional(string)
    dst_network_type = optional(string)
    dst_port         = optional(string)
    enabled          = optional(bool, true)
    rule_index       = optional(number)
  }))
  default = []
}

variable "port_profiles" {
  description = "List of port profiles to create"
  type = list(object({
    name         = string
    native_vlan  = optional(number)
    tagged_vlans = optional(list(number), [])
    poe_mode     = optional(string, "auto")
  }))
  default = []
}
