output "vm_name" {
  description = "Name of the Homebridge VM"
  value       = var.vm_name
}

output "vm_ip_address" {
  description = "IP address of the Homebridge VM"
  value       = var.vm_ip_address
}

output "homebridge_url" {
  description = "URL to access Homebridge UI"
  value       = "http://${var.vm_ip_address}:8581"
}

output "vm_configuration" {
  description = "VM configuration summary"
  value = {
    name       = var.vm_name
    memory     = var.vm_memory
    cpus       = var.vm_cpus
    disk_size  = var.vm_disk_size
    ip_address = var.vm_ip_address
    network    = var.vm_network
  }
}

output "monitoring_enabled" {
  description = "Whether monitoring is enabled"
  value       = var.enable_monitoring
}

output "backup_enabled" {
  description = "Whether backups are enabled"
  value       = var.backup_enabled
}
