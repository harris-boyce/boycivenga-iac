# Homebridge VM Module

This module manages a Homebridge VM for HomeKit integration.

## Features

- VM configuration for Homebridge
- Automated Homebridge installation
- Plugin management
- Configuration management
- Optional monitoring integration
- Automated backups

## Usage

```hcl
module "homebridge" {
  source = "../../terraform/modules/homebridge"

  vm_name       = "homebridge-main"
  vm_memory     = 2048
  vm_cpus       = 2
  vm_disk_size  = 20
  vm_network    = "Management"
  vm_ip_address = "10.10.10.50"
  vm_gateway    = "10.10.10.1"

  homebridge_config = jsonencode({
    bridge = {
      name         = "Homebridge"
      username     = "CC:22:3D:E3:CE:30"
      port         = 51826
      pin          = "031-45-154"
    }
    platforms = [
      {
        platform = "config"
        name     = "Config"
        port     = 8581
      }
    ]
  })

  homebridge_plugins = [
    "homebridge-ring",
    "homebridge-nest",
    "homebridge-hue"
  ]

  enable_monitoring = true
  backup_enabled    = true
  backup_schedule   = "0 2 * * *"

  tags = {
    environment = "production"
    service     = "smart-home"
  }
}
```

## Customization

This module uses `null_resource` as a placeholder. Customize it for your hypervisor:

- **Proxmox**: Use `bpg/proxmox` provider
- **VMware**: Use `hashicorp/vsphere` provider
- **Hyper-V**: Use appropriate provider

## Requirements

- Terraform >= 1.6.0
- VM platform with Terraform provider support

## Inputs

See [variables.tf](variables.tf) for detailed input descriptions.

## Outputs

See [outputs.tf](outputs.tf) for available outputs.

## Notes

- Default Homebridge UI port is 8581
- Default HomeKit port is 51826
- Ensure network allows mDNS/Bonjour for HomeKit discovery
- Store sensitive configuration (PIN, credentials) securely
