# Secondary Site Configuration

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
      subnet       = "10.20.10.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.20.10.100"
      dhcp_stop    = "10.20.10.254"
      domain_name  = "mgmt.local"
    },
    {
      name         = "IoT"
      purpose      = "corporate"
      vlan_id      = 20
      subnet       = "10.20.20.0/24"
      dhcp_enabled = true
      dhcp_start   = "10.20.20.100"
      dhcp_stop    = "10.20.20.254"
      domain_name  = "iot.local"
    }
  ]

  wlans = [
    {
      name       = "Home-WiFi-Secondary"
      security   = "wpapsk"
      passphrase = var.wifi_password
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
}

module "automation" {
  source = "../../terraform/modules/automation"

  automation_platform = "home-assistant"
  automation_name     = "secondary-site"

  automations = [
    {
      name        = "security-away"
      description = "Enable security when away"
      trigger = {
        platform  = "state"
        entity_id = "binary_sensor.presence"
        to        = "off"
      }
      action = {
        service = "alarm_control_panel.alarm_arm_away"
        target = {
          entity_id = "alarm_control_panel.home"
        }
      }
      enabled = true
    }
  ]

  tags = {
    site = "secondary"
  }
}
