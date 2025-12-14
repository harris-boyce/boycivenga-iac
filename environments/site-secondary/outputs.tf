output "ubiquiti_site_id" {
  description = "UniFi site ID"
  value       = module.ubiquiti.site_id
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
