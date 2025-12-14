output "automation_names" {
  description = "List of automation names"
  value       = [for a in var.automations : a.name]
}

output "script_names" {
  description = "List of script names"
  value       = [for s in var.scripts : s.name]
}

output "scene_names" {
  description = "List of scene names"
  value       = [for s in var.scenes : s.name]
}

output "group_names" {
  description = "List of group names"
  value       = [for g in var.groups : g.name]
}

output "notification_platforms" {
  description = "List of notification platforms configured"
  value       = [for n in var.notifications : n.platform]
}

output "integration_platforms" {
  description = "List of integration platforms configured"
  value       = [for i in var.integrations : i.platform]
}

output "automation_summary" {
  description = "Summary of automation configuration"
  value = {
    platform           = var.automation_platform
    automation_count   = length(var.automations)
    script_count       = length(var.scripts)
    scene_count        = length(var.scenes)
    group_count        = length(var.groups)
    notification_count = length(var.notifications)
    integration_count  = length(var.integrations)
  }
}
