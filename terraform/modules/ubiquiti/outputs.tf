output "site_id" {
  description = "ID of the UniFi site"
  value       = data.unifi_site.main.id
}

output "site_name" {
  description = "Name of the UniFi site"
  value       = data.unifi_site.main.name
}

output "network_ids" {
  description = "Map of network names to their IDs"
  value       = { for k, v in unifi_network.networks : k => v.id }
}

output "wlan_ids" {
  description = "Map of WLAN names to their IDs"
  value       = { for k, v in unifi_wlan.wlans : k => v.id }
}

output "firewall_rule_ids" {
  description = "Map of firewall rule names to their IDs"
  value       = { for k, v in unifi_firewall_rule.rules : k => v.id }
}

output "port_profile_ids" {
  description = "Map of port profile names to their IDs"
  value       = { for k, v in unifi_port_profile.profiles : k => v.id }
}
