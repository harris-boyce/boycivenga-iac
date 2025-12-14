# Smart Home Automation Configuration Module

locals {
  automation_configs = {
    for automation in var.automations : automation.name => automation
  }

  script_configs = {
    for script in var.scripts : script.name => script
  }

  scene_configs = {
    for scene in var.scenes : scene.name => scene
  }

  group_configs = {
    for group in var.groups : group.name => group
  }

  notification_configs = {
    for notification in var.notifications : notification.name => notification
  }

  integration_configs = {
    for integration in var.integrations : integration.name => integration
  }

  common_tags = merge(
    var.tags,
    {
      "managed-by" = "terraform"
      "platform"   = var.automation_platform
    }
  )
}

# Automation configurations
resource "null_resource" "automations" {
  for_each = local.automation_configs

  triggers = {
    name        = each.value.name
    description = each.value.description
    enabled     = each.value.enabled
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Automation: ${each.value.name}"
      echo "  Description: ${coalesce(each.value.description, "N/A")}"
      echo "  Enabled: ${each.value.enabled}"
      echo "  Mode: ${each.value.mode}"
    EOT
  }
}

# Script configurations
resource "null_resource" "scripts" {
  for_each = local.script_configs

  triggers = {
    name        = each.value.name
    description = each.value.description
    enabled     = each.value.enabled
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Script: ${each.value.name}"
      echo "  Description: ${coalesce(each.value.description, "N/A")}"
      echo "  Enabled: ${each.value.enabled}"
    EOT
  }
}

# Scene configurations
resource "null_resource" "scenes" {
  for_each = local.scene_configs

  triggers = {
    name        = each.value.name
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = "echo 'Scene: ${each.value.name}'"
  }
}

# Group configurations
resource "null_resource" "groups" {
  for_each = local.group_configs

  triggers = {
    name        = each.value.name
    entities    = join(",", each.value.entities)
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Group: ${each.value.name}"
      echo "  Entities: ${join(", ", each.value.entities)}"
    EOT
  }
}

# Notification configurations
resource "null_resource" "notifications" {
  for_each = local.notification_configs

  triggers = {
    name        = each.value.name
    platform    = each.value.platform
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Notification: ${each.value.name}"
      echo "  Platform: ${each.value.platform}"
    EOT
  }
}

# Integration configurations
resource "null_resource" "integrations" {
  for_each = local.integration_configs

  triggers = {
    name        = each.value.name
    platform    = each.value.platform
    config_hash = md5(jsonencode(each.value))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Integration: ${each.value.name}"
      echo "  Platform: ${each.value.platform}"
    EOT
  }
}

# Generate automation configuration file
resource "null_resource" "config_file" {
  depends_on = [
    null_resource.automations,
    null_resource.scripts,
    null_resource.scenes,
    null_resource.groups
  ]

  triggers = {
    automation_count  = length(var.automations)
    script_count      = length(var.scripts)
    scene_count       = length(var.scenes)
    group_count       = length(var.groups)
    notification_count = length(var.notifications)
    integration_count  = length(var.integrations)
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Automation Configuration Summary:"
      echo "  Automations: ${length(var.automations)}"
      echo "  Scripts: ${length(var.scripts)}"
      echo "  Scenes: ${length(var.scenes)}"
      echo "  Groups: ${length(var.groups)}"
      echo "  Notifications: ${length(var.notifications)}"
      echo "  Integrations: ${length(var.integrations)}"
    EOT
  }
}
