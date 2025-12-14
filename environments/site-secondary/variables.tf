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
  description = "Name of the secondary site"
  type        = string
  default     = "secondary"
}

variable "wifi_password" {
  description = "Password for main WiFi network"
  type        = string
  sensitive   = true
}

variable "guest_wifi_password" {
  description = "Password for guest WiFi network"
  type        = string
  sensitive   = true
}
