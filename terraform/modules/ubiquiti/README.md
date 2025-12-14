# Ubiquiti Network Module

This module manages Ubiquiti UniFi network equipment including networks, WLANs, firewall rules, and port profiles.

## Features

- Network/VLAN management
- Wireless network (WLAN) configuration
- Firewall rule management
- Switch port profile configuration
- Multi-site support

## Usage

```hcl
module "ubiquiti" {
  source = "../../terraform/modules/ubiquiti"

  unifi_api_url  = "https://unifi.example.com:8443"
  unifi_username = var.unifi_username
  unifi_password = var.unifi_password
  site_name      = "default"

  networks = [
    {
      name         = "Management"
      purpose      = "corporate"
      vlan_id      = 10
      subnet       = "10.10.10.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.10.10.100"
      dhcp_stop    = "10.10.10.254"
      domain_name  = "mgmt.local"
    },
    {
      name         = "IoT"
      purpose      = "corporate"
      vlan_id      = 20
      subnet       = "10.10.20.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.10.20.100"
      dhcp_stop    = "10.10.20.254"
    }
  ]

  wlans = [
    {
      name       = "Home-WiFi"
      security   = "wpapsk"
      passphrase = var.wifi_password
      wlan_band  = "both"
    },
    {
      name       = "Guest-WiFi"
      security   = "wpapsk"
      passphrase = var.guest_wifi_password
      is_guest   = true
      wlan_band  = "both"
    }
  ]

  firewall_rules = [
    {
      name             = "Block IoT to LAN"
      action           = "drop"
      protocol         = "all"
      src_network_type = "ADDRv4"
      dst_network_type = "ADDRv4"
      enabled          = true
      rule_index       = 2000
    }
  ]

  port_profiles = [
    {
      name         = "Access Point"
      native_vlan  = 10
      tagged_vlans = [20, 30]
      poe_mode     = "auto"
    }
  ]
}
```

## Requirements

- Terraform >= 1.6.0
- UniFi Controller with API access
- UniFi Terraform Provider

## Inputs

See [variables.tf](variables.tf) for detailed input descriptions.

## Outputs

See [outputs.tf](outputs.tf) for available outputs.

## Notes

- Store credentials securely using Terraform variables or secrets management
- Test firewall rules carefully to avoid locking yourself out
- VLAN IDs must be unique across the site
- Port profiles require networks to be created first
