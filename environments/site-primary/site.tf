# Primary Site Configuration

module "ubiquiti" {
  source = "../../terraform/modules/ubiquiti"

  unifi_api_url  = var.unifi_api_url
  unifi_username = var.unifi_username
  unifi_password = var.unifi_password
  site_name      = var.site_name

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
      domain_name  = "iot.local"
    },
    {
      name         = "Guest"
      purpose      = "guest"
      vlan_id      = 30
      subnet       = "10.10.30.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.10.30.100"
      dhcp_stop    = "10.10.30.254"
    }
  ]

  wlans = [
    {
      name       = "Home-WiFi"
      security   = "wpapsk"
      passphrase = var.wifi_password
      wlan_band  = "both"
      hide_ssid  = false
    },
    {
      name       = "Guest-WiFi"
      security   = "wpapsk"
      passphrase = var.guest_wifi_password
      is_guest   = true
      wlan_band  = "both"
      hide_ssid  = false
    }
  ]

  firewall_rules = [
    {
      name             = "Block IoT to Management"
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
      name         = "Access-Point"
      native_vlan  = 10
      tagged_vlans = [20, 30]
      poe_mode     = "auto"
    },
    {
      name        = "IoT-Device"
      native_vlan = 20
      poe_mode    = "auto"
    }
  ]
}

module "homebridge" {
  source = "../../terraform/modules/homebridge"

  vm_name       = "homebridge-primary"
  vm_memory     = 2048
  vm_cpus       = 2
  vm_disk_size  = 20
  vm_network    = "Management"
  vm_ip_address = "10.10.10.50"
  vm_gateway    = "10.10.10.1"

  homebridge_config = jsonencode({
    bridge = {
      name     = "Homebridge Primary"
      username = "CC:22:3D:E3:CE:30"
      port     = 51826
      pin      = "031-45-154"
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
    "homebridge-nest"
  ]

  enable_monitoring = true
  backup_enabled    = true

  tags = {
    site        = "primary"
    environment = "production"
  }
}

module "automation" {
  source = "../../terraform/modules/automation"

  automation_platform = "home-assistant"
  automation_name     = "primary-site"

  automations = [
    {
      name        = "morning-lights"
      description = "Turn on lights in the morning"
      trigger = {
        platform = "time"
        at       = "07:00:00"
      }
      action = {
        service = "light.turn_on"
        target = {
          entity_id = "group.morning_lights"
        }
      }
      enabled = true
    },
    {
      name        = "night-security"
      description = "Enable security mode at night"
      trigger = {
        platform = "time"
        at       = "22:00:00"
      }
      action = {
        service = "alarm_control_panel.alarm_arm_night"
        target = {
          entity_id = "alarm_control_panel.home"
        }
      }
      enabled = true
    }
  ]

  scripts = [
    {
      name        = "all-off"
      description = "Turn off all devices"
      sequence = [
        {
          service = "light.turn_off"
          target = {
            entity_id = "group.all_lights"
          }
        }
      ]
    }
  ]

  groups = [
    {
      name = "morning-lights"
      entities = [
        "light.kitchen",
        "light.living_room"
      ]
    }
  ]

  tags = {
    site = "primary"
  }
}
