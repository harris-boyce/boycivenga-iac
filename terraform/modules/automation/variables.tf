variable "automation_platform" {
  description = "Automation platform to use (home-assistant, node-red, etc.)"
  type        = string
  default     = "home-assistant"

  validation {
    condition     = contains(["home-assistant", "node-red", "custom"], var.automation_platform)
    error_message = "Automation platform must be one of: home-assistant, node-red, custom"
  }
}

variable "automation_name" {
  description = "Name of the automation configuration"
  type        = string
}

variable "automations" {
  description = "List of automation configurations"
  type = list(object({
    name        = string
    description = optional(string)
    trigger     = any
    condition   = optional(any)
    action      = any
    mode        = optional(string, "single")
    enabled     = optional(bool, true)
  }))
  default = []
}

variable "scripts" {
  description = "List of automation scripts"
  type = list(object({
    name        = string
    description = optional(string)
    sequence    = list(any)
    mode        = optional(string, "single")
    enabled     = optional(bool, true)
  }))
  default = []
}

variable "scenes" {
  description = "List of scenes"
  type = list(object({
    name     = string
    entities = map(any)
  }))
  default = []
}

variable "groups" {
  description = "List of entity groups"
  type = list(object({
    name     = string
    entities = list(string)
  }))
  default = []
}

variable "notifications" {
  description = "Notification configurations"
  type = list(object({
    name     = string
    platform = string
    config   = map(any)
  }))
  default = []
}

variable "integrations" {
  description = "Third-party integrations to configure"
  type = list(object({
    name     = string
    platform = string
    config   = map(any)
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to automation resources"
  type        = map(string)
  default     = {}
}
