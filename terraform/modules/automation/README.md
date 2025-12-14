# Smart Home Automation Module

This module manages smart home automation configurations including automations, scripts, scenes, and integrations.

## Features

- Automation rule management
- Script definitions
- Scene configurations
- Entity grouping
- Notification configurations
- Third-party integrations
- Support for multiple automation platforms

## Usage

```hcl
module "automation" {
  source = "../../terraform/modules/automation"

  automation_platform = "home-assistant"
  automation_name     = "home-automations"

  automations = [
    {
      name        = "morning-routine"
      description = "Morning routine automation"
      trigger = {
        platform = "time"
        at       = "07:00:00"
      }
      action = {
        service = "light.turn_on"
        target = {
          entity_id = "light.bedroom"
        }
        data = {
          brightness_pct = 50
        }
      }
      mode    = "single"
      enabled = true
    },
    {
      name        = "motion-lights"
      description = "Turn on lights when motion detected"
      trigger = {
        platform = "state"
        entity_id = "binary_sensor.motion"
        to        = "on"
      }
      action = {
        service = "light.turn_on"
        target = {
          entity_id = "light.hallway"
        }
      }
      mode    = "single"
      enabled = true
    }
  ]

  scripts = [
    {
      name        = "bedtime"
      description = "Execute bedtime routine"
      sequence = [
        {
          service = "light.turn_off"
          target = {
            entity_id = "group.all_lights"
          }
        },
        {
          service = "lock.lock"
          target = {
            entity_id = "lock.front_door"
          }
        }
      ]
      mode = "single"
    }
  ]

  scenes = [
    {
      name = "movie-time"
      entities = {
        "light.living_room" = {
          state      = "on"
          brightness = 10
        }
        "light.kitchen" = {
          state = "off"
        }
      }
    }
  ]

  groups = [
    {
      name = "all-lights"
      entities = [
        "light.living_room",
        "light.bedroom",
        "light.kitchen"
      ]
    }
  ]

  notifications = [
    {
      name     = "mobile-notifications"
      platform = "mobile_app"
      config = {
        name = "my_phone"
      }
    }
  ]

  integrations = [
    {
      name     = "weather"
      platform = "met"
      config = {
        latitude  = 51.5074
        longitude = -0.1278
      }
    }
  ]

  tags = {
    environment = "production"
  }
}
```

## Supported Platforms

- **Home Assistant**: Full-featured home automation
- **Node-RED**: Flow-based automation
- **Custom**: Custom automation platform

## Requirements

- Terraform >= 1.6.0

## Inputs

See [variables.tf](variables.tf) for detailed input descriptions.

## Outputs

See [outputs.tf](outputs.tf) for available outputs.

## Notes

- Automations support various trigger types (time, state, event, etc.)
- Scripts can have multiple steps in sequence
- Scenes define desired states for multiple entities
- Groups help organize and control multiple entities together
- Store sensitive integration credentials securely using Terraform secrets
