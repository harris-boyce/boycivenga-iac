variable "vm_name" {
  description = "Name of the Homebridge VM"
  type        = string
  default     = "homebridge"
}

variable "vm_memory" {
  description = "Memory allocation for VM in MB"
  type        = number
  default     = 2048
}

variable "vm_cpus" {
  description = "Number of CPUs for the VM"
  type        = number
  default     = 2
}

variable "vm_disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

variable "vm_network" {
  description = "Network to attach the VM to"
  type        = string
}

variable "vm_ip_address" {
  description = "Static IP address for the VM"
  type        = string
}

variable "vm_gateway" {
  description = "Gateway IP address"
  type        = string
}

variable "vm_dns_servers" {
  description = "List of DNS servers"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "homebridge_config" {
  description = "Homebridge configuration as JSON string"
  type        = string
  default     = "{}"
}

variable "homebridge_plugins" {
  description = "List of Homebridge plugins to install"
  type        = list(string)
  default     = []
}

variable "enable_monitoring" {
  description = "Enable monitoring for the VM"
  type        = bool
  default     = true
}

variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_schedule" {
  description = "Backup schedule in cron format"
  type        = string
  default     = "0 2 * * *"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
