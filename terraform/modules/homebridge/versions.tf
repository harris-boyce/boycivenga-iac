terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # Using a generic provider - adjust based on your VM platform
    # Could be proxmox, vsphere, etc.
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}
