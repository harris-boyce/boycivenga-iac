output "ubiquiti_site_name" {
  description = "UniFi site name"
  value       = module.ubiquiti.site_name
}

output "ubiquiti_networks" {
  description = "Created network IDs"
  value       = module.ubiquiti.network_ids
}

output "homebridge_url" {
  description = "URL to access Homebridge UI"
  value       = module.homebridge.homebridge_url
}

output "automation_summary" {
  description = "Summary of automation configuration"
  value       = module.automation.automation_summary
}
