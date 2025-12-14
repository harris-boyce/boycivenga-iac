provider "unifi" {
  api_url  = var.unifi_api_url
  username = var.unifi_username
  password = var.unifi_password
  site     = var.site_name
}

# Create networks
resource "unifi_network" "networks" {
  for_each = { for net in var.networks : net.name => net }

  name    = each.value.name
  purpose = each.value.purpose

  vlan_id = each.value.vlan_id
  subnet  = each.value.subnet

  dhcp_enabled = each.value.dhcp_enabled
  dhcp_start   = each.value.dhcp_start
  dhcp_stop    = each.value.dhcp_stop
  domain_name  = each.value.domain_name
}

# Create WLANs
resource "unifi_wlan" "wlans" {
  for_each = { for wlan in var.wlans : wlan.name => wlan }

  name       = each.value.name
  security   = each.value.security
  passphrase = each.value.passphrase

  network_id    = each.value.network_id != null ? each.value.network_id : null
  user_group_id = each.value.user_group_id
  hide_ssid     = each.value.hide_ssid
  is_guest      = each.value.is_guest
  wlan_band     = each.value.wlan_band
}

# Create firewall rules
resource "unifi_firewall_rule" "rules" {
  for_each = { for rule in var.firewall_rules : rule.name => rule }

  name     = each.value.name
  ruleset  = each.value.ruleset
  action   = each.value.action
  protocol = each.value.protocol

  src_network_id   = each.value.src_network_id
  src_network_type = each.value.src_network_type
  dst_network_id   = each.value.dst_network_id
  dst_network_type = each.value.dst_network_type
  dst_port         = each.value.dst_port
  enabled          = each.value.enabled
  rule_index       = each.value.rule_index
}

# Create port profiles
resource "unifi_port_profile" "profiles" {
  for_each = { for profile in var.port_profiles : profile.name => profile }

  name = each.value.name

  native_networkconf_id = each.value.native_vlan != null ? lookup(
    { for k, v in unifi_network.networks : v.vlan_id => v.id },
    each.value.native_vlan,
    null
  ) : null

  tagged_networkconf_ids = [
    for vlan_id in each.value.tagged_vlans :
    lookup(
      { for k, v in unifi_network.networks : v.vlan_id => v.id },
      vlan_id,
      null
    )
    if lookup(
      { for k, v in unifi_network.networks : v.vlan_id => v.id },
      vlan_id,
      null
    ) != null
  ]

  poe_mode = each.value.poe_mode
}
